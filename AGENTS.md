# Project working rules

- Work only in this project; preserve neighbouring repositories.
- Use PowerShell, `uv sync --frozen`, and `uv run` with the locked environment.
- Keep Python simple, typed and documented so a student can explain it in a viva.
- Never invent data, metrics, plots or completed checks. Run evidence lives in `artifacts/`.
- Read `docs/ASSUMPTIONS.md` and `docs/API_CONTRACT.md` before changing behaviour.
- Keep preprocessing in the fitted pipeline. Never tune with test labels or refit after choosing the validation threshold.
- If model/schema/training source changes, rerun `uv run python scripts/train.py` so source hashes match; restart the app afterward.
- Run `uv run pytest -q`, `uv run ruff check .`, and `node --check static/app.js` after relevant changes. For UI changes run `uv run python scripts/browser_check.py` against the local server.
- Keep uploads in memory. Never load untrusted model files. Public hosting requires a separate production review.
