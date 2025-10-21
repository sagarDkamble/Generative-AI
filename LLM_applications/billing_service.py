import os, razorpay
from db_service import create_order

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
PRO_PRICE_PAISE = int(os.getenv("PRO_PRICE_PAISE", "19900"))
CURRENCY = os.getenv("CURRENCY", "INR")

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def create_razorpay_order(username):
    order = client.order.create(dict(amount=PRO_PRICE_PAISE, currency=CURRENCY, payment_capture=1))
    # Persist for later verification
    create_order(username=username, order_id=order["id"], amount=PRO_PRICE_PAISE, currency=CURRENCY)
    return order  # contains id, amount, currency, status
