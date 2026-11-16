"use strict";

// Every preview value is returned by the local API; no demo metrics are invented.
const homeState = { customers: [], index: 0, predictionRequest: 0, cohortRequest: 0, cohort: null };
const homeQuery = (selector) => document.querySelector(selector);
const homePercent = (value) => Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : "—";
const homeNumber = (value) => Number.isFinite(value) ? new Intl.NumberFormat("en-US").format(value) : "—";
const homeSigned = (value) => `${value >= 0 ? "+" : ""}${value.toFixed(3)}`;

function homeElement(tag, className = "", text = "") {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== "") node.textContent = text;
  return node;
}

async function homeApi(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 30000);
  try {
    const response = await fetch(path, { ...options, signal: controller.signal });
    if (!response.ok) {
      let message = `Local request failed (${response.status}).`;
      try { message = (await response.json()).error || message; } catch { /* A proxy can return a non-JSON error. */ }
      throw new Error(message);
    }
    return await response.json();
  } catch (error) {
    if (error.name === "AbortError") throw new Error("The local request timed out. Please try again.");
    throw error;
  } finally { clearTimeout(timer); }
}

function selectDemo(name) {
  document.querySelectorAll("#home-demo-controls button").forEach((button) => button.setAttribute("aria-pressed", String(button.dataset.demo === name)));
  homeQuery("#home-demo-cohort").hidden = name !== "cohort";
  homeQuery("#home-demo-explanation").hidden = name !== "explanation";
  if (name === "cohort" && homeState.cohort) renderHomeCohort(homeState.cohort);
}

async function loadPreview() {
  const status = homeQuery("#home-preview-status");
  try {
    const [summary, customers] = await Promise.all([
      homeApi("/api/summary"), homeApi("/api/customers?page=1&page_size=20"),
    ]);
    homeQuery("#home-customers").textContent = homeNumber(summary.dataset.rows);
    homeQuery("#home-auc").textContent = summary.test_metrics.roc_auc.toFixed(3);
    homeQuery("#home-churn").textContent = homePercent(summary.dataset.churn_rate);
    homeQuery("#home-ap").textContent = summary.test_metrics.average_precision.toFixed(3);
    homeQuery("#home-selected-model").textContent = summary.model.name;
    homeQuery("#home-test-count").textContent = homeNumber(summary.splits.test);
    homeState.customers = customers.items;
    status.textContent = `${summary.model.name} · Results loaded from the recorded local run.`;
    if (!homeState.customers.length) throw new Error("No held-out customer examples are available.");
    await loadHomePrediction();
  } catch (error) {
    status.textContent = error.message;
    status.classList.add("demo-error");
    homeQuery("#home-customer-id").textContent = "Customer example unavailable";
    homeQuery("#home-factors").replaceChildren(homeElement("p", "demo-loading demo-error", error.message));
    homeQuery("#home-next-customer").disabled = true;
  }
}

