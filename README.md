# Sales Performance Analytics — DDD portfolio project

An interview-friendly sales analytics project built around **Display → Diagnose → Decide**. It combines a responsive interactive dashboard, reproducible Python/pandas analysis, PostgreSQL reporting queries, data-quality checks, automated tests and an Infor Birst implementation blueprint.

- **GitHub:** https://github.com/Vikas915577/Sales-Performance-Analytics
- **GitHub Pages:** https://vikas915577.github.io/Sales-Performance-Analytics/

> **Data disclosure:** The current bundled metrics were calculated from a small synthetic sample for testing. They are not actual commercial/employer/client results. The Birst material is a build blueprint, not proof of a live Birst tenant deployment.

## Business user story

**As a sales operations manager, I want to see whether sales are changing, diagnose which periods/countries/merchandise items contribute to the pattern, and prioritize what to investigate next—so I can focus attention on evidence rather than guesswork.**

## Dashboard: Display → Diagnose → Decide

| Stage | Main question | What the dashboard provides |
|---|---|---|
| **Display** | What is happening? | Retained-line sales, merchandise sales, postage share, orders, AOV, units, date/source context |
| **Diagnose** | What contributes and what should be checked? | Date/country/type/product filters, monthly trend, contribution charts, line-level details and quality flags |
| **Decide** | What should be investigated next? | Evidence-backed review queue with rationale and accountable owner; no automated business actions |

The dashboard uses HTML/CSS/vanilla JavaScript and inline SVG charts—no CDN chart dependency. Filters should update all dependent KPIs, charts, table rows and review prompts. The detail table supports search and pagination.

## Key analysis improvement

**Shipping/postage is not a merchandise product.** The current sample previously showed `POSTAGE` as the top “product” because the source row was treated like any merchandise item. The updated pipeline adds `line_type` classification and separates:

- **Gross sales on retained lines:** includes eligible retained postage/shipping rows; not accounting net revenue.
- **Merchandise sales:** excludes lines classified as postage/shipping.
- **Postage/shipping share:** shipping charges divided by retained-line sales in the same filter context.

Rules classify common codes such as `POST`/`POSTAGE` and explicit postage/shipping labels. Verify those source mappings before using a different dataset. Cost/margin fields are absent, so the project does not claim product profitability or ROI.

## Tools and technical work

- Python 3.10+, pandas and matplotlib
- PostgreSQL-compatible SQL and an explicit transaction-line schema
- HTML, CSS and vanilla JavaScript for the responsive dashboard
- GitHub Pages for hosting the standalone project page
- Infor Birst: documented fact/dimension model, business-friendly subject area, Visualizer reports, dashboard filters/KPI dashlets and DDD page plan (manual tenant setup remains separate)
- GitHub Actions CI for unit tests, output build and JavaScript syntax check

## Run locally

From the repository root, install dependencies and run:

```bash
python -m pip install -r requirements.txt
python -m unittest test_analysis.py -v
python analyze_sales.py --input sales_transactions_sample.csv --source-label "Synthetic demo sample" --output-dir .
```

**Important:** the last command regenerates the root output CSVs, JSON reports, summaries and `charts/` images from the selected input. It does not modify `sales_transactions_sample.csv`. Commit updated output files only if you intentionally want to publish the refreshed generated results.

Run the static website on an HTTP server (not by opening the HTML as a `file://` URL) so the browser can fetch the CSV/JSON:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000`. On GitHub Pages, verify `index.html`, `dashboard.js`, `sales_transactions_sql_ready.csv` and `data_quality_report.json` are all accessible from the repository root.

## Repo guide

- `index.html`, `dashboard.js` — responsive interactive dashboard.
- `analyze_sales.py` — loading, cleaning, classification, aggregation, KPI/quality output and charts.
- `test_analysis.py` — cleaning, line classification and output-contract tests.
- `00_schema.sql`, `01_business_queries.sql`, `02_quality_checks.sql` — PostgreSQL model and analyses.
- `data_dictionary.md` — field/metric definitions and assumptions.
- `DDD_USER_STORY_AND_ACCEPTANCE_CRITERIA.md` — user journey, metrics and testable acceptance criteria.
- `dashboard_blueprint.md`, `RESEARCH_REFERENCES.md` — Birst build and validation notes.
- `APPLY_UPDATE.md` — safe overlay instructions for the supplied update ZIP.

## Responsible use and limitations

- The sample is synthetic; do not put its values on your resume as real business impact.
- Exclusion flags may overlap; do not add flag counts as if they were unique rejected rows.
- Rankings and month-over-month changes are descriptive signals, not causal findings.
- No cost/margin data means no profitability, ROI or margin recommendation.
- Do not infer current performance, seasonality or forecast accuracy from an old/synthetic time window.
- Use only synthetic, licensed public or permissioned data; add source, license, covered period and currency when swapping the dataset.
- Do not describe Birst as deployed until an actual Birst space has been configured and its filters/KPIs reconciled to Python/SQL.
