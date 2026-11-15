"""Serve a local explainable telecom churn dashboard and validated JSON API."""
from __future__ import annotations

import argparse
import csv
import io
import logging
from pathlib import Path
from typing import BinaryIO

from flask import Flask, Request, Response, jsonify, render_template, request, send_file
from waitress import serve
from werkzeug.exceptions import BadRequest, HTTPException, NotFound, RequestEntityTooLarge, ServiceUnavailable

from churn.inference import ChurnService
from churn.schema import FIELDS, validate_customer

ROOT = Path(__file__).resolve().parent
MAX_UPLOAD = 2 * 1024 * 1024
MAX_ROWS = 1000


class MemoryUploadRequest(Request):
    """Keep bounded uploads in RAM instead of temporary files."""

    def _get_file_stream(self, total_content_length: int | None, content_type: str | None,
                         filename: str | None = None, content_length: int | None = None) -> BinaryIO:
        return io.BytesIO()


def safe_csv_text(value: str) -> str:
    """Prevent user identifiers becoming executable spreadsheet formulas."""
    if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")):
        return "'" + value
    return value


def csv_download(rows: list[dict], fields: list[str], filename: str) -> Response:
    """Return UTF-8 CSV without persisting user data."""
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return send_file(io.BytesIO(stream.getvalue().encode("utf-8-sig")), mimetype="text/csv",
                     as_attachment=True, download_name=filename)


