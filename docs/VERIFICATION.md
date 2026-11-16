# Verification record

Date: 16 November 2026. Scope: this local Windows college demonstrator. Results below came from executed commands, actual source records and browser interactions.

## Final checks

| Check | Executed result |
|---|---|
| `uv sync --python 3.12` | Environment created and dependencies locked |
| `uv lock --check` | Passed |
| `uv run python scripts/train.py` | Training and artifact export completed |
| `uv run pytest -q` | **54 passed in 4.67 seconds** in the UI revision 3 run |
| `uv run ruff check .` | All checks passed |
| `node --check static/app.js` and `static/home.js` | Both exit 0 |
| `uv run python app.py --port 5050` | Waitress served app; health reported ready |
| `.\start.ps1 -Port 5051` | Launcher synced the locked environment and served a ready model |
| `uv run python scripts/browser_check.py` | 13 real workflow groups passed against native localhost; zero unexpected console errors |
| Independent review | Prior model/server review: [REVIEW.md](REVIEW.md); current UI review: [UI_V3_REVIEW.md](UI_V3_REVIEW.md) |
| Local Markdown links | No missing file targets |
| `uv run python scripts/reference_check.py` | V3 hierarchy, viewport fit, local Geist and sampled text/button contrast passed |
| Current V3 Linux image | Rebuild not verified: registry TLS timeout, then Docker engine unavailable; prior V2 image is historical |

The first implementation finished with 30 tests. The earlier website revision reached 52. Revision 3 adds the home/document UI contract, bringing the current run to 54. Earlier review counts reflect their own snapshots.

The test servers are stopped after verification. Start the app with `npm run dev` or `.\start.ps1` from the project directory; its default address is `http://127.0.0.1:5050`.

## Current container-build limit

The V3 rebuild was attempted. An initial build was interrupted so that its source snapshot could include the final history fix. The next build failed obtaining the public uv registry token with `net/http: TLS handshake timeout`. A retry could not connect to `dockerDesktopLinuxEngine` because the engine pipe was unavailable. No current V3 image or container result is claimed. The previous V2 image remains historical and must be rebuilt after Docker/network service is available. Native Windows verification completed independently.

## Model evidence

Original source SHA-256: `16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91`. Source: 7,043 customers, 1,869 churn labels. Eleven zero-tenure blank total-charge values were filled with zero under the documented rule; no rows dropped.

Partitions: 4,225 training / 1,409 validation / 1,409 test, with no identifier overlap. The validation-selected logistic model was not refitted. Threshold: `0.49934350911717607`.

Held-out ROC-AUC: `0.8324730682786947`; average precision: `0.6242117062478064`. Confusion matrix: `[[909,126],[179,195]]`. The 179 missed churn labels are a real limitation. Full metrics, bootstrap intervals, parameters, versions and timestamps are in `artifacts/summary.json` and [MODEL_CARD.md](MODEL_CARD.md).

Saved held-out IDs, labels and predictors match the original source. Probabilities reconcile with measured metrics. Fitted scaler means equal training-only means. SHAP background IDs belong to training; global-importance sample IDs belong to validation. Source-code hashes match the executed files. SHAP output/probability reconstruction passed on actual low/middle/high scoring rows. Corrupt artifacts fail integrity checks before deserialization.

## Browser and upload checks

The current UI revision passed 13 recorded workflow groups against native localhost with zero unexpected console errors. Direct entry and refresh work for home, overview, analysis, batch, model lab and guide. Browser history and old root hash links work. The four workspace views were checked at 1440, 1024, 768, 390 and 320 pixels; home/guide were checked at narrow phone widths. Source-derived cohort filters, delayed-response races, a deliberately failed chart request followed by resize, and non-overlapping phone axis labels have permanent browser checks. No dataset values or model responses were replaced with invented values.

New home checks reconcile cohort counts, the displayed probability and each preview SHAP factor with actual API results, verify clearing stale preview values while changing customers, follow a specific record into analysis, and exercise the native FAQ. Independent review found incorrect history restoration of customer IDs and an obsolete lookup error appearing under a newer customer. Both were fixed, and a permanent browser regression exercises them. Pending customer lookups clear the previous score. See [UI_V3_REVIEW.md](UI_V3_REVIEW.md).

Current reference work renders Attio, Vitally, ChurnZero and Planhat, then captures the actual local home and overview at 1440 by 1000 and 390 by 844. The local Geist font loaded and no page overflow was measured. Body text contrast was 13.60:1 on home and 13.37:1 on overview; white primary-button text on teal measured 4.91:1. These are computed samples, not a complete accessibility certification. Desktop and phone screenshots were visually inspected. The V3 [comparison board and captures](UI_MATCH.md) record intentional adaptation of related-product hierarchy. The old nine geometry checks belong only to [historical V2](UI_MATCH_V2.md).

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
