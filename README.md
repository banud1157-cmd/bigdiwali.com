# DIWALI OFFERS — Demo Website

A responsive, local-only demonstration project for VS Code. It includes:
- SQLite database (created automatically at first run)
- Registration and login using name, mobile number and password
-  wallet, offers, referral code and transaction history
- Five-minute  checkout timer with explicit **Simulate Success** / **Simulate Failure** controls
- Responsive layout for desktop and mobile

## Important
This is a **simulation only**. It does not accept real payments, create real financial products,
promise earnings, send OTPs, or provide cash withdrawals. The QR shown is a placeholder and
must not be used to collect money.  wallet balances and rewards have no monetary value.

## Run in VS Code (Windows)
1. Install Python 3.10+.
2. Open this folder in VS Code.
3. Open Terminal → New Terminal.
4. Run:
   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
   ```
5. Open `http://127.0.0.1:5000` in Chrome.

If `py` is unavailable, use `python` instead.


The SQLite database is created as `diwali_demo.db` in this folder. Do not use this demo
configuration to store real customer information. Before any real public service, obtain
appropriate legal advice, implement privacy/security controls, and use an authorized payment
provider. Never collect or store payment PINs, UPI PINs, or OTPs for payments.
