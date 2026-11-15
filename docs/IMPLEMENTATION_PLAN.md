# Telecom Churn Implementation Plan

**Goal:** Build and verify a complete local explainable churn app.
**Architecture:** Shared Python schema/training/inference, Flask JSON routes and a static client.
**Stack:** Python, Flask, pandas, scikit-learn, XGBoost, SHAP, matplotlib, pytest, uv.
**Spec:** docs/DESIGN.md. User authorizes parallel execution without questions.

## Constraints and review focus
No fabricated data, metrics or plots. Docstrings/type hints. Preserve neighbours. Watch unknown categories, contradictory services, CSV formula injection/size limits, corrupt artifacts, explanation additivity and held-out isolation.

## Execution
1. Research datasets, repositories and UI references with inspected evidence.
2. Implement and test reproducible download/train/evaluate pipeline; save hashes, split IDs, model and run-generated results.
3. Implement inference/SHAP and verify output reconstruction; use held-out examples.
4. Implement Flask API tests for readiness, prediction, batch limits/errors and export safety.
5. Build responsive accessible dashboard against docs/API_CONTRACT.md, without hard-coded metrics.
6. Train, test, inspect browser workflows, independently review and fix supported findings.
7. Complete setup, methodology, viva and verification documents; hand over working app.

## Ownership
Parent: app.py, API tests, environment and integration. ML agent: src/churn/, scripts/train.py, scripts/download_data.py, tests/test_model.py. UI agent: templates/, static/, browser checks. Research agents: separate research docs.
