# Current UI direction and rendered evidence

Revision 3 responds to the request for a stronger product home/hero and fixes across the entire UI. It supersedes the earlier neutral-dashboard geometry. The [V2 record](UI_MATCH_V2.md) is historical; its nine geometry checks are not a claim about this redesign.

## References and decisions

[Related-product research](UI_RESEARCH_V3.md) records desktop/mobile captures of Attio, Vitally, ChurnZero and Planhat, including five rendered public pages. Attio informs the editorial hero and substantial product preview. Vitally reporting informs account-health and investigation flows. These patterns are adapted to Retain's own black accent with white and neutral-gray surfaces (the user's later explicit preference), existing Geist font and local research workflow.

No reference branding, screenshots, customer identities, commercial claims or invented metrics are website content. The home preview uses actual held-out customer, score, cohort values and signed explanation factors. SHAP remains an association-based explanation rather than a causal claim.

## Current captures and checks

Run `uv run python scripts/reference_check.py` with the app running. It captures home/overview at desktop/mobile sizes, checks core text/button contrast and viewport fit, verifies the local font, and creates a comparison board. It does not invent a screenshot-similarity score.

- [Reference/current comparison board](../artifacts/references/v3/comparison.html)
- [Actual home at desktop size](../artifacts/references/v3/retain-home-desktop.png)
- [Actual home, full page](../artifacts/references/v3/retain-home-full.png)
- [Actual home on mobile](../artifacts/references/v3/retain-home-mobile.png)
- [Actual overview](../artifacts/references/v3/retain-overview-desktop.png)
- [Measurements and contrast calculations](../artifacts/references/v3/finish-results.json)

The complete workflow checks remain in `scripts/browser_check.py`: real navigation, predictions, CSV scoring, cohort interactions, delayed responses, failures and responsive layouts. See [VERIFICATION.md](VERIFICATION.md) for executed results and limits.

## Design intent

- A useful home page with a clear hero, live demonstration, truthful evidence, workflow, features, FAQs and direct next action.
- One palette, spacing system, button language and hierarchy across analyst pages and guide.
- Quiet readable data work: observations, predictions and edited scenarios stay distinct; controls, forms, tables and explanations stay functional.
- Local assets and the existing backend; no framework, account system or plugin without a concrete need.
- Useful loading/error/empty states, contrast, keyboard navigation, mobile drawer behavior and reduced-motion support.

Visual review and these checks support the local college project. They do not certify full accessibility, public hosting security, production load capacity or performance on new telecom data.
