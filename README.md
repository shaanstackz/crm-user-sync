# 🧠 CRM Automation Suite  

> *When working at numerous companies, I noticed one particular challenge — data was all over the place.*  
> Data is key to everything: decision-making, analytics, and growth. Yet in many organizations, it’s scattered across systems, platforms, and files.  

To combat this, I built a lightweight automation system that keeps CRM purchase data in sync, automatically generates clean financial reports, and powers live dashboards — all without manual data entry.  

---

## 🚀 Overview  
The **CRM Automation Suite** is a collection of simple, modular Python scripts that streamline CRM data management and reporting.  
It automatically syncs customer purchase information, aggregates sales metrics, and outputs dashboard-ready analytics.  

This system demonstrates how automation can bring structure, visibility, and real-time insight to any CRM workflow.  

---

## ⚙️ Features  
| Feature | Script | Description |
|----------|---------|-------------|
| **CRM Purchase Sync** | `crm_user_sync.py` | Captures new CRM purchases and appends them to `sales.csv`. |
| **Revenue Tracking** | `crm_revenue_tracking.py` | Summarizes total sales and revenue by product, generating an at-a-glance terminal summary. |
| **Automated Report Server** | `report_server.py` | Builds an Excel report (`report.xlsx`) and serves it through a lightweight local HTTP server. |
| **Client Dashboard Integration** | `client_dashboard.py` | Prepares the data for Power BI or Excel dashboards, automating the visualization pipeline. |

---

## 📊 Example Output  

### **Terminal Summary (`crm_revenue_tracking.py`)**
```bash
📊 CRM Revenue Summary
========================================
Total sales: 18
Total revenue: $3,250.00

Sales per product:
  Subscription: 10 sale(s)
  License: 5 sale(s)
  Upgrade: 3 sale(s)

Revenue per product:
  Subscription: $1,850.00
  License: $1,000.00
  Upgrade: $400.00
========================================
