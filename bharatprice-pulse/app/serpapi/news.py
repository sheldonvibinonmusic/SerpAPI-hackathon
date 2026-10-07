"""
news.py — BharatPrice Pulse
Specialized Google News Engine (engine='google_news').
Captures current supply shocks, import duty changes, crop developments, and category disruptions.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from app.config.category_drivers import get_driver
from app.config.search_budget import AnalysisBudget
from app.config.settings import get_settings
from app.models.evidence_models import EvidenceSource, NewsArticle
from app.models.request_models import NormalizedQuery
from app.processing.query_normalizer import build_cache_key
from app.serpapi.client import get_serpapi_client
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


async def search_google_news(
    query: NormalizedQuery,
    budget: Optional[AnalysisBudget] = None,
) -> List[NewsArticle]:
    """Execute Google News search for category and product market events."""
    settings = get_settings()
    client = get_serpapi_client()

    driver = get_driver(query.category)
    # Formulate relevant news search query with product context + India
    category_terms = " ".join(driver.news_keywords[:3]) if driver.news_keywords else "price supply"
    search_q = f"{query.product_name} {category_terms} India"

    params = {
        "q": search_q,
        "gl": settings.default_gl,
        "hl": query.search_language,
    }

    cache_key = build_cache_key(
        engine="google_news",
        query=search_q,
        city=query.city,
        language=query.search_language,
    )

    raw_response = await client.execute(
        engine="google_news",
        params=params,
        cache_key=cache_key,
        ttl_minutes=settings.cache_ttl_news_minutes,
        budget=budget,
    )

    articles: List[NewsArticle] = []
    news_results = raw_response.get("news_results", [])
    now = utc_now()

    for idx, item in enumerate(news_results):
        source_name = item.get("source", {}).get("name") if isinstance(item.get("source"), dict) else item.get("source")
        articles.append(
            NewsArticle(
                evidence_id=f"g_news_{idx+1}",
                source=EvidenceSource.GOOGLE_NEWS,
                retrieved_at=now,
                title=item.get("title", ""),
                snippet=item.get("snippet"),
                source_name=source_name,
                link=item.get("link"),
                published_date=item.get("date"),
            )
        )

    logger.info(f"Google News returned {len(articles)} articles for '{search_q}'")
    return articles
