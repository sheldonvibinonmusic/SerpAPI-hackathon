"""
local.py — BharatPrice Pulse
Specialized Google Local Engine (engine='google_local').
Discovers nearby merchants, wholesalers, distributors and shopkeepers.
CRITICAL RULE: Never claim verified inventory from Google Local.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from app.config.category_drivers import get_driver
from app.config.search_budget import AnalysisBudget
from app.config.settings import get_settings
from app.models.evidence_models import EvidenceSource, LocalMerchant
from app.models.request_models import NormalizedQuery
from app.processing.query_normalizer import build_cache_key
from app.serpapi.client import get_serpapi_client
from app.utils.datetime_utils import utc_now
from app.utils.security import safe_float, safe_int

logger = logging.getLogger(__name__)


async def search_google_local(
    query: NormalizedQuery,
    budget: Optional[AnalysisBudget] = None,
) -> List[LocalMerchant]:
    """Execute Google Local search to discover relevant local merchants/wholesalers."""
    settings = get_settings()
    client = get_serpapi_client()

    driver = get_driver(query.category)
    search_q = driver.local_search_template.format(
        product=query.product_name,
        city=query.city,
    )

    params = {
        "q": search_q,
        "location": query.location_string,
        "gl": settings.default_gl,
        "hl": query.search_language,
    }

    cache_key = build_cache_key(
        engine="google_local",
        query=search_q,
        city=query.city,
        language=query.search_language,
    )

    raw_response = await client.execute(
        engine="google_local",
        params=params,
        cache_key=cache_key,
        ttl_minutes=settings.cache_ttl_local_minutes,
        budget=budget,
    )

    merchants: List[LocalMerchant] = []
    local_results = raw_response.get("local_results", [])
    now = utc_now()

    for idx, place in enumerate(local_results):
        coords = None
        if "gps_coordinates" in place:
            gps = place["gps_coordinates"]
            coords = {"lat": float(gps.get("latitude", 0)), "lng": float(gps.get("longitude", 0))}

        types_list = place.get("types", [])
        if not types_list and place.get("type"):
            types_list = [place["type"]]

        merchants.append(
            LocalMerchant(
                evidence_id=f"g_local_{idx+1}",
                source=EvidenceSource.GOOGLE_LOCAL,
                retrieved_at=now,
                title=place.get("title", ""),
                place_id=place.get("place_id"),
                data_id=place.get("data_id"),
                address=place.get("address"),
                phone=place.get("phone"),
                coordinates=coords,
                type=place.get("type"),
                types=types_list,
                description=place.get("description"),
                is_open=place.get("open_now") or (place.get("hours").get("open_now") if isinstance(place.get("hours"), dict) else None),
                hours=place.get("hours"),
                rating=safe_float(place.get("rating")),
                reviews=safe_int(place.get("reviews")),
                price_level=place.get("price"),
                inventory_claimed=False,  # Enforce guardrail: never claim inventory
            )
        )

    logger.info(f"Google Local returned {len(merchants)} merchants for '{search_q}'")
    return merchants
