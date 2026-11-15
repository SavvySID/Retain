"""Independently reconcile train-only preprocessing and selection evidence."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from churn.inference import ChurnService
from churn.schema import NUMERIC
from churn.training import clean_data

ROOT = Path(__file__).resolve().parents[1]


def test_training_reference_and_model_selection_evidence() -> None:
    """Verify learned statistics/reference IDs against the actual saved partitions."""
    service = ChurnService(ROOT)
    splits = json.loads((ROOT / "artifacts/splits.json").read_text())
    data, _ = clean_data(pd.read_csv(ROOT / "data/raw/Telco-Customer-Churn.csv"))
    train = data.set_index("customerID").loc[splits["train"]]
    scaler = service.bundle["pipeline"].named_steps["preprocess"].named_transformers_["numeric"]
    np.testing.assert_allclose(scaler.mean_, train[NUMERIC].mean().to_numpy(), atol=1e-10)
    metadata = service.summary["training"]
    assert set(metadata["shap_background_customer_ids"]) <= set(splits["train"])
    assert set(metadata["global_importance_customer_ids"]) <= set(splits["validation"])
    assert metadata["refit_after_selection"] is False
    candidates = [item for item in service.summary["models"] if item["name"] != "Dummy baseline"]
    winner = max(candidates, key=lambda item: item["validation"]["average_precision"])
    assert winner["name"] == service.summary["model"]["name"]
