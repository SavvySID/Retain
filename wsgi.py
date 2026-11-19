"""Expose the same trained Flask application to Vercel's Python runtime."""

from app import create_app

app = create_app()
if app.extensions.get("churn_service") is None:
    raise RuntimeError("Model unavailable. Run the build check and include the verified artifacts before deploying.")
