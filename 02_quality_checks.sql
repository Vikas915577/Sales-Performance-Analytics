-- Load raw source into a separate staging table if you want to inspect excluded rows.
-- These queries assume a raw retail staging table named retail_raw with original fields.
-- Adjust identifier casing if your import tool preserves quoted UCI headers.

-- Cancellation-like invoices
SELECT COUNT(*) AS cancellation_rows
FROM retail_raw
WHERE UPPER(TRIM("InvoiceNo"::text)) LIKE 'C%';

-- Invalid quantities / prices
SELECT
  COUNT(*) FILTER (WHERE "Quantity" IS NULL OR "Quantity" <= 0) AS invalid_quantity_rows,
  COUNT(*) FILTER (WHERE "UnitPrice" IS NULL OR "UnitPrice" <= 0) AS invalid_price_rows,
  COUNT(*) FILTER (WHERE "InvoiceDate" IS NULL) AS missing_invoice_date_rows,
  COUNT(*) FILTER (WHERE "CustomerID" IS NULL) AS missing_customer_id_rows
FROM retail_raw;

-- Find obvious date/quantity/price problems before aggregation
SELECT *
FROM retail_raw
WHERE UPPER(TRIM("InvoiceNo"::text)) LIKE 'C%'
   OR "Quantity" IS NULL OR "Quantity" <= 0
   OR "UnitPrice" IS NULL OR "UnitPrice" <= 0
   OR "InvoiceDate" IS NULL
LIMIT 100;
