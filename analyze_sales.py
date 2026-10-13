"""Reproducible sales analytics for UCI Online Retail-compatible CSV/XLSX files."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import pandas as pd
import matplotlib.pyplot as plt

REQUIRED_COLUMNS = ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"]
CANONICAL = {re.sub(r"[^a-z0-9]", "", c.lower()): c for c in REQUIRED_COLUMNS}
POSTAGE_CODES = {"POST", "POSTAGE"}
POSTAGE_DESCRIPTIONS = {"POSTAGE", "POSTAGE CHARGE", "CARRIAGE", "SHIPPING", "DELIVERY CHARGE"}


def classify_line_type(stock_code, description) -> str:
    """Keep common shipping-charge rows separate from merchandise product rankings."""
    code = "" if pd.isna(stock_code) else str(stock_code).strip().upper()
    desc = "" if pd.isna(description) else str(description).strip().upper()
    return "Postage / shipping" if code in POSTAGE_CODES or desc in POSTAGE_DESCRIPTIONS else "Merchandise"


def load_input(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}. See README.md for dataset instructions.")
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    elif suffix == ".csv":
        df = pd.read_csv(path, encoding_errors="replace")
    else:
        raise ValueError("Supported input types are .xlsx, .xls and .csv")
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
    for col in ["InvoiceNo", "StockCode", "Description", "Country"]:
        df[col] = df[col].astype("string").str.strip()
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
    clean["Description"] = clean["Description"].fillna("Unknown product").replace("", "Unknown product")
    clean["Country"] = clean["Country"].fillna("Unknown country").replace("", "Unknown country")
    clean["InvoiceDate"] = pd.to_datetime(clean["InvoiceDate"])
    clean["CustomerID"] = clean["CustomerID"].astype("Int64")
    clean["line_type"] = [classify_line_type(c, d) for c, d in zip(clean["StockCode"], clean["Description"])]
    quality = {
        "input_rows": int(rows_input),
        "cancelled_invoice_rows_flagged": int(df["is_cancelled_invoice"].sum()),
        "non_positive_or_missing_quantity_rows_flagged": int(df["invalid_quantity"].sum()),
        "non_positive_or_missing_unit_price_rows_flagged": int(df["invalid_unit_price"].sum()),
        "invalid_or_missing_invoice_date_rows_flagged": int(df["invalid_invoice_date"].sum()),
        "missing_customer_id_rows_flagged": int(df["missing_customer_id"].sum()),
        "rows_retained_for_sales_analysis": int(len(clean)),
        "rows_excluded_from_sales_analysis": int(rows_input - len(clean)),
        "note": "Flags can overlap and must not be summed to estimate unique excluded rows. Cancellation-like invoices, non-positive/missing quantities or prices, and unparseable dates are excluded. Missing customer IDs remain in sales totals but are excluded from known-customer counts."
    }
    return df, clean, quality


def analyze(raw_path: Path, source_label: str, output_dir: Path):
    raw = load_input(raw_path)
    flagged, clean, quality = prepare_data(raw)
    output_dir.mkdir(parents=True, exist_ok=True)
    chart_dir = output_dir / "charts"
    chart_dir.mkdir(exist_ok=True)

    export = clean[["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country", "line_revenue", "line_type"]].copy()
    export.columns = ["invoice_no", "stock_code", "description", "quantity", "invoice_date", "unit_price", "customer_id", "country", "line_revenue", "line_type"]
    export.to_csv(output_dir / "sales_transactions_sql_ready.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
    export.to_csv(output_dir / "cleaned_sales.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")

    work = clean.assign(
        month=clean["InvoiceDate"].dt.to_period("M").dt.to_timestamp(),
        merchandise_revenue=clean["line_revenue"].where(clean["line_type"].eq("Merchandise"), 0),
        postage_revenue=clean["line_revenue"].where(clean["line_type"].eq("Postage / shipping"), 0),
    )
    monthly = work.groupby("month", as_index=False).agg(
        gross_sales_retained_lines=("line_revenue", "sum"), merchandise_sales=("merchandise_revenue", "sum"),
        postage_sales=("postage_revenue", "sum"), orders=("InvoiceNo", "nunique"), units_sold=("Quantity", "sum"))
    monthly["average_order_value"] = monthly["gross_sales_retained_lines"] / monthly["orders"].replace(0, pd.NA)
    monthly.to_csv(output_dir / "monthly_performance.csv", index=False, date_format="%Y-%m-%d")

    country = clean.groupby("Country", dropna=False, as_index=False).agg(
        gross_sales_retained_lines=("line_revenue", "sum"), orders=("InvoiceNo", "nunique"),
        units_sold=("Quantity", "sum"), distinct_customers=("CustomerID", "nunique"))
    country = country.sort_values("gross_sales_retained_lines", ascending=False)
    country.to_csv(output_dir / "country_performance.csv", index=False)

    # Merchandise ranking explicitly excludes postage/shipping charge lines.
    merchandise = clean.loc[clean["line_type"].eq("Merchandise")]
    product = merchandise.groupby(["StockCode", "Description"], dropna=False, as_index=False).agg(
        gross_sales_retained_lines=("line_revenue", "sum"), units_sold=("Quantity", "sum"), orders=("InvoiceNo", "nunique"))
    product = product.sort_values("gross_sales_retained_lines", ascending=False)
    product.to_csv(output_dir / "product_performance.csv", index=False)

    order = clean.groupby("InvoiceNo", as_index=False).agg(
        order_value=("line_revenue", "sum"), units=("Quantity", "sum"), order_date=("InvoiceDate", "min"),
        customer_id=("CustomerID", "first"), country=("Country", "first"))
    order.to_csv(output_dir / "order_summary.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")
    customer = clean.dropna(subset=["CustomerID"]).groupby("CustomerID", as_index=False).agg(
        gross_sales_retained_lines=("line_revenue", "sum"), orders=("InvoiceNo", "nunique"),
        units_sold=("Quantity", "sum"), first_purchase=("InvoiceDate", "min"), last_purchase=("InvoiceDate", "max"))
    customer.sort_values("gross_sales_retained_lines", ascending=False).to_csv(output_dir / "customer_summary.csv", index=False, date_format="%Y-%m-%d %H:%M:%S")

    total_sales = float(clean["line_revenue"].sum()) if len(clean) else 0.0
    merch_sales = float(merchandise["line_revenue"].sum()) if len(clean) else 0.0
    postage_sales = float(clean.loc[clean["line_type"].eq("Postage / shipping"), "line_revenue"].sum()) if len(clean) else 0.0
    orders = int(clean["InvoiceNo"].nunique()) if len(clean) else 0
    units = float(clean["Quantity"].sum()) if len(clean) else 0.0
    known_customers = int(clean["CustomerID"].nunique()) if len(clean) else 0
    start = clean["InvoiceDate"].min() if len(clean) else pd.NaT
    end = clean["InvoiceDate"].max() if len(clean) else pd.NaT
    kpis = {
        "source_label": source_label, "input_file": raw_path.name,
        "input_rows": quality["input_rows"], "rows_retained_for_sales_analysis": quality["rows_retained_for_sales_analysis"],
        "gross_sales_retained_lines": round(total_sales, 2), "merchandise_sales_retained_lines": round(merch_sales, 2),
        "postage_sales_retained_lines": round(postage_sales, 2),
        "postage_sales_share_pct": round(100 * postage_sales / total_sales, 2) if total_sales else 0.0,
        "orders": orders, "average_order_value": round(total_sales / orders, 2) if orders else 0,
        "units_sold": round(units, 2), "distinct_known_customers": known_customers,
        "date_min": str(start.date()) if pd.notna(start) else None,
        "date_max": str(end.date()) if pd.notna(end) else None,
        "definition": "Gross sales on retained positive lines includes classified postage/shipping charges. Merchandise sales excludes those charges. Both exclude cancellation-like invoices, non-positive/missing quantities or prices, and invalid dates. Not accounting net revenue; currency follows the source."
    }
    (output_dir / "kpi_summary.json").write_text(json.dumps(kpis, indent=2), encoding="utf-8")
    (output_dir / "data_quality_report.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")

    if len(monthly):
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(pd.to_datetime(monthly["month"]), monthly["gross_sales_retained_lines"], marker="o", label="All retained lines")
        ax.plot(pd.to_datetime(monthly["month"]), monthly["merchandise_sales"], marker="o", label="Merchandise only")
        ax.set_title(f"Monthly sales — {source_label}"); ax.set_xlabel("Month"); ax.set_ylabel("Sales value (source currency units)")
        ax.legend(); ax.grid(True, alpha=.25); fig.tight_layout(); fig.savefig(chart_dir / "monthly_sales_trend.png", dpi=160); plt.close(fig)
    if len(product):
        top = product.head(10).sort_values("gross_sales_retained_lines", ascending=True)
        fig, ax = plt.subplots(figsize=(10, 6)); ax.barh(top["Description"].astype(str).str.slice(0, 45), top["gross_sales_retained_lines"])
        ax.set_title(f"Top 10 merchandise products — {source_label}"); ax.set_xlabel("Sales value (source currency units)")
        fig.tight_layout(); fig.savefig(chart_dir / "top_products.png", dpi=160); plt.close(fig)
    if len(country):
        topc = country.head(10).sort_values("gross_sales_retained_lines", ascending=True)
        fig, ax = plt.subplots(figsize=(9, 5)); ax.barh(topc["Country"].astype(str), topc["gross_sales_retained_lines"])
        ax.set_title(f"Top 10 countries by retained-line sales — {source_label}"); ax.set_xlabel("Sales value (source currency units)")
        fig.tight_layout(); fig.savefig(chart_dir / "top_countries.png", dpi=160); plt.close(fig)

    pct_postage = (100 * postage_sales / total_sales) if total_sales else 0.0
    lines = [
        f"# Analysis Findings — {source_label}", "",
        "> **Interpretation:** values apply only to the selected input and filtering rules. The bundled dataset is synthetic and not commercial evidence.", "",
        "## KPI summary", f"- Input rows: {len(raw):,}", f"- Rows retained: {len(clean):,}",
        f"- Gross sales on retained lines (includes postage/shipping): {total_sales:,.2f} source currency units",
        f"- Merchandise sales (shipping excluded): {merch_sales:,.2f} source currency units",
        f"- Postage/shipping charges: {postage_sales:,.2f} ({pct_postage:.2f}% of retained-line sales)",
        f"- Distinct orders: {orders:,}", f"- Average order value: {total_sales / orders:,.2f}" if orders else "- Average order value: unavailable (no retained orders)",
        f"- Units sold on retained lines: {units:,.0f}", f"- Known customers: {known_customers:,}",
        f"- Date range: {kpis['date_min']} to {kpis['date_max']}", "", "## Data quality",
        f"- Cancellation-like invoice rows flagged: {quality['cancelled_invoice_rows_flagged']:,}",
        f"- Non-positive/missing quantity rows flagged: {quality['non_positive_or_missing_quantity_rows_flagged']:,}",
        f"- Non-positive/missing price rows flagged: {quality['non_positive_or_missing_unit_price_rows_flagged']:,}",
        f"- Invalid/missing invoice date rows flagged: {quality['invalid_or_missing_invoice_date_rows_flagged']:,}",
        f"- Rows excluded: {quality['rows_excluded_from_sales_analysis']:,}", "", "## Leading groups in this input"
    ]
    if len(monthly):
        row = monthly.loc[monthly["gross_sales_retained_lines"].idxmax()]
        lines.append(f"- Highest retained-line sales month: {pd.to_datetime(row['month']).strftime('%Y-%m')} ({row['gross_sales_retained_lines']:,.2f})")
    if len(country):
        row = country.iloc[0]; lines.append(f"- Highest retained-line sales country: {row['Country']} ({row['gross_sales_retained_lines']:,.2f})")
    if len(product):
        row = product.iloc[0]; lines.append(f"- Top merchandise product (shipping excluded): {row['Description']} ({row['gross_sales_retained_lines']:,.2f})")
    lines += ["", "## Decision caveats", "Rankings and month-over-month movements are descriptive signals, not causal explanations. The data has no product cost/margin fields, so profitability cannot be measured. Verify shipping-code mapping, currency, licensing and metric definitions before using external data."]
    (output_dir / "analysis_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return kpis, quality


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Path to source CSV/XLSX with required sales columns")
    parser.add_argument("--source-label", default="User-supplied dataset", help="Provenance label used in output reports")
    parser.add_argument("--output-dir", default="outputs/analysis", help="Directory for generated outputs")
    args = parser.parse_args()
    kpis, quality = analyze(Path(args.input), args.source_label, Path(args.output_dir))
    print(json.dumps({"status": "success", "output_dir": args.output_dir, "rows_retained": kpis["rows_retained_for_sales_analysis"], "gross_sales_retained_lines": kpis["gross_sales_retained_lines"], "merchandise_sales_retained_lines": kpis["merchandise_sales_retained_lines"], "postage_sales_share_pct": kpis["postage_sales_share_pct"], "data_quality": quality}, indent=2))

if __name__ == "__main__":
    main()
