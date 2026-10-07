"""
trend_processor.py — BharatPrice Pulse
Processes Google Trends evidence.
Computes search-interest direction (rising/stable/falling) and regional peak in India.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.models.evidence_models import TrendsEvidence

logger = logging.getLogger(__name__)


def process_trends_data(trends: Optional[TrendsEvidence]) -> Optional[TrendsEvidence]:
    """Calculate trend direction slope and find peak region in India."""
    if not trends or not trends.interest_over_time:
        return trends

    points = trends.interest_over_time
    recent_vals = [p.value for p in points[-5:]] if len(points) >= 5 else [p.value for p in points]

    if len(recent_vals) >= 2:
        # Simple linear slope calculation
        n = len(recent_vals)
        x_mean = (n - 1) / 2.0
        y_mean = sum(recent_vals) / float(n)

        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(recent_vals))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0.0

        if slope > 1.5:
            trends.trend_direction = "rising"
        elif slope < -1.5:
            trends.trend_direction = "falling"
        else:
            trends.trend_direction = "stable"
    else:
        trends.trend_direction = "stable"

    # Find peak region
    if trends.interest_by_region:
        sorted_regions = sorted(trends.interest_by_region, key=lambda r: r.max_value_index, reverse=True)
        if sorted_regions:
            trends.peak_region = sorted_regions[0].location

    return trends
