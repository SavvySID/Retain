"use strict";

// API values remain numeric until display; customer-provided strings use textContent.
const state = { summary: null, fields: [], page: 1, pageSize: 8, total: 0, customers: [], selected: null, scenario: false, request: 0, exampleIndex: 0, exampleRequest: 0, revision: 0, predictionRequest: 0, cohortRequest: 0, cohortData: null };
const $ = (selector) => document.querySelector(selector);
const number = new Intl.NumberFormat("en-US");
const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 });
const percent = (value, digits = 1) => Number.isFinite(value) ? `${(value * 100).toFixed(digits)}%` : "—";
const decimal = (value, digits = 3) => Number.isFinite(value) ? value.toFixed(digits) : "—";
const formatNumber = (value) => Number.isFinite(value) ? number.format(value) : "—";
const signed = (value) => Number.isFinite(value) ? `${value >= 0 ? "+" : ""}${value.toFixed(3)}` : "—";
const clampPercent = (value) => `${Math.max(0, Math.min(100, value))}%`;

function element(tag, className = "", text = "") {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== "") node.textContent = text;
  return node;
}

function clear(node) { node.replaceChildren(); return node; }
function append(parent, ...children) { parent.append(...children); return parent; }
function labelFor(name) { return state.fields.find((field) => field.name === name)?.label || name.replace(/([a-z])([A-Z])/g, "$1 $2"); }

async function api(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60000);
  try {
    const response = await fetch(path, { ...options, signal: controller.signal });
    if (!response.ok) {
      let message = `Request failed (${response.status}).`;
      try { message = (await response.json()).error || message; } catch { /* The server may return a non-JSON proxy error. */ }
      throw new Error(message);
    }
    return response;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("The request timed out. Please try again.");
    throw error;
  } finally { clearTimeout(timeout); }
}

function showGlobalError(message) { $("#global-error").textContent = message; $("#global-error").hidden = false; }
function setView() {
  const legacy = location.hash.slice(1);
  if (["overview", "analysis", "batch", "models"].includes(legacy)) history.replaceState({}, "", `/${legacy}`);
  const requested = location.pathname.split("/")[1] || "overview";
  const view = ["overview", "analysis", "batch", "models"].includes(requested) ? requested : "overview";
  const titles = { overview: "Overview", analysis: "Customer analysis", batch: "Batch scoring", models: "Model lab" };
  document.querySelectorAll(".view").forEach((node) => { node.hidden = node.id !== `view-${view}`; });
  document.querySelectorAll(".nav-link").forEach((node) => {
    const active = node.dataset.view === view;
    node.classList.toggle("active", active);
    if (active) node.setAttribute("aria-current", "page"); else node.removeAttribute("aria-current");
  });
  $("#breadcrumb-current").textContent = titles[view];
  document.title = `${titles[view]} · Retain`;
  const customerId = new URLSearchParams(location.search).get("customer");
  if (view === "analysis" && state.fields.length && (!state.selected || (customerId && (customerId !== state.selected.customer_id || state.scenario)))) loadExample(customerId);
}

function navigate(view, customerId = null) {
  const target = `/${view}${customerId ? `?customer=${encodeURIComponent(customerId)}` : ""}`;
  if (`${location.pathname}${location.search}${location.hash}` !== target) history.pushState({}, "", target);
  setView();
  closeDrawer();
  $("#main").focus({ preventScroll: true });
  window.scrollTo({ top: 0 });
}

