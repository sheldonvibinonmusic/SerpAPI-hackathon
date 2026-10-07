"""
test_trends.py — BharatPrice Pulse
Tests for Google Trends slope calculation and regional peak identification.
"""
from datetime import datetime
from app.models.evidence_models import TrendsEvidence, TrendsDataPoint, TrendsRegionPoint, EvidenceSource
from app.processing.trend_processor import process_trends_data
from app.utils.datetime_utils import utc_now


def test_rising_trend_slope():
    now = utc_now()
    points = [
        TrendsDataPoint(date="W1", value=40),
        TrendsDataPoint(date="W2", value=55),
        TrendsDataPoint(date="W3", value=70),
        TrendsDataPoint(date="W4", value=88),
    ]
    regions = [
        TrendsRegionPoint(location="Rajasthan", max_value_index=100),
        TrendsRegionPoint(location="Maharashtra", max_value_index=75),
    ]

    trends = TrendsEvidence(
        evidence_id="tr_1",
        source=EvidenceSource.GOOGLE_TRENDS,
        retrieved_at=now,
        query="mustard oil",
        interest_over_time=points,
        interest_by_region=regions,
    )

    processed = process_trends_data(trends)
    assert processed.trend_direction == "rising"
    assert processed.peak_region == "Rajasthan"


def test_stable_trend_slope():
    now = utc_now()
    points = [
        TrendsDataPoint(date="W1", value=60),
        TrendsDataPoint(date="W2", value=61),
        TrendsDataPoint(date="W3", value=59),
        TrendsDataPoint(date="W4", value=60),
    ]

    trends = TrendsEvidence(
        evidence_id="tr_2",
        source=EvidenceSource.GOOGLE_TRENDS,
        retrieved_at=now,
        query="mustard oil",
        interest_over_time=points,
    )

    processed = process_trends_data(trends)
    assert processed.trend_direction == "stable"
