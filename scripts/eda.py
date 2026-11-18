"""Export source-quality checks and training-only EDA without changing the model."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd

from churn.schema import CATEGORICAL, NUMERIC
from churn.training import clean_data

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def summarize(raw: pd.DataFrame, train_ids: list[str]) -> dict[str, Any]:
    """Describe source quality and only the saved training population's associations."""
    data, cleaning = clean_data(raw)
    if not train_ids or len(set(train_ids)) != len(train_ids):
        raise ValueError("Training IDs must be non-empty and unique.")
    if not set(train_ids) <= set(data["customerID"]):
        raise ValueError("Training IDs must belong to the source dataset.")
    train = data.set_index("customerID").loc[train_ids]
    target = train["Churn"].eq("Yes").astype(int)
    numeric = train[NUMERIC].copy()
    numeric["Churn"] = target
    outliers = {}
    for name in NUMERIC:
        lower, upper = train[name].quantile([.25, .75])
        spread = upper - lower
        outliers[name] = {
            "lower_fence": float(lower - 1.5 * spread),
            "upper_fence": float(upper + 1.5 * spread),
            "outside_fences": int(((train[name] < lower - 1.5 * spread)
                                   | (train[name] > upper + 1.5 * spread)).sum()),
        }
    return {
        "scope": "Source quality: full CSV. Distributions and associations: saved training rows only.",
        "source_quality": {
            "rows": len(raw), "columns": len(raw.columns),
            "unique_customer_ids": int(raw["customerID"].nunique()),
            "duplicate_rows": int(raw.duplicated().sum()),
            "duplicate_profiles_excluding_id": int(raw.drop(columns="customerID").duplicated().sum()),
            "missing_or_blank_before": {
                name: int((raw[name].isna() | raw[name].astype(str).str.strip().eq("")).sum())
                for name in raw.columns
            },
            "missing_after": {name: int(data[name].isna().sum()) for name in data.columns},
            "raw_dtypes": {name: str(dtype) for name, dtype in raw.dtypes.items()},
            "clean_dtypes": {name: str(dtype) for name, dtype in data.dtypes.items()},
            "cleaning": cleaning,
        },
        "training_rows": len(train),
        "class_counts": {label: int(train["Churn"].eq(label).sum()) for label in ("No", "Yes")},
        "training_churn_rate": float(target.mean()),
        "numeric_statistics": train[NUMERIC].describe().to_dict(),
        "iqr_diagnostics": outliers,
        "categorical_segments": {
            name: [{"category": str(label), "count": len(group),
                    "churned": int(group["Churn"].eq("Yes").sum()),
                    "churn_rate": float(group["Churn"].eq("Yes").mean())}
                   for label, group in train.groupby(name, sort=True)]
            for name in CATEGORICAL
        },
        "pearson_correlation": numeric.corr().to_dict(),
    }


