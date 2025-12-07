from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Date,
    ForeignKey,
    Text,
    DateTime,
    Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from lib.db import Base


class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, index=True)
    attempt_time = Column(DateTime, server_default=func.now())
    success = Column(Boolean, default=False)

    def __repr__(self):
        return f"<LoginAttempt(username='{self.username}', success={self.success}, time='{self.attempt_time}')>"


class UserAuth(Base):
    __tablename__ = "user_auth"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    profile = relationship(
        "UserProfile",
        back_populates="auth",
        uselist=False,
        cascade="all, delete-orphan",
    )
    billers = relationship("Biller", back_populates="user")
    reset_tokens = relationship("PasswordResetToken", back_populates="user")

    def __repr__(self):
        return f"<UserAuth(id={self.id}, username='{self.username}')>"


class UserProfile(Base):
    __tablename__ = "user_profile"
    id = Column(Integer, primary_key=True)
    user_auth_id = Column(Integer, ForeignKey("user_auth.id"), nullable=False)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)

    auth = relationship("UserAuth", back_populates="profile")

    def __repr__(self):
        return f"<UserProfile(id={self.id}, email='{self.email}')>"


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user_auth.id"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)

    user = relationship("UserAuth", back_populates="reset_tokens")

    def __repr__(self):
        return f"<PasswordResetToken(user_id={self.user_id}, expires_at='{self.expires_at}')>"


class Biller(Base):
    __tablename__ = "billers"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user_auth.id"), nullable=False)
    name = Column(String, nullable=False)
    biller_type = Column(String)
    account = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("UserAuth", back_populates="billers")
    bills = relationship("Bill", back_populates="biller", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Biller(id={self.id}, name='{self.name}')>"


class Bill(Base):
    __tablename__ = "bills"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user_auth.id"), nullable=False)
    # Enforce that a bill must belong to a biller
    biller_id = Column(Integer, ForeignKey("billers.id"), nullable=False)
    # Use Numeric for money to avoid float precision errors
    amount = Column(Numeric(10, 2), nullable=False)
    balance_amount = Column(Numeric(10, 2))
    due_date = Column(Date, nullable=False)
    period_month = Column(Integer)
    period_year = Column(Integer)
    status = Column(String, default="unpaid")
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    biller = relationship("Biller", back_populates="bills")
    payments = relationship(
        "Payment", back_populates="bill", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Bill(id={self.id}, amount={self.amount}, status='{self.status}')>"


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user_auth.id"), nullable=False)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    paid_on = Column(Date)
    status = Column(String)
    method = Column(String)
    reference = Column(String)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    bill = relationship("Bill", back_populates="payments")

    def __repr__(self):
        return f"<Payment(id={self.id}, amount={self.amount}, date='{self.paid_on}')>"


class PaymentHistory(Base):
    __tablename__ = "payment_history"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user_auth.id"), nullable=False)
    bill_id = Column(Integer, nullable=False)  # Snapshot of ID, no FK
    biller_name = Column(String)
    amount = Column(Numeric(10, 2))
    balance_amount = Column(Numeric(10, 2))
    due_date = Column(Date)
    paid_on = Column(Date)
    status = Column(String)
    method = Column(String)
    reference = Column(String)
    transaction_timestamp = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<PaymentHistory(id={self.id}, bill_id={self.bill_id}, amount={self.amount})>"
