# SQL setup

1. Run `00_schema.sql` in PostgreSQL.
2. Run `src/analyze_sales.py` as described in the root README.
3. Use pgAdmin Import/Export or PostgreSQL `\copy` to load `sales_transactions_sql_ready.csv` into `retail_transactions`. Match columns in this order: `invoice_no, stock_code, description, quantity, invoice_date, unit_price, customer_id, country, line_revenue`.
4. Example `psql` command (replace the absolute file path):

```sql
\copy retail_transactions(invoice_no, stock_code, description, quantity, invoice_date, unit_price, customer_id, country, line_revenue) FROM '/absolute/path/sales_transactions_sql_ready.csv' WITH (FORMAT csv, HEADER true, NULL '');
```

5. Execute `01_business_queries.sql`.

`02_quality_checks.sql` is a template for a separate raw staging table imported with UCI's original headers. The quotes assume case-sensitive original names were preserved. Some importers lower-case headers; adjust the identifiers if needed.
