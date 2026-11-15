# Shared application contract

Probabilities/metrics are fractions [0,1]. UI formats percentages. Never hard-code results. Errors: `{"error":"human-readable message"}` with 400/413/503.

## Python interface (ML owner)
- `churn.schema.FIELDS`: list of dicts `{name,label,type,group,options?,min?,max?,step?}`. type = number/category. `validate_customer(record: dict) -> dict` returns validated predictors, raises ValueError for missing/unknown/invalid fields or contradictory services.
- Predictors: tenure, MonthlyCharges, TotalCharges; Partner, Dependents, PhoneService, MultipleLines, InternetService, OnlineSecurity, OnlineBackup, DeviceProtection, TechSupport, StreamingTV, StreamingMovies, Contract, PaperlessBilling, PaymentMethod. Exclude gender/SeniorCitizen, customerID and target.
- `churn.inference.ChurnService(root: pathlib.Path)` loads trusted local artifacts; missing artifacts raise FileNotFoundError. `service.summary` = dict below. `service.customers` = list of held-out rows. `service.predict(record: dict, explain: bool = True) -> dict` validates input and returns prediction below. explain=False omits explanation/suggestions for batches.
- `uv run python scripts/train.py` downloads if needed and saves artifacts/summary.json, customers.json, model.joblib, splits.json and plots/*.png. scripts/download_data.py has bounded HTTPS timeout and GitHub contents API fallback. Additional provenance files allowed. ML tests: tests/test_model.py.

## Browser endpoints (parent owner)
- GET /api/health: `{status:"ready"|"unavailable", model?:string,error?:string}`; unavailable=503.
- GET /api/schema: `{fields:FIELDS,excluded_features:["customerID","Churn","gender","SeniorCitizen"]}`.
- GET /api/summary: summary below.
- GET /api/customers?search=&contract=&risk=&page=1&page_size=10: `{items:[row],total,page,page_size}`. risk=High/Low; contract exact source value; search customerID.
- GET /api/customers/<customer_id>: full row including features; 404 if absent.
- POST /api/predict: JSON predictor values only (no wrapper); returns prediction.
- POST /api/batch: multipart file CSV; predictor columns plus optional customerID. Reject missing/duplicate/unknown columns, bad rows; max 2 MiB/1000 rows. Validate whole file before scoring. Download CSV with customerID,churn_probability,predicted_churn,risk_level. Never persist uploads.
- GET /api/sample.csv: actual held-out customer rows and predictor columns plus customerID.
- GET /plots/<filename>: allowlisted generated PNGs only.

## Summary
```
{
 dataset:{rows,churned,churn_rate,avg_monthly_charges,avg_tenure,source_url,sha256,cleaning},
 splits:{train,validation,test},
 model:{name,threshold,selection_metric,explanation_units},
 test_metrics:{accuracy,precision,recall,f1,roc_auc,average_precision,brier,confusion_matrix:[[tn,fp],[fn,tp]]},
 models:[{name,validation:{metrics},test:{metrics}}],
 segments:[{name:"Contract",values:[{label,count,churn_rate}]}],
 charts:[{name,url:"/plots/filename.png"}],
 global_importance:[{feature,importance}],
 training:{...provenance fields...}
}
```
Identify global importance method/units in training metadata. Extra computed diagnostics allowed.

## Held-out row
`{customer_id,probability,prediction:bool,actual_churn:bool,risk_level:"High"|"Low",features:{predictor values}}`. No invented names. Include all test rows, not just selected successful predictions.

## Prediction
```
{probability,prediction:bool,risk_level:"High"|"Low",threshold,model_name,
 explanation:{base_value,output_value,units:"log-odds"|"probability",contributions:[{feature,value,contribution}],reconstructed_probability,additivity_error},
 suggestions:["Rule-based discussion prompt..."]}
```
Group transformed SHAP contributions into original predictors. Baseline plus all signed contributions equals output_value. Sigmoid output_value gives probability for log-odds. Suggestions are not causal results.
