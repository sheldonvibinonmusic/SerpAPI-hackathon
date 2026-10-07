"""
merchant_ranker.py — BharatPrice Pulse
Ranks discovered local merchants by category relevance and wholesale/distributor status.

CRITICAL: Rating is displayed as a merchant-quality context cue, NOT as an inventory proxy.
Never claim verified physical inventory from Google Local.
"""
from __future__ import annotations

import logging
from typing import List

from app.config.category_drivers import get_driver
from app.models.evidence_models import LocalMerchant
from app.models.request_models import ProductCategory

logger = logging.getLogger(__name__)

# Keywords indicating wholesale or distributor capacity
WHOLESALE_KEYWORDS = [
    "wholesale", "wholesaler", "distributor", "dealer", "mandi",
    "oil mill", "trader", "stockist", "supplier", "depot", "agency"
]


def rank_merchants(
    merchants: List[LocalMerchant],
    category: ProductCategory,
) -> List[LocalMerchant]:
    """Score and sort merchants by relevance to local procurement."""
    driver = get_driver(category)
    driver_types = [t.lower() for t in driver.local_merchant_types]

    for m in merchants:
        score = 0.3  # Base discovery score
        combined_text = f"{m.title} {m.type or ''} {' '.join(m.types)} {m.description or ''}".lower()

        # Check wholesale/distributor keywords
        is_wholesale = any(w in combined_text for w in WHOLESALE_KEYWORDS)
        m.is_wholesaler_or_distributor = is_wholesale
        if is_wholesale:
            score += 0.4

        # Check category-specific merchant types
        if any(dt in combined_text for dt in driver_types):
            score += 0.3

        m.type_relevance_score = min(1.0, round(score, 2))
        m.inventory_claimed = False  # Strictly False

    # Sort: wholesalers first, then by relevance score, then rating
    ranked = sorted(
        merchants,
        key=lambda x: (
            1 if x.is_wholesaler_or_distributor else 0,
            x.type_relevance_score,
            x.rating or 0.0,
            x.reviews or 0,
        ),
        reverse=True,
    )
    return ranked
