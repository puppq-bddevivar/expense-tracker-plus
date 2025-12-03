import secrets
from datetime import datetime, timedelta

from passlib.context import CryptContext
from sqlalchemy.orm import joinedload

from lib.db import provide_session
from lib.models import (
    Biller,
    Bill,
    Payment,
    PaymentHistory,
    UserAuth,
    UserProfile,
    LoginAttempt,
    PasswordResetToken,
)

# --- Auth Helpers ---

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def check_rate_limit(username):
    """
    Check if the username has exceeded 10 failed login attempts in the last 24 hours.
    Returns True if login is allowed, False if blocked.
    """
    with provide_session() as db:
        cutoff_time = datetime.now() - timedelta(hours=24)
        failed_count = (
            db.query(LoginAttempt)
            .filter(
                LoginAttempt.username == username,
                LoginAttempt.success == False,
                LoginAttempt.attempt_time >= cutoff_time,
            )
            .count()
        )
        return failed_count < 10


def log_login_attempt(username, success):
    """Log a login attempt."""
    with provide_session() as db:
        attempt = LoginAttempt(username=username, success=success)
        db.add(attempt)
        db.commit()


def hash_password(password):
    """Hash a password for storing."""
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    """Verify a stored password against one provided by user."""
    return pwd_context.verify(plain_password, hashed_password)


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


def authenticate_user(username, password):
    with provide_session() as db:
        user = db.query(UserAuth).filter_by(username=username).first()
        if not user:
            return None
        if verify_password(user.password_hash, password):
            return user
        return None


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
        # No relationships to eager load here currently, but good practice to expunge
        # if we want them to be usable after session close without lazy load errors.
        rows = (
            db.query(Biller)
            .filter(Biller.user_id == user_id)
            .order_by(Biller.name)
            .all()
        )
        # Determine if we need to eagerly load relationships.
        # Currently Biller doesn't have parents accessed in UI list.
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
        # Use joinedload to fetch the related 'biller' object immediately.
        # This prevents DetachedInstanceError when accessing bill.biller.name in the UI.
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

        # Recalculate balance in case amount changed
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
        # Retrieve bill first to get snapshot data for history
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
        # Flush to generate ID and ensure payment is visible in relationship calculation
        db.flush()

        # Calculate total paid including the new payment
        total_paid = sum([pay.amount for pay in bill.payments])

        # Update balance amount
        bill.balance_amount = bill.amount - total_paid

        final_status = "partial"
        if total_paid >= bill.amount:
            bill.status = "paid"
            final_status = "paid"
        elif 0 < total_paid < bill.amount:
            bill.status = "partial"
            final_status = "partial"

        # Create Payment History Log (Snapshot)
        history = PaymentHistory(
            user_id=user_id,
            bill_id=bill.id,
            biller_name=bill.biller.name if bill.biller else "Unknown",
            amount=amount,
            balance_amount=bill.balance_amount,
            due_date=bill.due_date,
            paid_on=paid_on,
            status=final_status,  # Use the calculated status (partial or paid)
            method=method,
            reference=reference,
        )
        db.add(history)

        db.commit()
        db.refresh(p)
        return p


def list_payments(user_id):
    with provide_session() as db:
        # Eager load Bill and Bill.biller to display biller name in history
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
