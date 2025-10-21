import os, yaml, json, streamlit as st
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from dotenv import load_dotenv
from gpt_service import get_gpt_response
from db_service import save_message, init_db, mark_order_paid
from billing_service import create_razorpay_order

# Setup
st.set_page_config(page_title="AI Personal Assistant", page_icon="🤖", layout="wide")
load_dotenv()
init_db()

APP_URL = os.getenv("APP_URL", "http://localhost:8501")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")

# Auth
with open('auth_config.yaml') as f:
    config = yaml.load(f, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

name, auth_status, username = authenticator.login("Login", "main")

if auth_status:
    st.sidebar.success(f"Welcome {name} 👋")
    st.title("💬 GPT Personal Assistant")

    if "history" not in st.session_state:
        st.session_state.history = []  # list of dicts: {"role": "user"/"assistant", "content": "..."}

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
        # Embed Razorpay Checkout
        checkout_html = f'''
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
            "prefill": {{"name": "{name}", "email": "{config['credentials']['usernames'][username]['email']}"}},
            "theme": {{"color": "#3399cc"}}
        }};
        var rzp1 = new Razorpay(options);
        document.getElementById('rzp-button1').onclick = function(e){{ rzp1.open(); e.preventDefault(); }}
        </script>
        '''
        st.components.v1.html(checkout_html, height=200)

    # Handle payment callback (simple GET param check)
    qs = st.query_params
    if qs.get("payment_status") == ["paid"] and "order_id" in qs:
        order_id = qs["order_id"][0] if isinstance(qs["order_id"], list) else qs["order_id"]
        mark_order_paid(order_id)
        st.success("Payment successful! Your plan is now Pro. (Implement plan enforcement in production.)")

    authenticator.logout("Logout", "sidebar")

elif auth_status is False:
    st.error("Invalid username or password")
else:
    st.warning("Please log in to continue")
