"""Deterministic training, validation-only selection and untouched test reporting."""

import hashlib
import importlib.metadata
import json
import platform
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import matplotlib
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from churn.inference import build_explainer, explain_matrix
from churn.schema import CATEGORICAL, FEATURE_NAMES, NUMERIC, validate_customer

matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEED = 42


def write_json(path: Path, value: Any) -> None:
    """Write standards-compliant JSON, refusing non-finite fabricated placeholders."""
    path.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def clean_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Validate the source; only zero-tenure blank total bills become zero."""
    expected = set(FEATURE_NAMES) | {"customerID", "gender", "SeniorCitizen", "Churn"}
    if set(raw.columns) != expected:
        raise ValueError("Unexpected source columns; use the pinned original IBM sample.")
    data = raw.copy()
    if data["customerID"].isna().any() or data["customerID"].duplicated().any():
        raise ValueError("customerID must be present and unique.")
    if not data["Churn"].isin(["Yes", "No"]).all():
        raise ValueError("Churn labels must be Yes or No.")
    totals = pd.to_numeric(data["TotalCharges"], errors="coerce")
    blank = data["TotalCharges"].astype(str).str.strip().eq("")
    if (totals.isna() & ~(blank & data["tenure"].eq(0))).any():
        raise ValueError("Unexplained missing or invalid TotalCharges; refusing to invent values.")
    data["TotalCharges"] = totals.fillna(0)
    for index, record in enumerate(data[FEATURE_NAMES].to_dict(orient="records")):
        try:
            validate_customer(record)
        except ValueError as exc:
            raise ValueError(f"Source row {index + 2}: {exc}") from exc
    report = {
        "zero_tenure_total_charges_filled": int(blank.sum()),
        "rows_dropped": 0, "duplicate_customer_ids": 0,
        "rule": "Blank TotalCharges is zero only when tenure is zero; all other missing values are rejected.",
    }
    return data, report


def split_data(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Produce stable stratified 60/20/20 partitions before fitting preprocessing."""
    train, remainder = train_test_split(data, test_size=0.4, stratify=data["Churn"], random_state=SEED)
    validation, test = train_test_split(
        remainder, test_size=0.5, stratify=remainder["Churn"], random_state=SEED
    )
    return train.copy(), validation.copy(), test.copy()


def make_pipeline(estimator: Any) -> Pipeline:
    """Bundle train-only scaling and encoding with the classifier to prevent serving drift."""
    preprocess = ColumnTransformer([
        ("numeric", StandardScaler(), NUMERIC),
        ("categorical", OneHotEncoder(handle_unknown="error", sparse_output=False), CATEGORICAL),
    ])
    return Pipeline([("preprocess", preprocess), ("model", estimator)])


def choose_threshold(labels: np.ndarray, scores: np.ndarray) -> float:
    """Maximize validation F1; ties choose the highest threshold (fewer alerts)."""
    precision, recall, thresholds = precision_recall_curve(labels, scores)
    f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-12)
    best = np.flatnonzero(np.isclose(f1, f1.max(), rtol=0, atol=1e-12))[-1]
    return float(thresholds[best])


def score_metrics(labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, Any]:
    """Compute all reported metrics directly from labels and model scores."""
    predicted = scores >= threshold
    return {
        "accuracy": float(accuracy_score(labels, predicted)),
        "precision": float(precision_score(labels, predicted, zero_division=0)),
        "recall": float(recall_score(labels, predicted, zero_division=0)),
        "f1": float(f1_score(labels, predicted, zero_division=0)),
        "roc_auc": float(roc_auc_score(labels, scores)),
        "average_precision": float(average_precision_score(labels, scores)),
        "brier": float(brier_score_loss(labels, scores)),
        "confusion_matrix": confusion_matrix(labels, predicted, labels=[0, 1]).tolist(),
        "threshold": threshold,
    }


def grouped_names(pipeline: Pipeline) -> list[str]:
    """Map transformed one-hot columns back to their original predictor field."""
    encoder = pipeline.named_steps["preprocess"].named_transformers_["categorical"]
    return NUMERIC + [name for name, categories in zip(CATEGORICAL, encoder.categories_) for _ in categories]


