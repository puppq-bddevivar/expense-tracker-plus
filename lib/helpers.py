import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import joinedload
import streamlit_authenticator as stauth

from lib.db import provide_session
from lib.models import (
    Biller,
    Bill,
    Payment,
    PaymentHistory,
    UserAuth,
    UserProfile,
    PasswordResetToken,
)

# --- Auth Helpers ---


def hash_password(password: str) -> str:
    """Hash a password for storing."""
    return stauth.Hasher().hash(password)


def register_user(username, password, full_name=None, email=None):
    with provide_session() as db:
        if db.query(UserAuth).filter_by(username=username).first():
            raise ValueError("Username already exists")

        hashed = hash_password(password)
        user = UserAuth(username=username, password_hash=hashed)
        db.add(user)
        db.flush()  # Generate ID

        profile = UserProfile(user_auth_id=user.id, full_name=full_name, email=email)
        db.add(profile)
        db.commit()
        return user


def create_password_reset_token(user_id: int) -> str:
    """Generate and store a password reset token."""
    with provide_session() as db:
        # Invalidate any existing tokens for this user
        db.query(PasswordResetToken).filter_by(user_id=user_id).delete()

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=1)
        reset_token = PasswordResetToken(
            user_id=user_id, token=token, expires_at=expires_at
        )
        db.add(reset_token)
        db.commit()
        return token


def get_user_by_password_reset_token(token: str):
    """Verify a password reset token and return the user if valid."""
    with provide_session() as db:
        reset_token = db.query(PasswordResetToken).filter_by(token=token).first()
        if not reset_token or reset_token.expires_at < datetime.now():
            return None
        return reset_token.user


def change_user_password(user_id: int, new_password: str):
    """Change a user's password."""
    with provide_session() as db:
        user = db.query(UserAuth).filter_by(id=user_id).first()
        if not user:
            raise ValueError("User not found")
        user.password_hash = hash_password(new_password)
        # Invalidate all reset tokens for the user after password change
        db.query(PasswordResetToken).filter_by(user_id=user_id).delete()
        db.commit()


def get_user_by_username_or_email(identifier: str):
    """Find a user by their username or email."""
    with provide_session() as db:
        user = (
            db.query(UserAuth)
            .join(UserProfile)
            .filter(
                (UserAuth.username == identifier) | (UserProfile.email == identifier)
            )
            .first()
        )
        return user


# CRUD helpers


def add_biller(user_id, name, biller_type=None, account=None, notes=None):
    with provide_session() as db:
        b = Biller(
            user_id=user_id,
            name=name,
            biller_type=biller_type,
            account=account,
            notes=notes,
        )
        db.add(b)
        db.commit()
        db.refresh(b)
        return b


def list_billers(user_id):
    with provide_session() as db:
        rows = (
            db.query(Biller)
            .filter(Biller.user_id == user_id)
            .order_by(Biller.name)
            .all()
        )
        return rows


def update_biller(user_id, biller_id, name, biller_type=None, account=None, notes=None):
    with provide_session() as db:
        biller = (
            db.query(Biller)
            .filter(Biller.id == biller_id, Biller.user_id == user_id)
            .first()
        )
        if not biller:
            raise ValueError(f"Biller with ID {biller_id} not found")
        biller.name = name
        biller.biller_type = biller_type
        biller.account = account
        biller.notes = notes
        db.commit()


def delete_biller(user_id, biller_id):
    with provide_session() as db:
        biller = (
            db.query(Biller)
            .filter(Biller.id == biller_id, Biller.user_id == user_id)
            .first()
        )
        if not biller:
            raise ValueError(f"Biller with ID {biller_id} not found")
        db.delete(biller)
        db.commit()


