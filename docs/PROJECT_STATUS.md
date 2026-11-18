# Project status update

**Project:** Telecom Customer Churn Prediction with Explainability

**Status date:** 18 November 2026

**Current stage:** An end-to-end localhost prototype is implemented. Dataset preparation, training, held-out evaluation and SHAP explanations are complete for the IBM benchmark. The audit added a reproducible standalone EDA report and this eight-point status update. Public deployment and external/temporal validation remain pending.

## Requirement audit

| Requirement | Before this audit | Current evidence and stage |
|---|---|---|
| Problem Statement | Present | Defined in the project report; implemented local decision-support scope |
| Dataset Collection | Present | Canonical IBM CSV, pinned SHA-256 and retrieval provenance |
| Data Preprocessing | Present | Shared schema, documented cleaning, stratified partitions and train-fitted pipeline |
| EDA | Partial: app segment/cohort summaries | Added an executed training-only report, machine-readable statistics and four generated figures |
| Model Development | Present | Four trained candidates including a dummy baseline; frozen validation-selected model |
| Model Evaluation | Present | Saved held-out metrics, curves, confusion matrix and bootstrap intervals |
| Application/Deployment | Application implemented; packaging provided | Local website/API implemented; latest container rebuild and public hosting not verified |
| Challenges and Next Steps | Distributed across specialist documents | Consolidated below, with unresolved work explicitly identified |

## 1. Problem Statement

Build a local web application that estimates the recorded telecom churn label, helps identify higher-scoring accounts and explains which recorded inputs influenced each prediction. The application supports individual analysis, edited scenarios, customer search/filtering and batch CSV scoring.

This is a college demonstrator using a fictional-company benchmark. It does not establish prospective accuracy for a real operator or prove that changing a feature will prevent churn.

**Stage:** Defined and implemented. Evidence: [project report](PROJECT_REPORT.md), [design](DESIGN.md), `app.py`, `src/churn/inference.py`.

## 2. Dataset Collection

The original IBM Telco Customer Churn CSV is collected and verified locally. It contains **7,043 customers and 21 source columns**, including **1,869 churn-labelled** and **5,174 non-churn-labelled** rows. The downloader checks the canonical SHA-256 and records source URL, retrieval time and license evidence. It reuses verified source bytes and does not synthesize replacement customers.

**Stage:** Completed for the chosen benchmark. Evidence: [data card](DATA_CARD.md), `scripts/download_data.py`, `data/provenance.json` and the local `data/raw/Telco-Customer-Churn.csv`.

## 3. Data Preprocessing

The pipeline converts total charges to numeric values, fills the **11 blank TotalCharges values only for zero-tenure customers**, and rejects unexplained invalid values. The source-quality audit found **zero exact duplicate rows** and **zero missing values after cleaning**. Repeated profiles with distinct customer IDs are retained; no source rows are dropped.

There are **17 predictors**. Customer ID, target, gender and SeniorCitizen are excluded from model inputs. Numerical features use standard scaling and categorical features use one-hot encoding, fitted on training data only. Saved stratified partitions contain **4,225 training / 1,409 validation / 1,409 test** rows.

**Stage:** Completed and tested. Evidence: `src/churn/schema.py`, `src/churn/training.py`, `artifacts/splits.json`, [methodology](METHODOLOGY.md), [EDA report](EDA_REPORT.md).

## 4. Exploratory Data Analysis (EDA)

The existing application already showed segment and tenure-cohort statistics. This audit adds a standalone, reproducible EDA report covering source types, blank/missing counts, duplicates, training class balance, numerical summaries and distributions, IQR diagnostics, all categorical predictor groups and numeric correlations.

The new figures and feature/target relationships use **only the saved training partition**; full-source inspection is limited to data quality. The training class counts are **3,104 non-churn / 1,121 churn**. EDA was documented after the original model was frozen and did not change model selection or threshold. The report distinguishes descriptive associations from causal findings.

