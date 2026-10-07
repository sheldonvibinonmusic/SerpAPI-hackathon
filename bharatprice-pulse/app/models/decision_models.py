"""
decision_models.py — BharatPrice Pulse
Pydantic v2 schemas for market metrics, fusion scores, decision output and the full API response.

InferredAssessment is always traceable to ObservedEvidence via evidence_ids.
Every numeric value in this module must have been computed by deterministic Python code,
never by an LLM.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enumerations for decision states
# ---------------------------------------------------------------------------

class MarketPosition(str, Enum):
    """Where the seller's price sits relative to the observed comparable market sample."""
    WELL_ABOVE = "well_above"      # > configured high threshold (e.g. >15%)
    ABOVE = "above"                # Above median and above Q3
    AT_MARKET = "at_market"        # Within the observed IQR band
    BELOW = "below"                # Below median and below Q1
    WELL_BELOW = "well_below"      # < configured low threshold (e.g. < -15%)
    INSUFFICIENT_DATA = "insufficient_data"  # Fewer than MIN_COMPARABLE_ITEMS found


class LocalSourcingSignal(str, Enum):
    HIGH = "high"      # Abundant relevant wholesalers/distributors found
    MEDIUM = "medium"  # Some relevant merchants found
    LOW = "low"        # Very few or no relevant merchants found
    UNKNOWN = "unknown"  # Local search not performed or failed


class ExternalSignal(str, Enum):
    HIGH_RISK = "high_risk"          # Strong category-relevant disruption signals
    MEDIUM_RISK = "medium_risk"      # Moderate signals present
    LOW_RISK = "low_risk"            # No significant disruptions detected
    COST_PRESSURE = "cost_pressure"  # Finance signals suggest rising input costs
    DEMAND_BOOST = "demand_boost"    # Trends/news suggest rising demand
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"  # External search not performed or failed


class TrendSignal(str, Enum):
    RISING = "rising"
    STABLE = "stable"
    FALLING = "falling"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    HIGH = "high"      # Strong comparable sample, all engines returned data
    MEDIUM = "medium"  # Adequate data but some gaps
    LOW = "low"        # Weak sample, multiple engines failed or returned insufficient data
    VERY_LOW = "very_low"  # Not enough to make any meaningful recommendation


class ActionCode(str, Enum):
    """The primary business action recommended to the seller."""
    HOLD = "HOLD"
    REVIEW_PRICE = "REVIEW_PRICE"
    CONSIDER_REPRICE_UP = "CONSIDER_REPRICE_UP"
    CONSIDER_REPRICE_DOWN = "CONSIDER_REPRICE_DOWN"
    SOURCE_LOCALLY = "SOURCE_LOCALLY"
    WATCH = "WATCH"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


# ---------------------------------------------------------------------------
# Computed market metrics
# ---------------------------------------------------------------------------

class MarketMetrics(BaseModel):
    """Deterministic market price statistics computed from the comparable_items set.
    Every number here was computed by price_calculator.py, not estimated."""

    # Sample quality
    total_retrieved: int = Field(description="Total shopping items retrieved from SerpApi")
    comparable_count: int = Field(description="Items passing product-matching filter")
    excluded_count: int = Field(description="Items excluded (wrong size, bundle, bulk, etc.)")

    # Price distribution — None when comparable_count < MIN_COMPARABLE_ITEMS
    price_min: Optional[float] = None
    price_q1: Optional[float] = None
    price_median: Optional[float] = None
    price_q3: Optional[float] = None
    price_max: Optional[float] = None
    price_mean: Optional[float] = None

    # Unit price distribution (when quantity is known)
    unit_price_min: Optional[float] = None
    unit_price_median: Optional[float] = None
    unit_price_max: Optional[float] = None
    unit_label: Optional[str] = Field(default=None, description="e.g. 'per Liter', 'per kg'")

    # Seller comparison
    seller_price: float
    price_gap_percent: Optional[float] = Field(
        default=None,
        description="(seller - median) / median * 100. Positive = seller is above median."
    )
    seller_vs_q1: Optional[float] = None
    seller_vs_q3: Optional[float] = None
    market_position: MarketPosition = MarketPosition.INSUFFICIENT_DATA

    # Seller economics (computed only when landed_cost supplied)
    gross_margin_percent: Optional[float] = Field(
        default=None,
        description="(selling_price - landed_cost) / selling_price * 100. None if cost not supplied."
    )
    margin_vs_market_median: Optional[float] = Field(
        default=None,
        description="Estimated gross margin at market median price (if cost supplied)"
    )


