#!/bin/bash
set -e

echo "==================================================="
echo "BharatPrice Pulse - Local Unix Launcher"
echo "==================================================="

# Copy .env if missing
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Setup venv if missing
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting BharatPrice Pulse on http://localhost:8000 ..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
