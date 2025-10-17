import pandas as pd
import io

# === SETTINGS ===
SALES_FILE = "sales.csv"              # Local sales log
OUTPUT_FILE = "dashboard_report.xlsx" # Output Excel for Power BI
REVENUE_SHARE = 0.12                  # 12% default; change as needed

def generate_dashboard_report():
    try:
        # 1. Load CSV data
        df = pd.read_csv(SALES_FILE)

        # Ensure minimal columns
        expected_cols = ["date", "email", "purchase_type", "amount"]
        if not all(c in df.columns for c in expected_cols):
            raise ValueError(f"CSV must contain {expected_cols}")

        # Normalize types
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # 2. Aggregate summaries
        total_revenue = df["amount"].sum()
        total_purchases = len(df)

        summary_df = pd.DataFrame([{
            "Total Revenue": total_revenue,
            "Total Purchases": total_purchases,
            f"Revenue Share ({int(REVENUE_SHARE*100)}%)": total_revenue * REVENUE_SHARE
        }])

        # 3. Top customers
        top_customers = (
            df.groupby("email")["amount"]
              .sum()
              .reset_index()
              .sort_values(by="amount", ascending=False)
              .head(10)
        )
        top_customers.rename(columns={"amount": "Total Spent"}, inplace=True)

        # 4. Revenue by purchase type
        revenue_by_type = (
            df.groupby("purchase_type")["amount"]
              .agg(["count", "sum"])
              .reset_index()
              .rename(columns={"count": "Num Purchases", "sum": "Total Revenue"})
              .sort_values(by="Total Revenue", ascending=False)
        )

        # 5. Daily breakdown
        daily = (
            df.groupby(df["date"].dt.date)["amount"]
              .agg(["count", "sum"])
              .reset_index()
              .rename(columns={"count": "Purchases", "sum": "Revenue"})
              .sort_values(by="date")
        )

        # 6. Write to Excel (Power BI ready)
        with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
            summary_df.to_excel(writer, index=False, sheet_name="Summary")
            top_customers.to_excel(writer, index=False, sheet_name="TopCustomers")
            revenue_by_type.to_excel(writer, index=False, sheet_name="ByPurchaseType")
            daily.to_excel(writer, index=False, sheet_name="DailyRevenue")

        print(f"✅ Dashboard report generated: {OUTPUT_FILE}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    generate_dashboard_report()
