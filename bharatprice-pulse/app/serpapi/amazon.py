"""
amazon.py — BharatPrice Pulse
Amazon India Search Engine (engine='amazon', amazon_domain='amazon.in').
Optional marketplace benchmark for electronics, FMCG, and packaged goods.
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

logger = logging.getLogger(__name__)


async def search_amazon_in(
    query: NormalizedQuery,
    budget: Optional[AnalysisBudget] = None,
) -> List[ShoppingItem]:
    """Execute Amazon India search for e-commerce benchmark."""
    settings = get_settings()
    client = get_serpapi_client()

    params = {
        "k": query.search_query,
        "amazon_domain": "amazon.in",
    }

    cache_key = build_cache_key(
        engine="amazon",
        query=query.search_query,
        city="india",
        language=query.search_language,
    )

    try:
        raw_response = await client.execute(
            engine="amazon",
            params=params,
            cache_key=cache_key,
            ttl_minutes=settings.cache_ttl_shopping_minutes,
            budget=budget,
        )

        items: List[ShoppingItem] = []
        organic_results = raw_response.get("organic_results", [])
        now = utc_now()

        for idx, item in enumerate(organic_results[:8]):
            price_val = None
            price_obj = item.get("price")
            if isinstance(price_obj, dict):
                price_val = price_obj.get("value")
            elif isinstance(price_obj, (int, float)):
                price_val = float(price_obj)

            items.append(
                ShoppingItem(
                    evidence_id=f"amz_{idx+1}",
                    source=EvidenceSource.AMAZON_SEARCH,
                    retrieved_at=now,
                    title=item.get("title", ""),
                    source_name="Amazon India",
                    product_link=item.get("link"),
                    product_id=item.get("asin"),
                    price_inr=float(price_val) if price_val else None,
                    rating=float(item["rating"]) if item.get("rating") is not None else None,
                    reviews=int(item["reviews"]) if item.get("reviews") is not None else None,
                )
            )
        return items
    except Exception as e:
        logger.warning(f"Amazon search failed: {e}")
        return []
