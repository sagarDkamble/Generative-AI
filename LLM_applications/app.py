import os
import yaml
import json
import streamlit as st
from yaml.loader import SafeLoader
from dotenv import load_dotenv
import streamlit_authenticator as stauth
from streamlit_oauth import OAuth2Component

# --- Local imports ---
from gpt_service import get_gpt_response
from db_service import save_message, init_db, mark_order_paid
from billing_service import create_razorpay_order


# ----------------------------------------------------------
# 1️⃣ Basic setup
# ----------------------------------------------------------
st.set_page_config(page_title="AI Personal Assistant", page_icon="🤖", layout="wide")
load_dotenv()
init_db()

APP_URL = os.getenv("APP_URL", "http://localhost:8501")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")

# ----------------------------------------------------------
# 2️⃣ Load authentication YAML (for username/password)
# ----------------------------------------------------------
try:
    with open("auth_config.yaml") as f:
        config = yaml.load(f, Loader=SafeLoader)
except FileNotFoundError:
    st.error("❌ 'auth_config.yaml' not found — make sure it's uploaded in the same folder as app.py.")
    st.stop()

# ----------------------------------------------------------
# 3️⃣ Initialize authenticator (for v0.3.3+)
# ----------------------------------------------------------
authenticator = stauth.Authenticate(
    credentials=config["credentials"],
    cookie_name=config["cookie"]["name"],
    key=config["cookie"]["key"],
    cookie_expiry_days=config["cookie"]["expiry_days"]
)

# ----------------------------------------------------------
# 4️⃣ Initialize Google OAuth2 (Sign in with Google)
# ----------------------------------------------------------
try:
    CLIENT_ID = st.secrets["GOOGLE_CLIENT_ID"]
    CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
    REDIRECT_URI = st.secrets["REDIRECT_URI"]
except Exception:
    st.warning("⚠️ Google OAuth credentials not found in Streamlit secrets.")
    CLIENT_ID = CLIENT_SECRET = REDIRECT_URI = None

AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REFRESH_TOKEN_URL = TOKEN_URL

oauth2 = OAuth2Component(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    authorize_url=AUTHORIZATION_URL,
    token_url=TOKEN_URL,
    refresh_token_url=REFRESH_TOKEN_URL,
)

# ----------------------------------------------------------
# 5️⃣ Show Login Options
# ----------------------------------------------------------
st.title("🤖 AI Personal Assistant")

tab1, tab2 = st.tabs(["🔑 Login with Account", "🌐 Login with Google"])

with tab1:
    try:
        name, auth_status, username = authenticator.login(location="main")
    except Exception as e:
        st.error(f"⚠️ Login error: {e}")
        st.stop()

with tab2:
    if CLIENT_ID and CLIENT_SECRET:
        if "google_token" not in st.session_state:
            result = oauth2.authorize_button(
                name="Continue with Google",
                icon="https://developers.google.com/identity/images/g-logo.png",
                redirect_uri=REDIRECT_URI,
                scope="openid email profile",
                key="google",
            )

            if result:
                st.session_state.google_token = result.get("token")
                st.experimental_rerun()

        if "google_token" in st.session_state:
            google_info = oauth2.get_user_info(st.session_state.google_token)
            auth_status = True
            name = google_info.get("name", "Google User")
            username = google_info.get("email", "unknown")
            st.success(f"✅ Logged in as {name} ({username}) via Google")

            if st.button("Logout"):
                del st.session_state["google_token"]
                st.experimental_rerun()

# ----------------------------------------------------------
# 6️⃣ If user authenticated
# ----------------------------------------------------------
if auth_status:
    st.sidebar.success(f"Welcome {name} 👋")
    authenticator.logout("Logout", location="sidebar")

    st.title("💬 GPT Personal Assistant")

    if "history" not in st.session_state:
        st.session_state.history = []

    user_prompt = st.chat_input("Ask me anything...")
    if user_prompt:
        st.chat_message("user").markdown(user_prompt)
        st.session_state.history.append({"role": "user", "content": user_prompt})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = get_gpt_response(user_prompt, st.session_state.history)
                st.markdown(reply)

        st.session_state.history.append({"role": "assistant", "content": reply})
        save_message(username, "user", user_prompt)
        save_message(username, "assistant", reply)

    st.divider()
    st.subheader("💳 Upgrade to Pro Plan")
    st.write("Unlock higher limits and priority access.")

    if st.button("Proceed to Payment"):
        order = create_razorpay_order(username)
        st.session_state.razorpay_order = order
        st.experimental_rerun()

    if "razorpay_order" in st.session_state:
        order = st.session_state.razorpay_order
        st.info("💰 Complete your payment below:")

        checkout_html = f"""
        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
        <form><button id="rzp-button1" type="button">Pay Now</button></form>
        <script>
        var options = {{
            "key": "{RAZORPAY_KEY_ID}",
            "amount": "{order['amount']}",
            "currency": "{order['currency']}",
            "name": "AI Assistant Pro",
            "description": "Pro Plan Access",
            "order_id": "{order['id']}",
            "callback_url": "{APP_URL}?payment_status=paid&order_id={order['id']}",
            "prefill": {{"name": "{name}", "email": "{username}"}},
            "theme": {{"color": "#3399cc"}}
        }};
        var rzp1 = new Razorpay(options);
        document.getElementById('rzp-button1').onclick = function(e) {{
            rzp1.open(); e.preventDefault();
        }}
        </script>
        """
        st.components.v1.html(checkout_html, height=220)

    qs = st.query_params
    if qs.get("payment_status") == ["paid"] and "order_id" in qs:
        order_id = qs["order_id"][0] if isinstance(qs["order_id"], list) else qs["order_id"]
        mark_order_paid(order_id)
        st.success("✅ Payment successful! You are now on the Pro plan.")

# ----------------------------------------------------------
# 7️⃣ If login failed or not attempted
# ----------------------------------------------------------
elif auth_status is False:
    st.error("❌ Invalid username or password.")
else:
    st.warning("🔑 Please log in to continue.")
