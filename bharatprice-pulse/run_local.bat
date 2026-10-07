@echo off
echo ===================================================
echo BharatPrice Pulse - Local Windows Launcher
echo ===================================================

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b 1
)

REM Copy .env if missing
if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
)

REM Setup venv if missing
if exist .venv (
    call .venv\Scripts\activate
) else if exist venv (
    call venv\Scripts\activate
) else (
    echo Creating virtual environment...
    python -m venv .venv
    call .venv\Scripts\activate
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Start FastAPI application
echo Starting BharatPrice Pulse on http://localhost:8000 ...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
