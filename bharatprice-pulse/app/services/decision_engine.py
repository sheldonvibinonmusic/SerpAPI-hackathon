"""
decision_engine.py — BharatPrice Pulse
Deterministic business action state machine.

Precedence order:
1. Data Sufficiency (< MIN_COMPARABLE_ITEMS → INSUFFICIENT_DATA)
2. Market Position (WELL_ABOVE / ABOVE / AT_MARKET / BELOW / WELL_BELOW)
3. Seller Margin (if landed cost was supplied)
4. Local Sourcing Opportunity
5. External Signals & Consumer Demand
"""
from __future__ import annotations

import logging
from typing import Tuple

from app.models.decision_models import (
    ActionCode,
    ExternalSignal,
    FusionResult,
    LocalSourcingSignal,
    MarketMetrics,
    MarketPosition,
    TrendSignal,
)
from app.models.request_models import NormalizedQuery

logger = logging.getLogger(__name__)


def decide_action(
    fusion: FusionResult,
    metrics: MarketMetrics,
    query: NormalizedQuery,
) -> Tuple[ActionCode, str]:
    """Determine the recommended business action using transparent deterministic rules."""
    # 1. Precedence 1: Data Sufficiency Check
    if metrics.comparable_count < 3 or metrics.market_position == MarketPosition.INSUFFICIENT_DATA:
        return (
            ActionCode.INSUFFICIENT_DATA,
            "Insufficient Market Data — Review Manually",
        )

    pos = metrics.market_position
    margin = metrics.gross_margin_percent
    local = fusion.local_sourcing_signal
    external = fusion.external_signal
    trend = fusion.trend_signal

    # 2. Position: WELL_ABOVE (> 15% above median)
    if pos == MarketPosition.WELL_ABOVE:
        if margin is not None and margin < 8.0:
            # High price but low margin indicates severe procurement cost issue!
            if local in (LocalSourcingSignal.HIGH, LocalSourcingSignal.MEDIUM):
                return (
                    ActionCode.SOURCE_LOCALLY,
                    "Source Locally — High Shelf Price With Compressed Margin",
                )
            return (
                ActionCode.REVIEW_PRICE,
                "Review Price — High Price With Thin Margins",
            )
        return (
            ActionCode.CONSIDER_REPRICE_DOWN,
            "Consider Repricing Down — Significantly Above Online Competitors",
        )

    # 3. Position: ABOVE (5% to 15% above median)
    if pos == MarketPosition.ABOVE:
        if external in (ExternalSignal.HIGH_RISK, ExternalSignal.COST_PRESSURE):
            # Market might catch up due to input cost pressure
            return (
                ActionCode.HOLD,
                "Hold Current Price — Above Median But Input Costs Rising",
            )
        return (
            ActionCode.REVIEW_PRICE,
            "Review Price — Moderately Above Observed Market Range",
        )

    # 4. Position: AT_MARKET (within ±5% of median)
    if pos == MarketPosition.AT_MARKET:
        if local == LocalSourcingSignal.HIGH and (margin is None or margin < 12.0):
            return (
                ActionCode.SOURCE_LOCALLY,
                "Source Locally — Competitive Retail Price, Explore Better Wholesale Deals",
            )
        if external in (ExternalSignal.HIGH_RISK, ExternalSignal.COST_PRESSURE):
            return (
                ActionCode.WATCH,
                "Watch Market Closely — Pricing Is Competitive But Macro Risks Emerging",
            )
        return (
            ActionCode.HOLD,
            "Hold Current Price — Well Aligned With Online Market",
        )

    # 5. Position: BELOW (-5% to -15% below median)
    if pos == MarketPosition.BELOW:
        if margin is not None and margin < 10.0:
            # Underpriced and thin margin → reprice up!
            return (
                ActionCode.CONSIDER_REPRICE_UP,
                "Consider Repricing Up — Below Market With Tight Margins",
            )
        if external in (ExternalSignal.DEMAND_BOOST, ExternalSignal.COST_PRESSURE) or trend == TrendSignal.RISING:
            return (
                ActionCode.CONSIDER_REPRICE_UP,
                "Consider Repricing Up — Growing Demand & Rising Market Costs",
            )
        return (
            ActionCode.HOLD,
            "Hold Competitive Price — Good Footfall Advantage",
        )

    # 6. Position: WELL_BELOW (< -15% below median)
    if pos == MarketPosition.WELL_BELOW:
        return (
            ActionCode.CONSIDER_REPRICE_UP,
            "Consider Repricing Up — Substantially Below Observed Market Levels",
        )

    # Default fallback
    return (ActionCode.HOLD, "Hold Current Price — Normal Market Range")
