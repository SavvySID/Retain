"use strict";

// API values remain numeric until display; customer-provided strings use textContent.
const state = { summary: null, fields: [], page: 1, pageSize: 8, total: 0, customers: [], selected: null, scenario: false, request: 0, exampleIndex: 0, revision: 0, predictionRequest: 0 };
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
  const requested = location.hash.slice(1) || "overview";
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
  if (view === "analysis" && state.fields.length && !state.selected) loadExample();
}

function renderOverview() {
  const { dataset, test_metrics: metrics, model } = state.summary;
  const kpis = [
    ["Customers in sample", formatNumber(dataset.rows), "◈", "Source records · descriptive cohort"],
    ["Observed churn rate", percent(dataset.churn_rate), "↗", `${formatNumber(dataset.churned)} customers departed`],
    ["Avg. monthly charge", money.format(dataset.avg_monthly_charges), "$", "USD · source sample average"],
    ["Model ROC AUC", decimal(metrics.roc_auc), "◎", "Evaluated on held-out test data"],
  ];
  const grid = clear($("#kpi-grid"));
  kpis.forEach(([title, value, icon, note]) => {
    const card = element("article", "card kpi-card");
    append(card, append(element("div", "kpi-top"), element("span", "", title), element("span", "kpi-icon", icon)), element("div", "kpi-value", value), element("div", "kpi-note", note));
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
  $("#profile-label").textContent = "User scenario";
  clear($("#analysis-source")).append(element("span", "source-icon", "◈"), element("span", "", "User scenario · Inputs have been edited. Run a fresh prediction to evaluate these values; no observed outcome is available."));
  updateServiceConsistency();
  const stale = element("article", "card explanation-empty");
  append(stale, element("span", "empty-symbol", "↻"), element("h2", "", "Inputs changed."), element("p", "", "Choose Predict & explain to calculate a new result for this scenario."));
  clear($("#prediction-result")).append(stale);
}

async function loadExample() {
  const button = $("#load-example"); button.disabled = true;
  try {
    const data = await (await api(`/api/customers?page=1&page_size=100`)).json();
    if (!data.items.length) throw new Error("No held-out examples are available.");
    const customer = data.items[state.exampleIndex % data.items.length];
    state.exampleIndex += 1;
    await openCustomer(customer);
  } catch (error) { showPredictionError(error.message); }
  finally { button.disabled = false; }
}

async function openCustomer(customer) {
  if (!state.fields.length) return;
  state.revision += 1;
  state.selected = customer; state.scenario = false;
  state.fields.forEach((field) => { $(`#field-${field.name}`).value = customer.features[field.name]; });
  updateServiceConsistency();
  $("#profile-label").textContent = customer.customer_id;
  clear($("#analysis-source")).append(element("span", "source-icon", "◈"), element("span", "", `Held-out customer ${customer.customer_id} · Actual source record · Observed outcome: ${customer.actual_churn ? "departed" : "stayed"}. Editing creates a user scenario.`));
  if (location.hash !== "#analysis") location.hash = "analysis";
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
    const card = element("article", "card");
    append(card, append(element("div", "card-heading"), append(element("div"), element("p", "eyebrow", "LOCAL SHAP EXPLANATION"), element("h2", "", "What shaped this score")), element("span", "subtle-tag", explanation.units)));
    card.append(element("p", "card-description", "Signed feature contributions to the model output. These describe associations, not causes."));
    const legend = element("div", "factor-legend");
    legend.append(append(element("span"), element("i"), document.createTextNode("Raises model score")), append(element("span"), element("i", "negative"), document.createTextNode("Lowers model score"))); card.append(legend);
    const contributions = [...explanation.contributions].sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
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

function bindEvents() {
  window.addEventListener("hashchange", () => { setView(); window.scrollTo({ top: 0 }); });
  let searchTimer;
  $("#customer-search").addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(() => { state.page = 1; loadCustomers(); }, 250); });
  ["#contract-filter", "#risk-filter"].forEach((selector) => $(selector).addEventListener("change", () => { state.page = 1; loadCustomers(); }));
  $("#previous-page").addEventListener("click", () => { if (state.page > 1) { state.page -= 1; loadCustomers(); } });
  $("#next-page").addEventListener("click", () => { if (state.page * state.pageSize < state.total) { state.page += 1; loadCustomers(); } });
  $("#load-example").addEventListener("click", loadExample);
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
    await loadCustomers();
    setView();
  } catch (error) {
    $("#model-status").textContent = "Model unavailable"; $("#model-status").classList.add("unavailable");
    showGlobalError(`${error.message} If the model is not trained yet, run the training command from the project README, restart the server and reload this page.`);
    $("#kpi-grid").replaceChildren(element("div", "card loading-card", "Results are unavailable. No metrics are shown until a valid model run is loaded."));
  }
}

initialize();
