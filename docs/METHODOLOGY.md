# Methodology

## The question being modelled

Given a customer's recorded account and service attributes, estimate the probability of the source dataset's `Churn = Yes` label. The IBM sample describes departure in the last month. It is not a longitudinal dataset with a verified prediction date and future observation window, so this project does not claim to forecast the next 30 days.

The app supports an analyst reviewing associations and model behaviour. Its retention prompts are discussion suggestions, not evidence that an intervention will prevent churn.

## Data and cleaning

The source is the original [IBM Telco Customer Churn CSV](https://github.com/IBM/telco-customer-churn-on-icp4d/blob/master/data/Telco-Customer-Churn.csv). The download records its SHA-256 so an examiner can identify the exact input. See [DATA_CARD.md](DATA_CARD.md) for provenance and limitations.

`customerID` identifies examples but is never a predictor. `Churn` is the target. `gender` and `SeniorCitizen` are deliberately excluded from modelling; this choice is not a fairness audit. Other variables can act as proxies.

`TotalCharges` is converted from text to a number. A blank is interpreted as zero only when the source row also has zero tenure. Other unexplained missing or invalid values must fail validation. Service combinations must be internally consistent: a customer without internet cannot have internet add-ons, and a customer without phone service cannot have multiple phone lines.

The shared schema is used by ingestion, the browser form, prediction and CSV scoring. It prevents training and inference from silently interpreting inputs differently.

## Experimental design

1. Split customer rows deterministically into approximately 60% training, 20% validation and 20% test, stratified on the churn label. Saved customer IDs make overlap auditable.
2. Fit transformations and model parameters on training rows only. Categorical values become one-hot columns; numerical processing stays within the fitted preprocessing pipeline.
3. Compare a dummy baseline, logistic regression, random forest and XGBoost using the same split.
4. Select the predictive model by validation **average precision**. This evaluates ranking with attention to the positive churn class. Average precision is a weighted precision summary; it is not necessarily identical to trapezoidal area under the precision-recall curve.
5. Choose the selected model's classification threshold by validation F1. The threshold is a demo operating point, not an optimised business decision with measured contact costs or customer value.
6. Preserve the train-fitted model after selection. Refitting on train plus validation would change its scores and weaken the justification for carrying over the chosen threshold.
7. Report final test results after those choices. Do not select a different model because its displayed test score looks better.

The fixed split and model settings are a reproducible baseline, not an exhaustive hyperparameter search or a cross-validated estimate of generalisation. Test comparisons are descriptive after validation-based selection.

Randomness uses seed `42`. Numeric fields are standardised and categories are one-hot encoded by a `ColumnTransformer` inside each `Pipeline`. Threshold ties choose the highest threshold, reducing alerts among equally scoring validation-F1 choices. The dummy baseline retains its fixed 0.5 threshold.

## Metrics and plots

| Measure | What it answers |
|---|---|
| Accuracy | What fraction of all test labels were classified correctly? |
| Precision | Of customers flagged for churn, what fraction actually have the churn label? |
| Recall | Of actual churn-labelled customers, what fraction were flagged? |
| F1 | What is the harmonic mean of precision and recall at the chosen threshold? |
| ROC-AUC | How well do scores rank a churn-labelled row above a non-churn row? |
| Average precision | How strong is positive-class precision across recall levels? |
| Brier score | How close are probability estimates to the binary outcomes, using squared error? Lower is better. |
| Confusion matrix | How many true negatives, false positives, false negatives and true positives occur? |

Accuracy alone can hide poor churn detection when non-churn is more common. ROC and precision-recall curves use the actual held-out labels and probabilities. Calibration compares predicted probabilities with observed frequencies. A calibration plot is a diagnostic; displaying it does not mean the model has been calibrated or certified reliable.

All plotted values and comparison tables come from the saved training run. The app does not invent trends, monthly histories, campaign savings or performance targets.

The run also estimates percentile intervals from 300 paired bootstrap resamples of held-out rows with the fitted model and threshold fixed. These quantify resampling variability within this test sample; they do not capture uncertainty from retraining, model selection, a different operator or temporal drift.

## Local explanations

SHAP attributes a model output to input features relative to a background/reference distribution. After one-hot encoding, contributions are grouped back to the original customer fields.

For each explanation:

`base_value + sum(feature_contributions) = output_value`

If the output is in log-odds, convert it with `probability = 1 / (1 + exp(-output_value))`. A positive contribution increases the model's explained output; a negative one decreases it. A log-odds contribution is not a percentage-point probability change.

The app explicitly reports explanation units and checks reconstruction against the actual model prediction. The selected model and explainer implementation are recorded in [MODEL_CARD.md](MODEL_CARD.md). A global ranking summarises absolute attribution magnitudes; it does not measure causality or the expected benefit of changing a feature.

The reference is a deterministic sample of 100 training rows. Global importance uses 200 deterministic validation rows and averages the absolute grouped contributions. This keeps test outcomes out of explanation-reference and global-ranking choices. The saved run metadata records those customer IDs.

Correlated variables such as tenure, monthly charges and total charges complicate attribution. SHAP values depend on the model and reference assumptions. They do not establish why a person left or what would make them stay. See the [SHAP TreeExplainer documentation](https://shap.readthedocs.io/en/latest/generated/shap.TreeExplainer.html) and [scikit-learn's average precision definition](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html).

## Operational boundaries

Actual test customers power the demo queue. Editing their fields creates a user scenario; it does not create new observed evidence. Batch files are bounded and validated, processed locally in memory, and not saved as an upload history. This loopback application is intended for a single-user college demonstration. Production use would need access control, monitoring, representative prospective data, calibration assessment, fairness testing and intervention evaluation.
