"""
account.py — BharatPrice Pulse
SerpApi Account API (GET https://serpapi.com/account.json).
FREE utility — does not count against search credits.
Exposes ONLY safe sanitized telemetry fields (monthly_limit, remaining, hourly).
NEVER exposes the API key or raw account responses.
"""
from __future__ import annotations

import logging
from typing import Dict, Any

import httpx

from app.config.search_budget import get_budget_controller
from app.config.settings import get_settings
from app.models.quota_models import QuotaTelemetry
from app.utils.security import safe_int

logger = logging.getLogger(__name__)


async def get_account_telemetry() -> QuotaTelemetry:
    """Fetch sanitized SerpApi account usage stats or return mock telemetry."""
    settings = get_settings()
    budget_ctrl = get_budget_controller()

    if settings.serpapi_mock_mode or not settings.serpapi_key_is_set:
        return QuotaTelemetry(
            monthly_limit=250,
            monthly_used=12,
            monthly_remaining=238,
            hourly_limit=50,
            hourly_used=budget_ctrl.get_hourly_calls_count(),
            mock_mode=True,
            cache_hit_rate_pct=85.0,
        )

    try:
        url = f"{settings.serpapi_base_url}/account.json?api_key={settings.serpapi_key}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                # Safely extract ONLY public numbers
                monthly_limit = safe_int(data.get("searches_per_month")) or 250
                monthly_used = safe_int(data.get("this_month_usage")) or 0
                remaining = max(0, monthly_limit - monthly_used)
                hourly_limit = safe_int(data.get("hourly_rate_limit")) or 50
                
                return QuotaTelemetry(
                    monthly_limit=monthly_limit,
                    monthly_used=monthly_used,
                    monthly_remaining=remaining,
                    hourly_limit=hourly_limit,
                    hourly_used=budget_ctrl.get_hourly_calls_count(),
                    mock_mode=False,
                    cache_hit_rate_pct=0.0,
                )
            else:
                logger.warning(f"Account API returned status {resp.status_code}")
    except Exception as e:
        logger.warning(f"Account API request failed: {e}")

    # Fallback to local estimation
    return QuotaTelemetry(
        monthly_limit=250,
        monthly_used=0,
        monthly_remaining=250,
        hourly_limit=50,
        hourly_used=budget_ctrl.get_hourly_calls_count(),
        mock_mode=settings.serpapi_mock_mode,
        cache_hit_rate_pct=0.0,
    )
