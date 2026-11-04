
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
import re
import secrets
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "diwali_demo.db")

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "local-demo-change-this-secret-key"
)

# Local  admin credentials.
# Change these before putting the website online.
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")

OFFERS = [
    {"id": "offer1", "name": "Diwali Spark", "deposit": 500, "daily": 300, "days": 10, "image": "diwali1.svg", "tag": "FESTIVE PICK"},
    {"id": "offer2", "name": "Golden Glow", "deposit": 1000, "daily": 500, "days": 15, "image": "diwali2.svg", "tag": "POPULAR"},
    {"id": "offer3", "name": "Mega Celebration", "deposit": 1500, "daily": 1500, "days": 15, "image": "diwali3.svg", "tag": "MEGA DEMO"},
    {"id": "offer4", "name": "Double Dhamaka", "deposit": 2000, "daily": 1500, "days": 5, "image": "diwali4.svg", "tag": "SPECIAL"},
    {"id": "offer5", "name": "Grand Dhamaka", "deposit": 5000, "daily": 2000, "days": 5, "image": "diwali4.svg", "tag": "SPECIAL"},
]


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn



def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            demo_wallet INTEGER NOT NULL DEFAULT 0,
            referral_code TEXT UNIQUE NOT NULL,
            referred_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")

        con.execute("""CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            offer_id TEXT NOT NULL,
            offer_name TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")

        con.execute("""CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")

        con.execute("""CREATE TABLE IF NOT EXISTS utr_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            offer_id TEXT NOT NULL,
            utr TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")

        con.execute("""CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            note TEXT,
            status TEXT NOT NULL DEFAULT 'PENDING',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")

        # Add amount column to UTR table
        existing_utr_columns = [
            row["name"]
            for row in con.execute(
                "PRAGMA table_info(utr_submissions)"
            ).fetchall()
        ]

        if "amount" not in existing_utr_columns:
            con.execute(
                "ALTER TABLE utr_submissions ADD COLUMN amount INTEGER NOT NULL DEFAULT 0"
            )

        # Fill demo amounts for older UTR records
        con.execute("""
            UPDATE utr_submissions
            SET amount = CASE offer_id
                WHEN 'offer1' THEN 500
                WHEN 'offer2' THEN 1000
                WHEN 'offer3' THEN 1500
                WHEN 'offer4' THEN 2000
                WHEN 'offer5' THEN 5000
                ELSE 0
            END
            WHERE amount = 0
        """)

        # Add bank details columns to withdrawals table
        columns = [
            "account_holder TEXT",
            "bank_name TEXT",
            "account_number TEXT",
            "ifsc_code TEXT"
        ]

        existing_columns = [
            row["name"]
            for row in con.execute(
                "PRAGMA table_info(withdrawals)"
            ).fetchall()
        ]

        for column in columns:
            column_name = column.split()[0]

            if column_name not in existing_columns:
                con.execute(
                    f"ALTER TABLE withdrawals ADD COLUMN {column}"
                )

        
        # Add amount column to existing UTR records
        existing_utr_columns = [
            row["name"]
            for row in con.execute(
                "PRAGMA table_info(utr_submissions)"
            ).fetchall()
        ]

        if "amount" not in existing_utr_columns:
            con.execute(
                "ALTER TABLE utr_submissions ADD COLUMN amount INTEGER NOT NULL DEFAULT 0"
            )

        # Fill demo amounts for older UTR records
        con.execute("""
            UPDATE utr_submissions
            SET amount = CASE offer_id
                WHEN 'offer1' THEN 500
                WHEN 'offer2' THEN 1000
                WHEN 'offer3' THEN 1500
                WHEN 'offer4' THEN 2000
                WHEN 'offer5' THEN 5000
                ELSE 0
            END
            WHERE amount = 0
        """)


        # New table:  withdrawal requests only
        con.execute("""CREATE TABLE IF NOT EXISTS withdrawals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            note TEXT,
            status TEXT NOT NULL DEFAULT 'PENDING',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")

        
        # Add bank detail columns to existing withdrawals table
        columns = [
            "account_holder TEXT",
            "bank_name TEXT",
            "account_number TEXT",
            "ifsc_code TEXT"
        ]

        existing_columns = [
            row["name"]
            for row in con.execute("PRAGMA table_info(withdrawals)").fetchall()
        ]

        for column in columns:
            column_name = column.split()[0]
            if column_name not in existing_columns:
                con.execute(
                    f"ALTER TABLE withdrawals ADD COLUMN {column}"
                )



def current_user():
    if not session.get("user_id"):
        return None

    with db() as con:
        return con.execute(
            "SELECT * FROM users WHERE id=?",
            (session["user_id"],)
        ).fetchone()


def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapped


def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_globals():
    return {"current_user": current_user(), "demo_mode": True}


@app.route("/")
def index():
    return redirect(
        url_for("dashboard") if current_user() else url_for("login")
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        mobile = re.sub(r"\D", "", request.form.get("mobile", ""))
        password = request.form.get("password", "")
        referral = request.form.get("referral", "").strip().upper() or None

        if len(name) < 2 or len(mobile) != 10 or len(password) < 6:
            flash(
                "Name, 10-digit mobile number aur minimum 6-character password enter karein.",
                "error"
            )
            return render_template("register.html")

        with db() as con:
            if con.execute(
                "SELECT id FROM users WHERE mobile=?", (mobile,)
            ).fetchone():
                flash("Is mobile number se account pehle se bana hua hai.", "error")
                return render_template("register.html")

            if referral and not con.execute(
                "SELECT id FROM users WHERE referral_code=?", (referral,)
            ).fetchone():
                flash("Referral code nahi mila. Referral field blank chhod sakte hain.", "error")
                return render_template("register.html")

            code = "DIW" + secrets.token_hex(3).upper()

            cur = con.execute(
                """INSERT INTO users
                (name, mobile, password_hash, referral_code, referred_by)
                VALUES (?, ?, ?, ?, ?)""",
                (name, mobile, generate_password_hash(password), code, referral)
            )
            user_id = cur.lastrowid

        session["user_id"] = user_id
        flash("Account successfully create ho gaya!", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        mobile = re.sub(r"\D", "", request.form.get("mobile", ""))
        password = request.form.get("password", "")

        with db() as con:
            user = con.execute(
                "SELECT * FROM users WHERE mobile=?", (mobile,)
            ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))

        flash("Mobile number ya password sahi nahi hai.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()

    with db() as con:
        subs = con.execute(
            "SELECT * FROM subscriptions WHERE user_id=? ORDER BY id DESC",
            (user["id"],)
        ).fetchall()

    return render_template(
        "dashboard.html",
        user=user,
        offers=OFFERS,
        subscriptions=subs
    )


@app.route("/wallet")
@login_required
def wallet():
    user = current_user()

    with db() as con:
        txns = con.execute(
            "SELECT * FROM transactions WHERE user_id=? ORDER BY id DESC LIMIT 30",
            (user["id"],)
        ).fetchall()

    return render_template(
        "wallet.html",
        user=user,
        transactions=txns
    )


@app.route("/checkout/<offer_id>")
@login_required
def checkout(offer_id):
    offer = next((o for o in OFFERS if o["id"] == offer_id), None)

    if not offer:
        return redirect(url_for("dashboard"))

    token = secrets.token_urlsafe(18)
    session["checkout_token"] = token

    return render_template(
        "checkout.html",
        offer=offer,
        token=token
    )


@app.route("/simulate-payment", methods=["POST"])
@login_required
def simulate_payment():
    token = request.form.get("token", "")
    offer_id = request.form.get("offer_id", "")
    result = request.form.get("result", "")

    if not token or token != session.get("checkout_token"):
        flash("Checkout session invalid. Dobara try karein.", "error")
        return redirect(url_for("dashboard"))

    offer = next((o for o in OFFERS if o["id"] == offer_id), None)

    if not offer or result not in ("success", "failed"):
        return redirect(url_for("dashboard"))

    user = current_user()
    session.pop("checkout_token", None)

    if result == "success":
        session["pending_utr_offer"] = offer_id
        return redirect(url_for("submit_utr"))

    with db() as con:
        con.execute(
            """INSERT INTO transactions
            (user_id, description, amount, status)
            VALUES (?, ?, ?, ?)""",
            (
                user["id"],
                "Demo checkout: " + offer["name"],
                offer["deposit"],
                "SIMULATED FAILED"
            )
        )

    flash("Demo payment failed. Wallet update nahi hua.", "error")
    return redirect(url_for("wallet"))


@app.route("/submit-utr", methods=["GET", "POST"])
@login_required
def submit_utr():
    offer_id = session.get("pending_utr_offer")

    if not offer_id:
        return redirect(url_for("dashboard"))

    offer = next((o for o in OFFERS if o["id"] == offer_id), None)

    if not offer:
        session.pop("pending_utr_offer", None)
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        utr = request.form.get("utr", "").strip()
        file = request.files.get("payment_screenshot")

        if not re.fullmatch(r"[0-9]{12}", utr):
            flash("Please enter a valid 12-digit UTR number.", "error")
            return render_template("utr.html", offer=offer)

        filename = None
        if file and file.filename != '':
            # Secure filename and save to static/uploads/
            from werkzeug.utils import secure_filename
            filename = secure_filename(file.filename)
            # Unique name banane ke liye timestamp ya random token jod sakte hain
            filename = secrets.token_hex(4) + "_" + filename
            
            upload_folder = os.path.join(BASE_DIR, "static", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            file.save(os.path.join(upload_folder, filename))

        with db() as con:
            # Check if screenshot column exists in utr_submissions, if not add it dynamically
            existing_cols = [row["name"] for row in con.execute("PRAGMA table_info(utr_submissions)").fetchall()]
            if "screenshot" not in existing_cols:
                con.execute("ALTER TABLE utr_submissions ADD COLUMN screenshot TEXT")

            con.execute(
                """INSERT INTO utr_submissions
                (user_id, offer_id, utr, status, amount, screenshot)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    current_user()["id"],
                    offer_id,
                    utr,
                    "PENDING",
                    offer["deposit"],
                    filename
                )
            )

        session.pop("pending_utr_offer", None)

        flash("Demo UTR and payment screenshot submitted successfully. Verification Pending.", "success")
        return redirect(url_for("wallet"))

    return render_template("utr.html", offer=offer)

        
        with db() as con:
            con.execute(
                """INSERT INTO utr_submissions
                (user_id, offer_id, utr, status, amount)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    current_user()["id"],
                    offer_id,
                    utr,
                    "PENDING",
                    offer["deposit"]
                )
            )


        session.pop("pending_utr_offer", None)

        flash(
            "Demo UTR submitted successfully. Verification Pending.",
            "success"
        )
        return redirect(url_for("wallet"))

    return render_template("utr.html", offer=offer)


@app.route("/referral")
@login_required
def referral():
    return render_template("referral.html", user=current_user())


# ---------------- DEMO WITHDRAWAL ----------------


@app.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    user = current_user()

    # Only these fixed  withdrawal amounts are allowed
    allowed_amounts = [500, 1000, 2000, 5000, 10000]

    if request.method == "POST":
        amount_text = request.form.get("amount", "").strip()
        note = request.form.get("note", "").strip()

        if not amount_text.isdigit():
            flash("Please select a valid withdrawal amount.", "error")
            return redirect(url_for("withdraw"))

        amount = int(amount_text)

        if amount not in allowed_amounts:
            flash("Only ₹500, ₹1000, ₹2000, ₹5000 or ₹10000 are allowed.", "error")
            return redirect(url_for("withdraw"))

        with db() as con:
            con.execute(
                """INSERT INTO withdrawals
                (user_id, amount, note, status)
                VALUES (?, ?, ?, 'PENDING')""",
                (user["id"], amount, note[:200])
            )

        flash(
            " withdrawal request submit ho gayi. Wait 24 Hour.",
            "success"
        )
        return redirect(url_for("withdraw"))

    with db() as con:
        requests_list = con.execute(
            """SELECT * FROM withdrawals
            WHERE user_id=? ORDER BY id DESC""",
            (user["id"],)
        ).fetchall()

    return render_template(
        "withdraw.html",
        user=user,
        withdrawals=requests_list
    )


# ---------------- ADMIN LOGIN & DASHBOARD ----------------

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if session.get("is_admin"):
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if (
            secrets.compare_digest(username, ADMIN_USERNAME)
            and secrets.compare_digest(password, ADMIN_PASSWORD)
        ):
            session.clear()
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))

        flash("Admin username ya password galat hai.", "error")

    return render_template("admin_login.html")


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    with db() as con:
        users = con.execute(
            """SELECT id, name, mobile, referral_code, created_at
            FROM users ORDER BY id DESC"""
        ).fetchall()

        utrs = con.execute(
            """SELECT utr_submissions.*, users.name, users.mobile
            FROM utr_submissions
            JOIN users ON users.id = utr_submissions.user_id
            ORDER BY utr_submissions.id DESC"""
        ).fetchall()

        withdrawals = con.execute(
            """SELECT withdrawals.*, users.name, users.mobile
            FROM withdrawals
            JOIN users ON users.id = withdrawals.user_id
            ORDER BY withdrawals.id DESC"""
        ).fetchall()

        total_users = con.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]

        total_utrs = con.execute(
            "SELECT COUNT(*) FROM utr_submissions"
        ).fetchone()[0]

        total_withdrawals = con.execute(
            "SELECT COUNT(*) FROM withdrawals"
        ).fetchone()[0]

        total_transactions = con.execute(
            "SELECT COUNT(*) FROM transactions"
        ).fetchone()[0]

    return render_template(
        "admin_dashboard.html",
        users=users,
        utrs=utrs,
        withdrawals=withdrawals,
        total_users=total_users,
        total_utrs=total_utrs,
        total_withdrawals=total_withdrawals,
        total_transactions=total_transactions
    )



@app.route("/admin/utr/<int:utr_id>", methods=["POST"])
@admin_required
def admin_update_utr(utr_id):
    utr = request.form.get("utr", "").strip()
    amount_text = request.form.get("amount", "").strip()
    status = request.form.get("status", "").upper()

    if not re.fullmatch(r"[0-9]{12}", utr):
        flash("UTR must contain exactly 12 digits.", "error")
        return redirect(url_for("admin_dashboard"))

    if not amount_text.isdigit():
        flash("Please enter a valid demo amount.", "error")
        return redirect(url_for("admin_dashboard"))

    amount = int(amount_text)

    if amount < 0 or amount > 100000:
        flash("Demo amount must be between 0 and 100000.", "error")
        return redirect(url_for("admin_dashboard"))

    if status not in ("PENDING", "VERIFIED", "REJECTED"):
        flash("Invalid UTR status.", "error")
        return redirect(url_for("admin_dashboard"))

    with db() as con:
        result = con.execute(
            """UPDATE utr_submissions
            SET utr=?, amount=?, status=?
            WHERE id=?""",
            (utr, amount, status, utr_id)
        )

        if result.rowcount == 0:
            flash("UTR record not found.", "error")
            return redirect(url_for("admin_dashboard"))

    flash("Demo UTR number, amount and status updated.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/wallet/<int:user_id>", methods=["POST"])
@admin_required
def admin_update_wallet(user_id):
    action = request.form.get("action")
    amount_text = request.form.get("amount", "").strip()

    if action not in ("add", "deduct"):
        flash("Invalid wallet action.", "error")
        return redirect(url_for("admin_dashboard"))

    if not amount_text.isdigit() or int(amount_text) <= 0:
        flash("Sahi amount enter karein.", "error")
        return redirect(url_for("admin_dashboard"))

    amount = int(amount_text)

    with db() as con:
        user = con.execute(
            "SELECT * FROM users WHERE id=?",
            (user_id,)
        ).fetchone()

        if not user:
            flash("User nahi mila.", "error")
            return redirect(url_for("admin_dashboard"))

        current_balance = user["demo_wallet"]

        if action == "add":
            new_balance = current_balance + amount
        else:
            if amount > current_balance:
                flash("Wallet mein itna balance nahi hai.", "error")
                return redirect(url_for("admin_dashboard"))

            new_balance = current_balance - amount

        con.execute(
            "UPDATE users SET demo_wallet=? WHERE id=?",
            (new_balance, user_id)
        )

    flash("Demo wallet update ho gaya.", "success")
    return redirect(url_for("admin_dashboard"))



@app.route("/admin/withdrawal/<int:request_id>", methods=["POST"])
@admin_required
def admin_update_withdrawal(request_id):
    status = request.form.get("status", "").upper()

    if status not in ("PENDING", "APPROVED", "REJECTED"):
        flash("Invalid withdrawal status.", "error")
        return redirect(url_for("admin_dashboard"))

    with db() as con:
        con.execute(
            "UPDATE withdrawals SET status=? WHERE id=?",
            (status, request_id)
        )

    flash("Demo withdrawal status update ho gaya. Koi paisa transfer nahi hua.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/health")
def health():
    return jsonify(status="ok", mode="demo")

import os

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
