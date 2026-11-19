"""Check frozen ML artifacts and prepare CDN assets; never train during deployment."""

from __future__ import annotations

import csv
import io
import json
import math
import os
import shutil
import sys
import sysconfig
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
if os.environ.get("VERCEL") == "1":
    sys.dont_write_bytecode = True

from app import create_app


def prune_dependency_tests() -> None:
    """Remove scientific test fixtures and caches only in Vercel's disposable build environment."""
    if os.environ.get("VERCEL") != "1":
        return
    site_packages = Path(sysconfig.get_path("purelib")).resolve()
    for package in ("numpy", "pandas", "scipy", "sklearn"):
        candidates = [path for path in (site_packages / package).rglob("*")
                      if path.name in ("tests", "__pycache__") and path.is_dir()]
        for path in candidates:
            if path.is_dir() and path.resolve().is_relative_to(site_packages):
                shutil.rmtree(path)


def build(root: Path = ROOT) -> dict[str, Any]:
    """Fail on broken inference, pages or plots before copying static files to public/."""
    application = create_app(root)
    service = application.extensions.get("churn_service")
    if service is None:
        raise RuntimeError("Model unavailable. Include artifacts/model.joblib and its matching manifest/results.")
    client = application.test_client()
    for path in ("/", "/overview", "/analysis", "/batch", "/models", "/guide", "/api/summary", "/api/cohorts"):
        response = client.get(path)
        if response.status_code != 200:
            raise RuntimeError(f"Build check failed: {path} returned {response.status_code}.")
    checked = service.customers[:10]
    if len(checked) != 10:
        raise RuntimeError("Expected genuine held-out examples for the deployment smoke check.")
    for row in checked:
        response = client.post("/api/predict", json=row["features"])
        result = response.get_json()
        if response.status_code != 200 or not math.isclose(result["probability"], row["probability"], abs_tol=1e-6):
            raise RuntimeError("Hosted prediction does not match its saved held-out result.")
        if not math.isclose(result["explanation"]["reconstructed_probability"], result["probability"], abs_tol=1e-5):
            raise RuntimeError("SHAP explanation does not reconstruct the actual prediction.")
    sample = client.get("/api/sample.csv")
    response = client.post("/api/batch", data={"file": (io.BytesIO(sample.data), "sample.csv")})
    if response.status_code != 200:
        raise RuntimeError("CSV scoring failed the deployment smoke check.")
    scored = list(csv.DictReader(io.StringIO(response.data.decode("utf-8-sig"))))
    if len(scored) != len(checked) or any(
        not math.isclose(float(actual["churn_probability"]), expected["probability"], abs_tol=1e-6)
        for actual, expected in zip(scored, checked, strict=True)
    ):
        raise RuntimeError("CSV scores do not match the saved held-out predictions.")
    for chart in service.summary["charts"]:
        if client.get(chart["url"]).status_code != 200:
            raise RuntimeError(f"Missing evaluation plot: {chart['url']}")
    for name in ("styles.css", "app.js", "home.js", "favicon.svg", "fonts/Geist-Variable.woff2"):
        if not (root / "static" / name).is_file():
            raise RuntimeError(f"Missing website asset: {name}")
    shutil.copytree(root / "static", root / "public/static", dirs_exist_ok=True)
    report = {"model": service.summary["model"]["name"], "predictions_checked": len(checked),
              "batch_rows_checked": len(scored), "static_assets": "public/static"}
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    prune_dependency_tests()
    build()
