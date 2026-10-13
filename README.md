# Sales Performance Analytics

A reproducible business-intelligence portfolio demo for sales trends, product/country contribution, order metrics and transaction quality. The analysis pipeline uses Python/pandas; SQL scripts provide a PostgreSQL reporting layer; the dashboard blueprint is designed for **Infor Birst**.

**Project website:** https://vikas915577.github.io/Sales-Performance-Analytics/  
**GitHub repository:** https://github.com/Vikas915577/Sales-Performance-Analytics

> **Data disclosure:** the charts and KPI figures currently bundled in this repository were generated from a small synthetic demo sample to test the pipeline. They are not real employer/client results and must not be presented as actual commercial findings. This project includes an Infor Birst dashboard blueprint; it does not claim a live Birst dashboard has already been built or deployed.

## What the project covers

- Normalize common variations in transaction CSV/XLSX column names.
- Flag cancellation-like invoices and non-positive/missing quantities or prices.
- Parse transaction dates and create a documented retained-sales dataset.
- Calculate monthly sales, orders, average order value, units, product rankings, country rankings and known-customer summaries.
- Export quality checks and chart images.
- Provide PostgreSQL schema and business queries for a normalized transaction-line table.
- Define an Infor Birst fact/dimension model, proposed measures, dashboard pages and validation steps.

## Demo KPI snapshot

These figures apply **only to the bundled synthetic sample**:

| Metric | Demo result |
|---|---:|
| Input rows | 383 |
| Rows retained after the documented filter | 368 |
| Gross sales on retained lines | 5,313.78 dataset currency units |
| Distinct orders | 50 |
| Average order value | 106.28 dataset currency units |
| Units sold | 1,082 |
| Known customers | 40 |
| Demo date range | 2010-12-04 to 2011-11-27 |

“Gross sales on retained lines” is the sum of positive retained transaction lines after excluding cancellation-like invoices, non-positive or missing quantities/prices, and invalid dates. It is **not accounting net revenue**. Currency is not assumed.

## Quick start

Python 3.10+ is recommended.

~~~bash
python -m pip install -r requirements.txt
python analyze_sales.py --input sales_transactions_sample.csv --source-label "Synthetic demo sample" --output-dir outputs/demo
python -m unittest test_analysis.py -v
~~~

The analysis command writes cleaned CSVs, KPI JSON, a data-quality JSON report, a findings summary and charts to the selected output folder.

To analyze a real source file, download the official UCI Online Retail dataset and pass its CSV/XLSX path to `--input`. Cite the source dataset, analysis period and filtering rules in any published findings. Do not quote the sample values above as findings from the UCI dataset.

## Key files

- [Project landing page](index.html) — responsive project overview and charts.
- [Python analysis script](analyze_sales.py) — loading, cleaning, aggregation and chart generation.
- [SQL schema](00_schema.sql) — PostgreSQL transaction-line table.
- [Business queries](01_business_queries.sql) — KPIs, monthly sales, country/product and customer analysis.
- [Quality checks](02_quality_checks.sql) — queries for a separate raw staging table; create/import that table before running them.
- [Infor Birst dashboard blueprint](dashboard_blueprint.md) — suggested model, measures, report pages and validation.
- [Data dictionary](data_dictionary.md) — field definitions and handling notes.
- [Demo findings](analysis_summary.md) and [quality report](data_quality_report.json).
- [Demo-only warning](DEMO_NOTICE.md).

## SQL setup

1. Open PostgreSQL and run `00_schema.sql`.
2. Run the Python command above to create `outputs/demo/sales_transactions_sql_ready.csv`.
3. Import that CSV into the `retail_transactions` table, matching the columns in the schema, or use a command similar to this after replacing the path:

~~~sql
\copy retail_transactions(invoice_no, stock_code, description, quantity, invoice_date, unit_price, customer_id, country, line_revenue) FROM '/absolute/path/outputs/demo/sales_transactions_sql_ready.csv' WITH (FORMAT csv, HEADER true, NULL '');
~~~

4. Run `01_business_queries.sql`.
5. `02_quality_checks.sql` assumes a separate table named `retail_raw` with the original source field names. It is a template and requires that staging table to exist first.

## Infor Birst approach

The model blueprint treats each retained transaction line as a fact row, with Date, Product/Stock Code, Country and Customer (where known) as dimensions. Suggested measures include retained-line gross sales, quantity, distinct orders and average order value. Build the KPI tiles, monthly trend, product/country rankings and data-quality view in a practice/demo space, then reconcile selected totals against the Python outputs. Add a Birst screenshot only after you have actually built and validated the dashboard.

## Important limitations

- Current bundled figures are synthetic demonstration outputs only.
- The script does not add margin/profit analysis because product-cost data is not supplied.
- Country and product rankings are descriptive and do not establish causation.
- Missing customer IDs are excluded from customer counts but are not automatically treated as invalid sales.
- This is a portfolio exercise, not audited financial reporting.

## Before using this on your resume

1. Run the pipeline on the official public dataset and save the new outputs separately.
2. Verify the cleaning rules and explain them in your own words.
3. Build and test the proposed dashboard in Infor Birst before claiming hands-on dashboard implementation for this project.
4. Replace synthetic charts on the website only after validating real-data outputs.
5. Never add company/client data or unverified percentages to GitHub or your resume.
