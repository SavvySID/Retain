# Model card

## Intended use

Educational, local analysis of IBM's original Telco sample. The app estimates the recorded historical churn label and explains its model output. It is not an externally validated future churn forecast, an automated customer-treatment policy or a guarantee that a retention action will work.

## Current executed run

These values were read from the generated `artifacts/summary.json`; they are this run's measurements, not targets or literature scores.

| Item | Recorded value |
|---|---|
| Selected classifier | Logistic regression |
| Selection criterion | Highest validation average precision among the predictive candidates |
| Decision threshold | `0.49934350911717607` |
| Threshold policy | Maximum validation F1; ties choose the highest threshold |
| Refit after selection | No |
| Seed | `42` |
| Training / validation / test rows | `4,225 / 1,409 / 1,409` |
| Experiment date | `16 November 2026` in the project's local time zone |
| Exact run timestamps | `training.started_at_utc` and `training.completed_at_utc` in `artifacts/summary.json` |
| Recorded Python | `3.12.13` |
| Source SHA-256 | `16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91` |

Retraining updates the machine-readable timestamps rather than requiring a copied timestamp table to stay synchronised. This document describes the measured experiment delivered on the date above. Source-code hashes and exact package versions are stored with the run.

## Pipeline and candidates

Numerical features use `StandardScaler`. Categories use `OneHotEncoder` with unknown categories rejected. A `ColumnTransformer` and estimator are persisted as a single fitted pipeline. All learned preprocessing is fitted only on training rows.

| Candidate | Declared principal settings |
|---|---|
| Dummy baseline | Prior-class probabilities, threshold `0.5` |
| Logistic regression | `C=1.0`, `max_iter=2000`, `solver=lbfgs`, no class weighting |
| Random forest | `180` trees, maximum depth `8`, minimum leaf size `5` |
| XGBoost | `240` trees, maximum depth `3`, learning rate `0.05`, row/column subsampling `0.9`, `reg_lambda=2` |

Each predictive candidate's threshold comes from its own validation F1. Logistic regression narrowly led validation average precision. This small difference is not evidence that it is universally superior. The test table is reported after selection; it does not retroactively change the winner.

## Measured comparison

Values below are rounded for readability. Full precision and all metrics for each candidate remain in `artifacts/summary.json`.

| Model | Validation AP | Test AP | Test ROC-AUC | Test F1 | Test recall |
|---|---:|---:|---:|---:|---:|
| Dummy baseline | 0.265436 | 0.265436 | 0.500000 | 0.000000 | 0.000000 |
| Logistic regression — selected | 0.676589 | 0.624212 | 0.832473 | 0.561151 | 0.521390 |
| Random forest | 0.676530 | 0.632893 | 0.830360 | 0.620462 | 0.754011 |
| XGBoost | 0.676298 | 0.629173 | 0.830875 | 0.613610 | 0.711230 |

The random forest has higher test AP, F1 and recall in this run. It is still not selected because selection was fixed using validation AP. Choosing it after seeing the test table would turn that test set into another selection set.

### Selected model's held-out metrics

| Metric | Observed value |
|---|---:|
| Accuracy | 0.783534 |
| Precision | 0.607477 |
| Recall | 0.521390 |
| F1 | 0.561151 |
| ROC-AUC | 0.832473 |
| Average precision | 0.624212 |
| Brier score | 0.141488 |

Confusion matrix: rows are actual classes and columns are predicted classes.

| Actual / predicted | Non-churn | Churn |
|---|---:|---:|
| Non-churn | 909 | 126 |
| Churn | 179 | 195 |

The model misses `179` churn-labelled test customers at this threshold. That limitation must be visible in a viva; the overall accuracy does not erase those errors.

### Fixed-model bootstrap intervals

The executed run uses `300` paired held-out-row bootstrap resamples and percentile `95%` intervals, with model and threshold fixed:

| Metric | Lower | Upper |
|---|---:|---:|
| ROC-AUC | 0.812523 | 0.851323 |
| Average precision | 0.574095 | 0.673608 |
| Recall | 0.468611 | 0.573059 |
| F1 | 0.518436 | 0.606215 |

These are within-sample resampling intervals. They do not include uncertainty from fitting/selecting a new model or transferring to another population.

## Explanation implementation

The selected logistic model uses `shap.LinearExplainer` with an independent masker over `100` deterministic training-background rows after the same fitted transformation. The explanation output is **log-odds**. The baseline and all grouped signed contributions reconstruct the linear decision output; applying the sigmoid reconstructs the model probability.

Global importance is the mean absolute grouped SHAP attribution over `200` deterministic validation rows, also in log-odds units. It is not a coefficient ranking, a causal effect size or a measured retention benefit. Background and global-sample customer IDs are saved in the run metadata.

An additional executed spot check loaded the saved service and reconstructed predictions for the lowest-score, middle-score and highest-score test rows. Their observed additivity errors were `0.0`, `2.220446049250313e-16` and `4.440892098500626e-16`, below the service's `1e-5` tolerance. This numerical check establishes reconstruction for those examples, not the truth of a causal interpretation. The complete project's test/browser record is in [VERIFICATION.md](VERIFICATION.md).

## Artifacts and integrity

`model.joblib` contains the selected fitted pipeline, threshold, training-only transformed background, predictor names and encoded-column grouping. `summary.json`, `customers.json` and `splits.json` preserve measurements and traceability. `manifest.json` stores SHA-256 digests for those local artifacts, and the service checks them before loading.

The manifest detects accidental mismatch; it is not a signed supply-chain guarantee. `joblib` deserialisation is unsafe for untrusted files. Load only artifacts generated locally by this project's trusted training code.

## Limitations

- Fictional-company benchmark; no external, temporal or prospective validation.
- A single stratified split and small predeclared candidate set; no exhaustive search or model-selection uncertainty estimate.
- Probability calibration is diagnosed, not guaranteed; no post-hoc calibrated model is claimed.
- Gender and senior-citizen predictors are excluded, but no complete subgroup fairness audit has been performed.
- Correlated inputs affect SHAP attribution; explanations are associations in a fitted model.
- No intervention study, campaign uplift, savings estimate or verified customer outcome follows from a score.
- Loopback, single-user app; no production access control, monitoring or drift response.

See [METHODOLOGY.md](METHODOLOGY.md), [DATA_CARD.md](DATA_CARD.md) and [ASSUMPTIONS.md](ASSUMPTIONS.md) for the supporting choices and boundaries.
