# Independent UI review, revision 3

Reviewed on 16 November 2026 against the running native localhost website and current source. Scope: the stronger home/hero, actual-data product demonstration, customer deep links, asynchronous states, FAQ/links, responsive layouts and consistency with the workspace/guide. The earlier V2 shadcn geometry is a historical target, not a requirement for this revision.

## Findings and corrections

1. **History could restore the wrong customer.** Opening customer A through `/analysis?customer=A`, navigating to overview, inspecting B, then going Back twice restored A's URL while retaining B's profile and score. The route now reconciles its customer query with the selected record, and selected records receive matching URLs. Chromium rechecked the original sequence using actual customers `9300-AGZNL` and `0295-PPHDO`: returning to A's URL loaded A. Editing a manual scenario also removed the source-record query.

2. **An obsolete customer lookup could display its error under a newer customer.** The lookup's successful response had a revision guard, but its failure handler did not. A delayed failed lookup for A displayed an error after B had successfully loaded. Success and failure now check request ownership, form revision and route. Chromium repeated the fault: B's valid result stayed visible and A's obsolete error remained hidden. The manual held-out loader remained functional after this sequence.

The current implementation also clears the prior score into an explicit pending state while loading a customer. The owner's permanent browser suite covers these corrected transitions. No unresolved material findings remain from this review for the documented local college-demo scope.

## Independently executed checks

- `uv run pytest -q`: **54 passed in 3.41 seconds** at the review snapshot.
- `uv run ruff check .`: **All checks passed**.
- JavaScript syntax checks for both application and home scripts: **exit 0**.
- Home metrics reconciled with the actual summary API. Two actual preview customers were independently retrieved and scored through `POST /api/predict`; their displayed probabilities matched those responses.
- The five displayed SHAP factors matched the five largest absolute API contributions, including feature names, numeric values and positive/negative direction. The reconstruction used the sum of **all** contributions, rather than only those five. Baseline plus the full sum matched the explained model output within `1e-5`; explicit log-odds units were retained.
- Following the preview's complete-analysis link opened the same actual customer and probability in the workspace.
- The home Two-year contract filter matched the API's **339** held-out customers. Accessible cohort-table labels, counts and displayed rates matched the returned bins; unavailable rates remained unavailable rather than becoming zero.
- A deliberately delayed genuine next-customer prediction cleared the previous score and factors while pending. A subsequent deliberate HTTP 503 produced an unavailable state without retaining the preceding result. Removing the fault and advancing again restored a genuine explanation. These faults changed availability only, not dataset values or model metrics.
- All six routes fit **320, 390, 768, 1024 and 1440 px** widths without whole-page horizontal overflow in Chromium. Internal table scrolling remains intentional.
- The native FAQ opened correctly. Every same-origin home/guide link returned HTTP 200, covering **12** distinct paths; linked section anchors existed in the target documents.
- Rechecked the two history/obsolete-lookup reproductions after their fixes, including manual-scenario URL cleanup.

## Visual and evidence review

The rendered desktop and mobile home captures were visually inspected. The current page has an emphatic hero, a substantial working product demonstration, a source-backed proof section, explanatory feature/workflow sections, a native FAQ and direct workspace actions. Warm paper, navy text, teal actions and the existing Geist font give the home, workspace and guide a consistent direction. These are Retain's own content and actual data, not reference-site customer claims or copied product screenshots.

The local primary-reference evidence and design decisions are in [UI_RESEARCH_V3.md](UI_RESEARCH_V3.md). The current [UI_MATCH.md](UI_MATCH.md) correctly treats V2 as historical. The owner's executed finish-check record reports sampled home/body contrast of **13.60:1** and primary-button contrast of **4.91:1**, with the local font loaded. I inspected that record and its actual screenshots; those samples are not a complete accessibility certification or a numerical visual-similarity score.

No ML/API source changed in this revision. The review did not retune models, substitute customer records, invent chart series, promise retention uplift or reuse third-party business metrics. The broader permanent browser result records **13** workflow groups and zero unexpected console errors; see [VERIFICATION.md](VERIFICATION.md) for the combined delivered snapshot.

## Verdict and limits

**Ship for the documented native localhost college-demo scope.** The two supported findings were repaired and rechecked. I did not restart the owning server, build/restart Docker, publish the site, certify assistive-technology coverage or test public multi-user load. Current container-build status and its network/engine limitations belong in [DEPLOYMENT.md](DEPLOYMENT.md); this UI verdict does not imply a newly verified container image.
