import random
import string

# --- Captcha ---


def generate_captcha_text(length=6):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def generate_captcha_image(st, image):
    if "captcha_text" not in st.session_state:
        st.session_state["captcha_text"] = generate_captcha_text()

    captcha_image = image.generate(st.session_state["captcha_text"])
    return captcha_image


def validate_captcha(user_input, st):
    if user_input.upper() == st.session_state.get("captcha_text", "").upper():
        if "captcha_text" in st.session_state:
            del st.session_state["captcha_text"]
        return True
    return False
