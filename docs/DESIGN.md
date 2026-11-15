# Telecom churn with explainability

Deliver a reproducible college project that predicts churn labels and makes each prediction inspectable. Flask serves a responsive dashboard and a JSON API; Python owns shared schema, training and inference. A locked uv environment supports Windows.

Alternatives: Streamlit is quick but restricts this UI; React plus an API adds two toolchains. Flask with plain JavaScript keeps the app understandable in a viva.

## Experience
Overview, customer analysis, batch scoring and model lab views. Show source-derived cohort statistics and real evaluation results. Search/filter actual held-out customers, open an explanation, edit a complete customer form and predict. Show signed SHAP factors in explicit units. Validate CSV scoring and download results. Model lab shows model comparisons, confusion matrix, ROC/PR curves, calibration, provenance, feature importance and limitations generated from the run.

## Evidence
Original IBM sample with SHA-256. Stratified partitions and train-only pipeline preprocessing prevent leakage. Validation selects model and threshold; final test results are labelled. Charts and metadata come from actual code execution. User scenarios, observations and evaluation evidence remain distinct.

## Acceptance
Fresh setup downloads data, trains and runs tests. Desktop/mobile browser QA covers navigation, prediction, explanation, errors and batch export. Tests cover schema boundaries, split disjointness, metrics, explanation additivity, prediction parity, CSV limits and model readiness. Deliver research, assumptions, methodology, API/model/data documentation, a viva guide and actual validation results.
