# Streamlit GPT Assistant SaaS (Username/Password + Razorpay + PostgreSQL)

Python-only SaaS starter: Streamlit UI + login (streamlit-authenticator), Razorpay subscriptions (checkout), PostgreSQL for chat history.

## Features
- 🔐 Username/password login via `streamlit-authenticator`
- 💬 GPT chat (OpenAI)
- 💳 Razorpay payment (Checkout modal) for Pro plan
- 🗄️ PostgreSQL storage (users, messages, orders)
- ☁️ One-click deploy to Streamlit Cloud (or Render/AWS)

## Quick Start (Local)
1) Create and fill `.env` from `.env.example`.
2) Ensure Postgres is reachable and create a DB (e.g., Neon).
3) Install deps:
   ```bash
   pip install -r requirements.txt
   ```
4) Initialize tables:
   ```bash
   python -c "from db_service import init_db; init_db()"
   ```
5) Run:
   ```bash
   streamlit run app.py
   ```

## Streamlit Cloud Deploy
- Push this folder to a GitHub repo.
- On Streamlit Cloud: New app → select repo → `app.py`.
- Add **Secrets** using the content of your `.env` (one key=value per line).
- Set `OPENAI_API_KEY`, `DATABASE_URL`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `APP_URL`, `PRO_PRICE_PAISE`, `CURRENCY`.

## Razorpay Notes
- This starter uses **Razorpay Orders + Checkout** for a one-time "Pro plan" payment. 
- For recurring subscriptions, switch to Razorpay Subscriptions API and add a small webhook receiver (Render/EC2) to confirm renewals.
- In test mode, use Razorpay test keys and cards.

## Passwords
- Passwords in auth_config.yaml are hashed. To add users, use `hash_passwords.py` or update YAML with hashed values.

## Environment Variables
See `.env.example`.

## File Structure
- `app.py` — Streamlit UI and flow
- `auth_config.yaml` — user credentials (hashed) and cookie settings
- `db_service.py` — Postgres models & helpers
- `gpt_service.py` — OpenAI chat
- `billing_service.py` — Razorpay helper
- `hash_passwords.py` — helper to hash plaintext passwords for YAML

## Upgrading
- Add usage quotas and plan checks inside `app.py` before calling GPT.
- Add webhooks server (FastAPI) to confirm payments and manage subscriptions.