function renderOverview() {
  const { dataset, test_metrics: metrics, model } = state.summary;
  const kpis = [
    ["Customers in sample", formatNumber(dataset.rows), "Source", "IBM Telco source cohort", "Descriptive benchmark data"],
    ["Observed churn rate", percent(dataset.churn_rate), "Observed", `${formatNumber(dataset.churned)} recorded departures`, "Source's last-month churn label"],
    ["Avg. monthly charge", money.format(dataset.avg_monthly_charges), "USD", "Average across the source sample", "Charges in source currency"],
    ["Model ROC AUC", decimal(metrics.roc_auc), "Held-out", model.name, "Final held-out test evaluation"],
  ];
  const grid = clear($("#kpi-grid"));
  kpis.forEach(([title, value, badge, footer, note]) => {
    const card = element("article", "card kpi-card");
    append(card, append(element("div", "kpi-top"), element("span", "", title), element("span", "kpi-badge", badge)), element("div", "kpi-value", value), element("div", "kpi-footer", footer), element("div", "kpi-note", note));
    grid.append(card);
  });
  const segment = state.summary.segments.find((item) => item.name === "Contract") || state.summary.segments[0];
  const chart = clear($("#segment-chart"));
  if (segment) segment.values.forEach((item) => {
    const label = append(element("div", "segment-label", item.label), element("small", "", `${formatNumber(item.count)} customers`));
    const fill = element("div", "segment-fill");
    fill.style.width = clampPercent(item.churn_rate * 100);
    const row = append(element("div", "segment-row"), label, append(element("div", "segment-track"), fill), element("div", "segment-number", percent(item.churn_rate)));
    row.setAttribute("aria-label", `${item.label}: ${percent(item.churn_rate)} observed churn, ${formatNumber(item.count)} customers`);
    chart.append(row);
  });
  $("#snapshot-model").textContent = model.name;
  const snapshot = clear($("#model-snapshot"));
  [["Average precision", decimal(metrics.average_precision)], ["Churn recall", percent(metrics.recall)], ["Precision", percent(metrics.precision)], ["Decision threshold", percent(model.threshold)]].forEach(([label, value]) => {
    snapshot.append(append(element("div", "snapshot-metric"), element("span", "", label), element("strong", "", value)));
  });
  $("#test-count").textContent = formatNumber(state.summary.splits.test);
}

async function loadCustomers() {
  const request = ++state.request;
  const query = new URLSearchParams({ page: state.page, page_size: state.pageSize, search: $("#customer-search").value.trim(), contract: $("#contract-filter").value, risk: $("#risk-filter").value });
  $("#customer-rows").setAttribute("aria-busy", "true");
  try {
    const data = await (await api(`/api/customers?${query}`)).json();
    if (request !== state.request) return;
    state.total = data.total;
    state.customers = data.items;
    renderCustomers(data);
  } catch (error) {
    if (request !== state.request) return;
    const cell = element("td", "empty-state", error.message);
    cell.colSpan = 7;
    clear($("#customer-rows")).append(append(element("tr"), cell));
    $("#pagination-label").textContent = "Could not load customers.";
  } finally { if (request === state.request) $("#customer-rows").removeAttribute("aria-busy"); }
}

function renderCustomers(data) {
  const body = clear($("#customer-rows"));
  data.items.forEach((customer) => {
    const row = element("tr");
    row.append(element("td", "customer-id", customer.customer_id), element("td", "", customer.features.Contract), element("td", "", `${customer.features.tenure} mo`), element("td", "", money.format(customer.features.MonthlyCharges)));
    const meterFill = element("span");
    meterFill.style.width = clampPercent(customer.probability * 100);
    const risk = append(element("div", `risk-score ${customer.risk_level === "Low" ? "risk-low" : ""}`), append(element("div", "risk-meter"), meterFill), element("span", "", percent(customer.probability)));
    risk.title = `${customer.risk_level === "High" ? "Higher" : "Lower"} risk at validation-selected threshold`;
    row.append(append(element("td"), risk), append(element("td"), element("span", `outcome ${customer.actual_churn ? "departed" : ""}`, customer.actual_churn ? "Departed" : "Stayed")));
    const button = element("button", "inspect-button", "Inspect ↗");
    button.type = "button";
    button.setAttribute("aria-label", `Inspect customer ${customer.customer_id}`);
    button.addEventListener("click", () => openCustomer(customer));
    row.append(append(element("td"), button));
    body.append(row);
  });
  if (!data.items.length) { const cell = element("td", "empty-state", "No customers match these filters. Try a different ID, contract or risk group."); cell.colSpan = 7; body.append(append(element("tr"), cell)); }
  const first = data.total ? (state.page - 1) * state.pageSize + 1 : 0;
  const last = Math.min(state.page * state.pageSize, data.total);
  $("#pagination-label").textContent = `Showing ${formatNumber(first)}–${formatNumber(last)} of ${formatNumber(data.total)} customers`;
  $("#previous-page").disabled = state.page <= 1;
  $("#next-page").disabled = state.page * state.pageSize >= data.total;
}

