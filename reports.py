"""
reports.py
────────────────────────────────────────────
Generates a detailed Excel report from sales.csv:
- Tracks purchases by customer and purchase type
- Fully GitHub-safe; no company-specific tags or schools
- Revenue share % configurable via environment variable
"""

import os
import io
import json
import pandas as pd
from http.server import BaseHTTPRequestHandler, HTTPServer

# Configuration
SALES_FILE = os.getenv("SALES_FILE", "sales.csv")
REVENUE_SHARE = float(os.getenv("REVENUE_SHARE", "0.10"))  # default 10%

# ─── HTTP Handler ─────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if not os.path.exists(SALES_FILE):
                raise FileNotFoundError(f"{SALES_FILE} not found.")

            # 1) Load CSV
            df = pd.read_csv(
                SALES_FILE,
                skiprows=1,  # skip header written by crm_user_sync
                names=["date","email","purchase_type","amount"],
                engine="python"
            )

            # Ensure purchase_type is string before strip
            df["purchase_type"] = df["purchase_type"].astype(str).str.strip()

            # Ensure amount is numeric
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)


            # 2) Aggregate summary by purchase type
            summary = (
                df.groupby("purchase_type")["amount"]
                  .agg(Purchases="count", TotalRevenue="sum")
                  .reset_index()
            )

            # 3) Add custom revenue share column
            summary["RevenueShare"] = summary["TotalRevenue"] * REVENUE_SHARE

            # 4) Stream Excel in memory
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                summary.to_excel(w, index=False, sheet_name="Report")
                # Optional: include unique purchase types for reference
                pd.DataFrame({"purchase_type": sorted(df["purchase_type"].unique())}) \
                  .to_excel(w, index=False, sheet_name="PurchaseTypes")
            buf.seek(0)

            # 5) Send response
            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            self.send_header(
                "Content-Disposition",
                "attachment; filename=report.xlsx"
            )
            self.end_headers()
            self.wfile.write(buf.read())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type","application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())


# ─── ENTRYPOINT ─────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8090"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"🚀 Listening for report requests on port {port}...")
    server.serve_forever()
