"use strict";

// Preview values come from the same actual artifacts as the analyst workspace.
async function loadPreview() {
  const status = document.querySelector("#home-preview-status");
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  try {
    const responses = await Promise.all([
      fetch("/api/summary", { signal: controller.signal }),
      fetch("/api/customers?page=1&page_size=1", { signal: controller.signal }),
    ]);
    if (responses.some((response) => !response.ok)) throw new Error("Recorded benchmark results are unavailable.");
    const summary = await responses[0].json();
    const customers = await responses[1].json();
    const customer = customers.items[0];
    document.querySelector("#home-customers").textContent = new Intl.NumberFormat("en-US").format(summary.dataset.rows);
    document.querySelector("#home-auc").textContent = summary.test_metrics.roc_auc.toFixed(3);
    document.querySelector("#home-churn").textContent = `${(summary.dataset.churn_rate * 100).toFixed(1)}%`;
    document.querySelector("#home-ap").textContent = summary.test_metrics.average_precision.toFixed(3);
    if (customer) {
      document.querySelector("#home-customer-id").textContent = customer.customer_id;
      document.querySelector("#home-probability").textContent = `${(customer.probability * 100).toFixed(1)}% churn probability`;
      document.querySelector("#home-risk-bar").style.width = `${Math.max(0, Math.min(100, customer.probability * 100))}%`;
      document.querySelector("#home-customer-note").textContent = `${customer.features.Contract} · ${customer.features.tenure} mo · Actual held-out record`;
    }
    status.textContent = `${summary.model.name} · Results loaded from the recorded local run.`;
  } catch (error) {
    status.textContent = error.name === "AbortError" ? "The local preview timed out. Open the workspace to check model readiness." : error.message;
  } finally { clearTimeout(timer); }
}

const legacyView = location.hash.slice(1);
if (["overview", "analysis", "batch", "models"].includes(legacyView)) {
  location.replace(`/${legacyView}`);
} else {
  loadPreview();
}
