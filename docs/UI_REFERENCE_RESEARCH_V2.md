# UI reference research, revision 2

Research date: 16 November 2026. The user asked for a complete localhost website whose appearance closely matches researched references. This pass includes actual browser rendering, screenshots and DOM measurements, rather than relying only on descriptive documentation. It is a bounded comparison, not a claim to have found an absolute best UI.

## Primary reference selected

**[Official shadcn/ui dashboard-01](https://ui.shadcn.com/view/new-york-v4/dashboard-01)**, also indexed on the [official dashboard blocks page](https://ui.shadcn.com/blocks/dashboard).

The exact preview returned HTTP 200 in Chromium. Its neutral sidebar, inset workspace, four summary cards, large analytical panel and table form a coherent visual system suitable for this project. Use this as the primary structural and visual reference; use the other sources for particular interaction and explanation requirements. Do not blend several unrelated template aesthetics.

Captured evidence:

- [Desktop reference, 1440 by 1000](../artifacts/references/shadcn-dashboard-01.png)
- [Mobile reference, 390 by 844](../artifacts/references/shadcn-dashboard-01-mobile.png)
- [Recorded DOM measurements](../artifacts/references/shadcn-measurements.json)
- [Reference navigation/status record](../artifacts/references/inspection.json)

The first screenshot was taken before the chart finished hydrating. The final desktop capture waited for network idle and a further rendering interval; it includes the rendered area chart. This transient reference-page state must not be mistaken for an intended blank chart.

### Measured visual contract

These values were read with `getComputedStyle` and `getBoundingClientRect` from the rendered primary reference at the desktop viewport above. They are measurements of that page, not arbitrary estimates.

| Element | Reference measurement | Implementation target |
|---|---|---|
| Sidebar container | 288 px wide; full viewport height; 8 px container padding | Neutral, light navigation with the same desktop rail proportions |
| Main inset | Starts at x=288, y=8; 14 px corners; white surface | Inset workspace, rather than the prior flat full-width content canvas |
| Header | 48 px tall | Compact title/breadcrumb, sidebar control and useful action |
| Content start | x=312, y=80 | 24 px horizontal inset and a consistent spacing rhythm |
| KPI row | Four cards; first 262 by 204 px at this viewport | Four source/model summaries, with similar density and hierarchy |
| Cards | 14 px radius; 1 px neutral border; 24 px padding/gap rhythm | Consistent borders and restrained surfaces; avoid oversized shadows |
| Main number | 30 px type, 36 px line height, weight 600 | Preserve the reference's numerical hierarchy |
| Secondary labels | 14 px type, 20 px line height, gray | Readable metadata rather than the prior very small uppercase labels |
| Sidebar links | 14 px/20 px, 32 px high, 8 px corner radius | Compact icon-and-label navigation with a clear selected state |
| Typeface | Geist with Geist Fallback | Match the type scale; self-host a licensed font if used, with an offline fallback |
| Palette | White workspace, near-white neutral sidebar, black text/action, neutral gray borders | Monochrome application shell; color reserved for semantic chart and risk information |
| Analytical panel | Full-width bordered chart below the KPI row | A genuine cohort/distribution visualization, with functional segmented controls |
| Table area | Toolbar/tabs above a bounded table; compact outlined status badges | Search/filter controls and a source-backed held-out customer table |

The sidebar-wrapper background was reported as CSS `lab(98.26 0 0)`; workspace white as `lab(100 0 0)`; border as `lab(90.952 0 -0.0000119209)`; primary text as black. The screenshot records their actual appearance. No approximate hexadecimal conversion is presented as a measured token.

## Compared primary sources

| Reference | Evidence actually inspected | Usefulness and decision |
|---|---|---|
| [shadcn dashboard-01](https://ui.shadcn.com/view/new-york-v4/dashboard-01) | Rendered desktop/mobile screenshots, DOM geometry/type/color, chart/table/navigation | **Primary.** Strongest complete shell match for this analyst website; replace the example business content with our actual data. |
| [shadcn Sidebar](https://ui.shadcn.com/docs/components/base/sidebar) | Official component documentation and composition patterns | Navigation, collapsing rail and mobile sheet behavior; adapt the interaction without introducing a React toolchain. |
| [shadcn Chart](https://ui.shadcn.com/docs/components/base/chart) | Official component documentation plus the rendered dashboard chart | Quiet axes, bounded chart panel and useful controls; keep chart labels and data explicit. |
| [shadcn Data Table](https://ui.shadcn.com/docs/components/base/data-table) | Official sorting, row-action, pagination and toolbar documentation | A functional customer explorer, not decorative placeholder rows. |
| [Tabler vertical dashboard](https://preview.tabler.io/layout-vertical.html) | HTTP 200, rendered screenshot and visible content | Useful information density and navigation hierarchy, but its blue theme, dashboard widgets and map would conflict with the chosen neutral primary reference. |
| [Tabler page layouts](https://docs.tabler.io/ui/layout/page-layouts) | Official layout documentation | Confirms alternate navigation/layout patterns; avoid importing its full Bootstrap stack only for this shell. |
| [Tremor Overview support dashboard](https://overview.tremor.so/support) | HTTP 200, rendered screenshot, compact KPI/table hierarchy | Good analytical hierarchy and restrained cards; horizontal navigation is a secondary alternative, not the selected shell. |
| [Tremor cohort retention](https://overview.tremor.so/retention) | Rendered weekly cohort matrix, counts and supporting labels | Topically relevant, but **do not reproduce its weekly retention chart**: the IBM data has no dated repeated observations establishing those cohorts. |
| [Tremor Insights reports](https://insights.tremor.so/reports) | HTTP 200, rendered screenshot and filter structure | URL/filter patterns and visible reset affordance. Its preview rendered zero-valued reports in this session, so it is not evidence of our metrics or a populated-data benchmark. |
| [Tremor Dashboard](https://dashboard.tremor.so/overview) | HTTP 200, rendered screenshot, compact usage/cost charts | Useful comparative-chart density; its billing, date ranges and invented account identity are outside this project's data. |
| [IBM Carbon data table and AI presence](https://www.carbondesignsystem.com/building-blocks/core/components/data-table/guidelines) | Official table guidance, toolbar, row actions, progressive disclosure and AI-label sections | Keep predictions visibly distinct from observed outcomes and provide an explanation action. Not a reason to apply AI styling to every source value. |
| [GitHub Primer DataTable](https://primer.style/product/components/data-table/) and [SHAP waterfall](https://shap.readthedocs.io/en/latest/example_notebooks/api_examples/plots/waterfall.html) | Primary API/interaction guidance; rendered SHAP documentation capture | Accessible table structure and pagination; signed feature values, baseline and model-output units in the customer explanation. |

Tremor preview URLs were obtained from the actual official [template directory](https://blocks.tremor.so/templates), not guessed. Supporting captures are saved as `tabler-vertical.png`, `tremor-overview.png`, `tremor-retention.png`, `tremor-insights.png`, `tremor-dashboard.png` and `shap-waterfall.png` under `artifacts/references/`. The additional status/content record is `additional-inspection.json` there. An attempted IBM Design for AI fetch timed out; this revision relies on the accessible Carbon guidance instead of claiming to have re-inspected that unavailable page.

## Match checklist and necessary adaptations

The completed implementation comparison is recorded separately in [UI_MATCH.md](UI_MATCH.md), with actual local captures and measured results. The checklist below preserves the research/design targets established before implementation.

The owner should use this checklist during the rendered implementation comparison. These are targets, not assertions that a future revision has already passed them.

- [ ] Match the light sidebar/inset white workspace, compact top header and black primary action.
- [ ] Match the four-card hierarchy and the measured spacing/type proportions at a comparable viewport.
- [ ] Place one wide real visualization below the summary row, then the customer table with its toolbar.
- [ ] Make all navigation, segmented chart controls, filters, pagination and row actions functional.
- [ ] Compare desktop and mobile implementation screenshots directly against the saved primary reference.
- [ ] Keep our own Retain name, telecom terminology and real dataset/model numbers; remove template company identities, visitors, fake notifications and account avatars.
- [ ] Replace the reference's calendar timeseries with a correctly labelled actual tenure cohort, contract group or held-out score distribution. Tenure is not an observation date; do not fabricate monthly history, uplift or trend deltas.
- [ ] Keep training/validation/test distinctions and observed/predicted fields visible without making the whole product flow a wall of implementation notes.
- [ ] Preserve signed SHAP factors and log-odds/probability explanation units even where the reference has simpler business charts.
- [ ] Preserve keyboard, loading, empty, invalid-input, pending-prediction and missing-model states.

## Reuse, licensing and limits

The [shadcn/ui repository license](https://github.com/shadcn-ui/ui/blob/main/LICENSE.md) and [Tabler license](https://github.com/tabler/tabler/blob/dev/LICENSE) were checked and identify MIT licensing. No third-party UI source code, logos, sample metric values, customer identities or brand assets were copied in this research task. Reference screenshots are local research evidence, not website assets. A future decision to copy source, distribute a font or embed imagery must retain its applicable license/attribution; a project's code license does not automatically license every page asset or trademark. No commercial Tremor template entitlement is assumed.

The comparison assessed a bounded set of official previews and guidance. It did not benchmark their code, test every interaction, certify accessibility, audit all licenses or prove one template universally best. The recommendation is a concrete fit judgment for this project's analyst workflow. Final implementation fidelity must be assessed against actual local screenshots and tested behavior, not inferred from this research document alone.