async function loadHomePrediction() {
  const customer = homeState.customers[homeState.index % homeState.customers.length];
  if (!customer) return;
  const request = ++homeState.predictionRequest;
  const button = homeQuery("#home-next-customer");
  button.disabled = true;
  homeQuery("#home-factors").setAttribute("aria-busy", "true");
  homeQuery("#home-factors").replaceChildren(homeElement("p", "demo-loading", "Computing this customer's explanation…"));
  homeQuery("#home-customer-id").textContent = customer.customer_id;
  homeQuery("#home-probability").textContent = "—";
  delete homeQuery("#home-probability").dataset.probability;
  homeQuery("#home-risk-bar").style.width = "0%";
  homeQuery("#home-prediction-label").textContent = "Evaluating";
  homeQuery("#home-factor-units").textContent = "—";
  homeQuery("#home-reconciliation").textContent = "Computing the baseline and signed contributions for this customer…";
  homeQuery("#home-customer-note").textContent = `${customer.features.Contract} · Actual held-out record`;
  homeQuery("#home-tenure").textContent = `${customer.features.tenure} mo`;
  homeQuery("#home-charge").textContent = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(customer.features.MonthlyCharges);
  homeQuery("#home-outcome").textContent = customer.actual_churn ? "Departed" : "Stayed";
  homeQuery("#home-analysis-link").href = `/analysis?customer=${encodeURIComponent(customer.customer_id)}`;
  try {
    const prediction = await homeApi("/api/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(customer.features) });
    if (request !== homeState.predictionRequest) return;
    homeQuery("#home-probability").textContent = homePercent(prediction.probability);
    homeQuery("#home-probability").dataset.probability = prediction.probability;
    homeQuery("#home-risk-bar").style.width = `${Math.max(0, Math.min(100, prediction.probability * 100))}%`;
    homeQuery("#home-prediction-label").textContent = prediction.prediction ? "Higher model risk" : "Lower model risk";
    const explanation = prediction.explanation;
    homeQuery("#home-factor-units").textContent = explanation.units;
    const factors = homeQuery("#home-factors"); factors.replaceChildren();
    const sorted = [...explanation.contributions].sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
    const max = Math.max(...sorted.map((item) => Math.abs(item.contribution)), Number.EPSILON);
    sorted.slice(0, 5).forEach((item) => {
      const row = homeElement("div", "home-factor");
      row.dataset.feature = item.feature; row.dataset.contribution = item.contribution;
      const label = homeElement("div", "home-factor-label", item.feature.replace(/([a-z])([A-Z])/g, "$1 $2"));
      label.append(homeElement("small", "", String(item.value)));
      const track = homeElement("div", "factor-track");
      const bar = homeElement("span", `factor-bar ${item.contribution < 0 ? "negative" : ""}`);
      bar.style.width = `${Math.abs(item.contribution) / max * 48}%`;
      track.append(bar);
      row.append(label, track, homeElement("span", "home-factor-value", homeSigned(item.contribution)));
      factors.append(row);
    });
    const sum = explanation.contributions.reduce((value, item) => value + item.contribution, 0);
    const reconciliation = homeQuery("#home-reconciliation");
    reconciliation.replaceChildren(
      homeElement("div", "", `Baseline ${explanation.base_value.toFixed(4)} + all contributions ${homeSigned(sum)} = ${explanation.output_value.toFixed(4)} ${explanation.units}`),
      homeElement("div", "", `Reconstructed probability ${homePercent(explanation.reconstructed_probability)} · Additivity error ${explanation.additivity_error.toExponential(2)}`),
    );
    if (explanation.units === "log-odds") reconciliation.append(homeElement("div", "", "Log-odds contributions are not percentage-point effects."));
  } catch (error) {
    if (request !== homeState.predictionRequest) return;
    homeQuery("#home-prediction-label").textContent = "Unavailable";
    homeQuery("#home-factors").replaceChildren(homeElement("p", "demo-loading demo-error", error.message));
    homeQuery("#home-reconciliation").textContent = "An explanation is unavailable. No previous customer's score or factors are retained.";
  } finally {
    if (request === homeState.predictionRequest) {
      button.disabled = false; homeQuery("#home-factors").removeAttribute("aria-busy");
    }
  }
}

function homeSvg(tag, attributes = {}) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  Object.entries(attributes).forEach(([name, value]) => node.setAttribute(name, value));
  return node;
}

async function loadHomeCohort() {
  const request = ++homeState.cohortRequest;
  homeState.cohort = null;
  const container = homeQuery("#home-cohort-chart");
  container.setAttribute("aria-busy", "true");
  container.replaceChildren(homeElement("p", "chart-loading", "Loading measured tenure cohorts…"));
  homeQuery("#home-cohort-count").textContent = "—";
  homeQuery("#home-cohort-data").replaceChildren();
  try {
    const contract = homeQuery("#home-contract-filter").value;
    const data = await homeApi(`/api/cohorts?${new URLSearchParams({ contract })}`);
    if (request !== homeState.cohortRequest) return;
    homeState.cohort = data;
    homeQuery("#home-cohort-count").textContent = homeNumber(data.count);
    renderHomeCohort(data);
    data.bins.forEach((bin) => {
      const row = homeElement("tr");
      [bin.label, homeNumber(bin.count), homePercent(bin.churn_rate), homePercent(bin.mean_probability)].forEach((value) => row.append(homeElement("td", "", value)));
      homeQuery("#home-cohort-data").append(row);
    });
  } catch (error) {
    if (request === homeState.cohortRequest) container.replaceChildren(homeElement("p", "chart-loading demo-error", error.message));
  } finally { if (request === homeState.cohortRequest) container.removeAttribute("aria-busy"); }
}

