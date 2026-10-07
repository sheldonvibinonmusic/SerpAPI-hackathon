"""
quota.py — BharatPrice Pulse
GET /api/quota endpoint for safe SerpApi usage telemetry.
Never exposes secret keys or raw Account API responses.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter

from app.models.quota_models import QuotaTelemetry
from app.serpapi.account import get_account_telemetry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Quota"])


@router.get(
    "/quota",
    response_model=QuotaTelemetry,
    summary="Get SerpApi Quota Telemetry",
    description="Returns public safe usage telemetry for dashboard header display.",
)
async def get_quota() -> QuotaTelemetry:
    """Return sanitized SerpApi credit monitoring metrics."""
    return await get_account_telemetry()
