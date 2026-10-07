"""
test_decision.py — BharatPrice Pulse
Tests for deterministic business action state machine.
"""
from app.models.decision_models import (
    ActionCode,
    ExternalSignal,
    FusionResult,
    LocalSourcingSignal,
    MarketMetrics,
    MarketPosition,
    TrendSignal,
    ConfidenceLevel,
)
from app.models.request_models import AnalysisRequest
from app.processing.query_normalizer import normalize_request
from app.services.decision_engine import decide_action


def test_insufficient_data_precedence():
    req = AnalysisRequest(product_raw="Mustard Oil", city_raw="Jaipur", selling_price=175.0)
    norm = normalize_request(req)

    metrics = MarketMetrics(
        total_retrieved=2,
        comparable_count=2,  # < 3
        excluded_count=0,
        seller_price=175.0,
        market_position=MarketPosition.INSUFFICIENT_DATA,
    )
    fusion = FusionResult(
        market_position=MarketPosition.INSUFFICIENT_DATA,
        local_sourcing_signal=LocalSourcingSignal.HIGH,
        trend_signal=TrendSignal.STABLE,
        external_signal=ExternalSignal.LOW_RISK,
        confidence=ConfidenceLevel.LOW,
        confidence_score=20.0,
    )

    action, _ = decide_action(fusion, metrics, norm)
    assert action == ActionCode.INSUFFICIENT_DATA


def test_review_price_when_above_market():
    req = AnalysisRequest(product_raw="Mustard Oil 1L", city_raw="Jaipur", selling_price=175.0)
    norm = normalize_request(req)

    metrics = MarketMetrics(
        total_retrieved=5,
        comparable_count=5,
        excluded_count=0,
        seller_price=175.0,
        price_median=160.0,
        price_gap_percent=9.37,
        market_position=MarketPosition.ABOVE,
    )
    fusion = FusionResult(
        market_position=MarketPosition.ABOVE,
        local_sourcing_signal=LocalSourcingSignal.MEDIUM,
        trend_signal=TrendSignal.STABLE,
        external_signal=ExternalSignal.LOW_RISK,
        confidence=ConfidenceLevel.HIGH,
        confidence_score=80.0,
    )

    action, _ = decide_action(fusion, metrics, norm)
    assert action == ActionCode.REVIEW_PRICE


def test_hold_when_at_market():
    req = AnalysisRequest(product_raw="Mustard Oil 1L", city_raw="Jaipur", selling_price=162.0)
    norm = normalize_request(req)

    metrics = MarketMetrics(
        total_retrieved=5,
        comparable_count=5,
        excluded_count=0,
        seller_price=162.0,
        price_median=160.0,
        price_gap_percent=1.25,
        market_position=MarketPosition.AT_MARKET,
    )
    fusion = FusionResult(
        market_position=MarketPosition.AT_MARKET,
        local_sourcing_signal=LocalSourcingSignal.MEDIUM,
        trend_signal=TrendSignal.STABLE,
        external_signal=ExternalSignal.LOW_RISK,
        confidence=ConfidenceLevel.HIGH,
        confidence_score=85.0,
    )

    action, _ = decide_action(fusion, metrics, norm)
    assert action == ActionCode.HOLD