def bootstrap_intervals(labels: np.ndarray, scores: np.ndarray, threshold: float) -> dict[str, Any]:
    """Estimate paired test-row bootstrap intervals without selecting or tuning the model."""
    rng = np.random.default_rng(SEED)
    measured: dict[str, list[float]] = {name: [] for name in ["roc_auc", "average_precision", "recall", "f1"]}
    for _ in range(300):
        indices = rng.integers(0, len(labels), len(labels))
        if len(np.unique(labels[indices])) != 2:
            continue
        metrics = score_metrics(labels[indices], scores[indices], threshold)
        for name, values in measured.items():
            values.append(metrics[name])
    return {
        "method": "Paired held-out row bootstrap, 300 resamples, percentile 95% interval; fixed fitted model and threshold.",
        "seed": SEED, "resamples": 300,
        "metrics": {name: [float(x) for x in np.quantile(values, [0.025, 0.975])] for name, values in measured.items()},
    }


def save_plots(
    directory: Path, labels: np.ndarray, scores: np.ndarray, matrix: list[list[int]],
    importance: list[dict[str, Any]], units: str, validation_labels: np.ndarray,
    validation_scores: np.ndarray, threshold: float,
) -> list[dict[str, str]]:
    """Render only observed held-out diagnostics and validation threshold evidence."""
    directory.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    charts = []

    def save(fig: Any, filename: str, title: str) -> None:
        """Persist a generated diagnostic and its browser route."""
        fig.tight_layout()
        fig.savefig(directory / filename, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        charts.append({"name": title, "url": f"/plots/{filename}"})

    fpr, tpr, _ = roc_curve(labels, scores)
    fig, axis = plt.subplots(figsize=(6.5, 4))
    axis.plot(fpr, tpr, color="#ea6c32", lw=2, label=f"ROC-AUC {roc_auc_score(labels, scores):.3f}")
    axis.plot([0, 1], [0, 1], "--", color="#9ca3af", label="Chance reference")
    axis.set(xlabel="False positive rate", ylabel="True positive rate", title="ROC curve · held-out test")
    axis.legend(frameon=False)
    save(fig, "roc_curve.png", "ROC curve")

    precision, recall, _ = precision_recall_curve(labels, scores)
    fig, axis = plt.subplots(figsize=(6.5, 4))
    axis.plot(recall, precision, color="#256b65", lw=2, label=f"Average precision {average_precision_score(labels, scores):.3f}")
    axis.axhline(float(labels.mean()), color="#9ca3af", linestyle="--", label=f"Test prevalence {labels.mean():.3f}")
    axis.set(xlabel="Recall", ylabel="Precision", title="Precision–recall · held-out test", ylim=(0, 1.04))
    axis.legend(frameon=False)
    save(fig, "precision_recall.png", "Precision–recall curve")

    observed, predicted = calibration_curve(labels, scores, n_bins=10, strategy="quantile")
    fig, axis = plt.subplots(figsize=(6.5, 4))
    axis.plot(predicted, observed, "o-", color="#256b65", label="Observed test bins")
    axis.plot([0, 1], [0, 1], "--", color="#9ca3af", label="Perfect calibration reference")
    axis.set(xlabel="Mean predicted score", ylabel="Observed churn fraction", title="Calibration · held-out test", xlim=(0, 1), ylim=(0, 1))
    axis.legend(frameon=False)
    save(fig, "calibration.png", "Calibration curve")

    fig, axis = plt.subplots(figsize=(6.5, 4))
    image = axis.imshow(matrix, cmap="Greens")
    for row in range(2):
        for column in range(2):
            axis.text(column, row, str(matrix[row][column]), ha="center", va="center", fontsize=22,
                      color="white" if matrix[row][column] > np.max(matrix) / 2 else "#16392d")
    axis.set(xticks=[0, 1], yticks=[0, 1], xticklabels=["Stay", "Churn"], yticklabels=["Stay", "Churn"],
             xlabel="Predicted class", ylabel="Actual class", title="Confusion matrix · held-out test")
    fig.colorbar(image, ax=axis, label="Customer count")
    save(fig, "confusion_matrix.png", "Confusion matrix")

    top = importance[:10][::-1]
    fig, axis = plt.subplots(figsize=(6.5, 4))
    axis.barh([item["feature"] for item in top], [item["importance"] for item in top], color="#256b65")
    axis.set(xlabel=f"Mean absolute grouped SHAP ({units})", title="Global explanation · validation sample")
    save(fig, "global_importance.png", "Global SHAP importance")

    precision, recall, thresholds = precision_recall_curve(validation_labels, validation_scores)
    f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-12)
    fig, axis = plt.subplots(figsize=(6.5, 4))
    axis.plot(thresholds, f1, color="#ea6c32", label="Validation F1")
    axis.axvline(threshold, linestyle="--", color="#256b65", label=f"Selected {threshold:.4f}")
    axis.set(xlabel="Decision threshold", ylabel="F1", title="Threshold selection · validation only")
    axis.legend(frameon=False)
    save(fig, "threshold_selection.png", "Validation threshold selection")
    return charts


