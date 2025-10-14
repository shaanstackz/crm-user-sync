"""
crm_user_sync.py
────────────────────────────────────────────
Webhook automation example:
Receives CRM purchase data and syncs user info
to a (mock) user platform — using JSONPlaceholder
as the backend for demonstration.

✅ 100% safe for GitHub and portfolio use.
"""

import os
import uuid
import time
import json
import requests
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

# ─── Configuration ─────────────────────────────────────────────────────────────
MYPLATFORM_BASE_URL = os.getenv("MYPLATFORM_BASE_URL", "https://jsonplaceholder.typicode.com")
DEFAULT_PLAN = os.getenv("MYPLATFORM_DEFAULT_PLAN", "free")

# ─── HTTP-CLASS ENTRYPOINT ─────────────────────────────────────────────────────
class handler(BaseHTTPRequestHandler):
    """Handles incoming CRM webhooks (POST requests)."""

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length)
            event = json.loads(raw_body)
        except Exception as e:
            return self.send_error(400, f"Invalid JSON: {e}")

        # Simulated CRM payload
        purchase = event.get("purchase", {})
        contact = {
            "FirstName": purchase.get("first_name", ""),
            "LastName":  purchase.get("last_name", ""),
            "Email":     purchase.get("email", ""),
            "Product":   purchase.get("product_name", "Unknown Product"),
            "Plan":      purchase.get("plan", DEFAULT_PLAN),
        }

        try:
            result = process_purchase(contact)
            status, body = 200, {"status": "ok", "detail": result}
        except Exception as e:
            status, body = 500, {"error": str(e)}

        response = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

# ─── HTTP Utility with Retry ──────────────────────────────────────────────────
def request_with_retry(url, method="GET", **kwargs):
    """Basic retry logic for API requests."""
    for attempt in range(3):
        try:
            resp = requests.request(method, url, timeout=10, **kwargs)
            resp.raise_for_status()
            return resp
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(0.5 * (attempt + 1))

# ─── Mock "Platform" Functions ────────────────────────────────────────────────
def get_user_by_email(email):
    """Check if a user exists by email (mocked)."""
    # JSONPlaceholder doesn’t really support search, so always return None
    return None

def create_user(contact):
    """Simulate creating a user record."""
    payload = {
        "id": str(uuid.uuid4()),
        "first_name": contact["FirstName"],
        "last_name": contact["LastName"],
        "email": contact["Email"],
        "plan": contact["Plan"],
        "product": contact["Product"],
        "joined": datetime.utcnow().isoformat(),
    }
    resp = request_with_retry(
        f"{MYPLATFORM_BASE_URL}/users",
        method="POST",
        json=payload
    )
    return resp.json()

def update_user(user_id, contact):
    """Simulate updating an existing user record."""
    payload = {
        "plan": contact["Plan"],
        "last_updated": datetime.utcnow().isoformat()
    }
    resp = request_with_retry(
        f"{MYPLATFORM_BASE_URL}/users/{user_id}",
        method="PUT",
        json=payload
    )
    return resp.json()

def send_welcome_email(contact, existing=False):
    """Print simulated welcome email to console."""
    subject = "Welcome Back!" if existing else "🎉 Welcome to MyPlatform!"
    message = (
        f"Hi {contact['FirstName']},\n\n"
        f"Thanks for your {contact['Product']} purchase! "
        f"Your account has been {'updated' if existing else 'created'} "
        f"successfully.\n\n"
        "→ Log in anytime at https://myplatform.example.com/login\n\n"
        "- The MyPlatform Team"
    )
    print("=" * 60)
    print(f"📧 Sending simulated email to {contact['Email']}")
    print(f"Subject: {subject}\n\n{message}")
    print("=" * 60)

# ─── Core Logic ───────────────────────────────────────────────────────────────
def process_purchase(contact):
    """Create or update user based on CRM purchase event."""
    user = get_user_by_email(contact["Email"])

    if user:
        updated = update_user(user["id"], contact)
        send_welcome_email(contact, existing=True)
        return {"action": "updated", "result": updated}
    else:
        new_user = create_user(contact)
        send_welcome_email(contact, existing=False)
        return {"action": "created", "result": new_user}

# ─── Local Dev Entrypoint ─────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), handler)
    print(f"🚀 Listening for CRM webhooks on port {port}...\n")
    print("Try posting sample data with:\n")
    print(
        "curl -X POST http://localhost:8080 "
        "-H 'Content-Type: application/json' "
        "-d '{\"purchase\": {\"first_name\":\"Jane\",\"last_name\":\"Doe\",\"email\":\"jane@example.com\",\"product_name\":\"CRM Pro\",\"plan\":\"gold\"}}'"
    )
    print()
    server.serve_forever()
