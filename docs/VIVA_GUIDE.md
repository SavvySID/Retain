# Viva guide and demo

## Explain the project in one minute

“This application estimates the churn label in IBM's Telco customer sample and explains each model prediction. I compare a simple baseline, logistic regression, random forest and XGBoost on separate training, validation and test partitions. Validation selects the model and decision threshold. The test partition supplies the final reported results. A Flask application serves an analyst dashboard, individual predictions with SHAP explanations, and validated CSV scoring. The explanations describe the model's associations, not proven causes of churn.”

Use the actual model name and results from **Model lab** or `artifacts/summary.json` when discussing the final run. Do not memorise an assumed accuracy target.

## Five-minute demonstration

1. Open **Overview**. Identify the IBM sample and distinguish full-dataset descriptive statistics from held-out model evaluation. Explain one actual contract segment; avoid describing it as a causal effect.
2. Search the customer queue and open any real held-out customer. Point out the customer ID, recorded features, actual label and predicted risk. Show a mistake as well as a correct prediction if the queue contains them.
3. Open **Customer analysis**. Explain the score, chosen threshold and signed SHAP contributions. State the units. Explain the baseline and show that the complete contributions reconstruct the output.
4. Change a field in the form. This is now a manual scenario. Compare the model response without claiming the edit would cause the same real-world change.
5. Download the actual sample CSV in **Batch scoring**, upload it, and inspect the returned probabilities. Demonstrate a missing column or invalid value and the resulting validation error.
6. Open **Model lab**. Explain why the validation-selected model is retained even if another model has a better isolated test metric. Read the confusion matrix and one precision-recall or calibration diagnostic.

## Questions you should be able to answer

### What is customer churn?

Customers discontinuing a service. Here the positive label is the dataset's recorded `Churn = Yes`. Because this benchmark is not a timestamped prospective study, do not call its output a validated next-month forecast.

### Why is this supervised learning?

The training rows contain both customer features and known churn labels. The classifier learns a mapping from those features to a probability of the positive label.

### Why exclude customer ID?

It identifies a record, not a meaningful service characteristic. Letting the model learn identifiers risks memorisation and usually does not transfer to new customers.

### Why exclude gender and SeniorCitizen?

They are not needed for this project's chosen predictor set. Removing them is a limited design decision, not proof of fairness: other features may be proxies, and group performance can still differ.

### Why three partitions?

Training fits parameters and transformations. Validation makes model and threshold choices. Test estimates the performance of the already selected procedure. Using test results to make those choices leaks evaluation information.

### What is stratification?

It keeps the churn/non-churn proportions approximately similar across the partitions. It does not guarantee that every other subgroup is equally represented.

### What is preprocessing leakage?

Learning transformation parameters from validation or test rows before evaluation. A fitted preprocessing pipeline learns only from training data and reuses those same transformations when scoring other rows.

### Why one-hot encoding rather than arbitrary category numbers?

Categories such as contract type do not have a general numerical distance. One-hot columns encode membership without pretending that one category is numerically twice another. The saved transformer keeps the same category mapping during inference.

### How do the models differ?

Logistic regression models log-odds as a weighted linear combination. Random forest averages many decision trees. XGBoost adds trees sequentially to improve the ensemble's objective. The dummy model provides a reference without meaningful feature learning. Complexity alone does not decide the winner.

### Why not choose by accuracy alone?

The churn class is less common. A model can obtain a seemingly useful accuracy by favouring non-churn while missing many churn-labelled customers. Precision, recall, F1, ranking metrics and calibration diagnostics reveal other aspects.

### What is average precision?

A summary of precision across recall increments. It evaluates the positive-class ranking without fixing a single classification threshold. It should not be casually renamed trapezoidal PR-AUC because those calculations can differ.

### Why is the threshold not always 0.5?

The probability score and the decision rule are separate. This demo selects a threshold using validation F1. A deployed business would need a policy based on contact costs, customer value, staffing and measured intervention effectiveness.

### Why not refit the winner on training plus validation?

That changes fitted parameters and score distributions. This project retains the train-fitted model so the validation-chosen threshold applies to the same scorer. A stronger deployment process could reserve another calibration/threshold set.

### Does a score of 0.8 mean 80% certainty for this person?

It is the fitted model's positive-class probability estimate. Whether such estimates match observed frequencies requires calibration assessment on representative data. It is not a guarantee about one person.

### What is the confusion matrix?

Rows are actual classes and columns predicted classes, ordered non-churn then churn. The entries are true negatives, false positives, false negatives and true positives. A false positive is a non-churn-labelled customer flagged as churn; a false negative is a churn-labelled customer missed.

### What does SHAP explain?

The model output relative to a reference/background distribution. Signed feature contributions add to the model's explained output with a baseline. The app groups encoded columns back into customer fields and reports whether the units are probability or log-odds.

### Are SHAP values causes?

No. They attribute predictions under modelling assumptions. Correlated inputs and the chosen reference affect those attributions. Changing an input in the form is a model scenario, not a causal experiment.

### Why can SHAP and a global importance ranking differ?

A local explanation concerns one row. A global ranking aggregates magnitudes across a set of rows and hides direction and customer-specific interactions. Neither alone identifies the best retention action.

### Did you prove a retention campaign would save money?

No. Rule-based suggestions are discussion prompts. There is no campaign trial, uplift model, measured cost model or evidence of causal benefit in this dataset.

### How is the project reproducible?

The raw-data hash, saved split membership, dependency lockfile, fixed randomness, training code and run artifacts identify the experiment. Rerun the documented commands and compare the generated evidence; hardware/library changes can still affect exact numerical output.

### What are the main limitations?

A fictional-company benchmark, a single random split, no verified prospective time window, no external validation, no completed fairness audit and no tested retention intervention. The local app also lacks production authentication and monitoring.

## Files to know before the viva

Read the shared schema, training pipeline, inference code, Flask routes and their tests. Then follow [METHODOLOGY.md](METHODOLOGY.md), [MODEL_CARD.md](MODEL_CARD.md), [DATA_CARD.md](DATA_CARD.md), the [research comparison](RESEARCH_ML.md) and [VERIFICATION.md](VERIFICATION.md). Be able to trace a displayed metric back to the actual saved labels and probabilities.
