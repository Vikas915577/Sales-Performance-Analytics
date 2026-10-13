(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var state = { all: [], filtered: [], quality: null, page: 0, pageSize: 12, tableSearch: "" };
  var number = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 });
  var integer = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });
  var money = function (value) { return number.format(Number(value || 0)); };
  var count = function (value) { return integer.format(Number(value || 0)); };
  var safe = function (value) { return String(value == null ? "" : value).replace(/[&<>"']/g, function (char) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]; }); };

  function parseCsv(text) {
    var rows = [], row = [], cell = "", quoted = false;
    for (var i = 0; i < text.length; i++) {
      var ch = text[i];
      if (quoted) {
        if (ch === '"' && text[i + 1] === '"') { cell += '"'; i++; }
        else if (ch === '"') quoted = false;
        else cell += ch;
      } else if (ch === '"') quoted = true;
      else if (ch === ",") { row.push(cell); cell = ""; }
      else if (ch === "\n") { row.push(cell.replace(/\r$/, "")); if (row.some(function (v) { return v.trim() !== ""; })) rows.push(row); row = []; cell = ""; }
      else cell += ch;
    }
    if (cell.length || row.length) { row.push(cell.replace(/\r$/, "")); if (row.some(function (v) { return v.trim() !== ""; })) rows.push(row); }
    if (!rows.length) return [];
    var headers = rows.shift().map(function (v) { return v.trim(); });
    return rows.map(function (values) {
      var out = {};
      headers.forEach(function (key, idx) { out[key] = (values[idx] == null ? "" : values[idx]).trim(); });
      return out;
    });
  }

  function classifyLineType(row) {
    var code = String(row.stock_code || row.StockCode || "").trim().toUpperCase();
    var desc = String(row.description || row.Description || "").trim().toUpperCase();
    if (code === "POST" || code === "POSTAGE" || ["POSTAGE", "POSTAGE CHARGE", "CARRIAGE", "SHIPPING", "DELIVERY CHARGE"].indexOf(desc) >= 0) return "Postage / shipping";
    return "Merchandise";
  }

  function normalizeRows(text) {
    return parseCsv(text).map(function (r) {
      var row = {
        invoice_no: String(r.invoice_no || r.InvoiceNo || "").trim(),
        stock_code: String(r.stock_code || r.StockCode || "").trim(),
        description: String(r.description || r.Description || "Unknown product").trim() || "Unknown product",
        quantity: Number(r.quantity != null ? r.quantity : r.Quantity) || 0,
        invoice_date: String(r.invoice_date || r.InvoiceDate || "").trim(),
        unit_price: Number(r.unit_price != null ? r.unit_price : r.UnitPrice) || 0,
        customer_id: String(r.customer_id != null ? r.customer_id : (r.CustomerID || "")).trim(),
        country: String(r.country || r.Country || "Unknown country").trim() || "Unknown country",
        line_revenue: Number(r.line_revenue) || 0,
        line_type: String(r.line_type || r.LineType || "").trim()
      };
      if (!row.line_revenue && row.quantity && row.unit_price) row.line_revenue = row.quantity * row.unit_price;
      row.date_only = row.invoice_date.slice(0, 10);
      row.line_type = row.line_type || classifyLineType(row);
      return row;
    }).filter(function (r) { return r.invoice_no && r.date_only && Number.isFinite(Date.parse(r.date_only)); });
  }

  function monthKey(row) { return row.date_only.slice(0, 7); }
  function groupBy(rows, keyFn) {
    var grouped = new Map();
    rows.forEach(function (row) {
      var key = keyFn(row);
      if (!grouped.has(key)) grouped.set(key, []);
      grouped.get(key).push(row);
    });
    return grouped;
  }
  function aggregate(rows, keyFn) {
    var groups = groupBy(rows, keyFn), out = [];
    groups.forEach(function (items, key) {
      out.push({ key: key, sales: items.reduce(function (s, r) { return s + r.line_revenue; }, 0), orders: new Set(items.map(function (r) { return r.invoice_no; })).size, units: items.reduce(function (s, r) { return s + r.quantity; }, 0), rows: items.length });
    });
    return out.sort(function (a, b) { return b.sales - a.sales; });
  }
  function sumSales(rows) { return rows.reduce(function (sum, r) { return sum + r.line_revenue; }, 0); }
  function uniqueCount(rows, getter) { return new Set(rows.map(getter).filter(function (v) { return String(v || "").trim() !== ""; })).size; }
  function currentFilters() {
    return { from: $("dateFrom").value, to: $("dateTo").value, country: $("countryFilter").value, type: $("lineTypeFilter").value, product: $("productFilter").value };
  }
  function filterRows() {
    var f = currentFilters();
    return state.all.filter(function (r) {
      return (!f.from || r.date_only >= f.from) && (!f.to || r.date_only <= f.to) && (!f.country || r.country === f.country) && (!f.type || r.line_type === f.type) && (!f.product || r.description === f.product);
    });
  }
  function populateFilters() {
    var countries = Array.from(new Set(state.all.map(function (r) { return r.country; }))).sort();
    var products = Array.from(new Set(state.all.map(function (r) { return r.description; }))).sort();
    $("countryFilter").innerHTML = '<option value="">All countries</option>' + countries.map(function (v) { return '<option value="' + safe(v) + '">' + safe(v) + '</option>'; }).join("");
    $("productFilter").innerHTML = '<option value="">All items</option>' + products.map(function (v) { return '<option value="' + safe(v) + '">' + safe(v) + '</option>'; }).join("");
    var dates = state.all.map(function (r) { return r.date_only; }).sort();
    $("dateFrom").min = dates[0] || ""; $("dateFrom").max = dates[dates.length - 1] || ""; $("dateFrom").value = dates[0] || "";
    $("dateTo").min = dates[0] || ""; $("dateTo").max = dates[dates.length - 1] || ""; $("dateTo").value = dates[dates.length - 1] || "";
  }
  function renderKpis(rows) {
    var allSales = sumSales(rows), postage = sumSales(rows.filter(function (r) { return r.line_type === "Postage / shipping"; }));
    var merch = sumSales(rows.filter(function (r) { return r.line_type !== "Postage / shipping"; }));
    var orders = uniqueCount(rows, function (r) { return r.invoice_no; });
    $("kpiSales").textContent = money(allSales); $("kpiOrders").textContent = count(orders);
    $("kpiAov").textContent = money(orders ? allSales / orders : 0); $("kpiMerch").textContent = money(merch);
    $("kpiUnits").textContent = count(rows.reduce(function (s, r) { return s + r.quantity; }, 0));
    $("kpiCustomers").textContent = count(uniqueCount(rows, function (r) { return r.customer_id; }));
    $("kpiPostageShare").textContent = (allSales ? (postage / allSales * 100) : 0).toFixed(2) + "%";
    $("kpiPostageValue").textContent = money(postage) + " dataset units";
    var dates = rows.map(function (r) { return r.date_only; }).sort();
    $("scopePeriod").textContent = dates.length ? dates[0] + " → " + dates[dates.length - 1] : "No rows in scope";
  }
  function drawTrend(rows) {
    var observed = groupBy(rows, monthKey);
    var allMonths = [];
    if (rows.length) {
      var dates = rows.map(function (r) { return r.date_only; }).sort();
      var cursor = new Date(dates[0].slice(0, 7) + "-01T00:00:00Z");
      var endMonth = dates[dates.length - 1].slice(0, 7);
      // Fill zero-sale months between the selected scope's first and last transaction months.
      // Otherwise a chart can visually connect non-adjacent months and mislabel the change as MoM.
      while (cursor.toISOString().slice(0, 7) <= endMonth) {
        var key = cursor.toISOString().slice(0, 7);
        var items = observed.get(key) || [];
        allMonths.push({ month: key, all: sumSales(items), merch: sumSales(items.filter(function (r) { return r.line_type !== "Postage / shipping"; })) });
        cursor.setUTCMonth(cursor.getUTCMonth() + 1);
      }
    }
    if (!allMonths.length) { $("monthlyTrend").innerHTML = '<div class="empty">No rows match these filters. Reset or widen the date range.</div>'; return allMonths; }
    var W = 740, H = 255, L = 54, R = 15, T = 24, B = 45, plotW = W - L - R, plotH = H - T - B;
    var maxValue = Math.max.apply(null, allMonths.map(function (m) { return Math.max(m.all, m.merch); }).concat([1])) * 1.1;
    var x = function (i) { return allMonths.length === 1 ? L + plotW / 2 : L + (i * plotW / (allMonths.length - 1)); };
    var y = function (v) { return T + plotH - (v / maxValue * plotH); };
    var grid = [0, .5, 1].map(function (f) { var gy = T + plotH - f * plotH; return '<line x1="' + L + '" y1="' + gy + '" x2="' + (W - R) + '" y2="' + gy + '" stroke="#2a3a55" stroke-width="1"/><text x="' + (L - 8) + '" y="' + (gy + 4) + '" fill="#93a5be" text-anchor="end" font-size="10">' + safe(money(maxValue * f)) + '</text>'; }).join("");
    var pointsAll = allMonths.map(function (m, i) { return x(i) + "," + y(m.all); }).join(" ");
    var pointsMerch = allMonths.map(function (m, i) { return x(i) + "," + y(m.merch); }).join(" ");
    var marks = allMonths.map(function (m, i) { return '<circle cx="' + x(i) + '" cy="' + y(m.all) + '" r="3" fill="#87b9ff"><title>' + safe(m.month) + ': ' + safe(money(m.all)) + '</title></circle><circle cx="' + x(i) + '" cy="' + y(m.merch) + '" r="2.7" fill="#7ce3c3"><title>' + safe(m.month) + ' merchandise: ' + safe(money(m.merch)) + '</title></circle>'; }).join("");
    var labels = allMonths.map(function (m, i) { if (allMonths.length > 8 && i % 2 !== 0 && i !== allMonths.length - 1) return ""; return '<text x="' + x(i) + '" y="' + (H - 15) + '" fill="#9cacc2" text-anchor="middle" font-size="10">' + safe(m.month) + '</text>'; }).join("");
    $("monthlyTrend").innerHTML = '<svg class="trend-svg" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Monthly retained-line sales and merchandise sales trend">' + grid + '<polyline fill="none" stroke="#87b9ff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" points="' + pointsAll + '"/><polyline fill="none" stroke="#7ce3c3" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" points="' + pointsMerch + '"/>' + marks + labels + '</svg>';
    return allMonths;
  }
  function renderBars(containerId, values, type) {
    var container = $(containerId);
    if (!values.length) { container.innerHTML = '<div class="empty">No data for this selection.</div>'; return; }
    var list = values.slice(0, 8), max = Math.max.apply(null, list.map(function (v) { return v.sales; }).concat([1]));
    container.innerHTML = list.map(function (v) {
      var width = Math.max(0, Math.min(100, (v.sales / max) * 100));
      var dataAttr = type === "country" ? 'data-country="' + safe(v.key) + '"' : 'data-product="' + safe(v.key) + '"';
      return '<button type="button" class="bar-row" ' + dataAttr + ' title="Filter by ' + safe(v.key) + '"><span class="bar-head"><span class="bar-label">' + safe(v.key) + '</span><span class="bar-value">' + safe(money(v.sales)) + '</span></span><span class="bar-track"><span class="bar-fill" style="display:block;width:' + width + '%"></span></span></button>';
    }).join("");
  }
  function renderInsights(rows, months) {
    var countries = aggregate(rows, function (r) { return r.country; });
    var products = aggregate(rows.filter(function (r) { return r.line_type !== "Postage / shipping"; }), function (r) { return r.description; });
    var topMonth = months.slice().sort(function (a, b) { return b.all - a.all; })[0];
    var topCountry = countries[0]; var topProduct = products[0];
    $("insights").innerHTML = '<article class="insight"><div class="mini-label">Strongest month by sales</div><div class="big">' + safe(topMonth ? topMonth.month : "Not available") + '</div><p>' + safe(topMonth ? money(topMonth.all) + ' dataset units in retained-line sales' : 'No month in selected scope') + '</p></article>' +
      '<article class="insight"><div class="mini-label">Leading country</div><div class="big">' + safe(topCountry ? topCountry.key : "Not available") + '</div><p>' + safe(topCountry ? money(topCountry.sales) + ' sales · ' + (sumSales(rows) ? (topCountry.sales / sumSales(rows) * 100).toFixed(1) : '0.0') + '% of selected scope' : 'No country in selected scope') + '</p></article>' +
      '<article class="insight"><div class="mini-label">Top merchandise item</div><div class="big">' + safe(topProduct ? topProduct.key : "No merchandise") + '</div><p>' + safe(topProduct ? money(topProduct.sales) + ' merchandise sales; postage excluded' : 'No merchandise rows in selected scope') + '</p></article>';
    renderBars("countryBars", countries, "country"); renderBars("productBars", products, "product");
  }
  function renderDecisions(rows, months) {
    var total = sumSales(rows), postage = sumSales(rows.filter(function (r) { return r.line_type === "Postage / shipping"; }));
    var byCountry = aggregate(rows, function (r) { return r.country; });
    var f = currentFilters();
    var cards = [];
    cards.push({ p: "P1 · Definition", title: "Keep shipping charges out of product rankings", evidence: money(postage) + " dataset units · " + (total ? (100 * postage / total).toFixed(2) : "0.00") + "% of selected retained-line sales", body: postage > 0 ? "Confirm that rows coded as postage/shipping are classified consistently. Keep them in the gross retained-line total, but separate them from merchandise performance." : "No classified postage/shipping sales are present in this selected scope. Validate the mapping whenever the source file changes.", note: "Owner: analyst / data steward" });
    var sortedMonths = months.slice().sort(function (a, b) { return a.month.localeCompare(b.month); });
    var decline = null;
    for (var i = 1; i < sortedMonths.length; i++) {
      var prev = sortedMonths[i - 1], curr = sortedMonths[i];
      if (prev.all > 0) { var pct = (curr.all - prev.all) / prev.all * 100; if (pct < 0 && (!decline || pct < decline.pct)) decline = { prev: prev, curr: curr, pct: pct, delta: curr.all - prev.all }; }
    }
    cards.push({ p: "P2 · Trend review", title: decline ? "Investigate the largest month-over-month decline" : "Check monthly movement before acting", evidence: decline ? decline.prev.month + " → " + decline.curr.month + ": " + money(decline.delta) + " (" + decline.pct.toFixed(1) + "%)" : (sortedMonths.length < 2 ? "Fewer than two months in scope" : "No decline found in this scope"), body: decline ? "Compare order count and average order value across these months; then check product/country mix and source completeness. The decline alone does not explain its cause." : "Use the monthly series and transaction details to compare order count and AOV. Widen the date filter if the selected scope is too narrow.", note: "Owner: sales operations" });
    var countryShare = total && byCountry.length ? byCountry[0].sales / total * 100 : 0;
    var countryEvidence = f.country ? "One country selected: clear the country filter to compare market concentration." : (byCountry.length ? byCountry[0].key + " = " + countryShare.toFixed(1) + "% of selected sales" : "No country data in scope");
    cards.push({ p: "P3 · Market review", title: "Review country contribution in context", evidence: countryEvidence, body: f.country ? "Market concentration cannot be assessed across countries while a single country is selected. Reset that filter to compare the full market mix." : "Compare the largest country's share with an approved business threshold and consider order counts, customer mix, local currency and go-to-market strategy before changing allocation.", note: "Owner: commercial lead · threshold must come from the business" });
    $("decisionQueue").innerHTML = cards.map(function (c) { return '<article class="decision"><span class="priority">' + safe(c.p) + '</span><h3>' + safe(c.title) + '</h3><div class="evidence">' + safe(c.evidence) + '</div><p>' + safe(c.body) + '</p><div class="owner-note">' + safe(c.note) + '</div></article>'; }).join("");
  }
  function renderQuality() {
    var q = state.quality || {};
    var items = [
      ["Input rows", q.input_rows], ["Retained rows", q.rows_retained_for_sales_analysis], ["Excluded rows", q.rows_excluded_from_sales_analysis],
      ["Cancellation-like rows", q.cancelled_invoice_rows_flagged], ["Invalid quantity rows", q.non_positive_or_missing_quantity_rows_flagged],
      ["Invalid price rows", q.non_positive_or_missing_unit_price_rows_flagged], ["Invalid date rows", q.invalid_or_missing_invoice_date_rows_flagged], ["Missing customer IDs", q.missing_customer_id_rows_flagged]
    ];
    $("qualityGrid").innerHTML = items.map(function (item) { return '<article class="quality-card"><div class="quality-label">' + safe(item[0]) + '</div><div class="quality-value">' + safe(item[1] == null ? "—" : count(item[1])) + '</div></article>'; }).join("");
    if (q.note) $("qualityNote").textContent = q.note;
  }
  function renderTable(rows) {
    var search = state.tableSearch.toLowerCase();
    var found = rows.filter(function (r) { return [r.invoice_no, r.description, r.country, r.stock_code, r.line_type].join(" ").toLowerCase().indexOf(search) >= 0; });
    var totalPages = Math.max(1, Math.ceil(found.length / state.pageSize));
    state.page = Math.min(state.page, totalPages - 1);
    var start = state.page * state.pageSize;
    var items = found.slice(start, start + state.pageSize);
    $("transactionRows").innerHTML = items.length ? items.map(function (r) { return '<tr><td>' + safe(r.invoice_no) + '</td><td>' + safe(r.date_only) + '</td><td>' + safe(r.country) + '</td><td>' + safe(r.description) + '</td><td>' + safe(r.line_type) + '</td><td class="num-cell">' + safe(count(r.quantity)) + '</td><td class="num-cell">' + safe(money(r.unit_price)) + '</td><td class="num-cell">' + safe(money(r.line_revenue)) + '</td></tr>'; }).join("") : '<tr><td colspan="8" style="text-align:center;padding:25px">No transaction rows match this search/filter.</td></tr>';
    $("tableCount").textContent = count(found.length) + " matching line items";
    $("pageSummary").textContent = found.length ? "Rows " + (start + 1) + "–" + Math.min(start + items.length, found.length) + " of " + found.length : "No rows";
    $("prevPage").disabled = state.page <= 0; $("nextPage").disabled = state.page >= totalPages - 1;
  }
  function render() {
    state.filtered = filterRows(); state.page = 0;
    var rows = state.filtered;
    renderKpis(rows);
    var months = drawTrend(rows);
    renderInsights(rows, months);
    renderDecisions(rows, months);
    renderTable(rows);
  }
  function loadQuality() {
    return fetch("data_quality_report.json", { cache: "no-store" }).then(function (response) { if (!response.ok) throw new Error("Quality report unavailable"); return response.json(); }).catch(function () { return null; });
  }
  function loadData() {
    $("loadStatus").classList.remove("error"); $("loadStatus").textContent = "Loading transaction data…";
    return fetch("sales_transactions_sql_ready.csv", { cache: "no-store" }).then(function (response) { if (!response.ok) throw new Error("Could not load sales_transactions_sql_ready.csv"); return response.text(); }).then(function (text) {
      state.all = normalizeRows(text);
      if (!state.all.length) throw new Error("The transaction file contains no usable rows");
      return loadQuality();
    }).then(function (quality) {
      state.quality = quality; populateFilters(); render(); renderQuality();
      $("loadStatus").textContent = "Loaded " + count(state.all.length) + " retained transaction lines";
    }).catch(function (error) {
      $("loadStatus").classList.add("error"); $("loadStatus").textContent = "Data load failed: " + error.message + ". Run the dashboard from GitHub Pages or a local HTTP server and confirm the CSV is present.";
      $("monthlyTrend").innerHTML = '<div class="empty">Unable to load data. Confirm sales_transactions_sql_ready.csv exists beside index.html, then use Retry.</div>';
      $("resetFilters").textContent = "Retry data load";
    });
  }
  function resetFilters() {
    if (!state.all.length) { loadData(); return; }
    var dates = state.all.map(function (r) { return r.date_only; }).sort();
    $("dateFrom").value = dates[0]; $("dateTo").value = dates[dates.length - 1];
    $("countryFilter").value = ""; $("lineTypeFilter").value = ""; $("productFilter").value = "";
    state.tableSearch = ""; $("tableSearch").value = ""; state.page = 0; render();
  }
  function applyBarFilter(event, attr, selectId) {
    var button = event.target.closest("[" + attr + "]");
    if (!button) return;
    $(selectId).value = button.getAttribute(attr); render();
    $("filters").scrollIntoView({ behavior: "smooth", block: "start" });
  }
  ["dateFrom", "dateTo", "countryFilter", "lineTypeFilter", "productFilter"].forEach(function (id) { $(id).addEventListener("change", render); });
  $("applyFilters").addEventListener("click", render);
  $("resetFilters").addEventListener("click", resetFilters);
  $("countryBars").addEventListener("click", function (e) { applyBarFilter(e, "data-country", "countryFilter"); });
  $("productBars").addEventListener("click", function (e) { applyBarFilter(e, "data-product", "productFilter"); });
  $("tableSearch").addEventListener("input", function () { state.tableSearch = this.value || ""; state.page = 0; renderTable(state.filtered); });
  $("prevPage").addEventListener("click", function () { state.page = Math.max(0, state.page - 1); renderTable(state.filtered); });
  $("nextPage").addEventListener("click", function () { state.page += 1; renderTable(state.filtered); });
  loadData();
}());
