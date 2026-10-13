-- Run after loading outputs/.../sales_transactions_sql_ready.csv into retail_transactions.
-- Metric definition is gross sales on retained positive lines, not accounting net revenue.

-- 1) Executive KPI snapshot
SELECT
    ROUND(SUM(line_revenue), 2) AS gross_sales_retained_lines,
    COUNT(DISTINCT invoice_no) AS orders,
    ROUND(SUM(line_revenue) / NULLIF(COUNT(DISTINCT invoice_no), 0), 2) AS average_order_value,
    ROUND(SUM(quantity), 0) AS units_sold,
    COUNT(DISTINCT customer_id) AS known_customers
FROM retail_transactions;

-- 2) Monthly sales trend (PostgreSQL)
SELECT DATE_TRUNC('month', invoice_date)::date AS sales_month,
       ROUND(SUM(line_revenue), 2) AS gross_sales_retained_lines,
       COUNT(DISTINCT invoice_no) AS orders,
       ROUND(SUM(line_revenue) / NULLIF(COUNT(DISTINCT invoice_no), 0), 2) AS average_order_value,
       ROUND(SUM(quantity), 0) AS units_sold
FROM retail_transactions
GROUP BY 1
ORDER BY 1;

-- 3) Country contribution
SELECT country,
       ROUND(SUM(line_revenue), 2) AS gross_sales_retained_lines,
       COUNT(DISTINCT invoice_no) AS orders,
       COUNT(DISTINCT customer_id) AS known_customers,
       ROUND(100.0 * SUM(line_revenue) / NULLIF(SUM(SUM(line_revenue)) OVER (), 0), 2) AS sales_share_pct
FROM retail_transactions
GROUP BY country
ORDER BY gross_sales_retained_lines DESC;

-- 4) Top 10 products by sales value
SELECT stock_code, description,
       ROUND(SUM(line_revenue), 2) AS gross_sales_retained_lines,
       SUM(quantity) AS units_sold,
       COUNT(DISTINCT invoice_no) AS orders
FROM retail_transactions
GROUP BY stock_code, description
ORDER BY gross_sales_retained_lines DESC
LIMIT 10;

-- 5) Order-level summary and AOV distribution
WITH order_totals AS (
    SELECT invoice_no, SUM(line_revenue) AS order_value,
           MIN(invoice_date) AS order_date,
           MAX(country) AS country,
           MAX(customer_id) AS customer_id
    FROM retail_transactions
    GROUP BY invoice_no
)
SELECT country, COUNT(*) AS orders,
       ROUND(AVG(order_value), 2) AS average_order_value,
       ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY order_value)::numeric, 2) AS median_order_value
FROM order_totals
GROUP BY country
ORDER BY orders DESC;

-- 6) Customer contribution (known customer IDs only)
SELECT customer_id,
       ROUND(SUM(line_revenue), 2) AS gross_sales_retained_lines,
       COUNT(DISTINCT invoice_no) AS orders,
       SUM(quantity) AS units_sold,
       MIN(invoice_date)::date AS first_purchase_date,
       MAX(invoice_date)::date AS last_purchase_date
FROM retail_transactions
WHERE customer_id IS NOT NULL
GROUP BY customer_id
ORDER BY gross_sales_retained_lines DESC
LIMIT 25;
