"""Reproducible sales analysis for UCI Online Retail or compatible CSV/XLSX files."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import pandas as pd
import matplotlib.pyplot as plt

REQUIRED_COLUMNS = ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"]
CANONICAL = {re.sub(r"[^a-z0-9]", "", c.lower()): c for c in REQUIRED_COLUMNS}


def load_input(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}\nDownload the UCI Online Retail file or use the bundled sample CSV. See README.md.")
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    elif suffix == ".csv":
        df = pd.read_csv(path, encoding_errors="replace")
    else:
        raise ValueError("Supported input types are .xlsx, .xls and .csv")
    # Normalize common CSV variations (case, spaces, punctuation).
    mapped = {}
    for col in df.columns:
        key = re.sub(r"[^a-z0-9]", "", str(col).lower())
        if key in CANONICAL:
            mapped[col] = CANONICAL[key]
    df = df.rename(columns=mapped)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}. Found: {list(df.columns)}")
    return df[REQUIRED_COLUMNS].copy()


def prepare_data(raw: pd.DataFrame):
    df = raw.copy()
    rows_input = len(df)
    df["InvoiceNo"] = df["InvoiceNo"].astype("string").str.strip()
    df["StockCode"] = df["StockCode"].astype("string").str.strip()
    df["Description"] = df["Description"].astype("string").str.strip()
    df["Country"] = df["Country"].astype("string").str.strip()
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce", dayfirst=True)
    df["line_revenue"] = df["Quantity"] * df["UnitPrice"]
    df["is_cancelled_invoice"] = df["InvoiceNo"].str.upper().str.startswith("C", na=False)
    df["invalid_quantity"] = df["Quantity"].isna() | (df["Quantity"] <= 0)
    df["invalid_unit_price"] = df["UnitPrice"].isna() | (df["UnitPrice"] <= 0)
    df["invalid_invoice_date"] = df["InvoiceDate"].isna()
    df["missing_customer_id"] = df["CustomerID"].isna()
    keep = (~df["is_cancelled_invoice"] & ~df["invalid_quantity"] & ~df["invalid_unit_price"] & ~df["invalid_invoice_date"])
    clean = df.loc[keep].copy()
    # Required for predictable aggregation; retain missing description/country rows as explicit labels.
    clean["Description"] = clean["Description"].fillna("Unknown product").replace("", "Unknown product")
    clean["Country"] = clean["Country"].fillna("Unknown country").replace("", "Unknown country")
    clean["InvoiceDate"] = pd.to_datetime(clean["InvoiceDate"])
    clean["CustomerID"] = clean["CustomerID"].astype("Int64")
    quality = {
        "input_rows": int(rows_input),
        "cancelled_invoice_rows_flagged": int(df["is_cancelled_invoice"].sum()),
        "non_positive_or_missing_quantity_rows_flagged": int(df["invalid_quantity"].sum()),
        "non_positive_or_missing_unit_price_rows_flagged": int(df["invalid_unit_price"].sum()),
        "invalid_or_missing_invoice_date_rows_flagged": int(df["invalid_invoice_date"].sum()),
        "missing_customer_id_rows_flagged": int(df["missing_customer_id"].sum()),
        "rows_retained_for_sales_analysis": int(len(clean)),
        "rows_excluded_from_sales_analysis": int(rows_input - len(clean)),
        "note": "Flags can overlap and must not be summed to estimate unique excluded rows. Sales analysis excludes cancellation invoices, non-positive/missing quantity or price, and unparseable dates."
    }
    return df, clean, quality


def analyze(raw_path: Path, source_label: str, output_dir: Path):
    raw = load_input(raw_path)
    flagged, clean, quality = prepare_data(raw)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "charts").mkdir(exist_ok=True)
    # Cleaned data for reproducible downstream analysis.
    clean_export = clean[["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country", "line_revenue"]].copy()
    clean_export.columns = ["invoice_no", "stock_code", "description", "quantity", "invoice_date", "unit_price", "customer_id", "country", "line_revenue"]
    clean_export.to_csv(output_dir / "sales_transactions_sql_ready.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
    clean_export.to_csv(output_dir / "cleaned_sales.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")

    monthly = clean.assign(month=clean["InvoiceDate"].dt.to_period("M").dt.to_timestamp()).groupby("month", as_index=False).agg(
        gross_sales_retained_lines=("line_revenue", "sum"), orders=("InvoiceNo", "nunique"), units_sold=("Quantity", "sum"))
    monthly["average_order_value"] = monthly["gross_sales_retained_lines"] / monthly["orders"].replace(0, pd.NA)
    monthly.to_csv(output_dir / "monthly_performance.csv", index=False, date_format="%Y-%m-%d")

    country = clean.groupby("Country", dropna=False, as_index=False).agg(
        gross_sales_retained_lines=("line_revenue", "sum"), orders=("InvoiceNo", "nunique"), units_sold=("Quantity", "sum"),
        distinct_customers=("CustomerID", "nunique"))
    country = country.sort_values("gross_sales_retained_lines", ascending=False)
    country.to_csv(output_dir / "country_performance.csv", index=False)

    product = clean.groupby(["StockCode", "Description"], dropna=False, as_index=False).agg(
        gross_sales_retained_lines=("line_revenue", "sum"), units_sold=("Quantity", "sum"), orders=("InvoiceNo", "nunique"))
    product = product.sort_values("gross_sales_retained_lines", ascending=False)
    product.to_csv(output_dir / "product_performance.csv", index=False)

    order = clean.groupby("InvoiceNo", as_index=False).agg(
        order_value=("line_revenue", "sum"), units=("Quantity", "sum"), order_date=("InvoiceDate", "min"),
        customer_id=("CustomerID", "first"), country=("Country", "first"))
    order.to_csv(output_dir / "order_summary.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")

    customer = clean.dropna(subset=["CustomerID"]).groupby("CustomerID", as_index=False).agg(
        gross_sales_retained_lines=("line_revenue", "sum"), orders=("InvoiceNo", "nunique"), units_sold=("Quantity", "sum"),
        first_purchase=("InvoiceDate", "min"), last_purchase=("InvoiceDate", "max"))
    customer = customer.sort_values("gross_sales_retained_lines", ascending=False)
    customer.to_csv(output_dir / "customer_summary.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")

    total_sales = float(clean["line_revenue"].sum()) if len(clean) else 0.0
    orders = int(clean["InvoiceNo"].nunique()) if len(clean) else 0
    units = float(clean["Quantity"].sum()) if len(clean) else 0.0
    customers = int(clean["CustomerID"].nunique()) if len(clean) else 0
    start = clean["InvoiceDate"].min() if len(clean) else pd.NaT
    end = clean["InvoiceDate"].max() if len(clean) else pd.NaT
    kpis = {
        "source_label": source_label,
        "input_file": raw_path.name,
        "input_rows": quality["input_rows"],
        "rows_retained_for_sales_analysis": quality["rows_retained_for_sales_analysis"],
        "gross_sales_retained_lines": round(total_sales, 2),
        "orders": orders,
        "average_order_value": round(total_sales / orders, 2) if orders else 0,
        "units_sold": round(units, 2),
        "distinct_known_customers": customers,
        "date_min": str(start.date()) if pd.notna(start) else None,
        "date_max": str(end.date()) if pd.notna(end) else None,
        "definition": "Gross sales on retained positive lines; excludes cancellation invoices, non-positive/missing quantities or prices, and invalid dates. Not accounting net revenue."
    }
    (output_dir / "kpi_summary.json").write_text(json.dumps(kpis, indent=2), encoding="utf-8")
    (output_dir / "data_quality_report.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")

    if len(monthly):
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(pd.to_datetime(monthly["month"]), monthly["gross_sales_retained_lines"], marker="o")
        ax.set_title(f"Monthly gross sales on retained lines — {source_label}")
        ax.set_xlabel("Month"); ax.set_ylabel("Sales value (dataset currency units)")
        ax.grid(True, alpha=.25); fig.tight_layout(); fig.savefig(output_dir / "charts/monthly_sales_trend.png", dpi=160); plt.close(fig)
    if len(product):
        top = product.head(10).sort_values("gross_sales_retained_lines", ascending=True)
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(top["Description"].astype(str).str.slice(0, 45), top["gross_sales_retained_lines"])
        ax.set_title(f"Top 10 products by gross sales on retained lines — {source_label}")
        ax.set_xlabel("Sales value (dataset currency units)"); ax.set_ylabel("Product")
        fig.tight_layout(); fig.savefig(output_dir / "charts/top_products.png", dpi=160); plt.close(fig)
    if len(country):
        topc = country.head(10).sort_values("gross_sales_retained_lines", ascending=True)
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.barh(topc["Country"].astype(str), topc["gross_sales_retained_lines"])
        ax.set_title(f"Top 10 countries by gross sales on retained lines — {source_label}")
        ax.set_xlabel("Sales value (dataset currency units)"); ax.set_ylabel("Country")
        fig.tight_layout(); fig.savefig(output_dir / "charts/top_countries.png", dpi=160); plt.close(fig)

    lines = [f"# Analysis Findings — {source_label}", "", "> **Interpretation:** all figures below apply only to the selected input dataset and the filtering rules documented in README. They are not externally verified business results.", "",
             "## KPI summary", f"- Source/input: `{source_label}` / `{raw_path.name}`", f"- Rows supplied: {quality['input_rows']:,}", f"- Rows retained: {len(clean):,}", f"- Gross sales on retained lines: {total_sales:,.2f} dataset currency units", f"- Distinct orders: {orders:,}", f"- Average order value: {total_sales / orders:,.2f}" if orders else "- Average order value: not available (no retained orders)", f"- Units sold: {units:,.0f}", f"- Distinct known customers: {customers:,}", f"- Date range: {kpis['date_min']} to {kpis['date_max']}", "", "## Data quality", f"- Cancellation invoice rows flagged: {quality['cancelled_invoice_rows_flagged']:,}", f"- Non-positive/missing quantities flagged: {quality['non_positive_or_missing_quantity_rows_flagged']:,}", f"- Non-positive/missing prices flagged: {quality['non_positive_or_missing_unit_price_rows_flagged']:,}", f"- Invalid/missing invoice dates flagged: {quality['invalid_or_missing_invoice_date_rows_flagged']:,}", f"- Rows excluded from the sales analysis: {quality['rows_excluded_from_sales_analysis']:,}", "", "## Highest-ranked groups in this input"]
    if len(monthly):
        row = monthly.loc[monthly["gross_sales_retained_lines"].idxmax()]
        lines.append(f"- Highest-sales month: {pd.to_datetime(row['month']).strftime('%Y-%m')} ({row['gross_sales_retained_lines']:,.2f})")
    if len(country):
        row = country.iloc[0]
        lines.append(f"- Highest-sales country: {row['Country']} ({row['gross_sales_retained_lines']:,.2f})")
    if len(product):
        row = product.iloc[0]
        lines.append(f"- Highest-sales product: {row['Description']} ({row['gross_sales_retained_lines']:,.2f})")
    lines += ["", "## How to use these findings", "Review the relevant CSV outputs and confirm whether the sales filter is suitable for the business question before putting a number on a resume. For the bundled sample, treat every finding as a code test only. For the UCI source, cite the public dataset and state the analysis period and filtering rules."]
    (output_dir / "analysis_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return kpis, quality


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to UCI Online Retail XLSX or compatible CSV")
    parser.add_argument("--source-label", default="User-supplied dataset", help="Label written into output report titles")
    parser.add_argument("--output-dir", default="outputs/analysis", help="Directory to write analysis outputs")
    args = parser.parse_args()
    kpis, quality = analyze(Path(args.input), args.source_label, Path(args.output_dir))
    print(json.dumps({"status": "success", "output_dir": args.output_dir, "rows_retained": kpis["rows_retained_for_sales_analysis"], "gross_sales_retained_lines": kpis["gross_sales_retained_lines"], "data_quality": quality}, indent=2))

if __name__ == "__main__":
    main()
