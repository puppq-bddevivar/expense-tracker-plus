from datetime import date
from decimal import Decimal

import pandas as pd
import streamlit as st

from lib.helpers import add_payment, list_payment_history, list_unpaid_bills


def show(user_id):
    st.header("Payments")

    # list_bills now uses eager loading (joinedload) from previous refactoring,
    # so accessing bill.biller.name here is safe.
    bills = list_unpaid_bills(user_id)

    if not bills:
        st.info("No unpaid bills to pay.")
        return

    # Create a descriptive label for the dropdown
    # Format: ID - Biller - Amount [Status]
    bmap = {}
    for b in bills:
        biller_name = b.biller.name if b.biller else "Unknown"
        # Show balance if available (it might be None for old records if migration didn't run, default to amount)
        bal = b.balance_amount if b.balance_amount is not None else b.amount
        label = f"{biller_name} (Total: ₱{b.amount:,.2f} | Bal: ₱{bal:,.2f}) - {b.status.upper()}"
        bmap[label] = b.id
        # Store the balance for this specific bill to use later
        # The key in bmap is unique enough for this simple UI
        # We can't easily attach data to the selectbox options directly,
        # so we'll retrieve the bill object again or store a lookup.

    # Create a lookup for balances
    balance_map = {
        b.id: (b.balance_amount if b.balance_amount is not None else b.amount)
        for b in bills
    }

    sel = st.selectbox("Select bill", options=list(bmap.keys()))
    bill_id = bmap[sel]
    current_balance = balance_map[bill_id]

    pay_full = st.checkbox("Pay Full Amount")

    with st.form("payment_form", clear_on_submit=True):
        # Use step=0.01 to enforce currency behavior in UI
        # Disable input if paying full
        amount_val = st.number_input(
            "Payment amount",
            min_value=0.0,
            format="%.2f",
            step=0.01,
            value=float(current_balance) if pay_full else 0.0,
            disabled=pay_full,
        )

        paid_on = st.date_input("Paid on", value=date.today())

        payment_methods = [
            "GCash",
            "Credit Card",
            "Cash",
            "Online Banking",
            "Bank Transfer",
            "Check",
            "Other",
        ]
        method = st.selectbox("Method", options=payment_methods)

        status = st.selectbox(
            "Status", ["Paid", "Pending", "Partial Payment", "Overpayment"]
        )

        ref = st.text_input("Reference / Receipt #")
        notes = st.text_area("Notes")

        submitted = st.form_submit_button("Save Payment")

        if submitted:
            final_amount = current_balance if pay_full else amount_val

            if final_amount <= 0:
                st.warning("Amount must be greater than 0")
            else:
                try:
                    # Convert float input to Decimal for financial accuracy
                    add_payment(
                        user_id,
                        bill_id,
                        Decimal(str(final_amount)),
                        paid_on,
                        method,
                        ref,
                        notes,
                        status,
                    )
                    st.success("Payment recorded successfully")
                except Exception as e:
                    st.error(f"Error recording payment: {e}")

        st.subheader("Payments history")
        rows = list_payment_history(user_id)

        if rows:
            # Transform for display
            data = []
            for r in rows:
                data.append(
                    {
                        "ID": r.id,
                        "Bill ID": r.bill_id,
                        "Biller": r.biller_name,
                        "Amount": r.amount,
                        "Balance": r.balance_amount,
                        "Due Date": r.due_date,
                        "Date": r.paid_on,
                        "Status": r.status,
                        "Method": r.method,
                        "Ref": r.reference,
                    }
                )

            df = pd.DataFrame(data)

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Amount": st.column_config.NumberColumn(format="₱%.2f"),
                    "Balance": st.column_config.NumberColumn(format="₱%.2f"),
                    "Date": st.column_config.DateColumn(format="MMM DD, YYYY"),
                    "Due Date": st.column_config.DateColumn(format="MMM DD, YYYY"),
                    "Bill ID": st.column_config.NumberColumn(format="%d"),
                },
            )
        else:
            st.info("No payments recorded.")