**Stage:** Added and executed during this audit. Evidence: [EDA report with figures](EDA_REPORT.md), `scripts/eda.py`, `artifacts/eda/summary.json`, `artifacts/eda/plots/`, `tests/test_eda.py`.

## 5. Model Development

A dummy baseline, logistic regression, random forest and XGBoost have been trained on the same training partition. Validation average precision selects the predictive model, and validation F1 selects its decision threshold. Logistic regression was selected with validation AP **0.676589** and threshold **0.49934350911717607**. It was not refitted after selection.

Genuine SHAP explanations group encoded attributions back to original fields. The selected linear model's explanations are in log-odds, include a training-background baseline and reconstruct the model probability. Explanations do not claim causal effects.

**Stage:** Completed for the declared experiment. Evidence: `src/churn/training.py`, `src/churn/inference.py`, trusted local `artifacts/model.joblib`, [model card](MODEL_CARD.md).

## 6. Model Evaluation

The frozen selected model was evaluated on **1,409 held-out test customers**. Values below are rounded from `artifacts/summary.json`, not copied from another repository.

| Metric | Measured test result |
|---|---:|
| Accuracy | 78.35% |
| Precision | 60.75% |
| Recall | 52.14% |
| F1 | 0.561151 |
| ROC-AUC | 0.832473 |
| Average precision | 0.624212 |
| Brier score | 0.141488 |

Confusion counts are **909 true negatives, 126 false positives, 179 false negatives and 195 true positives**. The missed churn labels are an explicit limitation. ROC, precision-recall, calibration, confusion-matrix, threshold-selection and global-explanation plots are saved. Bootstrap intervals are recorded in the model card and summary.

**Stage:** Completed for this fixed benchmark split. External and temporal validation are pending. Evidence: [model card](MODEL_CARD.md), `artifacts/summary.json`, `artifacts/plots/`, `tests/test_model.py`, `tests/test_evidence.py`.

## 7. Application/Deployment

A Flask/Waitress localhost website is implemented with home, overview, customer analysis, batch scoring, model lab and guide pages. It supports real held-out examples, SHAP explanations, scenario editing and bounded CSV uploads/exports. The current interface uses the requested black accent with neutral surfaces. Uploads are validated and processed in memory.

Windows startup is `npm run dev` or `.\start.ps1`; a portable `serve.py`, locked environment and Dockerfile support later deployment. A previous website container was tested, but it predates the final UI. The latest rebuild was blocked by registry/engine availability, and the Docker Linux engine is still unavailable during this audit. **The current application has not been published to a public host.**

**Stage:** Local application implemented; deployment preparation exists; current container verification and hosted deployment pending. Evidence: [README](../README.md), [deployment record](DEPLOYMENT.md), [verification record](VERIFICATION.md), `scripts/browser_check.py`.

## 8. Current Challenges and Next Steps

1. **Recall and class imbalance:** the current threshold misses 179 churn-labelled test rows. Document this trade-off; use validation data and an agreed cost policy for any future threshold changes, preserving a fresh final evaluation.
2. **Generalization:** the fictional benchmark has no external operator cohort or dated future outcomes. Obtain representative, appropriately authorized data before claiming operational or prospective performance.
3. **Fairness and probability reliability:** excluded demographics do not prove fairness. Subgroup error assessment, calibration review and drift monitoring remain future work for operational use.
4. **Deployment:** restore Docker/network availability, rebuild the latest source and repeat container checks. Public hosting additionally needs access controls where appropriate, HTTPS, resource/rate controls and operational review.
5. **College submission:** review the EDA report, project report and viva guide with the faculty guide; rehearse the actual-data demo and report the measured errors as well as aggregate scores.

**Immediate next stage:** Faculty review and submission preparation, followed by a verified current container build when Docker is available. This status does not claim production readiness, real-world retention uplift or public deployment.
