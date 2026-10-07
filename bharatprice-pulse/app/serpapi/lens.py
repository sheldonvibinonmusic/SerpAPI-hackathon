"""
lens.py — BharatPrice Pulse
Google Lens Engine (engine='google_lens').
Uses image_id or image_url to identify products from photo uploads.
CRITICAL: in_stock from Lens is strictly an online listing signal, NEVER physical inventory.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from app.config.search_budget import AnalysisBudget
from app.config.settings import get_settings
from app.models.evidence_models import EvidenceSource, ShoppingItem
from app.serpapi.client import get_serpapi_client
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


async def search_google_lens(
    image_id: str,
    budget: Optional[AnalysisBudget] = None,
) -> List[ShoppingItem]:
    """Execute Google Lens product recognition."""
    settings = get_settings()
    client = get_serpapi_client()

    params = {
        "image_id": image_id,
        "hl": settings.default_hl,
        "country": settings.default_country,
    }

    cache_key = f"lens_{image_id}"

    try:
        raw_response = await client.execute(
            engine="google_lens",
            params=params,
            cache_key=cache_key,
            ttl_minutes=120,
            budget=budget,
        )

        items: List[ShoppingItem] = []
        visual_matches = raw_response.get("visual_matches", [])
        now = utc_now()

        for idx, match in enumerate(visual_matches[:6]):
            price_info = match.get("price", {})
            extracted_price = price_info.get("extracted_value") if isinstance(price_info, dict) else None

            items.append(
                ShoppingItem(
                    evidence_id=f"lens_{idx+1}",
                    source=EvidenceSource.GOOGLE_LENS,
                    retrieved_at=now,
                    title=match.get("title", ""),
                    source_name=match.get("source"),
                    product_link=match.get("link"),
                    price_inr=float(extracted_price) if extracted_price else None,
                    rating=match.get("rating"),
                    reviews=match.get("reviews"),
                )
            )
        return items
    except Exception as e:
        logger.warning(f"Lens search failed: {e}")
        return []
