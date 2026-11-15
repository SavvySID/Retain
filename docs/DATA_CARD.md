# Data card

## Identity and provenance

| Item | Description |
|---|---|
| Dataset | Original IBM Telco Customer Churn CSV |
| Publisher/source | [IBM source repository](https://github.com/IBM/telco-customer-churn-on-icp4d) |
| Included file | [data/Telco-Customer-Churn.csv](https://github.com/IBM/telco-customer-churn-on-icp4d/blob/master/data/Telco-Customer-Churn.csv) |
| Local raw file | `data/raw/Telco-Customer-Churn.csv` |
| Provenance record | `data/provenance.json` |
| License evidence | Source repository [Apache-2.0 LICENSE](https://github.com/IBM/telco-customer-churn-on-icp4d/blob/master/LICENSE); no separate CSV-specific license was observed during research |
| Meaning | IBM sample representing a fictional telecom company, not this project's live customer collection |

The downloader preserves the source bytes, checks a pinned SHA-256, and refuses unexpected changed data. If the raw host fails, it tries the official GitHub Contents API and decodes the same included file. It never generates replacement customer rows. A failed download must be reported and resolved before training.

## Inspected local source

The following checks were executed against the downloaded local CSV using PowerShell `Import-Csv`, uniqueness checks and `Get-FileHash` on 16 November 2026:

| Check | Observed value |
|---|---:|
| Rows | 7,043 |
| Columns, including identifier and target | 21 |
| Unique customer IDs | 7,043 |
| Churn-labelled rows (`Yes`) | 1,869 |
| Non-churn-labelled rows (`No`) | 5,174 |
| Blank `TotalCharges` | 11 |
| Blank-charge rows also having zero tenure | 11 |

SHA-256: `16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91`.
The provenance record reports 970,457 source bytes and retrieval at `2026-11-15T22:58:55.457405+00:00` (UTC). These identify this file, not a guaranteed future upstream version.

Retain IBM attribution and the supplied source license when redistributing the included file. The repository's license identification is source evidence, not a legal opinion or a new license for unrelated third-party material.

## Unit, target and identifiers

Each row represents a sample customer account. `customerID` is retained to trace splits and examples and is excluded from predictors. `Churn` maps `Yes` to the positive class and `No` to the negative class. The source describes last-month departure. It does not supply the dated feature snapshots and future outcomes needed to demonstrate prospective prediction.

The raw file contains `gender` and `SeniorCitizen`; these fields are excluded from this project's predictor set. They are not accepted as scoring inputs. Their exclusion does not remove proxy relationships or establish fair treatment.

## Predictor dictionary

| Field(s) | Meaning and accepted values |
|---|---|
| `tenure` | Whole months with the company; supported schema range 0–72 |
| `MonthlyCharges` | Monthly account charge; nonnegative numerical value within the supported schema range |
| `TotalCharges` | Accumulated account charges; nonnegative numerical value within the supported schema range |
| `Partner`, `Dependents` | Recorded household indicators: `Yes` or `No` |
| `PhoneService` | `Yes` or `No` |
| `MultipleLines` | `Yes`, `No`, or `No phone service` |
| `InternetService` | `DSL`, `Fiber optic`, or `No` |
| `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies` | `Yes`, `No`, or `No internet service` |
| `Contract` | `Month-to-month`, `One year`, or `Two year` |
| `PaperlessBilling` | `Yes` or `No` |
| `PaymentMethod` | `Electronic check`, `Mailed check`, `Bank transfer (automatic)`, or `Credit card (automatic)` |

The executable source of truth is `src/churn/schema.py`, also exposed by `GET /api/schema`. Ranges bound the demo's supported input domain; they are not estimates of every telecom company's possible accounts. The interface labels the source's charge fields in dollars; the project performs no currency conversion.

## Preparation rules

- Preserve the raw CSV. Numerical conversion and modelling happen in code.
- Interpret blank `TotalCharges` as zero only for records with `tenure = 0`; record how many values were handled. Reject unexplained missing values.
- Check unique customer IDs and valid target labels before splitting.
- Enforce phone/internet dependency values, finite numerical inputs and known categories.
- Keep all learned preprocessing inside training-fitted pipelines.
- Save partition customer IDs. Only held-out test rows populate the demo customer queue.

The actual dataset checks and class counts are recorded by the training run in `artifacts/summary.json`. See [MODEL_CARD.md](MODEL_CARD.md) for the run used by the app and [VERIFICATION.md](VERIFICATION.md) for checks actually completed.

## Known limits and unsuitable uses

This is a familiar educational benchmark, not evidence for a specific operator, country, current customer population or future month. Service attributes and charges can be correlated with one another and with churn. A random within-sample split does not test temporal drift or cross-company transfer.

Do not enrich this original sample with target-revealing fields such as churn reason/category/status, or silently use another model's churn score as an input. Do not invent customer histories, real identities, geographies, retention outcomes or monetary benefits.

The application processes user uploads locally in memory and does not build an upload database. Use only appropriately authorised data. A local demo has no multi-user access-control or production privacy programme; avoid exposing it to a network as though those features exist.
