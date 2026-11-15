# Verification record

Date: 16 November 2026. Scope: this local Windows college demonstrator. Results below came from executed commands, actual source records and browser interactions.

## Final checks

| Check | Executed result |
|---|---|
| `uv sync --python 3.12` | Environment created and dependencies locked |
| `uv lock --check` | Passed |
| `uv run python scripts/train.py` | Training and artifact export completed |
| `uv run pytest -q` | **30 passed in 12.44 seconds** in final combined Python run |
| `uv run ruff check .` | All checks passed |
| `node --check static/app.js` | Exit 0 |
| `uv run python app.py --port 5050` | Waitress served app; health reported ready |
| `.\start.ps1 -Port 5051` | Launcher synced the locked environment and served a ready model |
| `uv run python scripts/browser_check.py` | Workflow results saved in `artifacts/browser/results.json` |
| Independent review | Four findings corrected/rechecked; see [REVIEW.md](REVIEW.md) |
| Local Markdown links | No missing file targets |

The review's earlier test count reflects its own snapshot. Two later regression/evidence tests increased the final count to 30.

The test servers are stopped after verification. Start the app with `.\start.ps1` from the project directory; its default address is `http://127.0.0.1:5050`.

## Model evidence

Original source SHA-256: `16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91`. Source: 7,043 customers, 1,869 churn labels. Eleven zero-tenure blank total-charge values were filled with zero under the documented rule; no rows dropped.

Partitions: 4,225 training / 1,409 validation / 1,409 test, with no identifier overlap. The validation-selected logistic model was not refitted. Threshold: `0.49934350911717607`.

Held-out ROC-AUC: `0.8324730682786947`; average precision: `0.6242117062478064`. Confusion matrix: `[[909,126],[179,195]]`. The 179 missed churn labels are a real limitation. Full metrics, bootstrap intervals, parameters, versions and timestamps are in `artifacts/summary.json` and [MODEL_CARD.md](MODEL_CARD.md).

Saved held-out IDs, labels and predictors match the original source. Probabilities reconcile with measured metrics. Fitted scaler means equal training-only means. SHAP background IDs belong to training; global-importance sample IDs belong to validation. Source-code hashes match the executed files. SHAP output/probability reconstruction passed on actual low/middle/high scoring rows. Corrupt artifacts fail integrity checks before deserialization.

## Browser and upload checks

Real Chromium checks exercised overview statistics, customer search, empty results, contract/risk filters, pagination, real-row inspection, all SHAP factors, edited scenarios, service consistency, sample CSV download, scoring/download and invalid-upload feedback.

Delayed genuine responses checked that edits cannot be overwritten by older results and that switching customers clears the previous score while computing. Model comparison, confusion counts, generated plot images and documentation links loaded successfully.

All four views were checked at widths 1440, 1024, 768, 390 and 320 pixels without whole-page horizontal overflow; tables retain internal scrolling. Keyboard skip-link/focus checks passed. Browser results contain no unexpected console errors. Desktop overview, desktop analysis and mobile overview screenshots were visually inspected.

An independent 1,000-row batch of genuine held-out records completed through the multipart API in 13.758 seconds on this host. Row counts/IDs were conserved and every score matched saved predictions within `1e-10`. This is one execution check, not a load benchmark or latency promise.

Tests cover invalid/missing/unknown fields, non-finite/oversized numbers, contradictory services, malformed CSV/encoding, duplicate columns, upload/row limits, whole-file validation, spreadsheet-formula escaping, missing/corrupt artifacts, partition isolation, train-only preprocessing, prediction parity and explanation additivity. Uploads use bounded memory streams, without saving customer history.

## Failures found and repaired

- Raw-host retrieval was unreliable here. The official GitHub Contents API fallback preserved pinned original bytes.
- Initial strict JSON export rejected XGBoost's NaN missing-value parameter. Metadata now records its sentinel explicitly; no source data or model score was substituted.
- Numeric overflow, documentation links and stale-result transitions were corrected with regression checks. The server was restarted after schema/template changes.

## Limits

No external/temporal validation, causal intervention study, fairness certification, production hosting, multi-user load test, full assistive-technology audit, competing-repository benchmark or exhaustive dependency legal audit was performed. Non-selected models' SHAP paths were inspected but not forced into service during independent review. These sample results do not establish future telecom performance.
