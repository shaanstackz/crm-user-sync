"""
crm_user_sync.py
────────────────────────────────────────────
Webhook automation example:
- Receives CRM purchase events
- Creates/updates users on mock platform
- Appends each purchase to sales.csv for revenue tracking
"""

import os
import uuid
import json
import csv
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

# Configuration
MYPLATFORM_BASE_URL = os.getenv("MYPLATFORM_BASE_URL", "https://jsonplaceholder.typicode.com")
DEFAULT_PLAN = os.getenv("MYPLATFORM_DEFAULT_PLAN", "free")
SALES_FILE = os.getenv("SALES_FILE", "sales.csv")

# ─── HTTP Handler ─────────────────────────────────────────────
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length))
        except Exception as e:
            self._send_error(400, f"Invalid JSON: {e}")
            return

        txn = payload.get("purchase", {})
        email = txn.get("email")
        product = txn.get("product_name", "Unknown Product")
        amount = txn.get("amount") or "0"
        date = txn.get("date") or datetime.utcnow().isoformat()

        contact = {
            "FirstName": txn.get("first_name", "First"),
            "LastName":  txn.get("last_name", "Last"),
            "Email":     email,
            "Product":   product,
            "Plan":      txn.get("plan", DEFAULT_PLAN),
        }

        try:
            # User creation/updating
            user_result = process_purchase(contact)

            # Append to sales.csv for revenue tracking
            append_to_sales_csv(date, email, product, amount, contact["Plan"])

            self._send_response({
                "status": "success",
                "user_action": user_result["action"],
                "rows_written": get_sales_row_count()
            })
        except Exception as e:
            self._send_error(500, str(e))

    # ─── Helpers ─────────────────────────────
    def _send_response(self, data):
        resp = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)

    def _send_error(self, code, message):
        resp = json.dumps({"error": message}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp)))
        self.end_headers()
        self.wfile.write(resp)

# ─── USER PLATFORM FUNCTIONS ──────────────────────────────────────────────
def request_with_retry(url, method="GET", **kwargs):
    for attempt in range(3):
        try:
            resp = requests.request(method, url, timeout=10, **kwargs)
            resp.raise_for_status()
            return resp
        except Exception:
            if attempt == 2:
                raise
            import time; time.sleep(0.5*(attempt+1))

def get_user_by_email(email):
    return None  # Always create new for demo

def create_user(contact):
    payload = {
        "id": str(uuid.uuid4()),
        "first_name": contact["FirstName"],
        "last_name": contact["LastName"],
        "email": contact["Email"],
        "plan": contact["Plan"],
        "product": contact["Product"],
        "joined": datetime.utcnow().isoformat(),
    }
    resp = request_with_retry(f"{MYPLATFORM_BASE_URL}/users", method="POST", json=payload)
    return resp.json()

def update_user(user_id, contact):
    payload = {
        "plan": contact["Plan"],
        "last_updated": datetime.utcnow().isoformat()
    }
    resp = request_with_retry(f"{MYPLATFORM_BASE_URL}/users/{user_id}", method="PUT", json=payload)
    return resp.json()

def send_welcome_email(contact, existing=False):
    subject = "Welcome Back!" if existing else "🎉 Welcome to MyPlatform!"
    message = (
        f"Hi {contact['FirstName']},\n\n"
        f"Thanks for your {contact['Product']} purchase! "
        f"Your account has been {'updated' if existing else 'created'}.\n\n"
        "→ Log in at https://myplatform.example.com/login\n\n"
        "- The MyPlatform Team"
    )
    print("="*50)
    print(f"📧 Simulated email to {contact['Email']}\nSubject: {subject}\n{message}")
    print("="*50)

def process_purchase(contact):
    user = get_user_by_email(contact["Email"])
    if user:
        updated = update_user(user["id"], contact)
        send_welcome_email(contact, existing=True)
        return {"action": "updated", "result": updated}
    else:
        new_user = create_user(contact)
        send_welcome_email(contact, existing=False)
        return {"action": "created", "result": new_user}

# ─── SALES CSV FUNCTIONS ──────────────────────────────────────────────
def append_to_sales_csv(date, email, product, amount, plan):
    header = ["date", "email", "product", "amount", "plan"]
    rows = []
    if os.path.exists(SALES_FILE):
        with open(SALES_FILE, "r", newline="") as f:
            reader = csv.reader(f)
            rows = [r for r in reader if len(r)==5 and r[0] != "date"]
    rows.append([date, email, product, amount, plan])
    with open(SALES_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

def get_sales_row_count():
    if not os.path.exists(SALES_FILE):
        return 0
    with open(SALES_FILE, "r") as f:
        return sum(1 for _ in f) - 1  # exclude header

# ─── ENTRYPOINT ─────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"🚀 Listening for CRM webhook events on port {port}...")
    server.serve_forever()
