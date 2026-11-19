"""Check the hosted entrypoint and fail deployment when real scoring is unavailable."""

import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_hosted_build_prunes_only_dependency_tests(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Build cleanup must preserve runtime modules and never run on local developer packages."""
    from scripts.build import prune_dependency_tests

    tests = tmp_path / "numpy/tests"
    tests.mkdir(parents=True)
    (tests / "fixture.txt").write_text("dependency test fixture")
    runtime = tmp_path / "numpy/__init__.py"
    runtime.write_text("# runtime module")
    cache = tmp_path / "numpy/__pycache__"
    cache.mkdir()
    (cache / "cached.pyc").write_bytes(b"bytecode cache")
    monkeypatch.setattr("scripts.build.sysconfig.get_path", lambda name: str(tmp_path))
    monkeypatch.delenv("VERCEL", raising=False)
    prune_dependency_tests()
    assert tests.is_dir()
    monkeypatch.setenv("VERCEL", "1")
    prune_dependency_tests()
    assert not tests.exists()
    assert not cache.exists()
    assert runtime.is_file()


def test_build_checks_real_predictions_and_prepares_cdn_assets(tmp_path: Path) -> None:
    """The build must exercise the model, explanations and CSV scoring, not just copy files."""
    from scripts.build import build

    for name in ("artifacts", "static", "templates", "docs"):
        shutil.copytree(ROOT / name, tmp_path / name)
    report = build(tmp_path)
    assert report["model"] == "Logistic regression"
    assert report["predictions_checked"] == 10
    assert report["batch_rows_checked"] == 10
    for source in (tmp_path / "static").rglob("*"):
        if source.is_file():
            assert (tmp_path / "public/static" / source.relative_to(tmp_path / "static")).read_bytes() == source.read_bytes()


def test_build_rejects_missing_model_before_publishing_assets(tmp_path: Path) -> None:
    """A deployment must fail instead of publishing a site whose model returns 503."""
    from scripts.build import build

    with pytest.raises(RuntimeError, match="Model unavailable"):
        build(tmp_path)
    assert not (tmp_path / "public").exists()


def test_vercel_entrypoint_loads_frozen_model() -> None:
    """Use Vercel's exported WSGI instance without starting Waitress."""
    from wsgi import app

    client = app.test_client()
    assert client.get("/api/health").json["status"] == "ready"
    row = client.get("/api/customers?page_size=1").json["items"][0]
    result = client.post("/api/predict", json=row["features"])
    assert result.status_code == 200
    assert result.json["probability"] == pytest.approx(row["probability"], abs=1e-6)
    assert result.json["explanation"]["additivity_error"] < 1e-5
