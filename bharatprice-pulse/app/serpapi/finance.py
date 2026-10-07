"""
finance.py — BharatPrice Pulse
Specialized Google Finance Engine (engine='google_finance').
Used selectively for verified instruments (e.g. USD/INR for electronics).
NEVER called blindly for categories without a validated instrument.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from app.config.category_drivers import get_driver
from app.config.search_budget import AnalysisBudget
from app.config.settings import get_settings
from app.models.evidence_models import EvidenceSource, FinanceSignal
from app.models.request_models import NormalizedQuery
from app.processing.query_normalizer import build_cache_key
from app.serpapi.client import get_serpapi_client
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


async def search_google_finance(
    query: NormalizedQuery,
    budget: Optional[AnalysisBudget] = None,
) -> Optional[FinanceSignal]:
    """Execute Google Finance query if category warrants it (e.g. USD/INR)."""
    settings = get_settings()
    client = get_serpapi_client()

    driver = get_driver(query.category)
    if not driver.use_finance or not driver.finance_instrument:
        logger.info(f"Finance search skipped: not relevant for category '{query.category}'")
        return None

    instrument = driver.finance_instrument
    params = {
        "q": instrument,
        "hl": query.search_language,
    }

    cache_key = build_cache_key(
        engine="google_finance",
        query=instrument,
        city="all",
        language=query.search_language,
    )

    try:
        raw_response = await client.execute(
            engine="google_finance",
            params=params,
            cache_key=cache_key,
            ttl_minutes=settings.cache_ttl_finance_minutes,
            budget=budget,
        )

        # Parse finance metrics safely
        summary = raw_response.get("summary", {})
        price_val = summary.get("price")
        change_val = summary.get("price_movement", {}).get("value")
        change_pct = summary.get("price_movement", {}).get("percentage")

        if price_val is None:
            # Alternate format
            markets = raw_response.get("markets", {})
            currencies = markets.get("currencies", [])
            for c in currencies:
                if instrument in c.get("name", "") or instrument in c.get("ticker", ""):
                    price_val = c.get("price")
                    change_pct = c.get("price_movement", {}).get("percentage")
                    break

        now = utc_now()
        return FinanceSignal(
            evidence_id="g_fin_1",
            source=EvidenceSource.GOOGLE_FINANCE,
            retrieved_at=now,
            instrument=instrument,
            instrument_label=driver.finance_instrument_label or instrument,
            current_value=float(price_val) if price_val is not None else None,
            change_value=float(change_val) if change_val is not None else None,
            change_percent=float(change_pct) if change_pct is not None else None,
            relevance="high" if query.category.value == "electronics_mobiles" else "medium",
            interpretation=driver.why_finance_relevant,
        )

    except Exception as e:
        logger.warning(f"Google Finance query failed gracefully: {e}")
        return None
