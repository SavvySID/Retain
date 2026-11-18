"""Check that EDA uses real training rows and does not inspect held-out labels."""

import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.eda import summarize

ROOT = Path(__file__).resolve().parents[1]


def test_eda_training_statistics_ignore_held_out_labels() -> None:
    """Changing held-out labels cannot change the exploratory training findings."""
    raw = pd.read_csv(ROOT / "data/raw/Telco-Customer-Churn.csv")
    train_ids = json.loads((ROOT / "artifacts/splits.json").read_text())["train"]
    report = summarize(raw, train_ids)
    training = raw[raw["customerID"].isin(train_ids)]
    assert report["class_counts"]["Yes"] == int(training["Churn"].eq("Yes").sum())
    assert report["numeric_statistics"]["tenure"]["mean"] == pytest.approx(training["tenure"].mean())
    assert sum(item["count"] for item in report["categorical_segments"]["Contract"]) == len(train_ids)
    assert report["source_quality"]["missing_or_blank_before"]["TotalCharges"] == 11
    assert sum(report["source_quality"]["missing_after"].values()) == 0
    changed = raw.copy()
    held_out = ~changed["customerID"].isin(train_ids)
    changed.loc[held_out, "Churn"] = changed.loc[held_out, "Churn"].map({"Yes": "No", "No": "Yes"})
    assert summarize(changed, train_ids) == report


def test_eda_rejects_duplicate_or_unknown_training_ids() -> None:
    """Refuse a training population that would duplicate rows or invent members."""
    raw = pd.read_csv(ROOT / "data/raw/Telco-Customer-Churn.csv")
    identifier = raw.iloc[0]["customerID"]
    for ids in ([], [identifier, identifier], ["unknown-customer"]):
        with pytest.raises(ValueError, match="Training IDs"):
            summarize(raw, ids)