def save_plots(train: pd.DataFrame, report: dict[str, Any], output: Path) -> list[str]:
    """Plot measured training counts, distributions, rates and Pearson correlations."""
    output.mkdir(parents=True, exist_ok=True)
    names = []

    def save(figure: plt.Figure, name: str) -> None:
        """Write one monochrome figure and release its memory."""
        figure.tight_layout()
        figure.savefig(output / name, dpi=150)
        plt.close(figure)
        names.append(name)

    figure, axis = plt.subplots(figsize=(6, 4))
    counts = list(report["class_counts"].values())
    bars = axis.bar(["Stayed (No)", "Churned (Yes)"], counts, color=["#a3a3a3", "#171717"])
    axis.bar_label(bars)
    axis.set(ylabel="Training customers", title="Training class balance")
    save(figure, "class_balance.png")

    figure, axes = plt.subplots(1, len(NUMERIC), figsize=(13, 4))
    for axis, name in zip(axes, NUMERIC):
        edges = np.histogram_bin_edges(train[name], bins=20)
        for label, color in (("No", "#a3a3a3"), ("Yes", "#171717")):
            axis.hist(train.loc[train["Churn"].eq(label), name], bins=edges, histtype="step",
                      label=label, color=color, linewidth=1.8, linestyle="--" if label == "No" else "-")
        axis.set(title=name, xlabel="Months" if name == "tenure" else "Source USD", ylabel="Training customers")
        axis.legend(title="Recorded churn")
    save(figure, "numeric_distributions.png")

    figure, axes = plt.subplots(1, 3, figsize=(13, 5))
    for axis, name in zip(axes, ("Contract", "InternetService", "PaymentMethod")):
        groups = report["categorical_segments"][name]
        bars = axis.bar([item["category"] for item in groups],
                        [100 * item["churn_rate"] for item in groups], color="#171717")
        axis.bar_label(bars, labels=[f"n={item['count']}" for item in groups], fontsize=8)
        axis.set(title=name, ylabel="Observed training churn (%)", ylim=(0, 100))
        axis.tick_params(axis="x", labelrotation=30, labelsize=8)
    save(figure, "categorical_churn.png")

    correlations = pd.DataFrame(report["pearson_correlation"])
    figure, axis = plt.subplots(figsize=(7, 5))
    image = axis.imshow(correlations, cmap="Greys", vmin=-1, vmax=1)
    axis.set(xticks=range(len(correlations)), yticks=range(len(correlations)),
             xticklabels=correlations.columns, yticklabels=correlations.index,
             title="Training Pearson correlation (Churn: Yes=1)")
    axis.tick_params(axis="x", labelrotation=30)
    for row in range(len(correlations)):
        for column in range(len(correlations)):
            value = correlations.iloc[row, column]
            axis.text(column, row, f"{value:.2f}", ha="center", va="center",
                      color="white" if value > .4 else "black")
    figure.colorbar(image, ax=axis, label="Pearson r")
    save(figure, "correlation.png")
    return names


