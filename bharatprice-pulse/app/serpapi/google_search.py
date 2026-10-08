"""
google_search.py — BharatPrice Pulse
Google Search Evidence Hub Engine (engine='google').
Retrieves broad multi-block evidence in ONE search credit:
- organic results
- inline shopping results
- local results (local pack)
- top stories / news results
- knowledge graph
- related questions
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config.search_budget import AnalysisBudget
from app.config.settings import get_settings
from app.models.evidence_models import (
    EvidenceSource,
    LocalMerchant,
    NewsArticle,
    ShoppingItem,
)
from app.models.request_models import NormalizedQuery
from app.processing.query_normalizer import build_cache_key
from app.serpapi.client import get_serpapi_client
from app.utils.datetime_utils import utc_now
from app.utils.security import safe_float, safe_int

logger = logging.getLogger(__name__)


class SearchHubResult:
    """Multi-block evidence bundle extracted from a single Google Search."""
    def __init__(self):
        self.raw_data: Dict[str, Any] = {}
        self.shopping_items: List[ShoppingItem] = []
        self.local_merchants: List[LocalMerchant] = []
        self.news_articles: List[NewsArticle] = []
        self.knowledge_graph: Optional[Dict[str, Any]] = None
        self.related_questions: List[str] = []


async def search_google_hub(
    query: NormalizedQuery,
    budget: Optional[AnalysisBudget] = None,
) -> SearchHubResult:
    """Execute the Google Search Hub search and parse structured blocks."""
    settings = get_settings()
    client = get_serpapi_client()

    params = {
        "q": query.search_query,
        "location": query.location_string,
        "gl": settings.default_gl,
        "hl": query.search_language,
    }

    cache_key = build_cache_key(
        engine="google",
        query=query.search_query,
        city=query.city,
        language=query.search_language,
    )

    raw_response = await client.execute(
        engine="google",
        params=params,
        cache_key=cache_key,
        ttl_minutes=settings.cache_ttl_search_hub_minutes,
        budget=budget,
    )

    result = SearchHubResult()
    result.raw_data = raw_response
    now = utc_now()

    # 1. Parse inline shopping results if present
    inline_shopping = raw_response.get("shopping_results", [])
    for idx, item in enumerate(inline_shopping):
        raw_price = item.get("price")
        extracted_price = safe_float(item.get("extracted_price"))
        if extracted_price is None and raw_price:
            extracted_price = safe_float(raw_price)

        result.shopping_items.append(
            ShoppingItem(
                evidence_id=f"hub_shop_{idx+1}",
                source=EvidenceSource.GOOGLE_SEARCH_HUB,
                retrieved_at=now,
                title=item.get("title", ""),
                source_name=item.get("source"),
                product_link=item.get("link"),
                price_raw=str(raw_price) if raw_price is not None else None,
                price_inr=extracted_price,
                rating=safe_float(item.get("rating")),
                reviews=safe_int(item.get("reviews")),
            )
        )

    # 2. Parse local pack results if present
    local_results = raw_response.get("local_results", {})
    if isinstance(local_results, list):
        places = local_results
    elif isinstance(local_results, dict):
        places = local_results.get("places", [])
    else:
        places = []

    for idx, place in enumerate(places):
        result.local_merchants.append(
            LocalMerchant(
                evidence_id=f"hub_local_{idx+1}",
                source=EvidenceSource.GOOGLE_SEARCH_HUB,
                retrieved_at=now,
                title=place.get("title", ""),
                place_id=place.get("place_id"),
                data_id=place.get("data_id"),
                address=place.get("address"),
                phone=place.get("phone"),
                type=place.get("type"),
                rating=safe_float(place.get("rating")),
                reviews=safe_int(place.get("reviews")),
                is_open=place.get("open_now"),
                inventory_claimed=False,
            )
        )

    top_stories = raw_response.get("top_stories", []) or raw_response.get("news_results", [])
    for idx, story in enumerate(top_stories):
        src = story.get("source")
        src_name = src.get("name") if isinstance(src, dict) else (str(src) if src is not None else None)
        result.news_articles.append(
            NewsArticle(
                evidence_id=f"hub_news_{idx+1}",
                source=EvidenceSource.GOOGLE_SEARCH_HUB,
                retrieved_at=now,
                title=story.get("title", ""),
                snippet=story.get("snippet"),
                source_name=src_name,
                link=story.get("link"),
                published_date=story.get("date"),
            )
        )

    # 4. Knowledge graph
    result.knowledge_graph = raw_response.get("knowledge_graph")

    # 5. Related questions
    for q in raw_response.get("related_questions", []):
        if "question" in q:
            result.related_questions.append(q["question"])

    return result
