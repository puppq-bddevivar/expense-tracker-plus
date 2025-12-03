import pandas as pd
import plotly.express as px
import streamlit as st

from lib.helpers import list_billers, list_bills, list_payments


def show(user_id):
    st.header("Dashboard")

    # Fetch data
    # In a high-scale production app, we would use specific SQL queries for aggregates
    # instead of loading all rows, but for this scale, loading into DF is acceptable.
    billers = list_billers(user_id)
    bills = list_bills(user_id)
    payments = list_payments(user_id)

    # --- Metrics Section ---
    total_billers = len(billers)

    # Process Bills
    if bills:
        data_bills = []
        for b in bills:
            # Use balance_amount for outstanding calculation if available, else amount
            outstanding = b.balance_amount if b.balance_amount is not None else b.amount

            data_bills.append(
                {
                    "biller": b.biller.name if b.biller else "Unknown",
                    "amount": float(b.amount),  # Original bill amount
                    "outstanding": float(outstanding),  # Remaining to pay
                    "status": b.status,
                    "due": b.due_date,
                }
            )
        df_bills = pd.DataFrame(data_bills)

        unpaid_mask = df_bills["status"] != "paid"
        # Sum the 'outstanding' column for total debt, not the original 'amount'
        total_outstanding = df_bills[unpaid_mask]["outstanding"].sum()
        count_outstanding = df_bills[unpaid_mask].shape[0]
    else:
        df_bills = pd.DataFrame()
        total_outstanding = 0.0
        count_outstanding = 0

    # Display KPIs
    m1, m2, m3 = st.columns(3)
    m1.metric("Registered Billers", total_billers)
    m2.metric("Outstanding Amount", f"₱{total_outstanding:,.2f}")
    m3.metric("Pending Bills", count_outstanding)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Billers Directory")
        if billers:
            df_b = pd.DataFrame(
                [
                    {"Name": b.name, "Type": b.biller_type, "Account": b.account}
                    for b in billers
                ]
            )
            st.dataframe(df_b, hide_index=True, use_container_width=True)
        else:
            st.info("No billers registered.")

    with col2:
        st.subheader("Outstanding by Biller")
        if not df_bills.empty and total_outstanding > 0:
            unpaid = df_bills[df_bills["status"] != "paid"]
            # Aggregate by biller for the pie chart using 'outstanding'
            pie_data = unpaid.groupby("biller")["outstanding"].sum().reset_index()

            fig = px.pie(
                pie_data,
                names="biller",
                values="outstanding",
                hole=0.4,
            )
            st.plotly_chart(fig, use_container_width=True)
        elif df_bills.empty:
            st.info("No bills to analyze.")
        else:
            st.success("All bills are paid! 🎉")

    st.subheader("Recent Payments")
    if payments:
        df_pay = pd.DataFrame(
            [
                {
                    "Date": p.paid_on,
                    "Amount": p.amount,
                    "Method": p.method,
                    "Reference": p.reference,
                }
                for p in payments
            ]
        )
        st.dataframe(
            df_pay,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Amount": st.column_config.NumberColumn(format="₱%.2f"),
                "Date": st.column_config.DateColumn(format="MMM DD, YYYY"),
            },
        )
    else:
        st.info("No payments recorded yet.")
