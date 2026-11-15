# Dataset, implementation and methodology research

Research date: 16 November 2026. This is a bounded comparison of relevant public projects, not a claim that every GitHub repository was found or that one is universally best. Selected source files were inspected; third-party projects were not installed or executed. Their model scores are not reproduced or adopted here.

## Decision

Use IBM's original Telco CSV, a local scikit-learn pipeline, a small comparison of understandable tabular classifiers, validation-only model and threshold selection, and genuine SHAP explanations with explicit units. Build the application independently rather than copying a portfolio repository. The strongest inspected experiment-structure reference is the kennyoomega notebook; IBM is the primary data source. The parent implementation decision is Flask and plain JavaScript, exclusion of gender and senior-citizen status from predictors, and keeping the selected train-fitted model unchanged after validation.

## Primary dataset and measured inspection

- [IBM source repository](https://github.com/IBM/telco-customer-churn-on-icp4d)
- [Original CSV](https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv)
- [GitHub Contents API fallback](https://api.github.com/repos/IBM/telco-customer-churn-on-icp4d/contents/data/Telco-Customer-Churn.csv?ref=master)
- [Repository license](https://github.com/IBM/telco-customer-churn-on-icp4d/blob/master/LICENSE): Apache-2.0. No separate CSV-specific license was observed; retain IBM attribution and the supplied license when redistributing its included file. This is a source inventory, not a legal opinion.
- [IBM description of its Telco samples](https://community.ibm.com/community/user/blogs/steven-macko/2019/07/11/telco-customer-churn-1113?hlmlt=QT): fictional/sample telecom customers. Do not describe the data as private operational records or validation on a real telecom deployment.

These results were actually computed by fetching the CSV through GitHub's Contents API, decoding base64, parsing with PowerShell `ConvertFrom-Csv`, and hashing its bytes with .NET SHA-256 during this research:

| Check | Measured result |
|---|---:|
| Customer records | 7,043 |
| Columns including identifier and target | 21 |
| Unique customer identifiers | 7,043 |
| `Churn=Yes` | 1,869 |
| `Churn=No` | 5,174 |
| Blank `TotalCharges` | 11 |
| Source byte count | 970,457 |

SHA-256: `16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91`.
Git blob SHA: `3de7a612d1609f25f21a455bda77948729369002`.

All inspected blank-charge records had `tenure=0` and `Churn=No`. Preserve the raw file. A documented policy may represent newborn-account charges as zero or use a train-fitted imputer; do not silently delete records. Inference must use the same cleaning policy.

Observed columns: `customerID`, `gender`, `SeniorCitizen`, `Partner`, `Dependents`, `tenure`, `PhoneService`, `MultipleLines`, `InternetService`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies`, `Contract`, `PaperlessBilling`, `PaymentMethod`, `MonthlyCharges`, `TotalCharges`, `Churn`. Exclude the identifier and target from predictors. The application's additional exclusion of gender and senior-citizen status reduces direct use of demographic attributes, but does not prove fairness or eliminate proxies. The target is historical churn status; this file has no dated longitudinal sequence establishing a prospectively validated forecast horizon.

Direct `raw.githubusercontent.com` requests timed out on this host during research; the official GitHub API fallback succeeded. This is a retrieval limitation, not a reason to substitute generated data.

## GitHub comparison

“Code inspected” means the listed source was actually retrieved and read, sometimes as relevant excerpts of a long notebook. It does not imply a whole-repository audit. No third-party score is presented as this project's result.

| Project and inspected evidence | Useful ideas | Limits and adoption decision |
|---|---|---|
| [IBM/telco-customer-churn-on-icp4d](https://github.com/IBM/telco-customer-churn-on-icp4d): README, CSV bytes/metadata, LICENSE, `flaskapp/telcochurn.py`; snapshot `d5371f5d83a446ad5673cbcca3b814b926491f8a` | Authoritative included dataset; notebook-to-prediction-interface workflow. | Archived in 2024. Cloud Pak/Watson setup is unnecessary for a local college app. Adopt data and attribution, not its cloud stack. |
| [kennyoomega/Telco-Customer-Churn-Prediction](https://github.com/kennyoomega/Telco-Customer-Churn-Prediction): README and `notebooks/01_telco_churn.ipynb`; snapshot `c1c4800dbe67d1fde5b7a9770650672460234020` | Stratified train/validation/test, cloned train-fitted pipelines, validation average-precision comparison, validation threshold tuning, TreeSHAP. | Notebook-centric with limited reusable app structure. Strongest inspected experiment-structure reference; implement a small typed package rather than inherit notebook state. |
| [infabuilds/customer-churn-prediction](https://github.com/infabuilds/customer-churn-prediction): README, source/test inventory, `src/explain.py`; snapshot `e6045adea3bed9ebee40f1cbfa04ef70bc00fb6c` | Raw-field pipeline, API/app separation, tests, aggregation of encoded contributions into original fields. | Inspected explanation calls coefficient times transformed input SHAP without subtracting background expectation. That is a coefficient decomposition relative to zero, not generally independent-background SHAP. Use a genuine explainer and additivity test. |
| [Shakya658/customer-churn](https://github.com/Shakya658/customer-churn): README, `app.py`, `tests/test_evaluation_curves.py`; snapshot `ebaaabd83c4cdee2d7fefd94a9c7eda7490922d5` | Model comparison UI, exported evaluation-curve artifacts, curve-structure tests, explicit explanation-failure reporting. | Inspected logistic branch supplies the current prediction row as `LinearExplainer` background. A one-row explanation relative to itself can erase contributions. Use fixed training background. Avoid its overconfident “Will churn” wording. |
| [felipesbonatti/telco-customer-churn](https://github.com/felipesbonatti/telco-customer-churn): data notes, source/test inventory, `src/churn_case/modeling.py`; snapshot `6fdddd309b7c54b1aa97845327bd4ee86d85b16a` | Compact functions, typed result object, validation threshold, ranking and calibration metrics, separate business/segmentation code. | It chooses a validation threshold then refits on train plus validation, changing the score distribution. Keep the evaluated train-fitted winner unchanged for the initial reproducible project. |
| [TanujaModugumudi/telco-churn-prediction](https://github.com/TanujaModugumudi/telco-churn-prediction): README and `app/app.py`; snapshot `48d4bf7104505029ef28b63dedbe4ee88198e382` | Grouped input form, probability/threshold display, waterfall, cached artifacts. | Manually reconstructs encoded inputs and hardcodes evaluation numbers in the sidebar. Avoid train/serve drift and stale scores: predict through the fitted pipeline and read generated metrics. |
| [OCHIENG-FELIX/telco_customer-churn-ai](https://github.com/OCHIENG-FELIX/telco_customer-churn-ai): README, source inventory, selected `app/app.py` sections | Customer-level factors, batch scoring, report downloads, explicit association-versus-causation distinction. | Large app mixes model logic, reporting and assistant knowledge. Local LLM/assistant is unnecessary for this viva-focused scope. Adopt workflow ideas, not the explanation-generation layer or hardcoded knowledge. |
| [bgoya/telco-churn-prediction](https://github.com/bgoya/telco-churn-prediction): README and notebook code cells; snapshot `d310bbdb449116b5cbd9624b2fda90aa56fa76c1` | Readable logistic baseline; train-only scaler fitting in the inspected baseline. | Repeated notebook fits/test evaluations do not enforce final selection on separate validation. Prefer one reproducible command and saved partition assignments. |
| [Augusto-98/churn_llm_explainer](https://github.com/Augusto-98/churn_llm_explainer): README/tree; retrieved `src/streamlit_app.py` contained no substantive matching prediction logic | Plain-language explanation use case and deployable dashboard presentation. | Model claims were not established by that retrieved file; no complete training audit. Adds external LLM dependency. Use deterministic wording grounded in actual attributions instead. |
| [vasif-asadov1/customer-churn-prediction-pipeline](https://github.com/vasif-asadov1/customer-churn-prediction-pipeline): browser-fetched README/file inventory only | EDA/report presentation; states SMOTE and SHAP support. | API tree retrieval returned 404, so training and resampling order were not verified. Presentation-level reference only; no code adoption or metric endorsement. |
| [IBM/customer-churn-prediction](https://github.com/IBM/customer-churn-prediction): README only | Historical scikit-learn-to-frontend example; points to IBM successors. | Explicitly unmaintained/archived; documented Python/cloud credential workflow is dated. Historical context only. |

No repository was chosen by popularity or executed for a benchmark. License checks were not completed for every third-party project because no third-party source code is copied. Recheck the relevant license before any future code reuse.

## Methodology decisions

### Leakage and reproducibility

The [scikit-learn pitfalls guide](https://scikit-learn.org/stable/common_pitfalls.html) supports training-only fitting and identical preprocessing at inference. Persist imputers, scaling, encoding and estimator together. Split before any learned transform; keep identifiers separately to check partition overlap.

IBM's [enriched field definitions](https://community.ibm.com/community/user/blogs/steven-macko/2019/07/11/telco-customer-churn-1113?hlmlt=QT) identify churn reason/category as information collected when customers leave and status as an outcome. These disclose the target. “Churn Score” is already another predictive model's output. Exclude such fields from independent prediction. The chosen original CSV avoids them.

Use fixed-seed stratified train, validation and test sets. Predeclare a small candidate set and choose by validation average precision. Choose the operating threshold by validation F1 as a transparent educational default. [Thresholding is a separate decision](https://scikit-learn.org/stable/modules/classification_threshold.html); a commercial threshold needs measured intervention costs/benefits unavailable here. Freeze estimator and threshold before final test evaluation. Do not retune against the test score.

Report [average precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html) by that name; it is not identical to trapezoidal precision-recall AUC. Include ROC-AUC, precision, recall, F1, confusion matrix, Brier score and observed calibration curve. Accuracy alone obscures minority-class failures. A lower Brier score alone does not prove improved calibration because it also reflects discrimination and uncertainty ([calibration guide](https://scikit-learn.org/stable/modules/calibration.html)).

A random holdout measures interpolation within this sample, not future-period or Indian-operator performance. Charts must show computed observations, not fabricated monthly trends. Save partition identifiers, predictions, metrics, parameters, versions and data hash so results are traceable to a run. Do not invent campaign lift, money saved, lifetime value or ROI.

### Explanations that survive a viva

[Lundberg and Lee's original SHAP paper](https://arxiv.org/abs/1705.07874) formalizes additive per-prediction feature attributions. Describe baseline, signed contributions and explained output. Global feature importance is different from a reason for one customer's score.

[TreeExplainer](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html) distinguishes raw and probability outputs. Binary XGBoost raw output is log-odds; probability explanations require an interventional background in the documented API. Logistic regression should use a fixed training-background `LinearExplainer`, not the current row as its own reference. Aggregate one-hot attributions back to source fields without losing their sum. Test that baseline plus all contributions reconstructs the explained output within numerical tolerance. Apply sigmoid only for log-odds outputs.

The [SHAP causality guide](https://shap.readthedocs.io/en/latest/example_notebooks/overviews/Be%20careful%20when%20interpreting%20predictive%20models%20in%20search%20of%20causal%20insights.html) explains why model attribution does not establish intervention effects. A contract-change scenario may recompute a score but cannot promise to retain a customer. Suggestions are hypotheses for human review.

### Deliberately unnecessary

This tabular sample does not require deep learning, a generative chatbot, paid APIs, distributed cloud pipelines, registry services or automated production campaigns. A small local app with typed/docstringed code, tested training/inference, reproducible artifacts, individual/batch predictions and honest explanations better serves the college goal. Add complexity only for a measured need.

## Verification limits

This research inspected primary documentation and selected public source. It did not execute competing repositories, verify their metrics, audit every file, prove causal effects, or find every related repository. The local project's actual model results belong in generated experiment artifacts, not this comparison.
