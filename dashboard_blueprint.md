# BI dashboard blueprint: Sales Performance Analytics

## Intended audience
Sales operations, commercial leadership, and BI/reporting stakeholders reviewing sales trend and product/country contribution.

## Page 1 — Executive Overview

**KPI cards**
- Gross sales on retained positive lines
- Distinct orders
- Average order value (AOV)
- Units sold
- Distinct known customers

**Visuals**
- Monthly gross sales line chart
- Orders by month (supporting line/column chart)
- Top 10 products by sales value
- Top 10 countries by sales value

**Filters**
- Invoice date / month
- Country
- Product / stock code

## Page 2 — Product & geography

- Bar chart: sales by product description
- Bar chart: sales by country
- Table with stock code, description, sales value, units sold and distinct orders
- Contribution % by country/product (carefully define denominator)

## Page 3 — Data quality & definition notes

- Input rows, retained rows, excluded rows
- Cancellation-like invoice row count
- Non-positive quantity and price flags (overlapping flags)
- Missing customer identifiers (do not automatically treat as invalid sales)
- A plain-language metric definition and the reporting period

## Suggested model

**Fact table:** `retail_transactions` at invoice line grain. Measures: `line_revenue`, `quantity`, distinct order count. Dimensions: Date, Product/Stock Code, Country, Customer (where ID is present). Use an explicit date dimension for time-intelligence.

**Data grain:** one row per source transaction line, not one row per invoice.

## Infor Birst build notes

1. Import the normalized CSV output as a source or load it through the team's approved data pipeline.
2. Check types: invoice date as date/time, quantity and price as numeric, stock code and invoice number as text.
3. Define a calculated measure `Line Revenue = Quantity * Unit Price` if not using the precomputed column.
4. Create a retained-sales filter matching the Python rule: invoice number does not begin with `C`, quantity > 0, unit price > 0, and valid invoice date.
5. Build the KPI cards and visuals above; compare a few filtered totals against `kpi_summary.json` and the CSV summaries.
6. Take a screenshot only after validation; do not represent this blueprint as a dashboard already built or deployed.

## Power BI build notes

Import `sales_transactions_sql_ready.csv`, set data types, create a Date table, relate it to the fact table, and reproduce the KPI cards and visuals. Reconcile totals to Python output after filters are applied.

## Limitations

The filtering approach is for a portfolio sales trend analysis, not audited financial reporting. It excludes cancellation invoices and non-positive rows, so the headline total is not net revenue after returns. Country/product rankings are descriptive and do not establish causality or profitability because cost and margin data are unavailable.
