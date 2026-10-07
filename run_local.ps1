# PowerShell Launcher for BharatPrice Pulse
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$scriptDir\bharatprice-pulse"

$venvPython = ".\.venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment in .venv..." -ForegroundColor Cyan
    python -m venv .venv
    & $venvPython -m pip install -r requirements.txt
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

Write-Host "Starting BharatPrice Pulse on http://localhost:8000 ..." -ForegroundColor Green
Write-Host "Open http://localhost:8000 in your browser." -ForegroundColor Yellow

& $venvPython -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
