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
@@ -152,38 +151,98 @@ if auth_status:
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
    def _get_query_params():
        """Return query parameters as {str: [str, ...]} across Streamlit versions."""

        # Modern API (Streamlit 1.30+)
        qs_obj = getattr(st, "query_params", None)
        if qs_obj is not None:
            try:
                items = qs_obj.items()
            except TypeError:
                items = dict(qs_obj).items()

            normalized = {}
            for key, value in items:
                if isinstance(value, (list, tuple)):
                    normalized[key] = list(value)
                elif value is None:
                    normalized[key] = []
                else:
                    normalized[key] = [value]
            return normalized

        # Legacy experimental API (pre-1.30)
        getter = getattr(st, "experimental_get_query_params", None)
        if getter is None:
            return {}
        legacy_params = getter() or {}
        return {key: list(value) for key, value in legacy_params.items()}

    def _clear_query_params(*keys):
        """Remove selected query parameters without breaking on Streamlit versions."""

        qs_obj = getattr(st, "query_params", None)
        if qs_obj is not None:
            try:
                if keys:
                    for key in keys:
                        if key in qs_obj:
                            del qs_obj[key]
                else:
                    qs_obj.clear()
                return
            except Exception:
                # Fall back to experimental API when mutation fails.
                pass

        getter = getattr(st, "experimental_get_query_params", None)
        setter = getattr(st, "experimental_set_query_params", None)
        if getter is None or setter is None:
            return

        remaining = getter() or {}
        if keys:
            for key in keys:
                remaining.pop(key, None)
        else:
            remaining = {}
        setter(**remaining)

    qs = _get_query_params()
    if qs.get("payment_status") == ["paid"] and "order_id" in qs:
        order_id = qs["order_id"][0] if isinstance(qs["order_id"], list) else qs["order_id"]
        order_id_values = qs["order_id"]
        order_id = order_id_values[0] if isinstance(order_id_values, list) else order_id_values
        mark_order_paid(order_id)
        st.success("✅ Payment successful! You are now on the Pro plan.")
        _clear_query_params("payment_status", "order_id")

# ----------------------------------------------------------
# 6. Invalid / No authentication
# ----------------------------------------------------------
elif auth_status is False:
    st.error("❌ Invalid username or password")
else:
    st.warning("Please log in to continue")
