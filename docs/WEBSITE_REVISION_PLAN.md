# Website revision

The user requested a fuller localhost website, more intensive UI research and a close match to selected references, with future deployment support. They delegated choices without further questions.

## Design
Use the rendered official shadcn/ui dashboard-01 as the primary visual reference. Match its light sidebar, inset workspace, compact header, neutral cards and chart/table hierarchy with Retain content. System/native browser code preserves the current Flask architecture and understandable viva implementation. A React rewrite adds a second toolchain without improving the model or required workflows.

Product home introduces the actual app. Workspace URLs support direct entry/refresh and history navigation. Guide explains use and limits inside the website. The main chart groups real held-out accounts by tenure and contract; its data is computed and checked against saved source rows.

## Work and checks
1. Capture/render primary and comparative references; record exact dimensions and adaptations.
2. Add route/cohort regression tests, verify failures, implement routes and real aggregation.
3. Rebuild all website screens around the chosen reference while preserving inference, uploads, accessibility and request-race guards.
4. Add portable serving and Linux container packaging using the locked environment; test actual startup/build where available.
5. Run Python, JavaScript and real-browser workflows, compare reference/local screenshots at the same viewport, and document matching choices plus remaining differences.
6. Update setup, deployment and verification records. No cloud publication, invented data, mock charts or model tuning against reported test results.

Ownership: parent handles app.py, API/cohort/browser checks and integration; UI owner handles templates/static; deployment owner handles serving/container/docs/tests; research owner handles reference evidence.
