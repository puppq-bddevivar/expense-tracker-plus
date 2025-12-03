import logging

import streamlit as st

from lib.db import init_db
from pages import dashboard, billers, bills, payments

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Bills & Expenses", layout="wide")


# Use cache_resource to ensure DB init only happens once per server start
# instead of every time the user clicks a button.
@st.cache_resource
def setup_application():
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        st.error("System Error: Could not initialize database connection.")


def main():
    # Initialize app resources
    setup_application()

    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"

    with st.sidebar:
        st.title("Navigation")
        # Direct routing based on selection is more stable than manual state syncing
        # for this specific router pattern.
        choice = st.radio(
            "Go to",
            ["Dashboard", "Billers", "Bills", "Payments"],
            label_visibility="collapsed",
        )

    # Router
    try:
        if choice == "Dashboard":
            dashboard.show()
        elif choice == "Billers":
            billers.show()
        elif choice == "Bills":
            bills.show()
        elif choice == "Payments":
            payments.show()
        else:
            st.write("Page not found")
    except Exception as e:
        logger.error(f"Error rendering page {choice}: {e}")
        st.error("An unexpected error occurred on this page.")


if __name__ == "__main__":
    main()
