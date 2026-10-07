"""
news_processor.py — BharatPrice Pulse
Processes retrieved news articles, evaluates category relevance, and classifies signal direction.

Direction classes:
- cost_pressure: import duty hike, commodity surge, fuel cost rise
- supply_pressure: crop shortfall, export ban, strike, factory shutdown
- demand_boost: festival buying, government procurement, subsidy
- regulatory: GST revision, packaging law, compliance deadline
- neutral: general news
"""
from __future__ import annotations

import logging
import re
from typing import List

from app.config.category_drivers import get_driver
from app.models.evidence_models import NewsArticle
from app.models.request_models import ProductCategory

logger = logging.getLogger(__name__)

# Keyword dictionaries for signal classification
PRESSURE_KEYWORDS = {
    "cost_pressure": [
        "tariff", "duty hike", "import duty", "inflation", "price hike",
        "rupee falls", "crude surge", "freight rates", "transport cost"
    ],
    "supply_pressure": [
        "shortage", "scarcity", "crop damage", "drought", "flood", "unseasonal rain",
        "export ban", "strike", "disruption", "plant shutdown", "deficit"
    ],
    "demand_boost": [
        "surge in demand", "festival demand", "wedding season", "diwali rush",
        "procurement drive", "msp hike", "consumption grows"
    ],
    "regulatory": [
        "gst council", "cbic notification", "fssai", "bis standard",
        "compliance", "maximum retail price", "mrp rule"
    ],
}


def process_news_articles(
    articles: List[NewsArticle],
    category: ProductCategory,
    product_name: str,
) -> List[NewsArticle]:
    """Score relevance and classify direction for news articles."""
    driver = get_driver(category)
    cat_keywords = [k.lower() for k in driver.news_keywords]
    prod_tokens = set(re.findall(r'\b\w{3,}\b', product_name.lower()))

    processed: List[NewsArticle] = []

    for art in articles:
        text = f"{art.title} {art.snippet or ''}".lower()
        score = 0.2  # Base score for coming from localized query

        # Product token overlap
        if any(token in text for token in prod_tokens):
            score += 0.4

        # Category keyword overlap
        if any(kw in text for kw in cat_keywords):
            score += 0.3

        # Classify direction
        direction = "neutral"
        for dir_name, kw_list in PRESSURE_KEYWORDS.items():
            if any(kw in text for kw in kw_list):
                direction = dir_name
                score += 0.1
                break

        art.relevance_score = min(1.0, round(score, 2))
        art.signal_direction = direction
        art.classified_by = "deterministic_keyword_heuristic"
        processed.append(art)

    # Sort by relevance score
    processed.sort(key=lambda x: x.relevance_score, reverse=True)
    return processed
