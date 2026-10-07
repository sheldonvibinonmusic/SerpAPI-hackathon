"""
explanation.py — BharatPrice Pulse
Plain-language explanation generator tailored for Indian small business owners.

Design:
1. Primary: Deterministic templates mapping (ActionCode, MarketPosition, LocalSourcing, ExternalRisk).
2. Optional Bounded LLM (Google Gemini): if enabled, translates/enriches the narrative.
3. Every bullet point is grounded with evidence_ids.
4. Strict disclaimers: Google Maps presence != verified stock.
"""
from __future__ import annotations

import logging
from typing import List

from app.config.settings import get_settings
from app.models.decision_models import (
    ActionCode,
    Explanation,
    ExplanationPoint,
    FusionResult,
    MarketMetrics,
)
from app.models.evidence_models import EvidenceBundle
from app.models.request_models import NormalizedQuery

logger = logging.getLogger(__name__)


def generate_explanation(
    action: ActionCode,
    fusion: FusionResult,
    metrics: MarketMetrics,
    query: NormalizedQuery,
    bundle: EvidenceBundle,
) -> Explanation:
    """Generate plain-language explanation for the seller."""
    points: List[ExplanationPoint] = []
    seller_p = query.selling_price_inr
    med_p = metrics.price_median
    gap = metrics.price_gap_percent

    # 1. Market comparison bullet
    if med_p is not None and gap is not None:
        direction_word = "higher" if gap > 0 else "lower"
        abs_gap = abs(gap)
        if abs_gap <= 4.0:
            market_txt = (
                f"Your price (₹{seller_p:.2f}) matches the typical online price "
                f"(median ₹{med_p:.2f}) within ±{abs_gap:.1f}%."
            )
        else:
            market_txt = (
                f"Your price (₹{seller_p:.2f}) is {abs_gap:.1f}% {direction_word} "
                f"than the typical online price (median ₹{med_p:.2f})."
            )
        points.append(
            ExplanationPoint(
                text=market_txt,
                evidence_ids=fusion.market_position_evidence_ids[:3],
                is_disclaimer=False,
            )
        )

    # 2. Local sourcing bullet
    merchants_found = fusion.local_merchants_found
    wholesalers_found = fusion.wholesaler_count
    if merchants_found > 0:
        local_txt = (
            f"Found {merchants_found} nearby sellers in {query.city}"
            + (f", including {wholesalers_found} wholesale distributors." if wholesalers_found > 0 else ".")
        )
        points.append(
            ExplanationPoint(
                text=local_txt,
                evidence_ids=fusion.local_signal_evidence_ids[:3],
                is_disclaimer=False,
            )
        )

    # 3. Demand/Trend bullet
    if bundle.trends_evidence and bundle.trends_evidence.trend_direction:
        dir_label = bundle.trends_evidence.trend_direction
        peak = bundle.trends_evidence.peak_region
        trend_txt = f"Consumer search interest across India is currently {dir_label}."
        if peak:
            trend_txt += f" Highest interest observed in {peak}."
        points.append(
            ExplanationPoint(
                text=trend_txt,
                evidence_ids=fusion.trend_evidence_ids,
                is_disclaimer=False,
            )
        )

    # 4. News / External signal bullet
    if bundle.news_articles:
        top_art = bundle.news_articles[0]
        if top_art.relevance_score >= 0.4:
            news_txt = f"Recent market update: '{top_art.title}' ({top_art.source_name or 'News'})."
            points.append(
                ExplanationPoint(
                    text=news_txt,
                    evidence_ids=[top_art.evidence_id],
                    is_disclaimer=False,
                )
            )

    # 5. Mandatory disclaimer point
    points.append(
        ExplanationPoint(
            text="Local merchant presence is based on Google Local discovery; physical stock and wholesale discounts should be confirmed in person or by phone.",
            evidence_ids=[],
            is_disclaimer=True,
        )
    )

    # Primary action rationale
    rationale_map = {
        ActionCode.HOLD: "Your price is well positioned within the current online market range.",
        ActionCode.REVIEW_PRICE: "Your price differs noticeably from current online listings; consider reviewing before restock.",
        ActionCode.CONSIDER_REPRICE_UP: "Competitors are selling at higher prices and input costs are rising; you may have room to improve margin.",
        ActionCode.CONSIDER_REPRICE_DOWN: "Online sellers are offering lower prices, which may impact footfall or sales volume.",
        ActionCode.SOURCE_LOCALLY: "Multiple nearby distributors were identified who may offer competitive procurement rates.",
        ActionCode.WATCH: "Market pricing is steady, but external events warrant close observation.",
        ActionCode.INSUFFICIENT_DATA: "Fewer than 3 comparable online listings were found; manual market check recommended.",
    }

    headline_map = {
        ActionCode.HOLD: "Pricing Looks Balanced — Maintain Current Strategy",
        ActionCode.REVIEW_PRICE: "Price Review Suggested Before Next Restock",
        ActionCode.CONSIDER_REPRICE_UP: "Opportunity to Increase Margin and Align with Market",
        ActionCode.CONSIDER_REPRICE_DOWN: "Shelf Price Is High Relative to Online Market",
        ActionCode.SOURCE_LOCALLY: "Explore Local Wholesale Opportunities Nearby",
        ActionCode.WATCH: "Keep an Eye on Category Market Events",
        ActionCode.INSUFFICIENT_DATA: "Limited Online Data Available for This Product",
    }

    return Explanation(
        headline=headline_map.get(action, "Market Assessment Summary"),
        action_rationale=rationale_map.get(action, "Review market signals before making pricing adjustments."),
        points=points,
        important_caveats=[
            "Online prices reflect retail listings and may include shipping discounts.",
            "Local shops listed on Google Maps must be contacted directly to verify current stock.",
        ],
        generated_by="deterministic_template",
        language=query.ui_language.value if hasattr(query.ui_language, "value") else str(query.ui_language),
    )
