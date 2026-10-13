# Analysis Findings — Synthetic demo sample

> **Interpretation:** all figures below apply only to the selected input dataset and the filtering rules documented in README. They are not externally verified business results.

## KPI summary
- Source/input: `Synthetic demo sample` / `sales_transactions_sample.csv`
- Rows supplied: 383
- Rows retained: 368
- Gross sales on retained lines: 5,313.78 dataset currency units
- Distinct orders: 50
- Average order value: 106.28
- Units sold: 1,082
- Distinct known customers: 40
- Date range: 2010-12-04 to 2011-11-27

## Data quality
- Cancellation invoice rows flagged: 8
- Non-positive/missing quantities flagged: 12
- Non-positive/missing prices flagged: 3
- Invalid/missing invoice dates flagged: 0
- Rows excluded from the sales analysis: 15

## Highest-ranked groups in this input
- Highest-sales month: 2011-04 (644.61)
- Highest-sales country: United Kingdom (3,254.16)
- Highest-sales product: POSTAGE (1,474.20)

## How to use these findings
Review the relevant CSV outputs and confirm whether the sales filter is suitable for the business question before putting a number on a resume. For the bundled sample, treat every finding as a code test only. For the UCI source, cite the public dataset and state the analysis period and filtering rules.
