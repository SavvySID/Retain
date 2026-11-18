# Assumptions and decisions

- Create a standalone local project at `D:\koding\Telecom Customer Churn Prediction with Explainability`. Neighbouring projects are outside scope.
- The student must explain every component in a viva: use readable typed Python, Flask, and plain HTML/CSS/JavaScript, with no separate frontend build system.
- The user explicitly delegates reasonable choices without questions. Research, implementation, training, tests and review proceed autonomously.
- Local use is the delivery target. No paid services, telemetry or cloud publication. Bind to loopback by default.
- IBM's original Telco sample represents a fictional company. It does not establish current operational telecom performance.
- Churn is the source's last-month departure label, not a verified prospective 30-day forecast.
- Deterministic stratified train/validation/test partitions; fit preprocessing on training only, select model/threshold on validation only, report final test results honestly.
- Compare logistic regression, random forest, XGBoost and a dummy baseline. Record actual runs, versions, source hash and split IDs. No target score is promised.
- Exclude customerID, Churn, gender and SeniorCitizen from predictors. This does not prove fairness; unmeasured group disparities remain a limitation.
- Blank TotalCharges may become zero only for source-supported zero-tenure rows. Record the count; reject unexplained missing or invalid values.
- SHAP explains fitted model associations, not causal reasons for departure. Label explanation units and verify additivity.
- Demo examples/risk queue use actual held-out rows. Edited inputs are labelled user scenarios.
- Retention suggestions are transparent rule-based discussion prompts. No savings, uplift or causal effectiveness claims.
- Validate bounded uploads in memory. Do not persist or send them to third parties.
- A single local analyst needs no authentication or database. Multi-user production hosting is outside this college demo.
- Research compares a documented bounded set of public repositories and UI references. It cannot enumerate every repository or prove an absolute best implementation.

## Website revision

- The later request expands delivery to a full localhost website with packaging for a future deployment. No publication is requested now.
- Official shadcn/ui dashboard-01 is the primary rendered reference: light sidebar, inset white workspace, neutral cards, large chart and compact table. Keep Retain branding and real data.
- Home, overview, analysis, batch, model lab and guide get refreshable URLs; retain legacy hash links where practical.
- No dated events exist in the benchmark. The reference visitor chart becomes measured held-out churn/probability by tenure cohort, with sample counts and contract filters. It is not an individual or temporal forecast.
- Preserve the existing Flask/Python model; UI work does not justify changing measured results or adding another framework.

## UI polish revision 3

- The user requests a stronger home/hero and site-wide UI fixes. Related customer-success/analytics products now inform a branded presentation; the old exact shadcn geometry is retained as historical V2 evidence, not a binding target for this redesign.
- Warm off-white, navy and restrained teal, the local Geist font, a live actual-data product preview, purposeful sections and FAQs are reasonable design choices made without further questions.
- Additional plugins are permitted but optional. Keep the existing stack when it can deliver the experience without new dependencies.
- Research examples may inform layout and interaction; they do not supply Retain's model results, customer identities, business benefits or operational capabilities.


## Black accent preference

- The user explicitly requests a single black accent instead of the teal/navy palette. Keep the current layouts and use black, white and neutral grays across navigation, controls, cards, diagrams and dynamic charts. Distinguish chart series with solid/dashed strokes and retain signed factor labels.


## Eight-point college status audit

- Treat the faculty checklist as a request to audit and complete evidence for the existing project, not to replace the model or claim public hosting. Add a reproducible standalone EDA report and consolidated status update.
- New EDA is descriptive follow-up after model freezing. Use the saved training partition for feature/target relationships; use the full source only for quality checks. Preserve model artifacts, thresholds and held-out evaluation.