def markdown(report: dict[str, Any]) -> str:
    """Render an examiner-readable report using only the computed values."""
    quality = report["source_quality"]
    lines = ["# Exploratory Data Analysis (EDA)", "",
             f"Generated at {report['generated_at_utc']}. Reproduce with `uv run python scripts/eda.py`.", "",
             "## Scope and timing", "",
             ("This report was added after the original model was frozen. It is descriptive follow-up, "
             "not evidence that these plots guided the original model choice. Source-quality checks use the full CSV; "
             "all plotted distributions and feature/target relationships use the saved training partition only. "
             "No fitting, model selection, threshold change or held-out-label EDA is performed."), "",
             f"Source SHA-256: `{report['source_sha256']}`. Saved split SHA-256: `{report['split_sha256']}`.", "",
             "## Data quality and preprocessing", "",
             "| Check | Executed result |", "|---|---:|",
             *[f"| {label} | {value:,} |" for label, value in (
                 ("Source rows", quality["rows"]), ("Source columns", quality["columns"]),
                 ("Unique customer IDs", quality["unique_customer_ids"]),
                 ("Exact duplicate rows", quality["duplicate_rows"]),
                 ("Repeated profiles excluding customer ID", quality["duplicate_profiles_excluding_id"]),
                 ("Blank zero-tenure TotalCharges filled with zero",
                  quality["cleaning"]["zero_tenure_total_charges_filled"]),
                 ("Missing values after cleaning", sum(quality["missing_after"].values())),
                 ("Rows dropped", quality["cleaning"]["rows_dropped"]))], "",
             ("Repeated profiles can belong to distinct customers and are not automatically removed. "
             "Only the documented zero-tenure blank-charge rule fills values; schema checks reject unexplained invalid values. "
             "Raw/cleaned types and per-column missing counts are recorded in `artifacts/eda/summary.json`."), "",
             "## Training class balance", "",
             (f"Training population: {report['training_rows']:,}. No: {report['class_counts']['No']:,}; "
             f"Yes: {report['class_counts']['Yes']:,}. Observed churn: {report['training_churn_rate']:.2%}. "
             "The unequal class counts motivate reporting precision, recall and average precision alongside accuracy."), "",
             "![Training class balance](../artifacts/eda/plots/class_balance.png)", "",
             "## Numerical distributions and outlier diagnostics", "",
             "| Field | Mean | Median | Min | Max | Outside 1.5-IQR fences |",
             "|---|---:|---:|---:|---:|---:|"]
    for name, values in report["numeric_statistics"].items():
        lines.append(f"| {name} | {values['mean']:.3f} | {values['50%']:.3f} | {values['min']:.3f} | "
                     f"{values['max']:.3f} | {report['iqr_diagnostics'][name]['outside_fences']:,} |")
    lines += ["", ("IQR fences are descriptive diagnostics, not automatic deletion rules. "
              "All validated source rows remain in the experiment. Histograms use identical bins for both labels; "
              "their vertical axes are counts, not within-class densities."), "",
              "![Training numerical distributions](../artifacts/eda/plots/numeric_distributions.png)", "",
              "## Categorical associations", "",
              ("The tables below cover every categorical predictor. Rates are descriptive training associations, "
              "not causal effects or prospective forecasts. Compare group counts as well as rates."), "",
              "![Selected training categorical rates](../artifacts/eda/plots/categorical_churn.png)"]
    contracts = {item["category"]: item for item in report["categorical_segments"]["Contract"]}
    lines += ["", "### Observed training findings", "",
              (f"Month-to-month accounts have observed churn {contracts['Month-to-month']['churn_rate']:.2%} "
               f"(n={contracts['Month-to-month']['count']:,}), compared with "
               f"{contracts['Two year']['churn_rate']:.2%} for two-year accounts "
               f"(n={contracts['Two year']['count']:,}). These groups may differ in other attributes; "
               "this is not evidence that changing a contract causes retention."), "",
              (f"Training Pearson r between tenure and the binary churn indicator is "
               f"{report['pearson_correlation']['Churn']['tenure']:.3f}; between monthly charges and churn it is "
               f"{report['pearson_correlation']['Churn']['MonthlyCharges']:.3f}. "
               "These are measured linear associations, not model performance or causal effects.")]
    for name, groups in report["categorical_segments"].items():
        lines += ["", f"### {name}", "", "| Category | Customers | Churned | Observed churn |",
                  "|---|---:|---:|---:|"]
        lines.extend(f"| {item['category']} | {item['count']:,} | {item['churned']:,} | {item['churn_rate']:.2%} |"
                     for item in groups)
    lines += ["", "## Correlation", "",
              "![Training Pearson correlation](../artifacts/eda/plots/correlation.png)", "",
              ("Pearson correlation describes linear relationships among the three numeric predictors and a binary "
              "churn indicator (Yes=1). It does not capture every nonlinear or categorical relationship. "
              "Total charges and tenure may encode overlapping account history; correlation alone does not justify "
              "dropping a predictor or establish leakage. The complete numeric matrix is in the JSON evidence."), "",
              "## Limits and next steps", "",
              ("This fictional-company sample supplies no external operator cohort or dated future outcomes. "
              "Group association, a model coefficient and SHAP are different quantities; none demonstrates a "
              "retention intervention's effectiveness. Keep the frozen evaluation and pursue representative "
              "temporal/external validation and subgroup error analysis before operational use."), ""]
    return "\n".join(lines)


def run(root: Path = ROOT) -> dict[str, Any]:
    """Verify saved partitions, then export independent EDA artifacts and a report."""
    sys.path.insert(0, str(ROOT))
    from scripts.download_data import download

    source = download(root)
    raw = pd.read_csv(source)
    split_path = root / "artifacts/splits.json"
    splits = json.loads(split_path.read_text(encoding="utf-8"))
    ids = [identifier for name in ("train", "validation", "test") for identifier in splits[name]]
    if len(ids) != len(set(ids)) or set(ids) != set(raw["customerID"]):
        raise ValueError("Saved partitions must cover the source exactly without overlap.")
    report = summarize(raw, splits["train"])
    report.update(generated_at_utc=datetime.now(UTC).isoformat(),
                  source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  split_sha256=hashlib.sha256(split_path.read_bytes()).hexdigest(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    output = root / "artifacts/eda"
    data, _ = clean_data(raw)
    train = data.set_index("customerID").loc[splits["train"]]
    report["plots"] = save_plots(train, report, output / "plots")
    (output / "summary.json").write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    (root / "docs/EDA_REPORT.md").write_text(markdown(report), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = run()
    print(f"EDA exported: {result['training_rows']:,} training rows; {len(result['plots'])} measured plots.")
