"""
confidence_engine.py — BharatPrice Pulse
Calculates deterministic Evidence Confidence Score [0-100].

Scoring breakdown:
1. Shopping component (40%): comparable sample size, brand matching quality
2. Local component (30%): count of relevant merchants & wholesalers discovered
3. External component (30%): news presence, trend completeness, finance signals

CRITICAL: High confidence is earned by strong evidence, NOT simply because an API returned 200.
"""
from __future__ import annotations

import logging
from typing import Dict, Tuple

from app.models.decision_models import ConfidenceLevel
from app.models.evidence_models import EvidenceBundle

logger = logging.getLogger(__name__)


def compute_confidence(bundle: EvidenceBundle) -> Tuple[ConfidenceLevel, float, Dict[str, float]]:
    """Compute evidence quality confidence score and level."""
    breakdown: Dict[str, float] = {
        "shopping_score": 0.0,
        "local_score": 0.0,
        "external_score": 0.0,
    }

    # 1. Shopping Component (max 40 pts)
    comp_count = len(bundle.comparable_items)
    if comp_count >= 6:
        shopping_score = 40.0
    elif comp_count >= 4:
        shopping_score = 30.0
    elif comp_count >= 3:
        shopping_score = 20.0
    elif comp_count >= 1:
        shopping_score = 10.0
    else:
        shopping_score = 0.0
    breakdown["shopping_score"] = shopping_score

    # 2. Local Component (max 30 pts)
    merchants = bundle.local_merchants
    wholesalers = [m for m in merchants if m.is_wholesaler_or_distributor]

    if len(wholesalers) >= 3 or len(merchants) >= 5:
        local_score = 30.0
    elif len(wholesalers) >= 1 or len(merchants) >= 3:
        local_score = 20.0
    elif len(merchants) >= 1:
        local_score = 10.0
    else:
        local_score = 0.0
    breakdown["local_score"] = local_score

    # 3. External Component (max 30 pts)
    external_score = 0.0
    # News completeness (up to 15 pts)
    rel_news = [n for n in bundle.news_articles if n.relevance_score >= 0.4]
    if len(rel_news) >= 3:
        external_score += 15.0
    elif len(rel_news) >= 1:
        external_score += 10.0

    # Trends completeness (up to 10 pts)
    if bundle.trends_evidence and bundle.trends_evidence.interest_over_time:
        external_score += 10.0

    # Finance completeness (up to 5 pts)
    if bundle.finance_signals:
        external_score += 5.0
    elif len(rel_news) >= 2:  # bonus for news if finance not applicable
        external_score += 5.0

    breakdown["external_score"] = min(30.0, external_score)

    total_score = round(sum(breakdown.values()), 1)

    # Map score to ConfidenceLevel
    if total_score >= 70.0:
        level = ConfidenceLevel.HIGH
    elif total_score >= 45.0:
        level = ConfidenceLevel.MEDIUM
    elif total_score >= 20.0:
        level = ConfidenceLevel.LOW
    else:
        level = ConfidenceLevel.VERY_LOW

    # Enforce penalty: if comparable items < 3, confidence CANNOT be HIGH
    if comp_count < 3 and level == ConfidenceLevel.HIGH:
        level = ConfidenceLevel.MEDIUM

    logger.info(f"Evidence confidence computed: {total_score}/100 ({level.value})")
    return level, total_score, breakdown
