# Related-product UI research and revision 3 direction

Research date: 16 November 2026. This pass addresses the request for a stronger product website and home hero, rather than another reproduction of a neutral dashboard block. References are public, primary product pages. Five pages were actually rendered in installed Chromium, with desktop/mobile and selected lower-section captures; additional sources were read as supporting context. This is a bounded design comparison, not a universal ranking of SaaS design.

## Recommendation

Use **Attio's product-led editorial hierarchy** as the main home-page reference: clear navigation, an emphatic headline, compact supporting copy, useful actions and a substantial product demonstration. Use **Vitally's reporting page** to ground the content in account health, customer segments and investigation, with **ChurnZero** supporting the customer-growth context. The intended Retain implementation should have its own warm paper surfaces, dark navy text and restrained teal actions.

This is a deliberate adaptation of related-product patterns, not a claim that those references already use Retain's proposed palette. Their proprietary typography, product screenshots, company names, claims and illustrations must not be copied. The strongest visual on Retain's page should be its own working product, populated with actual held-out records and signed explanation factors.

## Rendered evidence

All desktop screenshots use a 1440 by 1000 viewport. Mobile captures use 390 by 844. HTTP status and observed titles/headings are recorded in the JSON files under [artifacts/references/v3](../artifacts/references/v3/).

