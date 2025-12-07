import logging

import bcrypt
import streamlit as st
import streamlit_authenticator as stauth
from captcha.image import ImageCaptcha

from functions.authenticator import (
    get_users_from_db,
    password_reset_screen,
    render_forgot_password_form,
    render_registration_form,
)
from functions.captcha import (
    generate_captcha_image,
    generate_captcha_text,
    validate_captcha,
)
from lib.db import init_db
from lib.helpers import (
    get_user_by_username_or_email,
)
from pages import dashboard, billers, bills, payments

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Expense Tracker Plus App", layout="wide")


# --- Main App Setup ---


image = ImageCaptcha()


@st.cache_resource
def setup_application():
    """Initialize database connection."""
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        st.error("System Error: Could not initialize database connection.")


def main():
    try:
        setup_application()

        if "reset_token" in st.query_params:
            password_reset_screen(
                token=st.query_params["reset_token"],
                st=st,
                logger=logger,
            )
            return

        credentials = get_users_from_db()
        authenticator = stauth.Authenticate(
            credentials=credentials,
            cookie_name="expense_tracker_cookie",
            api_key=st.secrets["auth_secret_key"],
            cookie_expiry_days=30,
        )

        # Render main app if user is already logged in
        if st.session_state.get("authentication_status"):
            with st.sidebar:
                st.write(f'Welcome *{st.session_state["name"]}*')
                try:
                    authenticator.logout("Logout", "main")
                except Exception as e:
                    logger.error(f"Error during logout: {e}")
                    st.error("An error occurred during logout.")
                st.divider()
                st.title("Navigation")
                page_choice = st.radio(
                    "Go to",
                    ["Dashboard", "Billers", "Bills", "Payments"],
                    label_visibility="collapsed",
                )

            user = get_user_by_username_or_email(st.session_state["username"])
            user_id = user.id

            try:
                if page_choice == "Dashboard":
                    dashboard.show(user_id)
                elif page_choice == "Billers":
                    billers.show(user_id)
                elif page_choice == "Bills":
                    bills.show(user_id)
                elif page_choice == "Payments":
                    payments.show(user_id)
                else:
                    st.write("Page not found")
            except Exception as e:
                logger.error(f"Error rendering page {page_choice}: {e}")
                st.error("An unexpected error occurred on this page.")
            return

        # --- Authentication Forms ---
        choice = st.radio(
            "Authentication",
            [
                "Login",
                "Register",
                "Forgot Password",
            ],
            horizontal=True,
        )

        if choice == "Login":
            st.subheader("Login")

            if "captcha_text" not in st.session_state:
                st.session_state["captcha_text"] = generate_captcha_text()

            if st.button("Refresh Captcha", key="login_refresh"):
                st.session_state["captcha_text"] = generate_captcha_text()

            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")

                col1, col2 = st.columns([0.4, 0.6])
                with col1:
                    st.image(
                        generate_captcha_image(st, image), use_container_width=True
                    )
                captcha_input = st.text_input("Enter the text from the image")

                submitted = st.form_submit_button("Login")

                if submitted:
                    if not all([username, password, captcha_input]):
                        st.error("Please fill out all fields.")
                    elif not validate_captcha(captcha_input, st):
                        st.error("Captcha is incorrect.")
                        st.session_state["captcha_text"] = generate_captcha_text()
                    else:
                        user_data = credentials.get("usernames", {}).get(username)
                        if user_data and bcrypt.checkpw(
                            password.encode(), user_data["password"].encode()
                        ):
                            st.session_state["authentication_status"] = True
                            st.session_state["name"] = user_data["name"]
                            st.session_state["username"] = username
                            st.rerun()
                        else:
                            st.error("Username/password is incorrect")

        elif choice == "Register":
            render_registration_form(
                st=st,
                image=image,
                logger=logger,
            )
        elif choice == "Forgot Password":
            render_forgot_password_form(
                st=st,
                image=image,
                logger=logger,
            )
    except Exception as e:
        logger.critical(
            f"An unexpected error occurred in the main application: {e}", exc_info=True
        )
        st.error("A critical error occurred. Please check the logs for more details.")


if __name__ == "__main__":
    main()
