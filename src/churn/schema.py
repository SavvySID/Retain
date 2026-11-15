"""One predictor schema shared by training, forms, JSON and CSV validation."""

import math
from typing import Any

NUMERIC = ["tenure", "MonthlyCharges", "TotalCharges"]
INTERNET_EXTRAS = ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"]
FIELDS: list[dict[str, Any]] = [
    {"name": "tenure", "label": "Tenure (months)", "type": "number", "group": "Account", "min": 0, "max": 72, "step": 1},
    {"name": "MonthlyCharges", "label": "Monthly charges ($)", "type": "number", "group": "Account", "min": 0, "max": 200, "step": 0.01},
    {"name": "TotalCharges", "label": "Total charges ($)", "type": "number", "group": "Account", "min": 0, "max": 15000, "step": 0.01},
]


def _category(name: str, label: str, options: list[str], group: str) -> dict[str, Any]:
    """Describe a categorical field without duplicating validation rules."""
    return {"name": name, "label": label, "type": "category", "options": options, "group": group}


FIELDS.extend([
    _category("Partner", "Partner", ["Yes", "No"], "Household"),
    _category("Dependents", "Dependents", ["Yes", "No"], "Household"),
    _category("PhoneService", "Phone service", ["Yes", "No"], "Services"),
    _category("MultipleLines", "Multiple lines", ["Yes", "No", "No phone service"], "Services"),
    _category("InternetService", "Internet service", ["DSL", "Fiber optic", "No"], "Services"),
    *[_category(name, label, ["Yes", "No", "No internet service"], "Services") for name, label in zip(
        INTERNET_EXTRAS, ["Online security", "Online backup", "Device protection", "Technical support", "Streaming TV", "Streaming movies"]
    )],
    _category("Contract", "Contract", ["Month-to-month", "One year", "Two year"], "Billing"),
    _category("PaperlessBilling", "Paperless billing", ["Yes", "No"], "Billing"),
    _category("PaymentMethod", "Payment method", ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"], "Billing"),
])
FEATURE_NAMES = [field["name"] for field in FIELDS]
CATEGORICAL = [name for name in FEATURE_NAMES if name not in NUMERIC]


def validate_customer(record: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize a customer; reject unknown values and contradictory services."""
    if not isinstance(record, dict):
        raise ValueError("Customer must be an object containing predictor fields.")  # noqa: TRY004
    unknown = set(record) - set(FEATURE_NAMES)
    missing = set(FEATURE_NAMES) - set(record)
    if unknown:
        raise ValueError(f"Unknown fields: {', '.join(sorted(map(str, unknown)))}.")
    if missing:
        raise ValueError(f"Missing fields: {', '.join(sorted(missing))}.")
    result: dict[str, Any] = {}
    for field in FIELDS:
        name, value = field["name"], record[field["name"]]
        if field["type"] == "number":
            if isinstance(value, bool) or value is None:
                raise ValueError(f"{name} must be a finite number.")
            try:
                number = float(value)
            except (TypeError, ValueError, OverflowError):
                raise ValueError(f"{name} must be a finite number.") from None
            if not math.isfinite(number) or not field["min"] <= number <= field["max"]:
                raise ValueError(f"{name} must be between {field['min']} and {field['max']}.")
            if name == "tenure" and not number.is_integer():
                raise ValueError("tenure must be a whole number of months.")
            result[name] = int(number) if name == "tenure" else number
        else:
            if not isinstance(value, str) or value.strip() not in field["options"]:
                raise ValueError(f"{name} must be one of: {', '.join(field['options'])}.")
            result[name] = value.strip()
    no_phone = result["PhoneService"] == "No"
    if no_phone != (result["MultipleLines"] == "No phone service"):
        raise ValueError("MultipleLines must agree with PhoneService (use 'No phone service' when absent).")
    no_internet = result["InternetService"] == "No"
    if any(no_internet != (result[name] == "No internet service") for name in INTERNET_EXTRAS):
        raise ValueError("InternetService and internet add-ons must agree (use 'No internet service' when absent).")
    return result
