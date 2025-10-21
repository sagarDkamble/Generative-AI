import os
import yaml
import json
import streamlit as st
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

from gpt_service import get_gpt_response
from db_service import save_message, init_db, mark_order_paid
from billing_service import create_razorpay_order

# ---------------------------------------------------------------------
# 🌐 STREAMLIT PAGE CONFIG
# ---------------------------------------------------------------------
st.set_page_config(page_title="AI Personal Assistant", page_icon="🤖", layout="wide")

# ---------------------------------------------------------------------
# 🧠 INITIALIZE DATABASE
# ---------------------------------------------------------------------
init_db()

# ---------------------------------------------------------------------
# 🔐 LOAD SECRETS (FROM STREAMLIT CLOUD)
# ---------------------------------------------------------------------
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
DATABASE_URL = st.secrets["DATABASE_URL"]
RAZORPAY_KEY_ID = st.secrets["RAZORPAY_KEY_ID"]
RAZORPAY_KEY_SECRET = st.secrets["RAZORPAY_KEY_SECRET"]

# fallback for local testing
APP_URL = st.secrets.get("APP_URL", "http://localhost:8501")

# ---------------------------------------------------------------------
# 👥 AUTHENTICATION CONFIGURATION
# ---------------------------------------------------------------------
try:
    with open("auth_config.yaml") as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    st.error("❌ 'auth_config.yaml' not found. Please ensure it's uploaded to your repository.")
    st.stop()

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
    config["preauthorized"],
)

# ---------------------------------------------------------------------
# 🔑 LOGIN SECTION
# ---------------------------------------------------------------------
name, auth_status, username = authenticator.login("Login", "main")

# ---------------------------------------------------------------------
# ✅ IF LOGGED IN SUCCESSFULLY
# ---------------------------------------------------------------------
if auth_status:
    st.sidebar.success(f"Welcome {name} 👋")
    st.title("💬 GPT Personal Assistant")

    # Chat history in session
    if "history" not in st.session_state:
        st.session_state.history = []  # list of dicts: {"role": "user"/"assistant", "content": "..."}

    # User input box
    user_prompt = st.chat_input("Ask me anything...")
    if user_prompt:
        st.chat_message("user").markdown(user_prompt)
        st.session_state.history.append({"role": "user", "content": user_prompt})

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = get_gpt_response(user_prompt, st.session_state.history)
                st.markdown(reply)

        st.session_state.history.append({"role": "assistant", "content": reply})

        # Save conversation to database
        save_message(username, "user", user_prompt)
        save_message(username, "assistant", reply)

    # -----------------------------------------------------------------
    # 💳 PAYMENT SECTION (UPGRADE TO PRO)
    # -----------------------------------------------------------------
    st.divider()
    st.subheader("Upgrade to Pro 💳")
    st.write("Unlock higher limits and priority access.")

    if st.button("Proceed to Payment"):
        order = create_razorpay_order(username)
        st.session_state.razorpay_order = order
        st.experimental_rerun()

    if "razorpay_order" in st.session_state:
        order = st.session_state.razorpay_order
        st.info("Complete your payment in the Razorpay modal below (Test Mode).")

        # Razorpay Checkout HTML
        checkout_html = f"""
        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
        <form>
          <button id="rzp-button1" type="button">Pay Now</button>
        </form>
        <script>
        var options = {{
            "key": "{RAZORPAY_KEY_ID}",
            "amount": "{order['amount']}",
            "currency": "{order['currency']}",
            "name": "AI Assistant Pro",
            "description": "Pro Plan Subscription",
            "order_id": "{order['id']}",
            "callback_url": "{APP_URL}?payment_status=paid&order_id={order['id']}",
            "prefill": {{"name": "{name}", "email": "{config['credentials']['usernames'][username]['email']}" }},
            "theme": {{"color": "#3399cc"}}
        }};
        var rzp1 = new Razorpay(options);
        document.getElementById('rzp-button1').onclick = function(e){{ rzp1.open(); e.preventDefault(); }}
        </script>
        """
        st.components.v1.html(checkout_html, height=250)

    # -----------------------------------------------------------------
    # 🧾 PAYMENT CALLBACK HANDLING
    # -----------------------------------------------------------------
    qs = st.experimental_get_query_params()
    if qs.get("payment_status") == ["paid"] and "order_id" in qs:
        order_id = qs["order_id"][0] if isinstance(qs["order_id"], list) else qs["order_id"]
        mark_order_paid(order_id)
        st.success("✅ Payment successful! Your plan is now Pro. (Implement plan enforcement in production.)")

    # -----------------------------------------------------------------
    # 🚪 LOGOUT
    # -----------------------------------------------------------------
    authenticator.logout("Logout", "sidebar")
    st.session_state.clear()

# ---------------------------------------------------------------------
# ❌ INVALID LOGIN HANDLING
# ---------------------------------------------------------------------
elif auth_status is False:
    st.error("Invalid username or password")

else:
    st.warning("Please log in to continue")
