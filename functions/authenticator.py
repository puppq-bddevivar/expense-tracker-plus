from functions.captcha import (
    generate_captcha_text,
    generate_captcha_image,
    validate_captcha,
)
from lib.db import provide_session
from lib.helpers import (
    register_user,
    get_user_by_username_or_email,
    create_password_reset_token,
    get_user_by_password_reset_token,
    change_user_password,
)
from lib.models import UserAuth, UserProfile

# --- Streamlit Authenticator ---


def get_users_from_db():
    with provide_session() as db:
        users = db.query(UserAuth).join(UserProfile).all()
        credentials = {"usernames": {}}
        for user in users:
            credentials["usernames"][user.username] = {
                "name": user.profile.full_name,
                "password": user.password_hash,
                "email": user.profile.email,
            }
        return credentials


def render_registration_form(st, image, logger):
    st.subheader("Register")

    if st.button("Refresh Captcha", key="register_refresh"):
        st.session_state["captcha_text"] = generate_captcha_text()

    with st.form("register_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        col1, col2 = st.columns([0.4, 0.6])
        with col1:
            st.image(generate_captcha_image(st, image), use_container_width=True)
        captcha_input = st.text_input("Enter the text from the image")

        if st.form_submit_button("Register"):
            if not all(
                [name, email, username, password, confirm_password, captcha_input]
            ):
                st.error("Please fill out all fields.")
                return

            if password != confirm_password:
                st.error("Passwords do not match.")
                return

            if not validate_captcha(captcha_input, st):
                st.error("Captcha is incorrect.")
                return

            try:
                register_user(username, password, name, email)
                st.success("You have successfully registered! Please login.")
            except ValueError as e:
                st.error(e)
            except Exception as e:
                logger.error(f"Registration failed: {e}")
                st.error("An unexpected error occurred during registration.")


def render_forgot_password_form(st, image, logger):
    st.subheader("Forgot Password")

    if st.button("Refresh Captcha", key="forgot_password_refresh"):
        st.session_state["captcha_text"] = generate_captcha_text()

    with st.form("forgot_password_form"):
        identifier = st.text_input("Enter your username or email")
        col1, col2 = st.columns([0.4, 0.6])
        with col1:
            st.image(generate_captcha_image(st, image), use_container_width=True)
        captcha_input = st.text_input("Enter the text from the image")

        if st.form_submit_button("Submit"):
            if not identifier or not captcha_input:
                st.error("Please fill out all fields.")
                return

            if not validate_captcha(captcha_input, st):
                st.error("Captcha is incorrect.")
                return

            user = get_user_by_username_or_email(identifier)
            if user:
                token = create_password_reset_token(user.id)
                reset_link = f"?reset_token={token}"
                logger.info(f"Password reset link for {user.username}: {reset_link}")
                st.info(
                    "DEMO ONLY: In a real app, this link would be emailed. "
                    "Click the link below to reset password."
                )
                st.markdown(f"[{reset_link}]({reset_link})")
            st.success(
                "If an account with that username or email exists, a password reset link has been sent."
            )


def password_reset_screen(st, token, logger):
    st.title("Reset Your Password")

    if st.session_state.get("password_reset_complete"):
        st.success("Your password has been reset successfully! You can now log in.")
        if st.button("Go to Login"):
            del st.session_state["password_reset_complete"]
            st.query_params.clear()
            st.rerun()
        return

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
                    st.session_state["password_reset_complete"] = True
                    st.query_params.clear()
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    logger.error(f"Password reset failed for user {user.id}: {e}")
                    st.error("An unexpected error occurred. Please try again.")
