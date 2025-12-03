import streamlit as st

from lib.helpers import list_billers, add_biller, update_biller, delete_biller


def show(user_id):
    st.header("Manage Billers")

    tab_list, tab_new = st.tabs(["Registered Billers", "Add New Biller"])

    with tab_new:
        with st.form("add_biller_form", clear_on_submit=True):
            st.subheader("Add New Biller")
            name = st.text_input("Biller Name (e.g. Meralco, PLDT)")
            b_type = st.selectbox(
                "Type",
                ["Utility", "Credit Card", "Internet", "Rent", "Insurance", "Other"],
            )
            account = st.text_input("Account / Policy Number")
            notes = st.text_area("Notes")

            submitted = st.form_submit_button("Save Biller")

            if submitted:
                if not name:
                    st.error("Biller name is required")
                else:
                    try:
                        add_biller(user_id, name, b_type, account, notes)
                        st.success(f"Biller '{name}' added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding biller: {e}")

    with tab_list:
        billers = list_billers(user_id)
        if not billers:
            st.info("No billers found.")
        else:
            for b in billers:
                with st.expander(f"{b.name} ({b.biller_type})"):
                    with st.form(f"edit_biller_{b.id}"):
                        e_name = st.text_input("Name", value=b.name)
                        e_type = st.selectbox(
                            "Type",
                            [
                                "Utility",
                                "Credit Card",
                                "Internet",
                                "Rent",
                                "Insurance",
                                "Other",
                            ],
                            index=(
                                [
                                    "Utility",
                                    "Credit Card",
                                    "Internet",
                                    "Rent",
                                    "Insurance",
                                    "Other",
                                ].index(b.biller_type)
                                if b.biller_type
                                in [
                                    "Utility",
                                    "Credit Card",
                                    "Internet",
                                    "Rent",
                                    "Insurance",
                                    "Other",
                                ]
                                else 5
                            ),
                        )
                        e_account = st.text_input("Account", value=b.account or "")
                        e_notes = st.text_area("Notes", value=b.notes or "")

                        c1, c2 = st.columns([1, 4])
                        with c1:
                            if st.form_submit_button("Delete", type="primary"):
                                delete_biller(user_id, b.id)
                                st.rerun()
                        with c2:
                            if st.form_submit_button("Update"):
                                update_biller(
                                    user_id, b.id, e_name, e_type, e_account, e_notes
                                )
                                st.success("Updated!")
                                st.rerun()