function renderForm() {
  const container = clear($("#customer-form-fields"));
  const groups = new Map();
  state.fields.forEach((field) => {
    const group = field.group || "Customer details";
    if (!groups.has(group)) {
      const section = append(element("section", "form-group"), element("h3", "", group));
      const grid = element("div", "fields-grid"); section.append(grid); container.append(section); groups.set(group, grid);
    }
    const wrapper = element("div", "field");
    const label = element("label", "", field.label); label.htmlFor = `field-${field.name}`;
    const control = element(field.type === "number" ? "input" : "select");
    control.id = `field-${field.name}`; control.name = field.name; control.required = true;
    if (field.type === "number") {
      control.type = "number";
      if (field.min !== undefined) control.min = field.min;
      if (field.max !== undefined) control.max = field.max;
      control.step = field.step ?? (field.name === "tenure" ? 1 : 0.01);
    } else (field.options || []).forEach((option) => control.append(element("option", "", option)));
    control.addEventListener("input", markScenario);
    append(wrapper, label, control); groups.get(group).append(wrapper);
  });
  const columnList = clear($("#schema-columns"));
  state.fields.forEach((field) => columnList.append(element("code", "", field.name)));
}

function updateServiceConsistency() {
  const noInternet = $("#field-InternetService").value === "No";
  ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"].forEach((name) => {
    const control = $(`#field-${name}`);
    if (noInternet) control.value = "No internet service";
    else if (control.value === "No internet service") control.value = "No";
    control.disabled = noInternet;
    [...control.options].forEach((option) => { option.disabled = !noInternet && option.value === "No internet service"; });
  });
  const noPhone = $("#field-PhoneService").value === "No";
  const lines = $("#field-MultipleLines");
  if (noPhone) lines.value = "No phone service";
  else if (lines.value === "No phone service") lines.value = "No";
  lines.disabled = noPhone;
  [...lines.options].forEach((option) => { option.disabled = !noPhone && option.value === "No phone service"; });
}

function markScenario() {
  state.revision += 1;
  state.scenario = true;
  if (location.search) history.replaceState({}, "", "/analysis");
  $("#profile-label").textContent = "User scenario";
  clear($("#analysis-source")).append(element("span", "source-icon", "◈"), element("span", "", "User scenario · Inputs have been edited. Run a fresh prediction to evaluate these values; no observed outcome is available."));
  updateServiceConsistency();
  const stale = element("article", "card explanation-empty");
  append(stale, element("span", "empty-symbol", "↻"), element("h2", "", "Inputs changed."), element("p", "", "Choose Predict & explain to calculate a new result for this scenario."));
  clear($("#prediction-result")).append(stale);
}

async function loadExample(customerId = null) {
  const button = $("#load-example");
  if (button.disabled && !customerId) return;
  button.disabled = true;
  const request = ++state.exampleRequest;
  const revision = state.revision;
  const route = `${location.pathname}${location.search}`;
  const isCurrent = () => request === state.exampleRequest && revision === state.revision && route === `${location.pathname}${location.search}` && location.pathname === "/analysis";
  $("#prediction-error").hidden = true;
  $("#profile-label").textContent = "Loading customer…";
  clear($("#analysis-source")).append(element("span", "", "Loading the requested held-out record."));
  clear($("#prediction-result")).append(append(element("article", "card explanation-empty"), element("h2", "", "Loading customer…"), element("p", "", "The score and explanation will appear after this record has been evaluated.")));
  try {
    const index = state.exampleIndex++;
    let customer;
    if (customerId) customer = await (await api(`/api/customers/${encodeURIComponent(customerId)}`)).json();
    else {
      const data = await (await api(`/api/customers?page=1&page_size=100`)).json();
      if (!data.items.length) throw new Error("No held-out examples are available.");
      customer = data.items[index % data.items.length];
    }
    if (!isCurrent()) return;
    await openCustomer(customer);
  } catch (error) { if (isCurrent()) showPredictionError(error.message); }
  finally { if (request === state.exampleRequest) button.disabled = false; }
}

async function openCustomer(customer) {
  if (!state.fields.length) return;
  state.revision += 1;
  state.selected = customer; state.scenario = false;
  state.fields.forEach((field) => { $(`#field-${field.name}`).value = customer.features[field.name]; });
  updateServiceConsistency();
  $("#profile-label").textContent = customer.customer_id;
  clear($("#analysis-source")).append(element("span", "source-icon", "◈"), element("span", "", `Held-out customer ${customer.customer_id} · Actual source record · Observed outcome: ${customer.actual_churn ? "departed" : "stayed"}. Editing creates a user scenario.`));
  navigate("analysis", customer.customer_id);
  await predict();
}

function showPredictionError(message) { $("#prediction-error").textContent = message; $("#prediction-error").hidden = false; }

