import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from dotenv import load_dotenv
import os

# --- Optional helper imports (keep or remove based on your project) ---
from gpt_service import get_gpt_response
from db_service import save_message, init_db, mark_order_paid
from billing_service import create_razorpay_order


# ----------------------------------------------------------
# 1️⃣  Basic setup
# ----------------------------------------------------------
st.set_page_config(page_title="AI Personal Assistant", page_icon="🤖", layout="wide")
load_dotenv()
init_db()

APP_URL = os.getenv("APP_URL", "http://localhost:8501")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")


# ----------------------------------------------------------
# 2️⃣  Load authentication YAML
# ----------------------------------------------------------
try:
    with open("auth_config.yaml") as f:
        config = yaml.load(f, Loader=SafeLoader)
except FileNotFoundError:
    st.error("❌ 'auth_config.yaml' not found — upload it in the same folder as app.py.")
    st.stop()


# ----------------------------------------------------------
# 3️⃣  Initialize Authenticator (for v0.3.3+)
# ----------------------------------------------------------
authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
    config["preauthorized"]
)


# ----------------------------------------------------------
# 4️⃣  Login / Register Section
# ----------------------------------------------------------
st.title("🤖 AI Personal Assistant Login")

try:
    name, auth_status, username = authenticator.login(location="main")
except Exception as e:
    st.error(f"⚠️ Login error: {e}")
    st.stop()

# --- Registration (for new users you approve manually in YAML or via register_user API) ---
with st.expander("🆕 New User? Register Here"):
    try:
        email_of_registered_user, username_of_registered_user, name_of_registered_user = authenticator.register_user(
            location="main",
            preauthorization=False  # set True to allow auto-approve for emails listed under 'preauthorized'
        )
        if email_of_registered_user:
            st.success("✅ User registered! You can now log in.")
    except Exception as e:
        st.warning(f"⚠️ Registration error: {e}")


# ----------------------------------------------------------
# 5️⃣  If logged in successfully
# ----------------------------------------------------------
if auth_status:
    st.sidebar.success(f"Welcome {name} 👋")
    authenticator.logout("Logout", location="sidebar")

    st.header("💬 Chat with Your AI Assistant")

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
            "theme": {{"color": "#3399cc"}}
        }};
        var rzp1 = new Razorpay(options);
        document.getElementById('rzp-button1').onclick = function(e) {{ rzp1.open(); e.preventDefault(); }}
        </script>
        """
        st.components.v1.html(checkout_html, height=220)

    # Payment success callback
    qs = st.query_params
    if qs.get("payment_status") == ["paid"] and "order_id" in qs:
        order_id = qs["order_id"][0] if isinstance(qs["order_id"], list) else qs["order_id"]
        mark_order_paid(order_id)
        st.success("✅ Payment successful! You’re now on the Pro plan.")


# ----------------------------------------------------------
# 6️⃣  If login failed or not attempted
# ----------------------------------------------------------
elif auth_status is False:
    st.error("❌ Invalid username or password.")
else:
    st.warning("🔑 Please log in to continue.")
