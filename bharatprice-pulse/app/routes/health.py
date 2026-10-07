"""
health.py — BharatPrice Pulse
GET /api/health endpoint for Docker container and uptime healthchecks.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

from app.config.settings import get_settings
from app.utils.datetime_utils import utc_now

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health", summary="Service Healthcheck")
async def health_check() -> Dict[str, Any]:
    """Check API server, settings, and mock mode configuration."""
    settings = get_settings()
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "mock_mode": settings.serpapi_mock_mode,
        "serpapi_key_configured": settings.serpapi_key_is_set,
        "llm_available": settings.llm_is_available,
        "timestamp": utc_now().isoformat(),
    }
