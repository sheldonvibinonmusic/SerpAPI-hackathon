"""
product.py — BharatPrice Pulse
Google Product Engine (engine='google_product').
Optional Deep Check enrichment for detailed specs, sellers, and observed price history.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.config.search_budget import AnalysisBudget
from app.config.settings import get_settings
from app.serpapi.client import get_serpapi_client

logger = logging.getLogger(__name__)


async def get_google_product_details(
    product_id: str,
    budget: Optional[AnalysisBudget] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieve deep product page data including store offers and reviews."""
    settings = get_settings()
    client = get_serpapi_client()

    params = {
        "product_id": product_id,
        "gl": settings.default_gl,
        "hl": settings.default_hl,
    }

    cache_key = f"prod_{product_id}"

    try:
        raw_response = await client.execute(
            engine="google_product",
            params=params,
            cache_key=cache_key,
            ttl_minutes=180,
            budget=budget,
        )
        return raw_response
    except Exception as e:
        logger.warning(f"Google Product enrichment failed: {e}")
        return None
