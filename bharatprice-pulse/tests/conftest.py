"""
conftest.py — BharatPrice Pulse
Pytest fixtures for unit and integration testing.
Ensures tests run in MOCK MODE without requiring real SerpApi keys or network calls.
"""
import pytest
import os
import sys
from pathlib import Path

# Add project root to sys.path so app is always importable
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Set mock mode before settings import
os.environ["SERPAPI_MOCK_MODE"] = "true"
os.environ["SERPAPI_KEY"] = "mock_test_key"
os.environ["DATABASE_PATH"] = ":memory:"

from app.models.request_models import AnalysisRequest, AnalysisMode, UILanguage
from app.config.settings import get_settings


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Ensure mock mode is active for all tests."""
    monkeypatch.setenv("SERPAPI_MOCK_MODE", "true")
    monkeypatch.setenv("SERPAPI_KEY", "mock_test_key")
    monkeypatch.setenv("DATABASE_PATH", ":memory:")
    settings = get_settings()
    settings.serpapi_mock_mode = True
    settings.serpapi_key = "mock_test_key"
    return settings


@pytest.fixture
def sample_mustard_oil_request():
    return AnalysisRequest(
        product_raw="Fortune Mustard Oil 1L",
        city_raw="Jaipur",
        selling_price=175.0,
        landed_cost=142.0,
        analysis_mode=AnalysisMode.STANDARD,
        ui_language=UILanguage.EN,
    )


@pytest.fixture
def sample_phone_request():
    return AnalysisRequest(
        product_raw="Samsung Galaxy M14 5G 6GB 128GB",
        city_raw="Delhi",
        selling_price=13499.0,
        landed_cost=12100.0,
        analysis_mode=AnalysisMode.STANDARD,
    )