function renderHomeCohort(data) {
  const container = homeQuery("#home-cohort-chart");
  const width = container.clientWidth; const height = container.clientHeight;
  if (!width) return;
  const left = 34, right = width - 10, top = 14, bottom = height - 30;
  const x = (index) => left + index / Math.max(data.bins.length - 1, 1) * (right - left);
  const y = (value) => bottom - value * (bottom - top);
  const svg = homeSvg("svg", { viewBox: `0 0 ${width} ${height}`, role: "group", "aria-label": "Actual held-out churn and mean probability across tenure groups. Not a timeline." });
  const defs = homeSvg("defs");
  const gradient = homeSvg("linearGradient", { id: "home-cohort-gradient", x1: "0", y1: "0", x2: "0", y2: "1" });
  gradient.append(homeSvg("stop", { offset: "0%", "stop-color": "#087f70", "stop-opacity": ".24" }), homeSvg("stop", { offset: "100%", "stop-color": "#087f70", "stop-opacity": ".02" }));
  defs.append(gradient); svg.append(defs);
  [0, .25, .5, .75, 1].forEach((value) => {
    svg.append(homeSvg("line", { x1: left, x2: right, y1: y(value), y2: y(value), stroke: "#e7eeea", "stroke-width": 1 }));
    const label = homeSvg("text", { x: left - 7, y: y(value) + 4, "text-anchor": "end" }); label.textContent = `${value * 100}%`; svg.append(label);
  });
  [["churn_rate", "#087f70", ""], ["mean_probability", "#668991", "5 4"]].forEach(([key, color, dash]) => {
    const segments = []; let points = [];
    data.bins.forEach((bin, index) => {
      if (Number.isFinite(bin[key])) points.push([x(index), y(bin[key])]);
      else if (points.length) { segments.push(points); points = []; }
    });
    if (points.length) segments.push(points);
    segments.forEach((segment) => {
      const line = segment.map(([px, py], index) => `${index ? "L" : "M"}${px},${py}`).join(" ");
      if (key === "churn_rate") svg.append(homeSvg("path", { d: `${line} L${segment[segment.length - 1][0]},${bottom} L${segment[0][0]},${bottom} Z`, fill: "url(#home-cohort-gradient)", stroke: "none" }));
      svg.append(homeSvg("path", { d: line, fill: "none", stroke: color, "stroke-width": 2, "stroke-dasharray": dash }));
    });
  });
  const tooltip = homeElement("div", "cohort-tooltip"); tooltip.hidden = true;
  const labelStep = width < 360 ? 3 : width < 650 ? 2 : 1;
  data.bins.forEach((bin, index) => {
    const last = data.bins.length - 1;
    if (index === last || (index % labelStep === 0 && last - index >= labelStep)) {
      const label = homeSvg("text", { x: x(index), y: height - 7, "text-anchor": index === 0 ? "start" : index === last ? "end" : "middle" }); label.textContent = bin.label; svg.append(label);
    }
    const step = (right - left) / Math.max(last, 1);
    const hit = homeSvg("rect", { x: Math.max(left, x(index) - step / 2), y: top, width: index === 0 || index === last ? step / 2 : step, height: bottom - top, fill: "transparent", tabindex: "0", role: "img", "aria-label": `${bin.label} months: ${bin.count} customers, observed churn ${homePercent(bin.churn_rate)}, mean probability ${homePercent(bin.mean_probability)}` });
    hit.dataset.bin = index;
    const show = () => {
      tooltip.replaceChildren(homeElement("strong", "", `${bin.label} months`));
      [["Customers", homeNumber(bin.count)], ["Observed churn", homePercent(bin.churn_rate)], ["Mean probability", homePercent(bin.mean_probability)]].forEach(([label, value]) => {
        const row = homeElement("div"); row.append(homeElement("span", "", label), homeElement("span", "", value)); tooltip.append(row);
      });
      tooltip.style.left = `${Math.max(0, Math.min(width - 212, x(index) - 106))}px`; tooltip.style.top = "12px"; tooltip.hidden = false;
    };
    hit.addEventListener("mouseenter", show); hit.addEventListener("focus", show);
    hit.addEventListener("mouseleave", () => { tooltip.hidden = true; }); hit.addEventListener("blur", () => { tooltip.hidden = true; });
    svg.append(hit);
  });
  container.replaceChildren(svg, tooltip);
}

function initializeHome() {
  document.querySelectorAll("#home-demo-controls button").forEach((button) => button.addEventListener("click", () => selectDemo(button.dataset.demo)));
  homeQuery("#home-contract-filter").addEventListener("change", loadHomeCohort);
  homeQuery("#home-next-customer").addEventListener("click", () => { homeState.index += 1; loadHomePrediction(); });
  new ResizeObserver(() => { if (homeState.cohort) renderHomeCohort(homeState.cohort); }).observe(homeQuery("#home-cohort-chart"));
  loadPreview(); loadHomeCohort();
}

const legacyView = location.hash.slice(1);
if (["overview", "analysis", "batch", "models"].includes(legacyView)) location.replace(`/${legacyView}`);
else initializeHome();
