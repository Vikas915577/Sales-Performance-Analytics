# Infor Birst dashboard blueprint — Sales Performance Analytics

> **Status:** This is a target-state implementation guide. The GitHub Pages site is a standalone demo dashboard; it is not hosted inside Infor Birst, and no live Birst deployment is claimed.

## The user story

As a sales operations manager, I want to see whether retained-line sales are changing, understand which countries, periods and merchandise lines contribute to the pattern, and prioritize what to investigate next—so business decisions are evidence-led.

## Display → Diagnose → Decide pages

### Page 1 — DISPLAY: Executive performance
**Question:** What is happening for the selected period?
- KPI dashlets: gross retained-line sales, merchandise sales, postage/shipping sales and share, distinct orders, AOV, units and known customers.
- Trend: total retained-line sales compared with merchandise-only sales by month.
- Global context: source label, date range, metric definition and active filters.
- Filters: date/month, country, line type and product/stock code.

### Page 2 — DIAGNOSE: Drivers and data confidence
**Question:** What contributes to the result, and what requires validation?
- Monthly comparison with orders and AOV alongside sales.
- Country contribution with a clear denominator.
- Top merchandise items with shipping/postage excluded.
- Transaction-line detail, including invoice/date/country/item/type/quantity/price/sales.
- Data-quality report: input, retained/excluded rows, cancellation-like invoices, invalid quantity/price/date and missing customer IDs.
- Drill from an aggregate chart/report to the relevant transaction lines where the tenant supports it.

### Page 3 — DECIDE: Investigation queue
**Question:** What should the business owner check next?
- Validate shipping classification if postage materially affects headline sales or has previously appeared at the top of the product ranking.
- Investigate the largest month-over-month decline by comparing orders, AOV, product/country mix and source completeness.
- Review country concentration against an approved internal threshold and the relevant commercial context.
- Keep columns for evidence, reason, next investigation and accountable owner.
- These are review prompts, not causal conclusions, forecasts or automated actions.

## Semantic model

- **Fact grain:** one retained transaction line.
- **Dimensions:** Date, product/service (including line type), country, customer where known.
- **Measures:** retained-line sales, merchandise sales, postage/shipping sales, postage share, distinct orders, AOV, retained-line units, known customers.
- **Join integrity:** dimension keys must be unique at the relevant grain and joining dimensions must not multiply fact rows.
- **Metric labeling:** use “Gross sales on retained lines” rather than “net revenue.” Use a separate merchandise measure for product rankings.
- **Source mapping:** verify postage codes/descriptions against any new dataset; synthetic demo values must not be represented as commercial results.

## Recommended Birst build sequence

1. Use a permitted personal/practice Birst space and import only synthetic, licensed public or permissioned data.
2. Load the normalized CSV. Treat invoice/product/customer identifiers as text-like keys, date as date/time and quantity/price/revenue as numeric.
3. Confirm each fact row means one source transaction line; check duplicate keys and missing dimension joins before building charts.
4. Create a business-friendly **Sales Performance** subject area with only useful fields and reusable metric definitions.
5. Create and validate reports in Visualizer: KPI snapshot, monthly trend, country contribution, merchandise ranking, transaction details and quality summary.
6. Add KPI dashlets and report dashlets to the three DDD dashboard pages. Configure shared date/country/product/line-type filters, as supported by your tenant.
7. Test filter interactions (all data, one country, one month, postage-only, merchandise-only, no-results and reset). Reconcile KPI/aggregates with the Python output and SQL queries.
8. Publish only after checks pass. Record the Birst environment/version, refresh timestamp, source/date range and limitations. Only then take genuine screenshots and claim Birst implementation.

## Validation checklist

- [ ] Fact row count remains unchanged after dimension joins.
- [ ] Dimension keys are unique; unmatched rows are reported.
- [ ] Gross sales, merchandise sales, postage sales, orders and AOV reconcile across Python, SQL and Birst.
- [ ] Filter behavior stays consistent across dependent reports and KPIs.
- [ ] Product ranking excludes postage/shipping, while the total retained-line measure keeps eligible charges.
- [ ] Missing customer IDs do not remove valid sales lines.
- [ ] No profitability claims are made without cost/margin fields.
- [ ] Only valid, permissioned data is used.
- [ ] Actual Birst screenshots/status are added only after real implementation and verification.

## Official Infor references

- [Preparing to use Birst](https://docs.infor.com/birst/2026.x/en-us/birstolh/intro_user/jdj1655271231404.html) — sources, modeling, measures, subject areas, reports and dashboards.
- [Creating dashboards](https://docs.infor.com/birst/latest/en-us/birstolh/dashboards_user/ifj1655271234451.html) — dashboard pages, report/KPI dashlets, filters and publishing.
- [Subject areas](https://docs.infor.com/birst/latest/en-us/birstolh/reports_user/bha1655271152572.html) — business-friendly attributes and measures.
- [Filtering data in Visualizer](https://docs.infor.com/birst/2025.x/en-us/birstolh/reports_user/xah1655271135431.html) — report and filter behavior.
