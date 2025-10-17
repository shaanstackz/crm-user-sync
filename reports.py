import os
import io
import json
import pandas as pd
from http.server import BaseHTTPRequestHandler, HTTPServer

SALES_FILE = os.getenv("SALES_FILE", "sales.csv")
REVENUE_SHARE = float(os.getenv("REVENUE_SHARE", "0.10"))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if not os.path.exists(SALES_FILE):
                raise FileNotFoundError(f"{SALES_FILE} not found.")

            df = pd.read_csv(
                SALES_FILE,
                skiprows=1,
                names=["date", "email", "purchase_type", "amount"],
                engine="python"
            )

            df["purchase_type"] = df["purchase_type"].astype(str).str.strip()
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

            summary = (
                df.groupby("purchase_type")["amount"]
                .agg(Purchases="count", TotalRevenue="sum")
                .reset_index()
            )

            summary["RevenueShare"] = summary["TotalRevenue"] * REVENUE_SHARE

            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                summary.to_excel(w, index=False, sheet_name="Report")
                pd.DataFrame({"purchase_type": sorted(df["purchase_type"].unique())}).to_excel(
                    w, index=False, sheet_name="PurchaseTypes"
                )
            buf.seek(0)

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            self.send_header("Content-Disposition", "attachment; filename=report.xlsx")
            self.end_headers()
            self.wfile.write(buf.read())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8090"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"🚀 Listening for report requests on port {port}...")
    server.serve_forever()
