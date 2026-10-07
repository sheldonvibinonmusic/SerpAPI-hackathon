"""
maps_reviews.py — BharatPrice Pulse
Google Maps Reviews Engine (engine='google_maps_reviews').
Provides customer reviews for a selected local merchant in Deep Check mode.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.config.search_budget import AnalysisBudget
from app.config.settings import get_settings
from app.serpapi.client import get_serpapi_client

logger = logging.getLogger(__name__)


async def get_merchant_reviews(
    data_id: Optional[str] = None,
    place_id: Optional[str] = None,
    budget: Optional[AnalysisBudget] = None,
) -> List[Dict[str, Any]]:
    """Retrieve Google Maps reviews for deep verification of a local wholesaler."""
    settings = get_settings()
    client = get_serpapi_client()

    params: Dict[str, Any] = {"hl": settings.default_hl}
    if data_id:
        params["data_id"] = data_id
    elif place_id:
        params["place_id"] = place_id
    else:
        return []

    cache_key = f"reviews_{data_id or place_id}"

    try:
        raw_response = await client.execute(
            engine="google_maps_reviews",
            params=params,
            cache_key=cache_key,
            ttl_minutes=360,
            budget=budget,
        )
        return raw_response.get("reviews", [])
    except Exception as e:
        logger.warning(f"Maps reviews query failed: {e}")
        return []
