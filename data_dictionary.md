# Data dictionary and metric contract

| Field | Meaning | Notes |
|---|---|---|
| `invoice_no` | Invoice/order identifier | Kept as text; distinct count is the order metric. Cancellation-like identifiers beginning with `C` are excluded. |
| `stock_code` | Product/service identifier | Keep as text because IDs can contain letters. |
| `description` | Source line description | Missing descriptions are labeled `Unknown product`. |
| `quantity` | Units/quantity on a source line | Positive quantity is required for retained sales lines. |
| `invoice_date` | Transaction timestamp | Parsed to date/time; invalid dates are excluded. |
| `unit_price` | Unit price from source | Must be positive. Currency is source-specific and must be verified. |
| `customer_id` | Customer key when supplied | Missing keys remain in sales values but are not counted as known customers. |
| `country` | Source country label | Missing labels become `Unknown country`. |
| `line_revenue` | `quantity × unit_price` | Transaction-line calculation; not net revenue, profit or margin. |
| `line_type` | `Merchandise` or `Postage / shipping` | Derived from known postage codes/descriptions so shipping charges do not rank as merchandise. Validate against each new source. |

## Metric contract

- **Gross sales on retained lines** = sum of `line_revenue` after exclusions; includes retained postage/shipping charges.
- **Merchandise sales** = same sum for `line_type = Merchandise` only.
- **Postage/shipping share** = postage/shipping sales ÷ gross retained-line sales in the same filter context.
- **Orders** = distinct invoice identifiers, not transaction row count.
- **Average order value** = gross retained-line sales ÷ distinct orders. It includes shipping where shipping is part of retained invoice lines.
- **Units** = quantity sum of all retained lines. For merchandise-only unit analysis, filter `line_type = Merchandise`.
- **Known customers** = distinct, non-null customer identifiers.
- The current exclusion flags overlap. Do not add their counts to calculate unique rejected rows.
- Cost and margin are not included, so profitability and ROI cannot be inferred.
