from datetime import date

from sqlalchemy.orm import joinedload

from lib.db import provide_session
from lib.models import Biller, Bill, Payment, PaymentHistory


# CRUD helpers


def add_biller(name, biller_type=None, account=None, notes=None):
    with provide_session() as db:
        b = Biller(name=name, biller_type=biller_type, account=account, notes=notes)
        db.add(b)
        db.commit()
        db.refresh(b)
        return b


def list_billers():
    with provide_session() as db:
        # No relationships to eager load here currently, but good practice to expunge
        # if we want them to be usable after session close without lazy load errors.
        rows = db.query(Biller).order_by(Biller.name).all()
        # Determine if we need to eagerly load relationships.
        # Currently Biller doesn't have parents accessed in UI list.
        return rows


def update_biller(biller_id, name, biller_type=None, account=None, notes=None):
    with provide_session() as db:
        biller = db.query(Biller).get(biller_id)
        if not biller:
            raise ValueError(f"Biller with ID {biller_id} not found")
        biller.name = name
        biller.biller_type = biller_type
        biller.account = account
        biller.notes = notes
        db.commit()


def delete_biller(biller_id):
    with provide_session() as db:
        biller = db.query(Biller).get(biller_id)
        if not biller:
            raise ValueError(f"Biller with ID {biller_id} not found")
        db.delete(biller)
        db.commit()


def add_bill(
    biller_id, amount, due_date, period_month=None, period_year=None, notes=None
):
    with provide_session() as db:
        bill = Bill(
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


def list_bills():
    with provide_session() as db:
        # Use joinedload to fetch the related 'biller' object immediately.
        # This prevents DetachedInstanceError when accessing bill.biller.name in the UI.
        rows = (
            db.query(Bill)
            .options(joinedload(Bill.biller))
            .order_by(Bill.due_date)
            .all()
        )
        return rows


def list_unpaid_bills():
    with provide_session() as db:
        rows = (
            db.query(Bill)
            .options(joinedload(Bill.biller))
            .filter(Bill.status != "paid")
            .order_by(Bill.due_date)
            .all()
        )
        return rows


def update_bill(
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
        bill = db.query(Bill).get(bill_id)
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


def delete_bill(bill_id):
    with provide_session() as db:
        bill = db.query(Bill).get(bill_id)
        if not bill:
            raise ValueError(f"Bill with ID {bill_id} not found")
        db.delete(bill)
        db.commit()


def add_payment(
    bill_id, amount, paid_on=None, method=None, reference=None, notes=None, status=None
):
    if paid_on is None:
        paid_on = date.today()

    with provide_session() as db:
        # Retrieve bill first to get snapshot data for history
        bill = db.query(Bill).options(joinedload(Bill.biller)).get(bill_id)

        p = Payment(
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


def list_payments():
    with provide_session() as db:
        # Eager load Bill and Bill.biller to display biller name in history
        rows = (
            db.query(Payment)
            .options(joinedload(Payment.bill).joinedload(Bill.biller))
            .order_by(Payment.paid_on.desc())
            .all()
        )
        return rows


def list_payment_history():
    with provide_session() as db:
        rows = (
            db.query(PaymentHistory)
            .order_by(PaymentHistory.transaction_timestamp.desc())
            .all()
        )
        return rows
