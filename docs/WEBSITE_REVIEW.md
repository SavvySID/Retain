# Independent website and deployment review

Reviewed on 16 November 2026. Scope: the expanded localhost website, refreshable routes, held-out tenure-cohort chart, browser navigation, responsive shell and future-deployment packaging. The underlying ML source and experiment were unchanged by this revision.

## Findings and resolutions

1. **Failed cohort requests could revive an older filter's chart.** `loadCohort()` changed the selected contract while retaining the previous `state.cohortData` and accessible table. A resize callback could then redraw that old population after a failed request. The request now invalidates previous chart data and clears the graph/table into a loading state. Chromium verification loaded genuine cohort data, forced the next request to HTTP 503, then resized the viewport: no previous SVG reappeared and the accessible table remained empty with an explicit unavailable message.

2. **Legacy root hash URLs initially opened the new home page.** The old application's `/#analysis` style URLs reached `home.html`, while only the workspace script translated old hashes. Known legacy hash destinations now redirect to the corresponding refreshable path. Chromium verified `/#analysis` resolves to `/analysis` and displays customer analysis rather than the product home. The redirect is restricted to known workspace destinations.

No unresolved material findings remain from this review for the documented local single-analyst scope.

## Checks actually executed

- `uv run pytest -q`: **52 passed in 5.38 seconds** at the reviewed snapshot.
- `uv run ruff check .`: **All checks passed**.
- `node --check static/app.js` and `node --check static/home.js`: **exit 0**.
- Targeted website/deployment tests: **22 passed in 3.03 seconds**. These cover all six page routes, direct refresh, canonical cohort counts/rates, invalid contract filters, HOST/PORT validation, startup refusal without a model and Waitress request settings.
- Real Chromium navigation: `/overview` to `/analysis`, followed by browser Back, restores the overview URL and view.
- Real Chromium mobile checks at **390 by 844**: home, guide, overview, analysis, batch and model lab had no whole-page horizontal overflow. Table-local scrolling remains intentional.
- Mobile drawer checks: a closed off-canvas sidebar is inert; opening makes background content inert; focus remains in the drawer; Escape closes it and returns focus to the toggle. Selecting analysis closes the drawer and displays `/analysis`. No JavaScript page errors occurred in this sequence.
- A delayed genuine monthly-cohort response could not overwrite a newer Two-year selection. The selected chart and accessible-table counts reconciled with the API's **339** actual Two-year held-out customers.
- The cohort failure/resize regression and legacy root-hash behavior were independently exercised as described above. Fault injection changed only response availability, not dataset values or model metrics.

## Data honesty and reference fidelity

The cohort API aggregates saved held-out rows, using their observed churn labels and recorded model scores. Tenure buckets are labelled as months of customer tenure, not calendar dates. Empty buckets return null rates and split plotted paths rather than being drawn as zero. The API's bin counts and rates reconcile with their source rows for every supported contract filter.

I compared the rendered local overview with the captured official shadcn dashboard reference at the same desktop width. The neutral sidebar, white inset workspace, compact header, four-card hierarchy, chart panel and table follow the selected reference. Independent browser measurements confirmed a **288 px** sidebar and **48 px** header. The licensed self-hosted Geist font loaded successfully. Retain's real cohort labels, risk data and research limits replace the reference's unrelated sample content. No numerical pixel-similarity score is claimed.

The independently captured overview is [review-overview-desktop.png](../artifacts/browser/review-overview-desktop.png). The selected reference and its measurements are documented in [UI_REFERENCE_RESEARCH_V2.md](UI_REFERENCE_RESEARCH_V2.md). The owner's final full workflow and screenshot checks are recorded separately in [VERIFICATION.md](VERIFICATION.md).

## Deployment inspection

Reviewed `serve.py`, `Dockerfile`, `.dockerignore`, the application factory and deployment tests. Local serving defaults to loopback; explicit HOST/PORT values are validated before binding. Deployment startup refuses unavailable artifacts. Waitress and Flask bound request bodies, and permitted uploads use in-memory buffers. The container build excludes the host virtual environment, host data provenance and generated model artifacts, then downloads and trains inside Linux using the dependency lock. The runtime declares a non-root user and readiness health check. The documented Docker port mapping binds the host side to loopback.

The deployment owner executed the Linux build/run and recorded its evidence in [DEPLOYMENT.md](DEPLOYMENT.md). This reviewer inspected that packaging and ran its configuration tests; I did not independently rebuild images or restart any owned server or container. A release image must be rebuilt after final source edits.

## Verdict and limits

**Ship for the documented localhost college-demo scope.** This review does not establish production load capacity, public access control, TLS configuration, external-data model performance or a complete accessibility certification. No cloud publication was performed. The final combined verification record remains authoritative for the delivered source snapshot.
