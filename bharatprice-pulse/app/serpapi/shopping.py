"""
shopping.py — BharatPrice Pulse
Specialized Google Shopping engine (engine='google_shopping').
Provides structured e-commerce competitor listings with product links, prices, and seller metadata.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from app.config.search_budget import AnalysisBudget
from app.config.settings import get_settings
from app.models.evidence_models import EvidenceSource, ShoppingItem
from app.models.request_models import NormalizedQuery
from app.processing.query_normalizer import build_cache_key
from app.serpapi.client import get_serpapi_client
from app.utils.datetime_utils import utc_now
from app.utils.security import safe_float, safe_int

logger = logging.getLogger(__name__)


async def search_google_shopping(
    query: NormalizedQuery,
    budget: Optional[AnalysisBudget] = None,
) -> List[ShoppingItem]:
    """Execute specialized Google Shopping search and extract structured items."""
    settings = get_settings()
    client = get_serpapi_client()

    params = {
        "q": query.search_query,
        "location": query.location_string,
        "gl": settings.default_gl,
        "hl": query.search_language,
        "direct_link": True,
    }

    cache_key = build_cache_key(
        engine="google_shopping",
        query=query.search_query,
        city=query.city,
        language=query.search_language,
    )

    raw_response = await client.execute(
        engine="google_shopping",
        params=params,
        cache_key=cache_key,
        ttl_minutes=settings.cache_ttl_shopping_minutes,
        budget=budget,
    )

    items: List[ShoppingItem] = []
    shopping_results = raw_response.get("shopping_results", [])
    now = utc_now()

    for idx, item in enumerate(shopping_results):
        raw_price = item.get("price")
        extracted_price = safe_float(item.get("extracted_price"))
        if extracted_price is None and raw_price:
            extracted_price = safe_float(raw_price)

        old_price = item.get("old_price")
        extracted_old_price = safe_float(old_price)

        items.append(
            ShoppingItem(
                evidence_id=f"g_shop_{idx+1}",
                source=EvidenceSource.GOOGLE_SHOPPING,
                retrieved_at=now,
                title=item.get("title", ""),
                source_name=item.get("source"),
                product_link=item.get("link"),
                product_id=item.get("product_id"),
                price_raw=str(raw_price) if raw_price is not None else None,
                price_inr=extracted_price,
                old_price_inr=extracted_old_price,
                delivery_info=item.get("delivery"),
                on_sale=bool(extracted_old_price and extracted_price and extracted_price < extracted_old_price),
                rating=safe_float(item.get("rating")),
                reviews=safe_int(item.get("reviews")),
                is_small_business=bool(item.get("badges", {}).get("small_business")),
            )
        )

    logger.info(f"Google Shopping returned {len(items)} items for '{query.search_query}'")
    return items
