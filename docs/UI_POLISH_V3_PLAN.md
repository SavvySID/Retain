# Retain UI polish, revision 3

The user requests a stronger home/hero and fixes across the whole UI, with research into related products. They continue to delegate reasonable choices without questions.

## Findings and direction
The existing site already has a functional home, guide and four workspace views, but its monochrome landing page is visually flat and reads like documentation. A generic admin reference alone does not establish a strong customer-retention product experience.

Research related customer-success/analytics products and inspect rendered screens. Use their presentation hierarchy and product-context patterns with Retain's own brand and real data. The current design call is warm off-white surfaces, navy text, a restrained teal primary action, the existing licensed Geist font, and a substantial live product preview. The previous exact shadcn geometry is a historical V2 target, superseded by this requested redesign; no new pixel-identical claim is intended.

## Scope
- Strengthen home navigation, hero, actual-data demo, feature narrative, workflow, FAQs, closing action and footer.
- Apply a coherent visual system and clearer hierarchy to overview, analysis, batch, model lab and guide.
- Preserve real routes, npm launcher, forms, SHAP units/additivity, API validation, uploaded-file privacy and asynchronous error/race handling.
- Reuse Flask/native HTML/CSS/JavaScript and the existing font. Add no dependency or plugin without a concrete benefit.
- No model tuning, fabricated statistics, client logos, testimonials, savings, events or chart series.

## Ownership and verification
Research owner: related references and evidence. UI owner: templates/static implementation. Parent: tests, reference/finish-check script, integration and current verification documents. Review owner: independent execution/source review after implementation.

Run existing Python checks and real browser workflows. Extend checks for new hero interactions, data parity, mobile navigation, FAQ/anchor links and all six page layouts. Capture the current home/workspace at desktop and phone widths and visually inspect them. Update current reference documents so they do not misrepresent the historical V2 geometry as a check on V3. Stop temporary test services at completion, respecting the user's earlier server-stop request.
