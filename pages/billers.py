import streamlit as st

from lib.helpers import add_biller, list_billers, update_biller, delete_biller
from lib.ui import data_frame_from_models


def show():
    st.header("Billers")

    tab_view, tab_add, tab_manage = st.tabs(["View List", "Add New", "Manage"])

    # Fetch fresh data
    rows = list_billers()

    with tab_view:
        st.subheader("Existing billers")
        # Use shared UI helper
        df = data_frame_from_models(
            rows, columns=["id", "name", "biller_type", "account"]
        )

        if not df.empty:
            # Rename columns for better display
            df = df.rename(
                columns={"biller_type": "type", "name": "biller", "id": "ID"}
            )
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No billers found.")

    with tab_add:
        st.subheader("Add New Biller")
        # Use clear_on_submit=True to reset the form after adding
        with st.form("add_biller_form", clear_on_submit=True):
            name = st.text_input("Biller name")
            btype = st.selectbox(
                "Type",
                [
                    "Electricity",
                    "Internet",
                    "Water",
                    "Gas",
                    "Phone",
                    "Credit Card",
                    "Bank Loan",
                    "Insurance",
                    "Rent",
                    "Other",
                ],
            )
            acct = st.text_input("Account / Reference")
            notes = st.text_area("Notes")

            submitted = st.form_submit_button("Save")

            if submitted:
                if not name.strip():
                    st.warning("Please enter a biller name")
                else:
                    try:
                        add_biller(name, btype, acct, notes)
                        st.success("Biller saved successfully")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error saving biller: {e}")

    with tab_manage:
        st.subheader("Edit or Delete Biller")
        if not rows:
            st.info("No billers to manage.")
        else:
            biller_map = {f"{b.name} ({b.biller_type})": b for b in rows}
            selected_label = st.selectbox(
                "Select Biller", options=list(biller_map.keys())
            )
            selected_biller = biller_map[selected_label]

            st.divider()

            # Edit Form
            # Key the form widgets with ID to ensure they refresh when selection changes
            with st.form("edit_biller_form"):
                new_name = st.text_input(
                    "Biller name",
                    value=selected_biller.name,
                    key=f"edit_name_{selected_biller.id}",
                )

                types = [
                    "Electricity",
                    "Internet",
                    "Water",
                    "Gas",
                    "Phone",
                    "Credit Card",
                    "Bank Loan",
                    "Insurance",
                    "Rent",
                    "Other",
                ]
                try:
                    type_index = types.index(selected_biller.biller_type)
                except ValueError:
                    type_index = len(types) - 1

                new_type = st.selectbox(
                    "Type",
                    types,
                    index=type_index,
                    key=f"edit_type_{selected_biller.id}",
                )
                new_acct = st.text_input(
                    "Account / Reference",
                    value=selected_biller.account or "",
                    key=f"edit_acct_{selected_biller.id}",
                )
                new_notes = st.text_area(
                    "Notes",
                    value=selected_biller.notes or "",
                    key=f"edit_notes_{selected_biller.id}",
                )

                update_submitted = st.form_submit_button("Update Biller")

                if update_submitted:
                    if not new_name.strip():
                        st.warning("Name cannot be empty")
                    else:
                        try:
                            update_biller(
                                selected_biller.id,
                                new_name,
                                new_type,
                                new_acct,
                                new_notes,
                            )
                            st.success("Biller updated.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating: {e}")

            st.write("Danger Zone")
            if st.button(
                "Delete this Biller",
                key=f"del_btn_{selected_biller.id}",
                type="primary",
                help="Deleting a biller will also delete all associated bills and payments.",
            ):
                try:
                    delete_biller(selected_biller.id)
                    st.success("Biller deleted.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting: {e}")