async function predict() {
  const button = $("#predict-button");
  const request = ++state.predictionRequest;
  const revision = state.revision;
  button.disabled = true; button.textContent = "Computing explanation…";
  $("#prediction-error").hidden = true;
  $("#prediction-result").setAttribute("aria-busy", "true");
  const pending = element("article", "card explanation-empty");
  append(pending, element("span", "empty-symbol", "◎"), element("h2", "", "Computing this prediction…"), element("p", "", "The model score and SHAP factors will appear together when this customer has been evaluated."));
  clear($("#prediction-result")).append(pending);
  try {
    const record = {};
    state.fields.forEach((field) => { const value = $(`#field-${field.name}`).value; record[field.name] = field.type === "number" ? Number(value) : value; });
    const prediction = await (await api("/api/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(record) })).json();
    if (request === state.predictionRequest && revision === state.revision) renderPrediction(prediction);
  } catch (error) { if (request === state.predictionRequest && revision === state.revision) showPredictionError(error.message); }
  finally {
    if (request === state.predictionRequest) {
      button.disabled = false; button.textContent = "Predict & explain →";
      $("#prediction-result").removeAttribute("aria-busy");
    }
  }
}

function renderPrediction(prediction) {
  const result = clear($("#prediction-result"));
  const high = prediction.prediction;
  const score = element("article", "card score-card");
  append(score, append(element("div", "score-overline"), element("span", "", "PREDICTED CHURN PROBABILITY"), element("span", `risk-pill ${high ? "high" : ""}`, high ? "Higher risk" : "Lower risk")));
  const scoreNumber = element("div", `score-number ${high ? "high" : ""}`, (prediction.probability * 100).toFixed(1));
  scoreNumber.append(element("small", "", "%"));
  score.append(scoreNumber, element("p", "score-caption", `${prediction.model_name} · ${state.scenario ? "User scenario" : "Held-out customer"}`));
  const fill = element("div", `score-fill ${high ? "high" : ""}`); fill.style.width = clampPercent(prediction.probability * 100);
  const threshold = element("span", "score-threshold"); threshold.style.left = clampPercent(prediction.threshold * 100);
  threshold.title = `Decision threshold ${percent(prediction.threshold)}`;
  score.append(append(element("div", "score-track"), fill, threshold), append(element("div", "score-details"), element("span", "", "0%"), element("span", "", `Decision threshold ${percent(prediction.threshold)}`), element("span", "", "100%")));
  result.append(score);
  const explanation = prediction.explanation;
  if (explanation) {
    const contributions = [...explanation.contributions].sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
    const describe = (items) => items.map((item) => `${labelFor(item.feature)} (${item.value})`).join(" and ");
    const higher = contributions.filter((item) => item.contribution > 0).slice(0, 2);
    const lower = contributions.filter((item) => item.contribution < 0).slice(0, 2);
    const summary = element("article", "card plain-explanation");
    summary.append(element("p", "eyebrow", "IN PLAIN ENGLISH"), element("h2", "", "Why this score?"));
    summary.append(element("p", "", `The model estimates a ${percent(prediction.probability)} chance of churn and labels this profile ${high ? "higher" : "lower"} risk.`));
    if (higher.length) summary.append(element("p", "", `The strongest factors pushing the model's score higher are ${describe(higher)}.`));
    if (lower.length) summary.append(element("p", "", `The strongest factors pushing the model's score lower are ${describe(lower)}.`));
    if (!higher.length && !lower.length) summary.append(element("p", "", "No individual factor moved the model's score away from its reference value."));
    summary.append(element("p", "small-note", "These factors explain the model's prediction, not proven reasons a customer will leave."));
    result.append(summary);
    const card = element("article", "card");
    append(card, append(element("div", "card-heading"), append(element("div"), element("p", "eyebrow", "LOCAL SHAP EXPLANATION"), element("h2", "", "What shaped this score")), element("span", "subtle-tag", explanation.units)));
    card.append(element("p", "card-description", "Signed feature contributions to the model output. These describe associations, not causes."));
    const legend = element("div", "factor-legend");
    legend.append(append(element("span"), element("i"), document.createTextNode("Raises model score")), append(element("span"), element("i", "negative"), document.createTextNode("Lowers model score"))); card.append(legend);
    const max = Math.max(...contributions.map((item) => Math.abs(item.contribution)), Number.EPSILON);
    contributions.forEach((item) => {
      const label = append(element("div", "factor-label", labelFor(item.feature)), element("small", "", String(item.value)));
      const bar = element("div", `factor-bar ${item.contribution < 0 ? "negative" : ""}`);
      bar.style.width = clampPercent(Math.abs(item.contribution) / max * 48);
      card.append(append(element("div", "factor-row"), label, append(element("div", "factor-track"), bar), element("div", "factor-value", signed(item.contribution))));
    });
    const sum = contributions.reduce((total, item) => total + item.contribution, 0);
    const reconciliation = element("div", "explanation-reconciliation");
    reconciliation.append(element("div", "", `Baseline ${decimal(explanation.base_value, 4)} + contributions ${signed(sum)} = output ${decimal(explanation.output_value, 4)} ${explanation.units}`), element("div", "", `Reconstructed probability ${percent(explanation.reconstructed_probability)} · Additivity error ${Number(explanation.additivity_error).toExponential(2)}`));
    if (explanation.units === "log-odds") reconciliation.append(element("div", "", "The sigmoid function converts model output in log-odds to probability. Bar values are not percentage points."));
    card.append(reconciliation); result.append(card);
  }
  if (prediction.suggestions?.length) {
    const card = element("article", "card");
    append(card, element("p", "eyebrow", "FOR HUMAN REVIEW"), element("h2", "", "Retention discussion prompts"));
    const list = element("ul", "suggestions"); prediction.suggestions.forEach((suggestion) => list.append(element("li", "", suggestion)));
    card.append(list, element("p", "small-note", "Rule-based suggestions, not causal recommendations. No campaign effectiveness or financial benefit has been measured."));
    result.append(card);
  }
}

function renderModelLab() {
  const summary = state.summary;
  const total = Object.values(summary.splits).reduce((a, b) => a + b, 0);
  const protocol = clear($("#model-protocol"));
  [["Training", "train", "Fit preprocessing and models"], ["Validation", "validation", "Select model and threshold"], ["Held-out test", "test", "Final evaluation only"]].forEach(([label, key, note]) => {
    protocol.append(append(element("article", "card"), element("div", "protocol-label", `${label} · ${percent(summary.splits[key] / total, 0)}`), element("div", "protocol-value", formatNumber(summary.splits[key])), element("div", "protocol-note", note)));
  });
  const comparisons = clear($("#model-comparison"));
  summary.models.forEach((model) => {
    const row = element("tr", model.name === summary.model.name ? "comparison-winner" : "");
    const name = element("td", "customer-id", model.name);
    if (model.name === summary.model.name) name.append(element("span", "winner-label", "SELECTED"));
    row.append(name);
    row.append(element("td", "", decimal(model.validation.average_precision, 6)));
    [model.test.average_precision, model.test.roc_auc, model.test.precision, model.test.recall, model.test.f1, model.test.accuracy, model.test.brier].forEach((value) => row.append(element("td", "", decimal(value))));
    comparisons.append(row);
  });
  renderConfusion(summary.test_metrics.confusion_matrix);
  const importance = [...summary.global_importance].sort((a, b) => b.importance - a.importance);
  const max = Math.max(...importance.map((item) => item.importance), Number.EPSILON);
  const importanceContainer = clear($("#global-importance"));
  importance.slice(0, 10).forEach((item) => {
    const bar = element("div", "importance-fill"); bar.style.width = clampPercent(item.importance / max * 100);
    importanceContainer.append(append(element("div", "importance-row"), element("span", "", labelFor(item.feature)), append(element("div", "importance-track"), bar), element("span", "importance-value", decimal(item.importance))));
  });
  $("#importance-method").textContent = summary.training.global_importance_method || `Mean absolute SHAP contribution · ${summary.model.explanation_units}. Top ten original features.`;
  const plots = clear($("#evaluation-charts"));
  summary.charts.forEach((chart) => {
    if (!/^\/plots\/[a-zA-Z0-9_.-]+\.png$/.test(chart.url)) return;
    const image = element("img"); image.src = chart.url; image.alt = `${chart.name}: computed from the recorded model run`; image.loading = "lazy";
    plots.append(append(element("article", "card plot-card"), element("h2", "", chart.name), image));
  });
  const details = clear($("#provenance-details"));
  [["Dataset", "IBM Telco Customer Churn · fictional-company sample"], ["Rows", formatNumber(summary.dataset.rows)], ["Source SHA-256", summary.dataset.sha256], ["Selected model", summary.model.name], ["Selection criterion", summary.model.selection_metric], ["Decision threshold", percent(summary.model.threshold)], ["Excluded predictors", "customerID, Churn, gender, SeniorCitizen"]].forEach(([term, value]) => details.append(element("dt", "", term), element("dd", "", value)));
  const sourceUrl = summary.dataset.source_url;
  if (typeof sourceUrl === "string" && sourceUrl.startsWith("https://")) {
    const link = element("a", "", "Original dataset source ↗"); link.href = sourceUrl; link.target = "_blank"; link.rel = "noopener";
    details.append(element("dt", "", "Source"), append(element("dd"), link));
  }
  details.append(element("dt", "", "Cleaning report"), element("dd", "", typeof summary.dataset.cleaning === "string" ? summary.dataset.cleaning : JSON.stringify(summary.dataset.cleaning)));
  $("#training-metadata").textContent = JSON.stringify(summary.training, null, 2);
}

function renderConfusion(matrix) {
  const container = clear($("#confusion-matrix"));
  const grid = element("div", "matrix");
  grid.append(element("div"), element("div", "matrix-label", "Predicted stayed"), element("div", "matrix-label", "Predicted departed"));
  [["Actually stayed", matrix[0], ["True negative", "False positive"]], ["Actually departed", matrix[1], ["False negative", "True positive"]]].forEach(([label, values, terms], rowIndex) => {
    grid.append(element("div", "matrix-label", label));
    values.forEach((value, columnIndex) => grid.append(append(element("div", `matrix-cell ${rowIndex === columnIndex ? "correct" : "incorrect"}`), element("strong", "", formatNumber(value)), element("span", "", terms[columnIndex]))));
  });
  container.append(grid, element("p", "small-note", "Counts from held-out test customers, using the threshold selected on validation data."));
}

async function scoreBatch(event) {
  event.preventDefault();
  const file = $("#batch-file").files[0];
  const message = $("#batch-message");
  message.hidden = false; message.classList.remove("error");
  if (!file) { message.textContent = "Choose a CSV file first."; message.classList.add("error"); return; }
  if (file.size > 2 * 1024 * 1024) { message.textContent = "The file exceeds the 2 MiB upload limit."; message.classList.add("error"); return; }
  const button = $("#batch-button"); const original = button.textContent;
  button.disabled = true; button.textContent = "Validating & scoring…"; message.textContent = "Validating every row, then computing predictions locally…";
  try {
    const form = new FormData(); form.append("file", file);
    const response = await api("/api/batch", { method: "POST", body: form });
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = element("a"); link.href = url; link.download = "churn_predictions.csv";
    document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    message.textContent = "Scoring complete. Your results CSV has been downloaded. Your upload was not saved.";
  } catch (error) { message.textContent = error.message; message.classList.add("error"); }
  finally { button.disabled = false; button.textContent = original; }
}

function closeDrawer() {
  document.body.classList.remove("mobile-sidebar-open");
  $("#sidebar-backdrop").hidden = true;
  $(".shell").inert = false;
  const mobile = window.matchMedia("(max-width: 767px)").matches;
  $("#sidebar").inert = mobile;
  $("#sidebar").removeAttribute("aria-modal");
  $("#sidebar").removeAttribute("role");
  $("#sidebar").setAttribute("aria-hidden", String(mobile));
  $("#sidebar-toggle").setAttribute("aria-expanded", String(!mobile && !document.body.classList.contains("sidebar-collapsed")));
}

function bindSidebar() {
  const sidebar = $("#sidebar");
  const toggle = $("#sidebar-toggle");
  const mobile = window.matchMedia("(max-width: 767px)");
  sidebar.querySelectorAll("a").forEach((link) => {
    link.setAttribute("aria-label", link.getAttribute("aria-label") || link.textContent.trim());
    link.title = link.getAttribute("aria-label");
  });
  const close = element("button", "icon-button drawer-close", "×");
  close.id = "sidebar-close"; close.type = "button";
  close.setAttribute("aria-label", "Close navigation");
  close.addEventListener("click", () => { closeDrawer(); toggle.focus(); });
  sidebar.prepend(close);
  toggle.addEventListener("click", () => {
    if (!mobile.matches) {
      document.body.classList.toggle("sidebar-collapsed");
      toggle.setAttribute("aria-expanded", String(!document.body.classList.contains("sidebar-collapsed")));
      return;
    }
    if (document.body.classList.contains("mobile-sidebar-open")) { closeDrawer(); return; }
    document.body.classList.add("mobile-sidebar-open");
    sidebar.inert = false; sidebar.setAttribute("aria-hidden", "false");
    sidebar.setAttribute("role", "dialog"); sidebar.setAttribute("aria-modal", "true");
    $("#sidebar-backdrop").hidden = false;
    $(".shell").inert = true;
    toggle.setAttribute("aria-expanded", "true");
    close.focus();
  });
  $("#sidebar-backdrop").addEventListener("click", () => { closeDrawer(); toggle.focus(); });
  document.addEventListener("keydown", (event) => {
    if (!document.body.classList.contains("mobile-sidebar-open")) return;
    if (event.key === "Escape") { closeDrawer(); toggle.focus(); return; }
    if (event.key === "Tab") {
      const focusable = [...sidebar.querySelectorAll("a[href],button")].filter((node) => node.offsetParent !== null);
      const first = focusable[0]; const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
  mobile.addEventListener("change", closeDrawer);
  closeDrawer();
}

async function loadCohort(contract = "") {
  const request = ++state.cohortRequest;
  state.cohortData = null;
  clear($("#cohort-chart")).append(element("p", "chart-loading", "Loading held-out tenure cohorts…"));
  clear($("#cohort-data"));
  $("#cohort-count").textContent = "Loading cohort…";
  $("#cohort-chart").setAttribute("aria-busy", "true");
  document.querySelectorAll("#cohort-filters button").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.contract === contract)));
  try {
    const data = await (await api(`/api/cohorts?${new URLSearchParams({ contract })}`)).json();
    if (request !== state.cohortRequest) return;
    state.cohortData = data;
    renderCohort(data);
    const rows = clear($("#cohort-data"));
    data.bins.forEach((bin) => {
      const row = element("tr");
      [bin.label, formatNumber(bin.count), percent(bin.churn_rate), percent(bin.mean_probability)].forEach((value) => row.append(element("td", "", value)));
      rows.append(row);
    });
    $("#cohort-count").textContent = `${formatNumber(data.count)} held-out customers`;
  } catch (error) {
    if (request === state.cohortRequest) {
      clear($("#cohort-chart")).append(element("p", "chart-loading", `Chart unavailable: ${error.message}`));
      $("#cohort-count").textContent = "Cohort data unavailable";
    }
  } finally { if (request === state.cohortRequest) $("#cohort-chart").removeAttribute("aria-busy"); }
}

function svgElement(tag, attributes = {}) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  Object.entries(attributes).forEach(([name, value]) => node.setAttribute(name, value));
  return node;
}

function renderCohort(data) {
  const container = clear($("#cohort-chart"));
  const width = container.clientWidth;
  if (!width) return;
  const height = container.clientHeight;
  const left = 32, right = width - 10, top = 12, bottom = height - 30;
  const x = (index) => left + index / Math.max(data.bins.length - 1, 1) * (right - left);
  const y = (value) => bottom - value * (bottom - top);
  const svg = svgElement("svg", { viewBox: `0 0 ${width} ${height}`, role: "group", "aria-label": "Held-out observed churn and mean model probability by tenure group in months. Not a chronological forecast." });
  const defs = svgElement("defs");
  [["observed-fill", "#171717", ".26"], ["predicted-fill", "#8c8c8c", ".09"]].forEach(([id, color, opacity]) => {
    const gradient = svgElement("linearGradient", { id, x1: "0", y1: "0", x2: "0", y2: "1" });
    gradient.append(svgElement("stop", { offset: "0%", "stop-color": color, "stop-opacity": opacity }), svgElement("stop", { offset: "100%", "stop-color": color, "stop-opacity": ".02" }));
    defs.append(gradient);
  });
  svg.append(defs);
  [0, .25, .5, .75, 1].forEach((value) => {
    svg.append(svgElement("line", { x1: left, x2: right, y1: y(value), y2: y(value), stroke: "#eeeeee", "stroke-width": 1 }));
    const label = svgElement("text", { x: left - 7, y: y(value) + 4, "text-anchor": "end" });
    label.textContent = `${value * 100}%`; svg.append(label);
  });
  // Missing cohorts split the path; a missing rate is never drawn as a zero.
  [["mean_probability", "predicted-fill", "#8c8c8c", "4 3"], ["churn_rate", "observed-fill", "#171717", ""]].forEach(([key, fill, stroke, dash]) => {
    const segments = []; let points = [];
    data.bins.forEach((bin, index) => {
      if (Number.isFinite(bin[key])) points.push([x(index), y(bin[key])]);
      else if (points.length) { segments.push(points); points = []; }
    });
    if (points.length) segments.push(points);
    segments.forEach((segment) => {
      const line = segment.map(([px, py], index) => `${index ? "L" : "M"}${px},${py}`).join(" ");
      const area = `${line} L${segment[segment.length - 1][0]},${bottom} L${segment[0][0]},${bottom} Z`;
      svg.append(svgElement("path", { d: area, fill: `url(#${fill})`, stroke: "none" }));
      svg.append(svgElement("path", { d: line, fill: "none", stroke, "stroke-width": 1.5, "stroke-dasharray": dash }));
    });
  });
  const tooltip = element("div", "cohort-tooltip"); tooltip.hidden = true;
  const labelStep = width < 360 ? 3 : width < 650 ? 2 : 1;
  data.bins.forEach((bin, index) => {
    const last = data.bins.length - 1;
    if (index === last || (index % labelStep === 0 && last - index >= labelStep)) {
      const label = svgElement("text", { x: x(index), y: height - 7, "text-anchor": index === 0 ? "start" : index === data.bins.length - 1 ? "end" : "middle" });
      label.textContent = bin.label; svg.append(label);
    }
    const step = (right - left) / Math.max(data.bins.length - 1, 1);
    const hit = svgElement("rect", { x: Math.max(left, x(index) - step / 2), y: top, width: index === 0 || index === data.bins.length - 1 ? step / 2 : step, height: bottom - top, fill: "transparent", tabindex: "0", role: "img", "aria-label": `${bin.label} months: ${bin.count} customers, observed churn ${percent(bin.churn_rate)}, mean probability ${percent(bin.mean_probability)}` });
    const show = () => {
      clear(tooltip).append(element("strong", "", `${bin.label} months`));
      [["Customers", formatNumber(bin.count)], ["Observed churn", percent(bin.churn_rate)], ["Mean probability", percent(bin.mean_probability)]].forEach(([label, value]) => tooltip.append(append(element("div"), element("span", "", label), element("span", "", value))));
      tooltip.style.left = `${Math.max(0, Math.min(width - 212, x(index) - 106))}px`;
      tooltip.style.top = "8px"; tooltip.hidden = false;
    };
    hit.addEventListener("mouseenter", show); hit.addEventListener("focus", show);
    hit.addEventListener("mouseleave", () => { tooltip.hidden = true; }); hit.addEventListener("blur", () => { tooltip.hidden = true; });
    svg.append(hit);
  });
  container.append(svg, tooltip);
}

function bindEvents() {
  window.addEventListener("hashchange", setView);
  window.addEventListener("popstate", () => { setView(); closeDrawer(); });
  document.addEventListener("click", (event) => {
    const link = event.target.closest("a[href]");
    if (!link || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || link.target) return;
    const url = new URL(link.href, location.href);
    if (url.origin === location.origin && ["/overview", "/analysis", "/batch", "/models"].includes(url.pathname)) {
      event.preventDefault(); navigate(url.pathname.slice(1));
    }
  });
  bindSidebar();
  document.querySelectorAll("#cohort-filters button").forEach((button) => button.addEventListener("click", () => loadCohort(button.dataset.contract)));
  new ResizeObserver(() => { if (state.cohortData && $("#cohort-chart").clientWidth > 0) renderCohort(state.cohortData); }).observe($("#cohort-chart"));
  let searchTimer;
  $("#customer-search").addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(() => { state.page = 1; loadCustomers(); }, 250); });
  ["#contract-filter", "#risk-filter"].forEach((selector) => $(selector).addEventListener("change", () => { state.page = 1; loadCustomers(); }));
  $("#previous-page").addEventListener("click", () => { if (state.page > 1) { state.page -= 1; loadCustomers(); } });
  $("#next-page").addEventListener("click", () => { if (state.page * state.pageSize < state.total) { state.page += 1; loadCustomers(); } });
  $("#load-example").addEventListener("click", () => loadExample());
  $("#prediction-form").addEventListener("submit", (event) => { event.preventDefault(); predict(); });
  $("#batch-form").addEventListener("submit", scoreBatch);
  $("#batch-file").addEventListener("change", () => { $("#selected-file").textContent = $("#batch-file").files[0]?.name || "No file selected"; $("#batch-message").hidden = true; });
}

async function initialize() {
  bindEvents(); setView();
  try {
    const [schemaResponse, summaryResponse] = await Promise.all([api("/api/schema"), api("/api/summary")]);
    const schema = await schemaResponse.json(); state.fields = schema.fields;
    state.summary = await summaryResponse.json();
    renderForm(); renderOverview(); renderModelLab();
    $("#model-status").textContent = "Model ready";
    await Promise.all([loadCustomers(), loadCohort()]);
    setView();
  } catch (error) {
    $("#model-status").textContent = "Model unavailable"; $("#model-status").classList.add("unavailable");
    showGlobalError(`${error.message} If the model is not trained yet, run the training command from the project README, restart the server and reload this page.`);
    $("#kpi-grid").replaceChildren(element("div", "card loading-card", "Results are unavailable. No metrics are shown until a valid model run is loaded."));
  }
}

initialize();