def train(root: Path, source_path: Path) -> dict[str, Any]:
    """Train candidates, freeze the validation-selected model and export measured evidence."""
    started = time.perf_counter()
    started_at = datetime.now(UTC).isoformat()
    data, cleaning = clean_data(pd.read_csv(source_path, keep_default_na=False))
    train_frame, validation, test = split_data(data)
    x_train, x_validation, x_test = [frame[FEATURE_NAMES] for frame in [train_frame, validation, test]]
    y_train, y_validation, y_test = [frame["Churn"].eq("Yes").astype(int).to_numpy() for frame in [train_frame, validation, test]]
    estimators = {
        "Dummy baseline": DummyClassifier(strategy="prior"),
        "Logistic regression": LogisticRegression(C=1.0, max_iter=2000, random_state=SEED),
        "Random forest": RandomForestClassifier(n_estimators=180, max_depth=8, min_samples_leaf=5, random_state=SEED, n_jobs=2),
        "XGBoost": XGBClassifier(n_estimators=240, max_depth=3, learning_rate=0.05, subsample=0.9,
                                  colsample_bytree=0.9, reg_lambda=2, objective="binary:logistic",
                                  eval_metric="logloss", random_state=SEED, n_jobs=2),
    }
    fitted: dict[str, Pipeline] = {}
    validation_scores: dict[str, np.ndarray] = {}
    model_results = []
    for name, estimator in estimators.items():
        pipeline = make_pipeline(estimator)
        pipeline.fit(x_train, y_train)
        scores = pipeline.predict_proba(x_validation)[:, 1]
        threshold = 0.5 if name == "Dummy baseline" else choose_threshold(y_validation, scores)
        fitted[name] = pipeline
        validation_scores[name] = scores
        parameters = {
            key: "NaN (missing-value sentinel)" if isinstance(value, float) and not np.isfinite(value) else value
            for key, value in estimator.get_params().items()
        }
        model_results.append({"name": name, "validation": score_metrics(y_validation, scores, threshold), "parameters": parameters})
        print(f"{name}: validation AP={model_results[-1]['validation']['average_precision']:.6f}, threshold={threshold:.6f}", flush=True)
    best = max((item for item in model_results if item["name"] != "Dummy baseline"), key=lambda item: item["validation"]["average_precision"])
    selected = fitted[best["name"]]
    threshold = best["validation"]["threshold"]
    # Freeze selection before touching test labels; do not refit after threshold selection.
    for item in model_results:
        item["test"] = score_metrics(y_test, fitted[item["name"]].predict_proba(x_test)[:, 1], item["validation"]["threshold"])
    selected_scores = selected.predict_proba(x_test)[:, 1]
    background_frame = x_train.sample(n=min(100, len(x_train)), random_state=SEED)
    units = "log-odds" if best["name"] == "Logistic regression" else "probability"
    bundle = {
        "pipeline": selected, "background": selected.named_steps["preprocess"].transform(background_frame),
        "transformed_groups": grouped_names(selected), "model_name": best["name"],
        "threshold": threshold, "explanation_units": units, "feature_names": FEATURE_NAMES,
    }
    explainer = build_explainer(bundle)
    importance_frame = x_validation.sample(n=min(200, len(validation)), random_state=SEED)
    grouped, _ = explain_matrix(bundle, explainer, importance_frame)
    importance = sorted([{"feature": name, "importance": float(np.abs(grouped[:, i]).mean())}
                         for i, name in enumerate(FEATURE_NAMES)], key=lambda item: item["importance"], reverse=True)
    customers = [{
        "customer_id": row["customerID"], "probability": float(score), "prediction": bool(score >= threshold),
        "actual_churn": row["Churn"] == "Yes", "risk_level": "High" if score >= threshold else "Low",
        "features": {name: (int(row[name]) if name == "tenure" else float(row[name]) if name in NUMERIC else row[name]) for name in FEATURE_NAMES},
    } for (_, row), score in zip(test.iterrows(), selected_scores)]
    customers.sort(key=lambda row: row["probability"], reverse=True)
    artifacts = root / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    charts = save_plots(artifacts / "plots", y_test, selected_scores, best["test"]["confusion_matrix"],
                        importance, units, y_validation, validation_scores[best["name"]], threshold)
    provenance = json.loads((root / "data/provenance.json").read_text(encoding="utf-8"))
    code_paths = ["src/churn/schema.py", "src/churn/training.py", "src/churn/inference.py", "scripts/train.py", "scripts/download_data.py"]
    segments = [{"name": name, "values": [{"label": str(label), "count": len(group), "churn_rate": float(group["Churn"].eq("Yes").mean())}
                                          for label, group in data.groupby(name, sort=True)]}
                for name in ["Contract", "InternetService", "PaymentMethod"]]
    summary = {
        "dataset": {"rows": len(data), "churned": int(data["Churn"].eq("Yes").sum()),
                    "churn_rate": float(data["Churn"].eq("Yes").mean()), "avg_monthly_charges": float(data["MonthlyCharges"].mean()),
                    "avg_tenure": float(data["tenure"].mean()), "source_url": provenance["source_url"],
                    "sha256": provenance["sha256"], "cleaning": cleaning},
        "splits": {"train": len(train_frame), "validation": len(validation), "test": len(test)},
        "model": {"name": best["name"], "threshold": threshold, "selection_metric": "Validation average precision", "explanation_units": units},
        "test_metrics": best["test"], "models": model_results, "segments": segments, "charts": charts,
        "global_importance": importance,
        "test_confidence_intervals": bootstrap_intervals(y_test, selected_scores, threshold),
        "training": {
            "started_at_utc": started_at, "completed_at_utc": datetime.now(UTC).isoformat(),
            "elapsed_seconds": time.perf_counter() - started, "random_seed": SEED,
            "python": platform.python_version(), "platform": platform.platform(),
            "packages": {name: importlib.metadata.version(name) for name in ["pandas", "numpy", "scikit-learn", "shap", "xgboost", "joblib", "matplotlib"]},
            "code_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in code_paths},
            "command": "uv run python scripts/train.py", "refit_after_selection": False,
            "threshold_selection": "Maximum validation F1, ties choose highest threshold. Dummy uses 0.5.",
            "global_importance_method": f"Mean absolute grouped SHAP over {len(importance_frame)} deterministic validation rows; units={units}",
            "global_importance_customer_ids": validation.loc[importance_frame.index, "customerID"].tolist(),
            "shap_background_customer_ids": train_frame.loc[background_frame.index, "customerID"].tolist(),
            "excluded_predictors": ["customerID", "Churn", "gender", "SeniorCitizen"],
            "limitations": ["Fictional benchmark; no external or temporal validation.", "Last-month churn label is not a verified future forecast.",
                            "SHAP associations are not causal effects; suggestions are rule-based prompts.", "Dropping demographic predictors does not establish fairness.",
                            "Probability calibration is measured, not guaranteed. No business savings or campaign uplift estimated."],
        },
    }
    joblib.dump(bundle, artifacts / "model.joblib", compress=3)
    write_json(artifacts / "customers.json", customers)
    write_json(artifacts / "summary.json", summary)
    write_json(artifacts / "splits.json", {name: frame["customerID"].tolist() for name, frame in zip(["train", "validation", "test"], [train_frame, validation, test])})
    write_json(artifacts / "manifest.json", {"sha256": {name: hashlib.sha256((artifacts / name).read_bytes()).hexdigest()
                                                       for name in ["model.joblib", "summary.json", "customers.json", "splits.json"]}})
    print(f"Selected {best['name']}; test ROC-AUC={best['test']['roc_auc']:.6f}; AP={best['test']['average_precision']:.6f}", flush=True)
    return summary
