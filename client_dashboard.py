import pandas as pd
import io
import os


SALES_FILE = "sales.csv"
OUTPUT_FILE = "dashboard_report.xlsx"
REVENUE_SHARE = 0.12  

def generate_dashboard_report():
    try:
        if not os.path.exists(SALES_FILE):
            raise FileNotFoundError(f"{SALES_FILE} not found.")

        df = pd.read_csv(SALES_FILE)

        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        rename_map = {}

        for col in df.columns:
            if "sale" in col and "tag" in col:
                rename_map[col] = "purchase_type"
            elif "type" in col and "purchase" in col:
                rename_map[col] = "purchase_type"
            elif "school" in col or "org" in col:
                rename_map[col] = "organization"

        df.rename(columns=rename_map, inplace=True)

        required = ["date", "email", "amount"]
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing column: {col}")

        if "purchase_type" not in df.columns:
            print("⚠️  'purchase_type' not found — assigning 'Unknown'")
            df["purchase_type"] = "Unknown"


        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        total_revenue = df["amount"].sum()
        total_purchases = len(df)

        summary_df = pd.DataFrame([{
            "Total Revenue": total_revenue,
            "Total Purchases": total_purchases,
            f"Revenue Share ({int(REVENUE_SHARE*100)}%)": total_revenue * REVENUE_SHARE
        }])

        top_customers = (
            df.groupby("email")["amount"]
              .sum()
              .reset_index()
              .sort_values(by="amount", ascending=False)
              .head(10)
        )
        top_customers.rename(columns={"amount": "Total Spent"}, inplace=True)

        revenue_by_type = (
            df.groupby("purchase_type")["amount"]
              .agg(["count", "sum"])
              .reset_index()
              .rename(columns={"count": "Num Purchases", "sum": "Total Revenue"})
              .sort_values(by="Total Revenue", ascending=False)
        )

        org_tab = None
        if "organization" in df.columns:
            org_tab = (
                df.groupby("organization")["amount"]
                  .agg(["count", "sum"])
                  .reset_index()
                  .rename(columns={"count": "Num Purchases", "sum": "Total Revenue"})
                  .sort_values(by="Total Revenue", ascending=False)
            )

        daily = (
            df.groupby(df["date"].dt.date)["amount"]
              .agg(["count", "sum"])
              .reset_index()
              .rename(columns={"count": "Purchases", "sum": "Revenue"})
              .sort_values(by="date")
        )

        with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
            summary_df.to_excel(writer, index=False, sheet_name="Summary")
            top_customers.to_excel(writer, index=False, sheet_name="TopCustomers")
            revenue_by_type.to_excel(writer, index=False, sheet_name="ByPurchaseType")
            daily.to_excel(writer, index=False, sheet_name="DailyRevenue")
            if org_tab is not None:
                org_tab.to_excel(writer, index=False, sheet_name="ByOrganization")

        print(f"✅ Dashboard report generated: {OUTPUT_FILE}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    generate_dashboard_report()
