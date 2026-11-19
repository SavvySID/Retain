# Verification record

Date: 16 November 2026. Scope: this local Windows college demonstrator. Results below came from executed commands, actual source records and browser interactions.

## Latest checklist audit: 18 November 2026

The [eight-point college status](PROJECT_STATUS.md) maps every requested stage to code and evidence. The missing standalone EDA was added and executed with `uv run python scripts/eda.py`, exporting `docs/EDA_REPORT.md`, `artifacts/eda/summary.json` and four measured PNG figures. This is descriptive follow-up after model freezing: source quality uses the full canonical CSV; distributions and feature/target relationships use only the saved training partition. No model source, selected threshold or trained artifact was changed.

Executed during this audit:

- Full Python suite: **56 passed in 4.78 seconds**, including two EDA checks for training membership, held-out-label isolation and invalid training IDs.
- Ruff: all checks passed. Both application/home JavaScript syntax checks exited 0.
- Native Chromium: all **13** workflow groups passed with zero unexpected console errors, including all six routes, actual predictions/SHAP, CSV scoring and responsive layouts.
- Both new reports are linked from Guide and their HTTP document URLs return 200. Local Markdown/image links resolve.
- The EDA script/split hashes match its recorded provenance. All saved model artifact hashes still match the existing manifest. Four new figures were opened and visually inspected.
- Docker engine check failed because the installed Linux engine pipe was unavailable. No current container or public deployment is claimed.

The initial EDA CLI exposed a local script-import path error; the entry point was corrected and the export then completed successfully. The temporary native test server was started only for this audit and stopped afterward. Earlier verification entries below describe their own dated snapshots, including the original 54-test UI run. Current stage and unresolved deployment work are explicit in [PROJECT_STATUS.md](PROJECT_STATUS.md).

## Earlier model and UI checks

| Check | Executed result |
|---|---|
| `uv sync --python 3.12` | Environment created and dependencies locked |
| `uv lock --check` | Passed |
| `uv run python scripts/train.py` | Training and artifact export completed |
| `uv run pytest -q` | **54 passed in 4.46 seconds** in the UI revision 3 run |
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

Current reference work renders Attio, Vitally, ChurnZero and Planhat, then captures the actual local home and overview at 1440 by 1000 and 390 by 844. The local Geist font loaded and no page overflow was measured. After the requested black-accent follow-up, body text contrast measured 16.88:1 on home and 16.59:1 on overview; white primary-button text on black measured 17.93:1. These are computed samples, not a complete accessibility certification. Desktop and phone screenshots were visually inspected. The V3 [comparison board and captures](UI_MATCH.md) record intentional adaptation of related-product hierarchy. The old nine geometry checks belong only to [historical V2](UI_MATCH_V2.md).

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


## Black accent follow-up

The user requested black instead of teal. The existing layout now uses black, white and neutral grays throughout UI surfaces, navigation, controls, dynamic charts, factor bars and favicon. Observed/model chart series retain solid/dashed strokes; signed factor labels retain their meaning. Model artifacts and evaluation plots were not regenerated for this styling change.

The actual follow-up run passed 54 tests in 4.46 seconds, Ruff, both JavaScript syntax checks and all 13 native Chromium workflow groups with zero unexpected console errors. The finish checks assert the black primary button and neutral body text, verify contrast, font loading and viewport fit, and refresh the current desktop/mobile screenshots. A source scan found only neutral colors in the four edited UI assets. The independent V3 review above predates this color-only follow-up; its original palette/contrast observations describe that earlier snapshot. No Docker rebuild, hosting or full accessibility audit was repeated. The user's localhost server remains running after their explicit `npm run dev` request.

## Vercel preparation — 19 November 2026

The previous paragraph's running-server state is historical; the user subsequently stopped it. This revision adds Vercel packaging without changing training, model artifacts, metrics, plots or UI design.

- `npm run build` passed: genuine prediction/SHAP parity checks, ten-row CSV scoring, refreshable pages, evaluation plots and generated CDN assets. The missing-model build regression fails explicitly rather than publishing a broken scoring service.
- `uv run pytest -q`: **60 passed** in the final run; Ruff, both JavaScript syntax checks and `git diff --check` passed.
- A clean Linux Python 3.12.16 environment installed the locked runtime with `uv sync --frozen --no-dev`. The real model and SHAP/CSV checks passed without XGBoost, matplotlib or development tools. Before deployment-only pruning, this environment measured approximately 237.89 MiB; that is an installed environment measurement, not a Vercel function size.
- The official `@vercel/python` **33.0.0** builder and `@vercel/build-utils` **15.5.0** ran locally inside Linux, using the Flask preset, `wsgi:app`, the checked-in configuration and the actual build command. This directly exercised the builder API; it was not a Vercel cloud deployment or authenticated CLI build.
- The initial builder attempt exposed a stricter internal **225 MiB** packaging threshold than the current documentation's 500 MB Python allowance. Removing scientific dependency tests and bytecode caches in the disposable build environment resolved it. The successful generated Python 3.12 function contained **4,243 files / 216,180,445 bytes (206.17 MiB)**. No large-functions flag or runtime dependency downloads were required. The builder's route/function record is [vercel-builder-check.json](../artifacts/vercel-builder-check.json). This size describes the measured build snapshot; later documentation/evidence files can add a small amount.
- The materialized function was loaded using the base Python interpreter with `-S` (ordinary site-packages disabled), with only the function root and its `_vendor` on the import path. **All 1,409** genuine held-out rows predicted successfully and returned reconstructing SHAP explanations. Maximum absolute probability difference from the saved results was **2.220446049250313e-16**. A **1,000-row** genuine CSV batch conserved IDs and matched the saved scores. Pages, cohort/summary APIs, plots, documentation and invalid-input errors also passed.
- The same bundle passed again in a container with a **read-only root filesystem and read-only function mount**, using only bounded `/tmp` storage. The exported application loaded without writes to its source/model directories. Its observed 1,000-row batch took **3.810868518999996 seconds**. Evidence: [vercel-runtime-check.json](../artifacts/vercel-runtime-check.json).
- Cold import was **3.5143216829999346 seconds** with function files on the Linux filesystem, and **53.91833129700001 seconds** when all function files were read through a Windows bind mount. These are local filesystem-specific observations, not Vercel cold-start measurements or promises. Actual hosted cold starts still need checking.
- The read-only bundle was served temporarily on loopback port 5063 with middleware emulating CDN delivery of the build-generated `public/static/` directory. The complete Chromium browser script passed **all 13 workflow groups with zero unexpected console errors**, including actual prediction/explanation, sample download and CSV scoring, plots, direct-route refresh, history, error recovery and mobile/keyboard checks. This tests the generated code/assets, not Vercel's live CDN/control plane. Evidence: [vercel-browser-check.json](../artifacts/vercel-browser-check.json).

During verification, an early browser connection was attempted before the temporary smoke-test process finished and before its HTTP listener started; the connection failed. The full browser check was rerun after `/api/health` returned ready and then passed. Temporary test containers/listeners were stopped after verification.

The anonymous-demo production review covered artifact provenance/integrity, deployment file exclusions, bounded in-memory uploads, API validation, existing browser security headers, same-origin routes and read-only inference. No private dataset or credentials are required. This is not authentication for real customer records, a multi-user load test, or an exhaustive dependency vulnerability audit.

**Remaining:** the user must publish the current project to Vercel and verify the resulting live `/api/health`, prediction/explanation, sample upload and plots. No cloud deployment, Vercel account settings, live TLS/CDN behavior or public load test is claimed here. See [DEPLOYMENT.md](DEPLOYMENT.md) for the exact import settings.
