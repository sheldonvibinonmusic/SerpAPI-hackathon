"""
evidence_fusion.py — BharatPrice Pulse
Fuses normalized evidence into independent analytical dimensions:
1. Market Position
2. Local Sourcing Signal
3. Demand Trend Signal
4. External Risk & Macro Signal
5. Evidence Confidence
"""
from __future__ import annotations

import logging
from typing import List

from app.models.decision_models import (
    ConfidenceLevel,
    ExternalSignal,
    FusionResult,
    LocalSourcingSignal,
    MarketMetrics,
    MarketPosition,
    TrendSignal,
)
from app.models.evidence_models import EvidenceBundle
from app.services.confidence_engine import compute_confidence

logger = logging.getLogger(__name__)


def fuse_evidence(
    bundle: EvidenceBundle,
    metrics: MarketMetrics,
) -> FusionResult:
    """Fuse multi-source evidence into structured analytical dimensions."""
    # 1. Market Position Dimension
    market_pos = metrics.market_position
    market_evidence_ids = [item.evidence_id for item in bundle.comparable_items[:8]]

    # 2. Local Sourcing Dimension
    merchants = bundle.local_merchants
    wholesalers = [m for m in merchants if m.is_wholesaler_or_distributor]
    local_evidence_ids = [m.evidence_id for m in merchants[:6]]

    if len(wholesalers) >= 2 or len(merchants) >= 5:
        local_signal = LocalSourcingSignal.HIGH
    elif len(wholesalers) >= 1 or len(merchants) >= 2:
        local_signal = LocalSourcingSignal.MEDIUM
    elif len(merchants) >= 1:
        local_signal = LocalSourcingSignal.LOW
    else:
        local_signal = LocalSourcingSignal.UNKNOWN

    # 3. Trend Signal Dimension
    trend_evidence_ids: List[str] = []
    if bundle.trends_evidence:
        trend_evidence_ids.append(bundle.trends_evidence.evidence_id)
        raw_direction = bundle.trends_evidence.trend_direction
        if raw_direction == "rising":
            trend_sig = TrendSignal.RISING
        elif raw_direction == "falling":
            trend_sig = TrendSignal.FALLING
        else:
            trend_sig = TrendSignal.STABLE
    else:
        trend_sig = TrendSignal.UNKNOWN

    # 4. External Risk Dimension (News + Finance)
    external_evidence_ids: List[str] = []
    rel_news = [n for n in bundle.news_articles if n.relevance_score >= 0.4]
    external_evidence_ids.extend([n.evidence_id for n in rel_news[:4]])
    if bundle.finance_signals:
        external_evidence_ids.extend([f.evidence_id for f in bundle.finance_signals])

    # Count pressures
    supply_pressures = [n for n in rel_news if n.signal_direction == "supply_pressure"]
    cost_pressures = [n for n in rel_news if n.signal_direction == "cost_pressure"]
    demand_boosts = [n for n in rel_news if n.signal_direction == "demand_boost"]

    fin_adverse = any(f.change_percent and f.change_percent > 1.0 for f in bundle.finance_signals)

    if len(supply_pressures) >= 2 or (len(supply_pressures) >= 1 and fin_adverse):
        external_signal = ExternalSignal.HIGH_RISK
    elif len(cost_pressures) >= 1 or fin_adverse:
        external_signal = ExternalSignal.COST_PRESSURE
    elif len(demand_boosts) >= 1 or trend_sig == TrendSignal.RISING:
        external_signal = ExternalSignal.DEMAND_BOOST
    elif len(rel_news) >= 1:
        external_signal = ExternalSignal.MEDIUM_RISK
    else:
        external_signal = ExternalSignal.LOW_RISK

    # 5. Compute Confidence
    conf_level, conf_score, conf_breakdown = compute_confidence(bundle)

    fusion = FusionResult(
        market_position=market_pos,
        market_position_evidence_ids=market_evidence_ids,
        local_sourcing_signal=local_signal,
        local_merchants_found=len(merchants),
        wholesaler_count=len(wholesalers),
        local_signal_evidence_ids=local_evidence_ids,
        trend_signal=trend_sig,
        trend_evidence_ids=trend_evidence_ids,
        external_signal=external_signal,
        external_signal_evidence_ids=external_evidence_ids,
        relevant_news_count=len(rel_news),
        confidence=conf_level,
        confidence_score=conf_score,
        confidence_breakdown=conf_breakdown,
    )
    return fusion
