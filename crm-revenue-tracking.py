"""
crm_revenue_tracking.py
────────────────────────────────────────────
Simple revenue tracking for CRM purchases.
- Reads sales.csv produced by crm_user_sync.py
- Aggregates total sales, revenue per product, and other stats
- Fully local; no Azure storage required
"""

import os
import csv
from collections import defaultdict

# ─── Configuration ─────────────────────────────────────────────
SALES_FILE = os.getenv("SALES_FILE", "sales.csv")

# ─── UTILITY FUNCTIONS ─────────────────────────────────────────
def read_sales_csv():
    if not os.path.exists(SALES_FILE):
        print(f"No sales data found at {SALES_FILE}")
        return []

    with open(SALES_FILE, "r", newline="") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]
    return rows

def summarize_sales(rows):
    total_sales = len(rows)
    total_revenue = sum(float(r.get("amount", 0) or 0) for r in rows)

    revenue_per_product = defaultdict(float)
    sales_per_product = defaultdict(int)

    for r in rows:
        product = r.get("product", "Unknown")
        amount = float(r.get("amount", 0) or 0)
        revenue_per_product[product] += amount
        sales_per_product[product] += 1

    return {
        "total_sales": total_sales,
        "total_revenue": total_revenue,
        "revenue_per_product": dict(revenue_per_product),
        "sales_per_product": dict(sales_per_product)
    }

def print_summary(summary):
    print("\n📊 CRM Revenue Summary")
    print("="*40)
    print(f"Total sales: {summary['total_sales']}")
    print(f"Total revenue: ${summary['total_revenue']:.2f}")
    print("\nSales per product:")
    for product, count in summary["sales_per_product"].items():
        print(f"  {product}: {count} sale(s)")

    print("\nRevenue per product:")
    for product, revenue in summary["revenue_per_product"].items():
        print(f"  {product}: ${revenue:.2f}")
    print("="*40)

# ─── ENTRYPOINT ─────────────────────────────────────────────
if __name__ == "__main__":
    sales_rows = read_sales_csv()
    if not sales_rows:
        exit(0)

    summary = summarize_sales(sales_rows)
    print_summary(summary)
