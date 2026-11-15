param([int]$Port = 5050)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
uv sync --frozen --python 3.12
if ($LASTEXITCODE -ne 0) { throw 'Dependency setup failed.' }
if (-not (Test-Path -LiteralPath 'artifacts\model.joblib')) {
    uv run python scripts/train.py
    if ($LASTEXITCODE -ne 0) { throw 'Model training failed. Review the output above.' }
}
Write-Host "Open http://127.0.0.1:$Port in your browser. Press Ctrl+C here to stop."
uv run python app.py --port $Port
if ($LASTEXITCODE -ne 0) { throw 'Application stopped with an error.' }
