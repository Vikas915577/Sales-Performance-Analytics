# Data dictionary

| Column | Meaning | Notes |
|---|---|---|
| `InvoiceNo` / `invoice_no` | Source invoice identifier | Values starting with `C` are flagged as cancellation-like invoices |
| `StockCode` / `stock_code` | Product identifier | Treat as text; may include letters |
| `Description` / `description` | Product name | Missing values are labelled `Unknown product` in aggregation |
| `Quantity` / `quantity` | Units on the line | Positive quantity is required for included sales lines |
| `InvoiceDate` / `invoice_date` | Transaction timestamp | Parsed as date/time; invalid dates excluded |
| `UnitPrice` / `unit_price` | Unit price in source currency | Positive price required |
| `CustomerID` / `customer_id` | Customer identifier where supplied | Missing IDs are retained for sales value but excluded from customer counts |
| `Country` / `country` | Customer country field | Missing values are labelled `Unknown country` in aggregation |
| `line_revenue` | Quantity × unit price | Computed field; currency/unit follows the source dataset |
