"""
crm_user_sync.py
────────────────────────────────────────────
A webhook receiver that listens for CRM purchase events
and automatically syncs user data into your own platform.

Use this as a safe, open-source automation example.
"""

import os
import uuid
import time
import json
import requests
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

# ─── Environment ────────────────────────────────────────────────────────────────
# Example env vars (set in your GitHub Actions or .env file)
MYPLATFORM_API_TOKEN = os.getenv("MYPLATFORM_API_TOKEN", "demo_token")
MYPLATFORM_BASE_URL  = os.getenv("MYPLATFORM_BASE_URL", "https://api.myplatform.io")
DEFAULT_PLAN         = os.getenv("MYPLATFORM_DEFAULT_PLAN", "free")

# ─── HTTP-CLASS ENTRYPOINT ──────────────────────────────────────────────────────
class handler(BaseHTTPRequestHandler):
    """Handles incoming CRM webhooks (POST requests)."""

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length)
            event = json.loads(raw_body)
        except Exception as e:
            return self.send_error(400, f"Invalid JSON: {e}")

        # Parse minimal customer info from CRM event
        purchase = event.get("purchase", {})
        contact = {
            "FirstName": purchase.get("first_name", ""),
            "LastName":  purchase.get("last_name", ""),
            "Email":     purchase.get("email", ""),
            "Product":   purchase.get("product_name", "Unknown"),
            "Plan":      purchase.get("plan", DEFAULT_PLAN),
        }

        try:
            result = process_purchase(contact)
            status, body = 200, {"status": "ok", "detail": result}
        except Exception as e:
            status, body = 500, {"error": str(e)}

        # Send response
        response = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

# ─── HELPER FUNCTIONS ──────────────────────────────────────────────────────────
def request_with_retry(url, method="GET", **kwargs):
    """HTTP request helper with retry logic."""
    for attempt in range(3):
        try:
            resp = requests.request(method, url, timeout=15, **kwargs)
            resp.raise_for_status()
            return resp
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(0.5 * (attempt + 1))

def get_headers():
    """Return authorization headers for MyPlatform API."""
    return {
        "Authorization": f"Bearer {MYPLATFORM_API_TOKEN}",
        "Content-Type": "application/json"
    }

def get_user_by_email(email):
    """Check if a user exists by email."""
    resp = request_with_retry(
        f"{MYPLATFORM_BASE_URL}/users",
        method="GET",
        params={"email": email},
        headers=get_headers()
    )
    data = resp.json()
    return data[0] if isinstance(data, list) and data else None

def create_user(contact):
    """Create a new user on MyPlatform."""
    payload = {
        "id": str(uuid.uuid4()),
        "first_name": contact["FirstName"],
        "last_name": contact["LastName"],
        "email": contact["Email"],
        "plan": contact["Plan"],
        "joined": datetime.utcnow().isoformat(),
    }
    resp = request_with_retry(
        f"{MYPLATFORM_BASE_URL}/users",
        method="POST",
        headers=get_headers(),
        json=payload
    )
    return resp.json()

def update_user(user_id, contact):
    """Update existing user's plan or details."""
    payload = {
        "plan": contact["Plan"],
        "last_updated": datetime.utcnow().isoformat()
    }
    resp = request_with_retry(
        f"{MYPLATFORM_BASE_URL}/users/{user_id}",
        method="PUT",
        headers=get_headers(),
        json=payload
    )
    return resp.json()

def send_welcome_email(contact, existing=False):
    """Simulated email send (replace with SendGrid/Mailgun in real use)."""
    subject = (
        "Welcome back!" if existing
        else "🎉 Welcome to MyPlatform!"
    )
    body = (
        f"Hi {contact['FirstName']},\n\n"
        f"Thanks for your {contact['Product']} purchase! "
        f"Your account is now {'updated' if existing else 'created'} "
        f"and ready to use.\n\n"
        "Log in anytime at https://myplatform.io/login\n\n"
        "- The MyPlatform Team"
    )
    print(f"Simulated email to {contact['Email']}:\n{subject}\n{body}\n")

# ─── MAIN PROCESS ──────────────────────────────────────────────────────────────
def process_purchase(contact):
    """Create or update user based on CRM purchase event."""
    existing_user = get_user_by_email(contact["Email"])

    if existing_user:
        result = update_user(existing_user["id"], contact)
        send_welcome_email(contact, existing=True)
        return {"action": "updated", "user_id": existing_user["id"], "result": result}
    else:
        new_user = create_user(contact)
        send_welcome_email(contact, existing=False)
        return {"action": "created", "user_id": new_user.get("id"), "result": new_user}

# ─── LOCAL DEV ENTRYPOINT ──────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"🚀 Listening for CRM webhooks on port {port}...")
    server.serve_forever()
