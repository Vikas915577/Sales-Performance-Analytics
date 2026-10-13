# Sales Analytics: Display → Diagnose → Decide

## Primary user story

**As a sales operations manager, I want to see whether retained-line sales are changing, diagnose which months, countries and merchandise items contribute to the pattern, and prioritize the next investigation—so I can focus business attention on evidence rather than guesses.**

## Decision context

- **Primary user:** Sales operations manager / business analyst.
- **Secondary users:** Commercial manager and finance/reporting stakeholder.
- **Decision to support:** What changed, what contributes to the change, and what should be checked next?
- **Decision owner:** The responsible commercial/finance stakeholder, not the dashboard.
- **Grain:** One retained source transaction line.
- **Data status:** Packaged records are synthetic and only demonstrate the pipeline; they are not sales evidence from a real business.

## DDD journey

### 1 — DISPLAY: What is happening?

Show gross sales on retained lines, merchandise sales, postage/shipping charges and share, distinct invoices, average order value, units, known customers, selected date range and source-data notice. Provide filters for date, country, line type and product. Keep metric definitions accessible.

### 2 — DIAGNOSE: What contributes, and what should be verified?

Allow the analyst to compare monthly sales and merchandise-only sales, review country contribution, rank merchandise products without shipping charges, and inspect transaction-level lines. Display input/retained/excluded counts and quality flags. Make the denominator and selected filters visible. Treat a high/low segment or monthly drop as a signal to investigate, not proof of cause.

### 3 — DECIDE: What should be investigated next?

Provide a concise review queue with **evidence → why it matters → suggested investigation → accountable owner**. Prompts include validating postage classification when material, checking the largest month-over-month decline against orders and AOV, and assessing country concentration against an approved company threshold. These are review prompts, not forecasts or automated decisions. No profitability recommendation is allowed without cost/margin data.

## Metrics

- **Gross retained-line sales:** sum of positive quantity × positive unit price for lines whose invoice is not cancellation-like and whose date is parseable. Includes classified postage/shipping; not accounting net revenue.
- **Merchandise sales:** gross retained-line sales excluding lines classified as postage/shipping.
- **Postage/shipping share:** postage/shipping sales divided by gross retained-line sales in the same selected scope.
- **Orders:** distinct invoice IDs.
- **AOV:** gross retained-line sales divided by distinct invoice IDs.
- **Known customers:** distinct non-null customer IDs.
- **Product sales ranking:** merchandise only; shipping codes/labels excluded by the documented mapping.

## Acceptance criteria

1. Date, country, line-type and product filters update all dependent KPI values, charts, insight cards, transaction rows and review prompts.
2. Empty filter results show a clear empty state, not fabricated zero-result charts or a broken page.
3. Sales and AOV labels state retained-line definitions; total is never mislabeled as accounting net revenue.
4. Shipping/postage rows remain in gross retained-line sales when eligible but do not appear in top merchandise products.
5. Python, CSV, SQL and dashboard figures reconcile under the same source, exclusions and filters.
6. Distinct invoice IDs define orders; line revenue remains at transaction-line grain.
7. The chosen period and source are visible; no forecast, YoY or seasonality claim is made without sufficient observations.
8. Country/month/product results are descriptive leads, not causal explanations.
9. Cost/margin is absent, so no profit, ROI or profitability claims appear.
10. Data-quality flags and missing customers are exposed; overlapping quality counts are not summed as unique exclusions.
11. Only synthetic, licensed public, or permissioned data is included; demo metrics are not presented as business achievements.
12. Birst is described as a blueprint until a real tenant implementation, filter checks, KPI reconciliation and dated screenshots have been completed.

## Definition of done

- Python cleaning/aggregation tests pass.
- SQL schema and queries share the same field names and line-type contract.
- Dashboard loads the local CSV without third-party chart dependencies; filters and clear/reset work on mobile and desktop.
- Automated CI runs Python tests, builds outputs and checks JavaScript syntax.
- Birst implementation guide covers modeling, subject area, dashboard pages, filters and reconciliation.
