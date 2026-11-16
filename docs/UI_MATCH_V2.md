# Historical V2 reference comparison

This records the earlier monochrome UI. Revision 3 supersedes its exact geometry; the current `reference_check.py` checks and captures V3. These old measurements/captures remain historical evidence, not assertions about the redesigned website. See [UI_MATCH.md](UI_MATCH.md) for the current design.

Primary reference: [official shadcn/ui dashboard-01](https://ui.shadcn.com/view/new-york-v4/dashboard-01). The [additional research](UI_REFERENCE_RESEARCH_V2.md) compares 12 reference families and records why this one fits the analyst workflow. Screenshots are actual browser captures, not generated mockups.

## View the evidence

- [Side-by-side comparison board](../artifacts/references/comparison.html)
- [Official reference at 1440 × 1000](../artifacts/references/shadcn-dashboard-01.png)
- [Actual Retain website at the same viewport](../artifacts/references/retain-dashboard-v2.png)
- [Machine-readable measured comparison](../artifacts/references/match-results.json)
- [Source measurements](../artifacts/references/shadcn-measurements.json)

Run `uv run python scripts/reference_check.py` with the local server running to regenerate the implementation capture and checks. It reads the saved official reference measurements and asserts the layout tolerances plus actual Geist font loading.

## Measured match

| Element | Reference | Actual |
|---|---:|---:|
| Sidebar width | 288 px | 288 px |
| Workspace left / top | 288 / 8 px | 288 / 8 px |
| Header height | 48 px | 48 px |
| First card left / top | 312 / 80 px | 313 / 81 px |
| Card width / height | 262 / 204 px | 261.5 / 204 px |
| KPI font size | 30 px | 30 px |

All nine checked quantities are within one CSS pixel at this viewport. The one-pixel content offset comes from the implementation's explicit workspace border. These checks measure selected geometry, not a numerical pixel-similarity score for the whole screenshot.

The implementation uses the same light rail, inset white workspace, compact header, four summary cards, wide analytical panel, neutral palette, black primary control and compact bordered customer table. Geist is served locally with its original OFL license and [verified provenance](FONT_PROVENANCE.md).

## Intentional content differences

- Retain replaces the reference company/profile and unrelated admin documents. No fake user identity, visitors, notifications or improvement percentages are displayed.
- Summary values come from the actual IBM sample and saved model run. Chart controls filter real contract groups instead of invented date ranges.
- The reference's visitor timeline becomes observed churn and mean model probability across actual held-out tenure groups. Tenure is not a calendar date. Counts, null rates, tooltips and an accessible table make the chart inspectable.
- SHAP, model evidence, batch validation and data limitations remain available. Additional explanatory content can change lower-page heights; the page is not claimed to be a literal copy of unrelated demo content.
- Secondary text is slightly darker than the initial reference-inspired gray to remain readable over the pale card gradient. Executed contrast calculation: `#737373` on `#f0f0f0` was 4.1608:1; the chosen `#6b6b6b` is 4.6763:1. This spot check is not a complete accessibility audit.

## Website behavior

Home, overview, analysis, batch, model lab and guide use real URLs and direct refresh works. Existing root hash links redirect to the appropriate workspace. The desktop rail collapses; the mobile drawer manages inert content, focus trapping, Escape and backdrop closing. Phone chart labels become sparser to avoid overlap. All values and predictions continue to use the same backend and fitted model.

See [VERIFICATION.md](VERIFICATION.md) and [WEBSITE_REVIEW.md](WEBSITE_REVIEW.md) for executed tests and limits. No cloud publication or production accessibility/load certification is implied.

The recorded browser results are retained for both [native localhost](../artifacts/references/native-browser-results.json) and the [Linux website container](../artifacts/references/container-browser-results.json).
