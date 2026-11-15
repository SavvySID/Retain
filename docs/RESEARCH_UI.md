# UI research and design decisions

Research date: 16 November 2026. A bounded comparison of primary sources, not a claim to have found every UI or an absolute best design. Inspected official documentation, reference-page content and repository metadata. No third-party source code, metric values or brand assets were copied.

## References inspected

| Source | Evidence inspected | Applied decisions | Avoided |
| --- | --- | --- | --- |
| [Carbon data table guidelines](https://www.carbondesignsystem.com/building-blocks/core/components/data-table/guidelines) | Official component anatomy, toolbar, density, pagination, progressive disclosure and AI presence. The old usage page redirects here. | Group search/filters, paginate real customers, provide an explicit inspect action, distinguish predictions from outcomes. | Full Carbon React stack for a small Flask app; unexplained score badges. |
| [IBM Design for AI](https://www.ibm.com/design/ai/) | Official practice page and its explainability, fairness and data-rights topic structure. | Keep limitations adjacent to predictions; name the source population; separate associations from causal statements; keep uploads local. | Ambiguous confidence gauges or claims that excluding demographics proves fairness. |
| [SHAP waterfall guide](https://shap.readthedocs.io/en/latest/example_notebooks/api_examples/plots/waterfall.html) | Official explanation of expected value, signed factors, feature values and XGBoost log-odds. | Show signed contributions, actual inputs, baseline and reconstructed output. Label units explicitly. | Calling raw-margin contributions probability changes or dropping unexplained factors. Every original feature is shown. |
| [Tabler dashboard preview](https://preview.tabler.io/) | Official reference-page component/navigation structure, charts, table, layout/theme controls. | Persistent navigation, compact KPIs, useful asymmetric content, quiet surfaces and predictable controls. | Fake notifications, people, trend lines and account menus. |
| [Tabler data table](https://preview.tabler.io/datatables.html) | Official preview contents, table structure, density and dark-navigation/layout options. | Readable numeric columns, controls above a bounded scrollable table, explicit row actions and mobile touch targets. | Copying unrelated sample records or importing Bootstrap for a few controls. |
| [tabler/tabler](https://github.com/tabler/tabler) | README/metadata and MIT license link; not a code audit. | Credible open-source reference with a live inspectable implementation. | Inferring code correctness from stars or importing the entire kit. |

Two guessed Carbon AI-label URLs were inaccessible in the research browser. The app does not rely on them; the accessible data-table guide explicitly describes AI presence and explainability.

## Design contract

**Screen's job:** Move from source-derived cohort context to an inspectable prediction without confusing observations, model outputs or scenarios.

**Primary action:** Analyze a customer. A table action opens an actual held-out row. Editing clears the result and marks a scenario. In-flight predictions are discarded if their inputs changed.

**Visual direction:** Forest navigation, off-white canvas, white surfaces, restrained green primary actions and warm warning accents. System fonts support offline use. No external font, icon, telemetry or chart CDN.

**Hierarchy:** Dataset context; four real KPIs; descriptive contract rates and model snapshot; held-out explorer. Model comparisons, confusion counts, run-generated plots and provenance live in Model lab.

**Explanation:** Signed factors extend right/left of zero; signs and text supplement color. All original features remain visible. Numeric reconciliation shows baseline, contribution sum, output units, reconstructed probability and measured error.

**States:** Loading, missing model, invalid prediction, empty search, changed inputs, scoring progress, invalid file and completed download. No placeholder is displayed as a real metric.

**Responsive:** Sidebar becomes horizontal navigation; KPIs become two columns; charts/analysis/batch panels stack; tables scroll within cards. Narrow phones use single-column forms.

**Accessibility:** Semantic navigation/headings/tables, labels, keyboard controls, focus outlines/skip link, live error/status messages, text risk indicators and reduced-motion support. Browser checks supplement visual review; they do not prove full assistive-technology compliance.

## Implementation and attribution

Original HTML/CSS/JavaScript lives in `templates/index.html` and `static/`. No third-party UI source or branded assets are redistributed. Dataset statistics, customer rows, thresholds, metrics, SHAP values and plots come from the local API and recorded training run.

Skipped paid inspiration libraries, framework downloads and exhaustive market-coverage claims. Reference content inspection is recorded honestly; it is not a rendered-screen usability study.
