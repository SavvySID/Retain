# Independent implementation review

Reviewed on 16 November 2026 for one local analyst running a college demonstrator. This is a source and execution review of this implementation, not a certification of production suitability.

## What this change does

The project trains classifiers against the original IBM fictional-company sample, selects a model and threshold using validation data, and serves individual and batch predictions. The dashboard exposes real evaluation evidence and signed SHAP contributions instead of invented performance or business-impact claims.

## Findings and corrections

1. **Oversized JSON integers caused a server error** (`src/churn/schema.py`, numeric conversion). A JSON integer such as `10**1000` was small enough for the request limit but raised `OverflowError` during float conversion. This was reproduced through the API as HTTP 500. The numeric validator now catches that error and returns the normal validation failure; schema/API regression tests pass.
2. **An in-flight prediction could overwrite an edited scenario** (`static/app.js`, `markScenario`, `openCustomer`, `predict`). An old response was originally rendered without checking which form revision it belonged to. The implementation now uses form revisions and prediction request IDs. A real Chromium test delayed a genuine prediction response, edited tenure, released the response and verified that the old score was discarded. A fresh request then rendered the new scenario score.
3. **Documentation links returned 404** (`templates/index.html`). The UI linked to `/docs/`, while the server exposed individual Markdown files. Links now target `/docs/PROJECT_REPORT.md`.
4. **Previously rendered scores remained visible while switching customers** (`static/app.js`, `openCustomer`/`predict`). Chromium reproduced the old customer's 82.8% score remaining visible under a different selected customer while that customer's request was delayed. A computing placeholder now replaces the old result immediately when prediction starts. The delayed-response regression passed after this change.

## Independently executed checks

- `uv run pytest -q`: **28 passed in 9.38 seconds** at this review snapshot.
- `uv run ruff check .`: **All checks passed**.
- `node --check static/app.js`: **exit 0**.
- All **1,409** saved test-customer identifiers, observed labels and predictor values match the original source records exactly.
- The fitted numeric scaler's means equal the training partition means. SHAP background identifiers belong only to training; the global-importance sample belongs only to validation.
- Every recorded ML source hash matched the current code at the time of checking. The source dataset and model artifacts passed their integrity checks.
- Saved test ROC-AUC and average precision reconcile with held-out labels and probabilities. The selected logistic regression has ROC-AUC **0.8324730682786947** and average precision **0.6242117062478064** for this run. These are benchmark results, not a prospective production guarantee.
- A maximum-size row-count batch of **1,000 actual held-out records** completed through the Flask multipart API in **13.758 seconds** on this host. The downloaded file contained exactly 1,000 rows, conserved all identifiers and matched every saved probability within `1e-10`.
- Reviewed JSON/CSV required fields, category and service-combination validation, upload bounds, all-or-nothing CSV validation, spreadsheet-formula escaping, memory-only upload streams, missing-artifact readiness, plot/document route allowlists and local-only asset policy.
- Inspected train/validation/test separation, train-only preprocessing, validation average-precision model selection, validation F1 threshold selection, no post-selection refit, measured plots, baseline comparison, SHAP grouping and additivity.

## Final recheck

Chromium rechecked the transition from genuine customer `0295-PPHDO` to `9300-AGZNL` with the second genuine API response deliberately delayed. No old score was present while waiting; the computing placeholder appeared, then the new result rendered on completion. The earlier form-edit response-discard regression also passed.

**Verdict: Ship for the documented local college-demo scope.** No unresolved material findings remain from this review. The final combined verification record is [VERIFICATION.md](VERIFICATION.md).

## Limits

The review did not train on external or future-period telecom data, establish causal retention effects, execute competing GitHub projects, prove fairness, or test production hosting/multi-user load. The selected model's actual SHAP path was exercised; explanation paths for non-selected models were inspected but were not independently forced into service. Full visual/accessibility browser checks are tracked separately in the combined verification record.
