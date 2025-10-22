import os
import yaml
import streamlit as st
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from dotenv import load_dotenv
from gpt_service import get_gpt_response
from db_service import save_message, init_db, mark_order_paid
from billing_service import create_razorpay_order

# -------------------------------------------------------
# 🔧 INITIAL SETUP
# -------------------------------------------------------
st.set_page_config(page_title="AI Personal Assistant", page_icon="🤖", layout="wide")

# Load secrets (Streamlit Cloud provides these automatically)
load_dotenv()
init_db()

APP_URL = st.secrets.get("APP_URL", "http://localhost:8501")
RAZORPAY_KEY_ID = st.secrets["RAZORPAY_KEY_ID"]

# -------------------------------------------------------
# 🔐 AUTHENTICATION CONFIG
# -------------------------------------------------------
auth_path = os.path.join(os.path.dirname(__file__), "auth_config.yaml")
if not os.path.exists(auth_path):
    st.error("'auth_config.yaml' not found. Please ensure it's uploaded to your repository.")
    st.stop()

with open(auth_path) as f:
    config = yaml.load(f, Loader=SafeLoader)

# ✅ Updated for streamlit-authenticator v0.3.3+
authenticator = stauth.Authenticate(
    credentials=config["credentials"],
    cookie_name=config["cookie"]["name"],
    key=config["cookie"]["key"],
    cookie_expiry_days=config["cookie"]["expiry_days"]
)

# New API: keyword args required
name, auth_status, username = authenticator.login(
    form_name="Login",
    location="main"
)

# -------------------------------------------------------
# 🧠 MAIN APPLICATION
# -------------------------------------------------------
if auth_status:
    st.sidebar.success(f"Welcome {name} 👋")
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
    st.subheader("Upgrade to Pro 💳")
    st.write("Unlock higher limits and priority access.")

    if st.button("Proceed to Payment"):
        order = create_razorpay_order(username)
        st.session_state.razorpay_order = order
        st.experimental_rerun()

    if "razorpay_order" in st.session_state:
        order = st.session_state.razorpay_order
        st.info("Complete your payment in the Razorpay modal below.")

        # Razorpay Checkout widget
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
            "description": "Pro Plan",
            "order_id": "{order['id']}",
            "callback_url": "{APP_URL}?payment_status=paid&order_id={order['id']}",
            "prefill": {{
                "name": "{name}",
                "email": "{config['credentials']['usernames'][username]['email']}"
            }},
            "theme": {{"color": "#3399cc"}}
        }};
        var rzp1 = new Razorpay(options);
        document.getElementById('rzp-button1').onclick = function(e) {{
            rzp1.open();
            e.preventDefault();
        }}
        </script>
        """
        st.components.v1.html(checkout_html, height=200)

    # ✅ Payment callback
    qs = st.query_params
    if qs.get("payment_status") == ["paid"] and "order_id" in qs:
        order_id = qs["order_id"][0] if isinstance(qs["order_id"], list) else qs["order_id"]
        mark_order_paid(order_id)
        st.success("✅ Payment successful! Your plan is now Pro.")

    authenticator.logout("Logout", "sidebar")

elif auth_status is False:
    st.error("Invalid username or password")
else:
    st.warning("Please log in to continue")
