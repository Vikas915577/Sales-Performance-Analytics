"""Unit tests for sales-cleaning rules and the bundled sample CSV."""
import sys
from pathlib import Path
import unittest
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from analyze_sales import prepare_data, load_input


class SalesAnalysisTests(unittest.TestCase):
    def test_excludes_cancelled_and_invalid_lines(self):
        raw = pd.DataFrame({
            "InvoiceNo": ["100", "C101", "102", "103"],
            "StockCode": ["A", "A", "B", "C"],
            "Description": ["Item A", "Item A", "Item B", "Item C"],
            "Quantity": [2, -1, 0, 3],
            "InvoiceDate": ["01/10/2026", "01/10/2026", "01/10/2026", "01/10/2026"],
            "UnitPrice": [5, 5, 10, 0],
            "CustomerID": [1, 1, 2, 3],
            "Country": ["UK", "UK", "FR", "UK"]
        })
        _, clean, quality = prepare_data(raw)
        self.assertEqual(len(clean), 1)
        self.assertEqual(float(clean.iloc[0]["line_revenue"]), 10.0)
        self.assertEqual(quality["rows_excluded_from_sales_analysis"], 3)

    def test_sample_file_schema(self):
        df = load_input(ROOT / "sales_transactions_sample.csv")
        self.assertGreater(len(df), 100)
        self.assertIn("InvoiceNo", df.columns)
        self.assertIn("InvoiceDate", df.columns)

    def test_demo_sample_kpis(self):
        df = load_input(ROOT / "sales_transactions_sample.csv")
        _, clean, _ = prepare_data(df)
        self.assertEqual(len(df), 383)
        self.assertEqual(len(clean), 368)
        self.assertAlmostEqual(float((clean["Quantity"] * clean["UnitPrice"]).sum()), 5313.78, places=2)


if __name__ == "__main__":
    unittest.main()
