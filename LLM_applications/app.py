import os
import yaml
import json
import streamlit as st
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from dotenv import load_dotenv

# Local imports
from gpt_service import get_gpt_response
from db_service import save_message, init_db, mark_order_paid
from billing_service import create_razorpay_order


# ----------------------------------------------------------
# 1. Basic setup
# ----------------------------------------------------------
st.set_page_config(page_title="AI Personal Assistant", page_icon="🤖", layout="wide")
load_dotenv()
init_db()

# Environment variables (from Streamlit Secrets or local .env)
APP_URL = os.getenv("APP_URL", "http://localhost:8501")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")

# ----------------------------------------------------------
# 2. Load authentication config (auth_config.yaml)
# ----------------------------------------------------------
try:
    # Read YAML relative to this file so deployments find it even when working dir differs
    cfg_path = os.path.join(os.path.dirname(__file__), "auth_config.yaml")
    with open(cfg_path) as f:
        config = yaml.load(f, Loader=SafeLoader)
except FileNotFoundError:
    st.error("❌ 'auth_config.yaml' not found. Please ensure it's uploaded to your repository.")
    st.stop()

# ----------------------------------------------------------
# 3. Initialize authenticator (robust across streamlit-authenticator versions)
# ----------------------------------------------------------
# Different streamlit-authenticator versions use different ctor signatures/kw names.
# Try the modern signature first (cookie_key), fall back to older alternatives.
def _init_authenticator(cfg):
    # Try modern (v0.3.x+) named args
    try:
        return stauth.Authenticate(
            credentials=cfg["credentials"],
            cookie_name=cfg["cookie"]["name"],
            cookie_key=cfg["cookie"]["key"],
            cookie_expiry_days=cfg["cookie"]["expiry_days"],
        )
    except TypeError:
        pass

    # Try alternative keyword 'key'
    try:
        return stauth.Authenticate(
            credentials=cfg["credentials"],
            cookie_name=cfg["cookie"]["name"],
            key=cfg["cookie"]["key"],
            cookie_expiry_days=cfg["cookie"]["expiry_days"],
        )
    except TypeError:
        pass

    # Last-resort: positional args used by very old versions
    return stauth.Authenticate(
        cfg["credentials"],
        cfg["cookie"]["name"],
        cfg["cookie"]["key"],
        cfg["cookie"]["expiry_days"],
    )


authenticator = _init_authenticator(config)

# ----------------------------------------------------------
# 4. Login form (robust location handling)
# ----------------------------------------------------------
# streamlit-authenticator implementations require location to be one of:
# 'main', 'sidebar', or 'unrendered'. Some versions accept `location` keyword.
def _safe_login(auth):
    # preferred: keyword argument
    try:
        return auth.login("Login", location="sidebar")
    except TypeError:
        # fallback: positional form
        try:
            return auth.login("Login", "main")
        except Exception as e:
            raise e
    except Exception as e:
        raise e

try:
    name, auth_status, username = _safe_login(authenticator)
except Exception as e:
    st.error(f"⚠️ Login error: {e}")
    st.stop()

# ----------------------------------------------------------
# 5. Authenticated section
# ----------------------------------------------------------
if auth_status:
    st.sidebar.success(f"Welcome {name} 👋")
    # logout: try keyword then positional
    try:
        authenticator.logout("Logout", location="sidebar")
    except TypeError:
        try:
            authenticator.logout("Logout", "sidebar")
        except Exception:
            # If logout fails for any reason, continue (it shouldn't break app)
            pass

    st.title("💬 GPT Personal Assistant")

    if "history" not in st.session_state:
        st.session_state.history = []  # chat history

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
        st.info("Complete your payment below 👇")

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

    qs = st.query_params
    if qs.get("payment_status") == ["paid"] and "order_id" in qs:
        order_id = qs["order_id"][0] if isinstance(qs["order_id"], list) else qs["order_id"]
        mark_order_paid(order_id)
        st.success("✅ Payment successful! You are now on the Pro plan.")

# ----------------------------------------------------------
# 6. Invalid / No authentication
# ----------------------------------------------------------
elif auth_status is False:
    st.error("❌ Invalid username or password")
else:
    st.warning("Please log in to continue")
