import logging
import random

import streamlit as st

from lib.db import init_db
from lib.helpers import (
    authenticate_user,
    register_user,
    check_rate_limit,
    log_login_attempt,
    create_password_reset_token,
    get_user_by_password_reset_token,
    change_user_password,
    get_user_by_username_or_email,
)
from pages import dashboard, billers, bills, payments

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Bills & Expenses", layout="wide")


# --- Main App Setup ---


@st.cache_resource
def setup_application():
    """Initialize database connection."""
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        st.error("System Error: Could not initialize database connection.")


# --- Authentication Screens ---


def generate_math_challenge():
    """Generate and store a simple math problem if one doesn't exist."""
    if "math_answer" not in st.session_state:
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        operator = random.choice(["+", "-", "*"])

        problem = f"What is {num1} {operator} {num2}?"
        if operator == "+":
            answer = num1 + num2
        elif operator == "-":
            answer = num1 - num2
        else:  # '*'
            answer = num1 * num2

        st.session_state["math_problem"] = problem
        st.session_state["math_answer"] = str(answer)


def render_login_tab():
    """Render the login form and handle its logic."""
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        math_input = st.text_input(
            st.session_state.get("math_problem", "Loading..."), key="login_captcha"
        )
        submit = st.form_submit_button("Login")

        if submit:
            correct_answer = st.session_state.pop("math_answer", None)
            if math_input != correct_answer:
                st.error("Incorrect answer to the math challenge.")
                return

            if not username or not password:
                st.error("Please enter username and password")
                return

            if not check_rate_limit(username):
                st.error(
                    "Too many failed attempts. Account access is temporarily blocked for 24 hours."
                )
                log_login_attempt(username, False)
                return

            user = authenticate_user(username, password)
            if user:
                log_login_attempt(username, True)
                st.session_state.logged_in = True
                st.session_state.user_id = user.id
                st.session_state.username = user.username
                st.session_state.pop("math_problem", None)
                st.success("Logged in successfully!")
                st.rerun()
            else:
                log_login_attempt(username, False)
                st.error("Invalid username or password")


def render_register_tab():
    """Render the registration form and handle its logic."""
    with st.form("register_form"):
        new_user = st.text_input("Username", key="reg_user")
        new_pass = st.text_input("Password", type="password", key="reg_pass")
        new_email = st.text_input("Email", key="reg_email")
        new_name = st.text_input("Full Name", key="reg_name")
        math_input = st.text_input(
            st.session_state.get("math_problem", "Loading..."), key="reg_captcha"
        )
        submit = st.form_submit_button("Register")

        if submit:
            correct_answer = st.session_state.pop("math_answer", None)
            if math_input != correct_answer:
                st.error("Incorrect answer to the math challenge.")
                return

            if not new_user or not new_pass:
                st.error("Username and password are required")
                return

            try:
                register_user(new_user, new_pass, new_name, new_email)
                st.success("Account created! You can now login.")
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                logger.error(f"Registration failed: {e}")
                st.error("Registration failed: An unexpected error occurred.")


def render_forgot_password_tab():
    """Render the forgot password form and handle its logic."""
    with st.form("forgot_form"):
        st.info("Enter your username or email to reset your password.")
        identifier = st.text_input("Username or Email")
        math_input = st.text_input(
            st.session_state.get("math_problem", "Loading..."), key="forgot_captcha"
        )
        submit = st.form_submit_button("Submit")

        if submit:
            correct_answer = st.session_state.pop("math_answer", None)
            if math_input != correct_answer:
                st.error("Incorrect answer to the math challenge.")
                return

            if not identifier:
                st.warning("Please enter a username or email.")
                return

            user = get_user_by_username_or_email(identifier)
            st.success(
                f"If an account exists for '{identifier}', a reset link has been sent to the registered email."
            )
            if user:
                token = create_password_reset_token(user.id)
                reset_link = f"?reset_token={token}"
                logger.info(f"Password reset link for {user.username}: {reset_link}")
                st.info(
                    "DEMO ONLY: In a real app, this link would be emailed. "
                    "Click the link below to reset password."
                )
                st.markdown(f"[{reset_link}]({reset_link})")


def login_screen():
    """Display the main login/registration screen with tabs."""
    st.title("Login")
    generate_math_challenge()

    tab_login, tab_register, tab_forgot = st.tabs(
        ["Login", "Register", "Forgot Password"]
    )

    with tab_login:
        render_login_tab()
    with tab_register:
        render_register_tab()
    with tab_forgot:
        render_forgot_password_tab()


def password_reset_screen(token):
    """Display the screen for a user to reset their password."""
    st.title("Reset Your Password")
    user = get_user_by_password_reset_token(token)

    if not user:
        st.error("This password reset link is invalid or has expired.")
        if st.button("Go to Login"):
            st.query_params.clear()
            st.rerun()
        return

    with st.form("reset_password_form"):
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        submit = st.form_submit_button("Reset Password")

        if submit:
            if not new_password or not confirm_password:
                st.error("Please fill out both password fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                try:
                    change_user_password(user.id, new_password)
                    st.success(
                        "Your password has been reset successfully! You can now log in."
                    )
                    st.query_params.clear()
                    if st.button("Go to Login"):
                        st.rerun()
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    logger.error(f"Password reset failed for user {user.id}: {e}")
                    st.error("An unexpected error occurred. Please try again.")


# --- Main Application Logic ---


def main():
    """Main function to run the Streamlit application."""
    setup_application()

    # Router for password reset
    if "reset_token" in st.query_params:
        password_reset_screen(st.query_params["reset_token"])
        return

    # Main app router
    if not st.session_state.get("logged_in"):
        login_screen()
        return

    # --- Logged-in User Interface ---
    with st.sidebar:
        st.write(f"👤 **{st.session_state.username}**")
        if st.button("Logout"):
            # Clear all session state on logout
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

        st.divider()
        st.title("Navigation")
        choice = st.radio(
            "Go to",
            ["Dashboard", "Billers", "Bills", "Payments"],
            label_visibility="collapsed",
        )

    # Page router
    user_id = st.session_state.user_id
    try:
        if choice == "Dashboard":
            dashboard.show(user_id)
        elif choice == "Billers":
            billers.show(user_id)
        elif choice == "Bills":
            bills.show(user_id)
        elif choice == "Payments":
            payments.show(user_id)
        else:
            st.write("Page not found")
    except Exception as e:
        logger.error(f"Error rendering page {choice}: {e}")
        st.error("An unexpected error occurred on this page.")


if __name__ == "__main__":
    main()
