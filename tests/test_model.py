"""Check model evidence, input validation and explanation reconstruction."""

import base64
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import average_precision_score, roc_auc_score

from churn.inference import ChurnService
from churn.schema import FEATURE_NAMES, validate_customer
from churn.training import clean_data, split_data
from scripts import download_data

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def service() -> ChurnService:
    """Load the real trained model; missing artifacts fail the integration check."""
    return ChurnService(ROOT)


@pytest.fixture
def customer(service: ChurnService) -> dict:
    """Use a real held-out record rather than invented observations."""
    return dict(service.customers[0]["features"])


def test_service_missing_artifacts_is_explicit(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ChurnService(tmp_path)


@pytest.mark.parametrize("field,value", [
    ("tenure", -1), ("tenure", 1.5), ("tenure", True),
    ("MonthlyCharges", float("nan")), ("TotalCharges", float("inf")),
    ("Contract", "Unknown"), ("Partner", None),
])
def test_invalid_inputs_are_rejected(customer: dict, field: str, value: object) -> None:
    customer[field] = value
    with pytest.raises(ValueError, match=field):
        validate_customer(customer)


def test_extreme_integer_is_validation_error(customer: dict) -> None:
    customer["tenure"] = 10 ** 1000
    with pytest.raises(ValueError, match="tenure"):
        validate_customer(customer)


def test_unknown_and_missing_fields_rejected(customer: dict) -> None:
    with pytest.raises(ValueError, match="Unknown"):
        validate_customer({**customer, "Churn": "Yes"})
    customer.pop("tenure")
    with pytest.raises(ValueError, match="tenure"):
        validate_customer(customer)


def test_service_dependencies_are_validated(customer: dict) -> None:
    customer.update(PhoneService="No", MultipleLines="Yes")
    with pytest.raises(ValueError, match="MultipleLines"):
        validate_customer(customer)
    customer.update(PhoneService="Yes", MultipleLines="No", InternetService="No", TechSupport="Yes")
    with pytest.raises(ValueError, match="internet|Internet"):
        validate_customer(customer)


def test_csv_numerical_values_and_json_values_have_prediction_parity(customer: dict, service: ChurnService) -> None:
    csv_record = {key: str(value) for key, value in customer.items()}
    assert service.predict(csv_record, explain=False)["probability"] == pytest.approx(
        service.predict(customer, explain=False)["probability"], abs=1e-12
    )


def test_split_isolation_and_determinism() -> None:
    raw = pd.read_csv(ROOT / "data/raw/Telco-Customer-Churn.csv")
    data, _ = clean_data(raw)
    first = split_data(data)
    second = split_data(data)
    ids = [set(part["customerID"]) for part in first]
    assert not ids[0] & ids[1] and not ids[0] & ids[2] and not ids[1] & ids[2]
    assert sum(map(len, ids)) == len(raw)
    assert all(a["customerID"].tolist() == b["customerID"].tolist() for a, b in zip(first, second))
    saved = json.loads((ROOT / "artifacts/splits.json").read_text())
    assert all(ids[i] == set(saved[name]) for i, name in enumerate(["train", "validation", "test"]))


def test_cleaning_only_zero_tenure_blanks() -> None:
    raw = pd.read_csv(ROOT / "data/raw/Telco-Customer-Churn.csv")
    clean, report = clean_data(raw)
    blanks = pd.to_numeric(raw.TotalCharges, errors="coerce").isna()
    assert (raw.loc[blanks, "tenure"] == 0).all()
    assert (clean.loc[blanks, "TotalCharges"] == 0).all()
    assert report["zero_tenure_total_charges_filled"] == int(blanks.sum())
    broken = raw.copy()
    broken.loc[0, "TotalCharges"] = " "
    broken.loc[0, "tenure"] = 1
    with pytest.raises(ValueError, match="TotalCharges"):
        clean_data(broken)


def test_reported_metrics_reconcile_with_saved_heldout_predictions(service: ChurnService) -> None:
    labels = [int(row["actual_churn"]) for row in service.customers]
    scores = [row["probability"] for row in service.customers]
    assert service.summary["test_metrics"]["roc_auc"] == pytest.approx(roc_auc_score(labels, scores))
    assert service.summary["test_metrics"]["average_precision"] == pytest.approx(
        average_precision_score(labels, scores)
    )
    assert sum(map(sum, service.summary["test_metrics"]["confusion_matrix"])) == len(labels)


def test_predictions_match_saved_scores_and_shap_additivity(service: ChurnService) -> None:
    ordered = sorted(service.customers, key=lambda row: row["probability"])
    for row in [ordered[0], ordered[len(ordered) // 2], ordered[-1]]:
        result = service.predict(row["features"])
        explanation = result["explanation"]
        output = explanation["base_value"] + sum(item["contribution"] for item in explanation["contributions"])
        assert output == pytest.approx(explanation["output_value"], abs=1e-5)
        probability = 1 / (1 + np.exp(-output)) if explanation["units"] == "log-odds" else output
        assert probability == pytest.approx(result["probability"], abs=1e-5)
        assert result["probability"] == pytest.approx(row["probability"], abs=1e-7)
        assert {item["feature"] for item in explanation["contributions"]} == set(FEATURE_NAMES)
        assert explanation["additivity_error"] < 1e-5


def test_dataset_download_checks_existing_integrity(tmp_path: Path) -> None:
    target = tmp_path / "data/raw/Telco-Customer-Churn.csv"
    target.parent.mkdir(parents=True)
    target.write_text("not the canonical dataset", encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        download_data.download(tmp_path)
    assert target.read_text() == "not the canonical dataset"


def test_dataset_api_fallback_keeps_original_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = (ROOT / "data/raw/Telco-Customer-Churn.csv").read_bytes()
    calls = []

    def fake_open(request: object, timeout: int) -> io.BytesIO:
        """Simulate unavailable raw hosting while serving actual canonical bytes via the API."""
        calls.append((request.full_url, timeout))
        if request.full_url == download_data.SOURCE_URL:
            raise TimeoutError("Raw host unavailable in this transport test")
        return io.BytesIO(json.dumps({"content": base64.b64encode(payload).decode()}).encode())

    monkeypatch.setattr(download_data, "urlopen", fake_open)
    target = download_data.download(tmp_path)
    assert target.read_bytes() == payload
    assert calls == [(download_data.SOURCE_URL, 20), (download_data.API_URL, 20)]
    provenance = json.loads((tmp_path / "data/provenance.json").read_text())
    assert provenance["sha256"] == download_data.EXPECTED_SHA256
    assert provenance["download_transport"] == download_data.API_URL


def test_reported_source_hashes_match_executed_code(service: ChurnService) -> None:
    for name, expected in service.summary["training"]["code_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
