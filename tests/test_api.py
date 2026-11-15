"""Exercise real model integration and untrusted HTTP/CSV boundaries."""

import csv
import io
import shutil
from pathlib import Path

import pytest

from app import create_app


@pytest.fixture(scope="module")
def client():
    """Use real trained artifacts; train first rather than silently skip tests."""
    application = create_app()
    application.config["TESTING"] = True
    assert application.extensions["churn_service"] is not None, "Run scripts/train.py first"
    return application.test_client()


def sample(client) -> dict:
    """Read an actual held-out feature row from the API."""
    return client.get("/api/customers?page_size=1").json["items"][0]["features"]


def upload(client, rows: list[dict], fields: list[str] | None = None):
    """Encode a test CSV as a multipart upload."""
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields or list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return client.post("/api/batch", data={"file": (io.BytesIO(stream.getvalue().encode()), "rows.csv")})


def test_unavailable_model_reports_503(tmp_path: Path):
    """A new folder must not imply a ready model or fake a prediction."""
    empty = create_app(tmp_path).test_client()
    assert empty.get("/api/health").status_code == 503
    assert empty.get("/api/summary").status_code == 503
    assert empty.post("/api/predict", json={}).status_code == 503


def test_corrupt_model_is_rejected_before_deserialization(tmp_path: Path, monkeypatch):
    """A broken model must fail integrity checking before pickle is invoked."""
    source = Path(__file__).resolve().parents[1] / "artifacts"
    target = tmp_path / "artifacts"
    target.mkdir()
    for name in ["manifest.json", "model.joblib", "summary.json", "customers.json", "splits.json"]:
        shutil.copyfile(source / name, target / name)
    (target / "model.joblib").write_bytes(b"deliberately corrupted model for a failure-path test")
    calls = []
    monkeypatch.setattr("churn.inference.joblib.load", lambda path: calls.append(path))
    response = create_app(tmp_path).test_client().get("/api/health")
    assert response.status_code == 503
    assert not calls


def test_health_schema_and_actual_summary(client):
    assert client.get("/api/health").json["status"] == "ready"
    schema = client.get("/api/schema").json
    assert len(schema["fields"]) == 17
    summary = client.get("/api/summary").json
    assert sum(summary["splits"].values()) == summary["dataset"]["rows"]
    assert 0 <= summary["test_metrics"]["roc_auc"] <= 1


def test_prediction_matches_saved_holdout_and_reconstructs(client):
    row = client.get("/api/customers?page_size=1").json["items"][0]
    response = client.post("/api/predict", json=row["features"])
    assert response.status_code == 200
    result = response.json
    assert result["probability"] == pytest.approx(row["probability"], abs=1e-6)
    assert result["explanation"]["reconstructed_probability"] == pytest.approx(result["probability"], abs=1e-5)


def test_prediction_rejects_bad_json_missing_and_target_leakage(client):
    assert client.post("/api/predict", data="{}", content_type="text/plain").status_code == 400
    assert client.post("/api/predict", json=[]).status_code == 400
    assert client.post("/api/predict", data="{", content_type="application/json").status_code == 400
    assert client.post("/api/predict", json={}).status_code == 400
    record = sample(client)
    record["Churn"] = "Yes"
    assert client.post("/api/predict", json=record).status_code == 400
    huge_number = {**sample(client), "tenure": 10**1000}
    assert client.post("/api/predict", json=huge_number).status_code == 400


def test_customers_search_filters_pagination_and_unknown(client):
    row = client.get("/api/customers?page_size=1").json["items"][0]
    assert client.get("/api/customers", query_string={"search": row["customer_id"]}).json["total"] == 1
    assert client.get(f"/api/customers/{row['customer_id']}").json == row
    assert client.get("/api/customers/does-not-exist").status_code == 404
    for query in ["page=0", "page_size=101", "page=NaN", "risk=unknown", "contract=unknown"]:
        assert client.get(f"/api/customers?{query}").status_code == 400
    result = client.get("/api/customers?risk=High").json
    assert all(row["risk_level"] == "High" for row in result["items"])


def test_batch_matches_single_and_escapes_spreadsheet_formula(client):
    record = sample(client)
    expected = client.post("/api/predict", json=record).json["probability"]
    response = upload(client, [{"customerID": "=1+1", **record}])
    assert response.status_code == 200
    rows = list(csv.DictReader(io.StringIO(response.data.decode("utf-8-sig"))))
    assert rows[0]["customerID"] == "'=1+1"
    assert float(rows[0]["churn_probability"]) == pytest.approx(expected, abs=1e-8)
    assert "attachment" in response.headers["Content-Disposition"]


def test_batch_rejects_invalid_file_headers_rows_and_encoding(client):
    assert client.post("/api/batch").status_code == 400
    row = sample(client)
    assert upload(client, [{**row, "unexpected": "x"}]).status_code == 400
    assert upload(client, [row], list(row) + [next(iter(row))]).status_code == 400
    bad = {**row, "tenure": "invalid"}
    assert upload(client, [row, bad]).status_code == 400
    for payload in [b"", b"a,b\n", b"\xff\xfe", b"x" * (2 * 1024 * 1024 + 1)]:
        response = client.post("/api/batch", data={"file": (io.BytesIO(payload), "bad.csv")})
        assert response.status_code in (400, 413)
    assert upload(client, [row] * 1001).status_code == 400


def test_sample_is_real_and_target_free(client):
    rows = list(csv.DictReader(io.StringIO(client.get("/api/sample.csv").data.decode("utf-8-sig"))))
    assert rows and "Churn" not in rows[0]
    assert "gender" not in rows[0] and "customerID" in rows[0]
    assert upload(client, rows).status_code == 200


def test_headers_errors_and_plot_allowlist(client):
    response = client.get("/api/summary")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert client.get("/plots/unknown.png").status_code == 404
    assert client.get("/plots/model.joblib").status_code == 404
    assert client.get("/docs/ASSUMPTIONS.md").status_code == 200
    assert client.get("/docs/../../pyproject.toml").status_code == 404