def add_bill(
    user_id,
    biller_id,
    amount,
    due_date,
    period_month=None,
    period_year=None,
    notes=None,
):
    with provide_session() as db:
        bill = Bill(
            user_id=user_id,
            biller_id=biller_id,
            amount=amount,
            balance_amount=amount,
            due_date=due_date,
            period_month=period_month,
            period_year=period_year,
            notes=notes,
            status="unpaid",
        )
        db.add(bill)
        db.commit()
        db.refresh(bill)
        return bill


def list_bills(user_id):
    with provide_session() as db:
        rows = (
            db.query(Bill)
            .filter(Bill.user_id == user_id)
            .options(joinedload(Bill.biller))
            .order_by(Bill.due_date)
            .all()
        )
        return rows


def list_unpaid_bills(user_id):
    with provide_session() as db:
        rows = (
            db.query(Bill)
            .options(joinedload(Bill.biller))
            .filter(Bill.user_id == user_id, Bill.status != "paid")
            .order_by(Bill.due_date)
            .all()
        )
        return rows


def update_bill(
    user_id,
    bill_id,
    biller_id,
    amount,
    due_date,
    period_month=None,
    period_year=None,
    notes=None,
    status=None,
):
    with provide_session() as db:
        bill = (
            db.query(Bill).filter(Bill.id == bill_id, Bill.user_id == user_id).first()
        )
        if not bill:
            raise ValueError(f"Bill with ID {bill_id} not found")

        bill.biller_id = biller_id
        bill.amount = amount
        bill.due_date = due_date
        bill.period_month = period_month
        bill.period_year = period_year
        bill.notes = notes
        if status:
            bill.status = status

        total_paid = sum([p.amount for p in bill.payments])
        bill.balance_amount = bill.amount - total_paid

        db.commit()


def delete_bill(user_id, bill_id):
    with provide_session() as db:
        bill = (
            db.query(Bill).filter(Bill.id == bill_id, Bill.user_id == user_id).first()
        )
        if not bill:
            raise ValueError(f"Bill with ID {bill_id} not found")
        db.delete(bill)
        db.commit()


def add_payment(
    user_id,
    bill_id,
    amount,
    paid_on=None,
    method=None,
    reference=None,
    notes=None,
    status=None,
):
    if paid_on is None:
        paid_on = datetime.today().date()

    with provide_session() as db:
        bill = (
            db.query(Bill)
            .options(joinedload(Bill.biller))
            .filter(Bill.id == bill_id, Bill.user_id == user_id)
            .first()
        )

        if not bill:
            raise ValueError("Bill not found or access denied")

        p = Payment(
            user_id=user_id,
            bill_id=bill_id,
            amount=amount,
            paid_on=paid_on,
            method=method,
            reference=reference,
            notes=notes,
            status=status,
        )
        db.add(p)
        db.flush()

        total_paid = sum([pay.amount for pay in bill.payments])
        bill.balance_amount = bill.amount - total_paid

        final_status = "partial"
        if total_paid >= bill.amount:
            bill.status = "paid"
            final_status = "paid"
        elif 0 < total_paid < bill.amount:
            bill.status = "partial"
            final_status = "partial"

        history = PaymentHistory(
            user_id=user_id,
            bill_id=bill.id,
            biller_name=bill.biller.name if bill.biller else "Unknown",
            amount=amount,
            balance_amount=bill.balance_amount,
            due_date=bill.due_date,
            paid_on=paid_on,
            status=final_status,
            method=method,
            reference=reference,
        )
        db.add(history)

        db.commit()
        db.refresh(p)
        return p


def list_payments(user_id):
    with provide_session() as db:
        rows = (
            db.query(Payment)
            .filter(Payment.user_id == user_id)
            .options(joinedload(Payment.bill).joinedload(Bill.biller))
            .order_by(Payment.paid_on.desc())
            .all()
        )
        return rows


def list_payment_history(user_id):
    with provide_session() as db:
        rows = (
            db.query(PaymentHistory)
            .filter(PaymentHistory.user_id == user_id)
            .order_by(PaymentHistory.transaction_timestamp.desc())
            .all()
        )
        return rows
