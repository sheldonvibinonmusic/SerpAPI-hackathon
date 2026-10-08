"""
trends.py — BharatPrice Pulse
Specialized Google Trends Engine (engine='google_trends').
Gives consumer search-interest and Indian state-level demand insights (geo=IN).
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from app.config.category_drivers import get_driver
from app.config.search_budget import AnalysisBudget
from app.config.settings import get_settings
from app.models.evidence_models import (
    EvidenceSource,
    TrendsDataPoint,
    TrendsEvidence,
    TrendsRegionPoint,
)
from app.models.request_models import NormalizedQuery
from app.processing.query_normalizer import build_cache_key
from app.serpapi.client import get_serpapi_client
from app.utils.datetime_utils import utc_now
from app.utils.security import safe_int

logger = logging.getLogger(__name__)


async def search_google_trends(
    query: NormalizedQuery,
    budget: Optional[AnalysisBudget] = None,
) -> Optional[TrendsEvidence]:
    """Execute Google Trends search for consumer demand signals in India."""
    settings = get_settings()
    client = get_serpapi_client()

    driver = get_driver(query.category)
    if not driver.use_trends:
        logger.info(f"Trends search skipped: not configured for category '{query.category}'")
        return None

    # Trend term: product name or category
    trend_q = query.product_name
    params = {
        "q": trend_q,
        "geo": settings.default_country,  # "IN"
        "data_type": "TIMESERIES",
    }

    cache_key = build_cache_key(
        engine="google_trends",
        query=trend_q,
        city="india",
        language=query.search_language,
    )

    try:
        raw_response = await client.execute(
            engine="google_trends",
            params=params,
            cache_key=cache_key,
            ttl_minutes=settings.cache_ttl_trends_minutes,
            budget=budget,
        )

        now = utc_now()
        timeseries_points: List[TrendsDataPoint] = []
        region_points: List[TrendsRegionPoint] = []

        # Parse interest over time
        iot = raw_response.get("interest_over_time", {})
        timeline_data = iot.get("timeline_data", []) if isinstance(iot, dict) else []
        for pt in timeline_data:
            date_str = pt.get("date", "")
            vals = pt.get("values", [])
            val = vals[0].get("extracted_value", 0) if vals else 0
            timeseries_points.append(TrendsDataPoint(date=date_str, value=safe_int(val) or 0))

        # Parse interest by region (Indian states)
        ibr = raw_response.get("interest_by_region", [])
        if isinstance(ibr, dict):
            region_list = ibr.get("region_data", [])
        elif isinstance(ibr, list):
            region_list = ibr
        else:
            region_list = []

        for reg in region_list:
            reg_name = reg.get("location", "")
            reg_val = reg.get("extracted_value", 0)
            region_points.append(TrendsRegionPoint(location=reg_name, max_value_index=safe_int(reg_val) or 0))

        return TrendsEvidence(
            evidence_id="g_trend_1",
            source=EvidenceSource.GOOGLE_TRENDS,
            retrieved_at=now,
            query=trend_q,
            geo=settings.default_country,
            interest_over_time=timeseries_points,
            interest_by_region=region_points,
        )

    except Exception as e:
        logger.warning(f"Google Trends query failed gracefully: {e}")
        return None