# ---------------------------------------------------------------------------
# Fusion dimensions (InferredAssessment)
# ---------------------------------------------------------------------------

class FusionResult(BaseModel):
    """Evidence fusion output — four independent dimensions plus overall confidence.
    Every field carries evidence_ids showing exactly which ObservedEvidence records
    contributed to each assessment."""

    # Market position
    market_position: MarketPosition
    market_position_evidence_ids: List[str] = Field(default_factory=list)

    # Local sourcing
    local_sourcing_signal: LocalSourcingSignal
    local_merchants_found: int = Field(default=0)
    wholesaler_count: int = Field(default=0)
    local_signal_evidence_ids: List[str] = Field(default_factory=list)

    # Demand/trends
    trend_signal: TrendSignal
    trend_evidence_ids: List[str] = Field(default_factory=list)

    # External risk
    external_signal: ExternalSignal
    external_signal_evidence_ids: List[str] = Field(default_factory=list)
    relevant_news_count: int = Field(default=0)

    # Confidence in the overall evidence
    confidence: ConfidenceLevel
    confidence_score: float = Field(
        ge=0.0,
        le=100.0,
        description="Deterministic score [0-100] from confidence_engine.py based on sample size, "
                    "data completeness, source diversity and freshness. "
                    "NOT an AI-generated probability of being correct."
    )
    confidence_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Component scores: shopping_score, local_score, external_score"
    )


# ---------------------------------------------------------------------------
# Explanation (human-readable, language-aware)
# ---------------------------------------------------------------------------

class ExplanationPoint(BaseModel):
    """One plain-language explanation bullet point.
    Must link to at least one evidence_id."""
    text: str
    evidence_ids: List[str] = Field(default_factory=list)
    is_disclaimer: bool = Field(default=False)


class Explanation(BaseModel):
    """Complete seller-facing explanation of the recommendation.
    Template-generated for deterministic cases; optionally LLM-synthesized for complex narratives,
    but LLM output is bounded and reviewed against structured evidence before display."""
    headline: str = Field(description="One-sentence primary finding")
    action_rationale: str = Field(description="Why this specific action is suggested")
    points: List[ExplanationPoint] = Field(default_factory=list)
    important_caveats: List[str] = Field(default_factory=list)
    generated_by: str = Field(default="deterministic_template")  # or "bounded_llm_gemini"
    language: str = Field(default="en")


# ---------------------------------------------------------------------------
# Source record (for the Sources panel)
# ---------------------------------------------------------------------------

class SourceRecord(BaseModel):
    """One clickable evidence source shown in the UI Sources panel."""
    evidence_id: str
    source_type: str
    title: str
    url: Optional[str] = None
    source_name: Optional[str] = None
    retrieved_at: Optional[datetime] = None
    is_mock: bool = Field(default=False)
    disclaimer: Optional[str] = None


# ---------------------------------------------------------------------------
# Complete analysis response
# ---------------------------------------------------------------------------

class AnalysisResponse(BaseModel):
    """Full API response for one analysis request.
    This is what the FastAPI route returns to the browser JavaScript."""

    analysis_id: str
    status: str = Field(description="success | partial_success | insufficient_data | error")
    timestamp: datetime

    # Normalized query summary (safe to expose to browser)
    product_display: str = Field(description="Clean product name for display")
    location_display: str
    seller_price_display: str = Field(description="Formatted INR string e.g. '₹175.00'")
    analysis_mode: str
    ui_language: str

    # Primary recommendation — shown FIRST in the UI
    action: ActionCode
    action_label: str = Field(description="Plain-language action label in the selected UI language")
    explanation: Optional[Explanation] = None

    # Evidence dimensions
    market_metrics: Optional[MarketMetrics] = None
    fusion: Optional[FusionResult] = None

    # Sources for the Sources/Why panel
    sources: List[SourceRecord] = Field(default_factory=list)

    # API budget telemetry (safe to expose — no keys)
    searches_consumed: int
    searches_from_cache: int
    mock_mode: bool

    # GST reference (local module only, never from live SerpApi call)
    gst_reference_display: Optional[Dict[str, Any]] = None

    # Partial failure notice
    partial_failure: bool = Field(default=False)
    partial_failure_note: Optional[str] = None