| Exact primary page | Observed design and flow | Use for Retain |
|---|---|---|
| [Attio home](https://attio.com/) | HTTP 200. Large centered editorial type, restrained navigation, two primary paths and a large framed application demonstration. Subsequent sections develop capabilities through detailed product views. Actual mobile menu opened successfully. | Primary home hierarchy and product-demonstration emphasis. Replace sales/signup capture with immediate localhost workspace and example-analysis actions. |
| [Vitally home](https://www.vitally.io/) | HTTP 200. Its current page promotes the Quin AI assistant, with a dark field, vivid color and a product scene. Capability sections lead to a closing action and resource content. | Related-product storytelling and coherent capability sections. Its launch aesthetic and assistant claims are not Retain's visual or functional brief. |
| [Vitally reporting](https://www.vitally.io/features/reporting) | HTTP 200. Split hero: substantial copy/action area beside a dashboard preview. The following section pairs an enlarged customer-health dashboard with a short reporting feature sequence. Mobile stacks copy, full-width actions and product visual. | Concrete account-health/reporting context, product-first feature explanation and a useful visual counterpart to each section. Avoid unsupported real-time/revenue claims and copied charts. |
| [ChurnZero home](https://churnzero.com/) | HTTP 200. Teal field, editorial serif headline, clear demo path and subsequent customer-growth narrative. The page uses a sticky navigation and colored section transitions. A cookie banner remained in the captured session. | A warmer editorial tone and a purposeful narrative transition after the hero; do not copy its sales form, claims or branding. |
| [Planhat home](https://www.planhat.com/) | HTTP 200. Full-screen animated imagery and typographic storytelling, followed by customer marks and platform narrative. Captures show animation states, not static canonical compositions. | Useful evidence for deliberate section rhythm and stronger product storytelling. Reject the large decorative video, logo wall and animation complexity for this academic local tool. |

### Captures inspected

- [Attio desktop](../artifacts/references/v3/attio-home-desktop.png), [product section](../artifacts/references/v3/attio-home-product-section.png), [mobile](../artifacts/references/v3/attio-home-mobile.png), [opened mobile navigation](../artifacts/references/v3/attio-mobile-menu-open.png).
- [Vitally home](../artifacts/references/v3/vitally-home-desktop.png), [reporting hero](../artifacts/references/v3/vitally-reporting-desktop.png), [reporting section](../artifacts/references/v3/vitally-reporting-section.png), [reporting mobile](../artifacts/references/v3/vitally-reporting-mobile.png).
- [ChurnZero hero](../artifacts/references/v3/churnzero-home-desktop.png), [following section](../artifacts/references/v3/churnzero-home-section.png), [mobile](../artifacts/references/v3/churnzero-home-mobile.png).
- [Planhat hero](../artifacts/references/v3/planhat-home-desktop.png), [following section](../artifacts/references/v3/planhat-home-section.png), [mobile](../artifacts/references/v3/planhat-home-mobile.png).

`first-inspection.json`, `additional-inspection.json`, `attio-detail.json` and `mobile-menu-inspection.json` retain URL/status and observation evidence. Extracted heading lists can include hidden navigation text; screenshots and visibly rendered main content were used for design judgments.

### Measured type hierarchy

These values were actually read from rendered DOM styles at the desktop viewport, rather than guessed from a screenshot:

| Page element | Observed type |
|---|---|
| Attio hero heading | Inter Display, 69.33 px, weight 600, 65.86 px line height |
| Attio body | Inter, 16 px, 22 px line height |
| Attio major section heading | 40 px, weight 500, 44 px line height |
| Vitally reporting hero heading | Agrandir Wide, 52 px, weight 300, 65 px line height |
| Vitally reporting body | Inter, 16 px, 25.6 px line height |
| ChurnZero hero heading | Gelasio serif, 56 px, weight 500, 67.2 px line height |
| ChurnZero body | Barlow, 16 px, 27.2 px line height |

Retain can achieve the hierarchy with its already self-hosted Geist family and sensible fallbacks. Introducing those proprietary reference fonts is unnecessary. A heading should be visibly stronger than dashboard-card text; supporting copy should remain comfortably readable on mobile.

## Supporting sources and exclusions

- [Custify](https://www.custify.com/) was read for its account-health, risk and workflow positioning; it was not rendered in this capture set. It reinforces the value of connecting a risk view to a concrete investigation workflow, but its commercial outcomes and automation claims do not transfer to Retain.
- [PostHog](https://posthog.com/) was read for product-demonstration structure and visible labeling of illustrative examples. Retain should use its actual model output and name the sample population, rather than invent a conversational assistant or copy PostHog's illustrated brand.
- [Amplitude](https://amplitude.com/) was read for platform organization and product-preview progression; it was not rendered here. Its large commercial platform navigation is unnecessarily broad for this project.
- [June's current homepage](https://www.june.so/) was checked. It is an acquisition/new-chapter announcement, not the current product hero sometimes shown in older inspiration collections. It is excluded as a present-day product-hero reference.

## Concrete Retain design mapping

| Website area | Reference pattern | Actual Retain implementation direction |
|---|---|---|
| Header | Compact product navigation with one unmistakable primary action | Retain name, a small number of useful section/page links, and Open workspace; mobile navigation must open, close and remain keyboard usable. |
| Hero | Editorial hierarchy plus a credible product demonstration | Warm paper/off-white, navy headline and restrained teal action. Pair a direct churn-analysis promise with a framed, detailed product scene. |
| Hero product scene | Product shown performing its core job | Render an actual held-out customer, its model score, observed label where appropriate, and signed SHAP factors. A working customer selector or linked example provides more credibility than decorative mock statistics. |
| Initial proof/context | A concise reason to trust what is being shown | Source dataset, held-out evaluation and explanation method, all drawn from existing artifacts. No client logos, testimonials, invented accounts or commercial savings. |
| Workflow | A brief sequence that connects product capabilities | Explore the held-out cohort; inspect one account and its factors; score a validated CSV. Link each stage to its working page. |
| Feature sections | Specific capability paired with an informative product visual | Use real cohort/distribution data, the complete explanation view and batch-input validation. Avoid three identical vague cards with stock icons. |
| Evaluation section | Evidence available when a user wants detail | Compare the actual candidate models and link to Model lab. Preserve validation selection, test reporting and limitations. |
| FAQ | Address decisions a new visitor must understand | Explain historical labels versus forecasts, associations versus causes, supported inputs, upload handling and local/deployment use. Answers must agree with current code/docs. |
| Closing action/footer | A clear next step and useful navigation | Open workspace or analyze a real example; link to Guide, Model lab and project material. No fake signup, sales team, social counters or unavailable product links. |
| Analyst pages | The same product's quieter working mode | Carry the palette, typography, button language and spacing into overview, analysis, batch, model and guide views while preserving dense usable tables/forms. |

The desired page is product-led, not an unbroken sales pitch. A suitable sequence is header → hero with real product preview → truthful source/model context → short workflow → detailed product features → evaluation evidence → FAQ → final action/footer. These are design recommendations, not claims that implementation has already passed review.

## Data and quality boundaries

- No invented dated history, trend arrows, revenue, ROI, uplift, customer names, customer logos or testimonials. Tenure groups are not calendar time series.
- A preview score must be computed for the displayed row. Editing/selecting a customer must not leave another customer's score visible or allow late responses to overwrite the current state.
- Show pending/error states and real retry paths. A broken model or API must not turn into a polished fake demo.
- Keep navigation, charts, details, downloads and calls to action useful. Any decorative element should support reading the product rather than imply unavailable functionality.
- Compare the actual local home and working pages at desktop and mobile widths. Check heading wraps, product-visual cropping, contrast, focus, menu behavior, tables, forms and section spacing. A reference screenshot is not proof that the resulting site meets those checks.

## Scope and limits

This research changed only this document and local reference evidence. No commercial source code, fonts, brand imagery or screenshots were copied into the website. Screenshots are research material, not redistribution-ready site assets. Proprietary reference claims and demo data are not evidence of Retain's performance.

Public pages change; the recorded captures describe this session. Only Attio's mobile menu was actively opened; other mobile navigation was visually inspected rather than comprehensively tested. No authenticated product tour, full accessibility audit, all-site interaction audit, commercial-code benchmark or exhaustive licensing review was performed.
