import datetime

import streamlit as st

from lib.helpers import list_billers, add_bill, list_bills, update_bill, delete_bill


def show():
    st.header("Bills")

    # Common resources
    months = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    current_year = datetime.date.today().year
    years = [str(y) for y in range(current_year - 2, current_year + 6)]

    # 1. Fetch billers for the dropdown
    billers = list_billers()

    tab_view, tab_add, tab_manage = st.tabs(["View List", "Add New", "Manage"])

    with tab_add:
        if not billers:
            st.warning(
                "No billers found. Please go to the 'Billers' page and add one first."
            )
        else:
            # Create a dictionary for mapping name -> id
            biller_options = {b.name: b.id for b in billers}

            with st.form("add_bill_form", clear_on_submit=True):
                st.subheader("Add New Bill")

                selected_biller_name = st.selectbox(
                    "Biller", list(biller_options.keys())
                )
                amount = st.number_input(
                    "Amount", min_value=0.0, step=0.01, format="%.2f"
                )
                due_date = st.date_input("Due Date", datetime.date.today())

                col1, col2 = st.columns(2)
                with col1:
                    # Default to current month
                    current_month_idx = datetime.date.today().month - 1
                    selected_month = st.selectbox(
                        "Period Month", months, index=current_month_idx
                    )

                with col2:
                    # Default to current year (index 2 in the list starting from current-2)
                    selected_year = st.selectbox("Period Year", years, index=2)

                notes = st.text_area("Notes")

                submitted = st.form_submit_button("Save Bill")

                if submitted:
                    if amount <= 0:
                        st.error("Amount must be greater than 0.")
                    else:
                        biller_id = biller_options[selected_biller_name]
                        try:
                            period_month = months.index(selected_month) + 1
                            add_bill(
                                biller_id,
                                amount,
                                due_date,
                                period_month,
                                int(selected_year),
                                notes,
                            )
                            st.success("Bill added successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding bill: {e}")

    with tab_view:
        st.subheader("Existing Bills")
        bills_data = list_bills()

        if not bills_data:
            st.info("No bills recorded yet.")
        else:
            # Flatten data for display
            display_data = []
            for b in bills_data:
                period_display = ""
                if b.period_month and b.period_year and 1 <= b.period_month <= 12:
                    period_display = f"{months[b.period_month - 1]} {b.period_year}"

                display_data.append(
                    {
                        "ID": b.id,
                        "Biller": b.biller.name if b.biller else "Unknown",
                        "Amount": float(b.amount),
                        "Due Date": b.due_date,
                        "Status": b.status,
                        "Period": period_display,
                    }
                )

            st.dataframe(display_data, use_container_width=True, hide_index=True)

    with tab_manage:
        st.subheader("Edit or Delete Bill")

        # Fetch fresh data for management
        bills_data_manage = list_bills()

        if not bills_data_manage:
            st.info("No bills to manage.")
        elif not billers:
            st.info("No billers available to assign.")
        else:
            # Create a dictionary for selecting a bill
            bill_map = {
                f"{b.biller.name if b.biller else 'Unknown'} (₱{b.amount:,.2f}) - Due {b.due_date}": b
                for b in bills_data_manage
            }

            selected_label = st.selectbox("Select Bill", options=list(bill_map.keys()))
            selected_bill = bill_map[selected_label]

            st.divider()

            biller_options_manage = {b.name: b.id for b in billers}

            with st.form("edit_bill_form"):
                # Pre-fill values
                current_biller_name = (
                    selected_bill.biller.name if selected_bill.biller else None
                )
                if current_biller_name and current_biller_name in biller_options_manage:
                    b_idx = list(biller_options_manage.keys()).index(
                        current_biller_name
                    )
                else:
                    b_idx = 0

                new_biller_name = st.selectbox(
                    "Biller",
                    list(biller_options_manage.keys()),
                    index=b_idx,
                    key="edit_biller",
                )

                new_amount = st.number_input(
                    "Amount",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                    value=float(selected_bill.amount),
                    key="edit_amount",
                )
                new_due_date = st.date_input(
                    "Due Date", value=selected_bill.due_date, key="edit_due_date"
                )

                c1, c2 = st.columns(2)
                with c1:
                    # Month
                    m_idx = (
                        (selected_bill.period_month - 1)
                        if (
                            selected_bill.period_month
                            and 1 <= selected_bill.period_month <= 12
                        )
                        else 0
                    )
                    new_month = st.selectbox(
                        "Period Month", months, index=m_idx, key="edit_month"
                    )
                with c2:
                    # Year
                    y_str = (
                        str(selected_bill.period_year)
                        if selected_bill.period_year
                        else str(current_year)
                    )
                    try:
                        y_idx = years.index(y_str)
                    except ValueError:
                        y_idx = 2  # default
                    new_year = st.selectbox(
                        "Period Year", years, index=y_idx, key="edit_year"
                    )

                status_options = ["unpaid", "partial", "paid"]
                try:
                    s_idx = status_options.index(selected_bill.status)
                except ValueError:
                    s_idx = 0
                new_status = st.selectbox(
                    "Status", status_options, index=s_idx, key="edit_status"
                )

                new_notes = st.text_area(
                    "Notes", value=selected_bill.notes or "", key="edit_notes"
                )

                update_submitted = st.form_submit_button("Update Bill")

                if update_submitted:
                    biller_id_val = biller_options_manage[new_biller_name]
                    p_month = months.index(new_month) + 1
                    p_year = int(new_year)

                    try:
                        update_bill(
                            selected_bill.id,
                            biller_id_val,
                            new_amount,
                            new_due_date,
                            p_month,
                            p_year,
                            new_notes,
                            new_status,
                        )
                        st.success("Bill updated.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating bill: {e}")

            st.write("Danger Zone")
            if st.button(
                "Delete this Bill",
                type="primary",
                help="Deleting this bill will remove associated payments as well.",
            ):
                try:
                    delete_bill(selected_bill.id)
                    st.success("Bill deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting: {e}")
