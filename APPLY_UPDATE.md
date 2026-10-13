# Apply this update safely (GitHub / Android friendly)

This ZIP is an **overlay patch**, not a full copy of your dataset. It intentionally does not contain or overwrite your source CSVs, existing sample data, `LICENSE`, or prior generated outputs unless named below.

## What is included

- New `index.html` and `dashboard.js`: DDD dashboard with filters, responsive charts, transaction detail search/pagination and a review queue.
- Updated `analyze_sales.py`, tests, SQL schema/queries, README, data dictionary and Birst blueprint.
- New DDD acceptance criteria and research-reference files.
- GitHub Actions workflow under `.github/workflows/ci.yml`.

## Merge into the existing repository

1. Download and extract this ZIP on your phone/computer. It contains overlay files directly (there is no extra parent folder).
2. Open the existing repository: https://github.com/Vikas915577/Sales-Performance-Analytics
3. Upload the extracted files into the **repository root**, preserving `.github/workflows/ci.yml` at that exact path. For same-name files, replace with the ZIP version; add new files alongside the current dataset. On Android, if the uploader cannot see hidden `.github` folders, upload the regular files first, then use **Add file → Create new file** and name it `.github/workflows/ci.yml`; copy the contents from the ZIP.
4. **Keep existing data files**, especially `sales_transactions_sample.csv`, `data_quality_report.json` and `sales_transactions_sql_ready.csv`. The sample CSV is an input and is not bundled in this patch.
5. Commit the upload to `main` with a message such as `Upgrade sales dashboard to DDD workflow`.
6. Open the Actions tab and wait for CI / Pages deployment to finish. Then open https://vikas915577.github.io/Sales-Performance-Analytics/ and check the data-load status.

## Validate locally (or in a Python environment)

```bash
python -m pip install -r requirements.txt
python -m unittest test_analysis.py -v
python analyze_sales.py --input sales_transactions_sample.csv --source-label "Synthetic demo sample" --output-dir .
python -m http.server 8000
```

The analysis command regenerates the output CSVs/JSON/summaries and the `charts/` directory from the source CSV. Review the diff before committing regenerated artifacts. The web dashboard must be served via HTTP so `fetch()` can load the CSV/JSON; direct `file://` opening is expected to fail.

## Birst is a separate implementation

The GitHub dashboard is a standalone web page. The `dashboard_blueprint.md` explains how to build the data model, subject area, Visualizer reports, dashboard pages and filters in an actual Birst practice space. Only claim a live Birst implementation once you have performed that setup and reconciled it.

## Current GitHub integration note

At the time this update was prepared, the connected GitHub integration allowed repository reads but GitHub rejected write calls with a permission error. Therefore this ZIP has **not** changed your online repository yet; you must upload/commit the overlay with your signed-in GitHub account.