def create_app(project_root: Path | None = None) -> Flask:
    """Create the app; missing/corrupt artifacts yield explicit 503s, never fake scores."""
    root = project_root or ROOT
    application = Flask(__name__, template_folder=str(ROOT / "templates"), static_folder=str(ROOT / "static"))
    application.request_class = MemoryUploadRequest
    application.config.update(MAX_CONTENT_LENGTH=MAX_UPLOAD + 65536,
                              MAX_FORM_MEMORY_SIZE=MAX_UPLOAD + 65536, MAX_FORM_PARTS=4)
    application.json.sort_keys = False
    try:
        application.extensions["churn_service"] = ChurnService(root)
    except Exception:
        logging.getLogger(__name__).exception("Model unavailable; run uv run python scripts/train.py")
        application.extensions["churn_service"] = None

    def service() -> ChurnService:
        """Require local trained artifacts for data/scoring routes."""
        model = application.extensions["churn_service"]
        if model is None:
            raise ServiceUnavailable("Model unavailable. Run uv run python scripts/train.py, then restart.")
        return model

    @application.after_request
    def security_headers(response: Response) -> Response:
        """Restrict assets to this host and avoid caching customer responses."""
        response.headers.update({
            "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; "
            "base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
        })
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @application.errorhandler(HTTPException)
    def http_error(error: HTTPException) -> tuple[Response, int]:
        """Return intentional HTTP errors as actionable JSON."""
        return jsonify(error=error.description), error.code or 500

    @application.errorhandler(ValueError)
    def validation_error(error: ValueError) -> tuple[Response, int]:
        """Expose intentional schema validation errors."""
        return jsonify(error=str(error)), 400

    @application.errorhandler(Exception)
    def unexpected_error(error: Exception) -> tuple[Response, int]:
        """Log faults locally without leaking traces into the browser."""
        application.logger.exception("Request failed", exc_info=error)
        return jsonify(error="Request failed. Check the local server log; no result was produced."), 500

    @application.get("/")
    def index() -> str:
        """Serve the dashboard shell."""
        return render_template("index.html")

    @application.get("/api/health")
    def health() -> Response | tuple[Response, int]:
        """Report model readiness rather than merely process liveness."""
        if application.extensions["churn_service"] is None:
            return jsonify(status="unavailable", error="Run uv run python scripts/train.py, then restart."), 503
        return jsonify(status="ready", model=service().summary["model"]["name"])

    @application.get("/api/schema")
    def schema() -> Response:
        """Expose the fields shared with training and inference."""
        return jsonify(fields=FIELDS, excluded_features=["customerID", "Churn", "gender", "SeniorCitizen"])

    @application.get("/api/summary")
    def summary() -> Response:
        """Return recorded metrics and source-derived statistics."""
        return jsonify(service().summary)

    @application.get("/api/customers")
    def customers() -> Response:
        """Filter/page the complete test cohort without cherry-picking predictions."""
        try:
            page, size = int(request.args.get("page", "1")), int(request.args.get("page_size", "10"))
        except ValueError as error:
            raise BadRequest("page and page_size must be integers.") from error
        if page < 1 or not 1 <= size <= 100:
            raise BadRequest("page must be positive; page_size must be between 1 and 100.")
        risk, contract = request.args.get("risk", ""), request.args.get("contract", "")
        contracts = next(field["options"] for field in FIELDS if field["name"] == "Contract")
        if risk not in ("", "High", "Low") or contract not in ["", *contracts]:
            raise BadRequest("Unknown risk or contract filter.")
        search = request.args.get("search", "").strip().lower()
        rows = [row for row in service().customers if search in row["customer_id"].lower()
                and (not risk or row["risk_level"] == risk)
                and (not contract or row["features"]["Contract"] == contract)]
        start = (page - 1) * size
        return jsonify(items=rows[start:start + size], total=len(rows), page=page, page_size=size)

    @application.get("/api/customers/<customer_id>")
    def customer(customer_id: str) -> Response:
        """Retrieve a genuine held-out row by source identifier."""
        row = next((row for row in service().customers if row["customer_id"] == customer_id), None)
        if row is None:
            raise NotFound("Customer is not in the held-out test set.")
        return jsonify(row)

    @application.post("/api/predict")
    def predict() -> Response:
        """Compute a validated probability and real SHAP explanation."""
        model = service()
        if not request.is_json:
            raise BadRequest("Send predictor fields as application/json.")
        record = request.get_json()
        if not isinstance(record, dict):
            raise BadRequest("Expected a JSON object of predictor fields.")
        return jsonify(model.predict(record))

    @application.post("/api/batch")
    def batch() -> Response:
        """Validate the whole CSV before scoring; keep uploads only in memory."""
        model = service()
        uploaded = request.files.get("file")
        if uploaded is None:
            raise BadRequest("Choose a UTF-8 CSV file in the file field.")
        raw = uploaded.stream.read(MAX_UPLOAD + 1)
        if len(raw) > MAX_UPLOAD:
            raise RequestEntityTooLarge("CSV exceeds the 2 MiB upload limit.")
        try:
            reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
            fields = reader.fieldnames or []
            expected = {field["name"] for field in FIELDS}
            if len(fields) != len(set(fields)):
                raise BadRequest("CSV contains duplicate column headers.")
            missing, unknown = expected - set(fields), set(fields) - expected - {"customerID"}
            if missing or unknown:
                raise BadRequest(f"CSV columns do not match. Missing: {sorted(missing)}; unknown: {sorted(unknown)}.")
            records: list[tuple[str, dict]] = []
            for line, row in enumerate(reader, start=2):
                if None in row or any(value is None for value in row.values()):
                    raise BadRequest(f"CSV row {line}: inconsistent column count.")
                if len(records) >= MAX_ROWS:
                    raise BadRequest("CSV exceeds the 1000 customer limit.")
                identifier = row.pop("customerID", "")
                if len(identifier) > 100:
                    raise BadRequest(f"CSV row {line}: customerID exceeds 100 characters.")
                try:
                    records.append((identifier, validate_customer(row)))
                except ValueError as error:
                    raise BadRequest(f"CSV row {line}: {error}") from error
        except (UnicodeDecodeError, csv.Error) as error:
            raise BadRequest("CSV must be valid UTF-8 with comma-separated columns.") from error
        if not records:
            raise BadRequest("CSV contains no customer rows.")
        output = []
        for identifier, record in records:
            result = model.predict(record, explain=False)
            output.append({"customerID": safe_csv_text(identifier), "churn_probability": result["probability"],
                           "predicted_churn": "Yes" if result["prediction"] else "No",
                           "risk_level": result["risk_level"]})
        return csv_download(output, list(output[0]), "churn-predictions.csv")

    @application.get("/api/sample.csv")
    def sample_csv() -> Response:
        """Offer real test-set rows without labels or excluded demographics."""
        rows = [{"customerID": row["customer_id"], **row["features"]} for row in service().customers[:10]]
        return csv_download(rows, ["customerID", *[field["name"] for field in FIELDS]], "held-out-sample.csv")

    @application.get("/plots/<filename>")
    def plot(filename: str) -> Response:
        """Serve only PNGs recorded in the successful training run."""
        allowed = {Path(chart["url"]).name for chart in service().summary["charts"]}
        if filename not in allowed or Path(filename).suffix != ".png":
            raise NotFound("Unknown training plot.")
        return send_file(root / "artifacts" / "plots" / filename)

    @application.get("/docs/<filename>")
    def documentation(filename: str) -> Response:
        """Serve project Markdown as plain text, never arbitrary local files."""
        path = root / "docs" / filename
        if Path(filename).name != filename or path.suffix != ".md" or not path.is_file():
            raise NotFound("Unknown documentation file.")
        return send_file(path, mimetype="text/plain; charset=utf-8")

    return application


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5050)
    args = parser.parse_args()
    print(f"Telecom churn dashboard: http://{args.host}:{args.port}", flush=True)
    serve(create_app(), host=args.host, port=args.port, threads=4)
