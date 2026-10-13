"""Unit and output-contract tests for sales analytics and DDD metrics."""
import json
import sys
import tempfile
from pathlib import Path
import unittest
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from analyze_sales import prepare_data, load_input, classify_line_type, analyze


class SalesAnalysisTests(unittest.TestCase):
    def test_excludes_cancelled_and_invalid_lines(self):
        raw = pd.DataFrame({
            "InvoiceNo": ["100", "C101", "102", "103"],
            "StockCode": ["A", "A", "B", "C"],
            "Description": ["Item A", "Item A", "Item B", "Item C"],
            "Quantity": [2, -1, 0, 3],
            "InvoiceDate": ["01/10/2026", "01/10/2026", "01/10/2026", "01/10/2026"],
            "UnitPrice": [5, 5, 10, 0], "CustomerID": [1, 1, 2, 3], "Country": ["UK", "UK", "FR", "UK"]
        })
        _, clean, quality = prepare_data(raw)
        self.assertEqual(len(clean), 1)
        self.assertEqual(float(clean.iloc[0]["line_revenue"]), 10.0)
        self.assertEqual(quality["rows_excluded_from_sales_analysis"], 3)

    def test_line_type_classification(self):
        self.assertEqual(classify_line_type("POST", "POSTAGE"), "Postage / shipping")
        self.assertEqual(classify_line_type("POSTAGE", "Postage"), "Postage / shipping")
        self.assertEqual(classify_line_type("85123A", "WHITE HANGING HEART T-LIGHT HOLDER"), "Merchandise")
        self.assertEqual(classify_line_type("POSTER", "Poster print"), "Merchandise")

    def test_sample_schema_if_present(self):
        sample = ROOT / "sales_transactions_sample.csv"
        if not sample.exists():
            self.skipTest("The update ZIP intentionally omits the existing repository's sample dataset; merge it with the current repo before running the full project tests.")
        df = load_input(sample)
        self.assertGreater(len(df), 100)
        self.assertIn("InvoiceNo", df.columns)
        self.assertIn("InvoiceDate", df.columns)

    def test_current_demo_sample_business_metrics_if_present(self):
        sample = ROOT / "sales_transactions_sample.csv"
        if not sample.exists():
            self.skipTest("The existing sample dataset is preserved in the target repository but is not included in the overlay ZIP.")
        raw = load_input(sample)
        _, clean, _ = prepare_data(raw)
        self.assertEqual(len(raw), 383)
        self.assertEqual(len(clean), 368)
        self.assertAlmostEqual(float(clean["line_revenue"].sum()), 5313.78, places=2)
        shipping = clean[clean["line_type"].eq("Postage / shipping")]
        self.assertEqual(len(shipping), 33)
        self.assertAlmostEqual(float(shipping["line_revenue"].sum()), 1474.20, places=2)
        self.assertAlmostEqual(float(clean.loc[clean["line_type"].eq("Merchandise"), "line_revenue"].sum()), 3839.58, places=2)

    def test_generated_files_agree_and_merchandise_ranking_excludes_postage(self):
        # Build a deterministic fixture: 4 valid rows and 3 excluded rows.
        fixture = pd.DataFrame({
            "InvoiceNo": ["100", "100", "101", "102", "C103", "104", "105"],
            "StockCode": ["A", "POST", "B", "C", "D", "E", "F"],
            "Description": ["Item A", "POSTAGE", "Item B", "Item C", "Item D", "Item E", "Item F"],
            "Quantity": [2, 1, 3, 1, -1, 0, 1],
            "InvoiceDate": ["2026-01-01", "2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-04", "2026-01-05"],
            "UnitPrice": [5, 2, 3, 7, 1, 9, 0],
            "CustomerID": [1, 1, 2, None, 3, 3, 4],
            "Country": ["UK", "UK", "FR", "UK", "DE", "DE", "UK"]
        })
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            src = tmp / "fixture.csv"
            fixture.to_csv(src, index=False)
            out = tmp / "out"
            kpis, quality = analyze(src, "Unit test fixture", out)
            exported = pd.read_csv(out / "sales_transactions_sql_ready.csv")
            product = pd.read_csv(out / "product_performance.csv")
            saved_kpis = json.loads((out / "kpi_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(quality["input_rows"], 7)
            self.assertEqual(quality["rows_retained_for_sales_analysis"], 4)
            self.assertEqual(len(exported), 4)
            self.assertIn("line_type", exported.columns)
            self.assertFalse(product["StockCode"].astype(str).str.upper().eq("POST").any())
            self.assertAlmostEqual(kpis["gross_sales_retained_lines"], 28.0, places=2)
            self.assertAlmostEqual(kpis["merchandise_sales_retained_lines"], 26.0, places=2)
            self.assertAlmostEqual(kpis["postage_sales_retained_lines"], 2.0, places=2)
            self.assertAlmostEqual(saved_kpis["average_order_value"], 28.0 / 3, places=2)
            self.assertEqual(len(pd.read_csv(out / "monthly_performance.csv")), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
