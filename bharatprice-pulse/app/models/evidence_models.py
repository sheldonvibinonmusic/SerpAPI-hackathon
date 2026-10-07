"""
evidence_models.py — BharatPrice Pulse
Pydantic v2 schemas for normalized evidence from all SerpApi sources.

Core design principle from the specification:
  ObservedEvidence — what SerpApi actually returned (prices, merchants, articles, values)
  InferredAssessment — what our deterministic code computed FROM that evidence

Every inference must carry evidence_ids pointing back to specific ObservedEvidence records.
Never allow a numeric value in InferredAssessment to lack a traceable source.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


# ---------------------------------------------------------------------------
# Source engine labels
# ---------------------------------------------------------------------------

class EvidenceSource(str, Enum):
    """Which SerpApi engine or local module produced this evidence record."""
    GOOGLE_SEARCH_HUB = "google_search_hub"
    GOOGLE_SHOPPING = "google_shopping"
    GOOGLE_PRODUCT = "google_product"
    GOOGLE_LOCAL = "google_local"
    GOOGLE_NEWS = "google_news"
    GOOGLE_FINANCE = "google_finance"
    GOOGLE_TRENDS = "google_trends"
    GOOGLE_LENS = "google_lens"
    AMAZON_SEARCH = "amazon_search"
    AMAZON_PRODUCT = "amazon_product"
    MAPS_REVIEWS = "maps_reviews"
    FIXTURE_MOCK = "fixture_mock"
    LOCAL_CACHE = "local_cache"
    SEARCH_ARCHIVE = "search_archive"
    GST_REFERENCE = "gst_reference"          # Local reference module, 0 API calls
    DETERMINISTIC_CALC = "deterministic_calc" # Pure Python computation


# ---------------------------------------------------------------------------
# Shopping price evidence
# ---------------------------------------------------------------------------

class ShoppingItem(BaseModel):
    """One normalized listing from Google Shopping, Amazon, or Search hub shopping block.
    All prices are raw as-retrieved — do NOT modify them here."""

    evidence_id: str = Field(description="Unique ID within this analysis batch, e.g. 'shop_001'")
    source: EvidenceSource
    retrieved_at: datetime

    # Product identification
    title: str
    source_name: Optional[str] = Field(default=None, description="Seller/retailer name")
    product_link: Optional[str] = Field(default=None)
    product_id: Optional[str] = Field(default=None, description="SerpApi product_id for Product API enrichment")
    immersive_token: Optional[str] = Field(default=None, description="For Google Immersive Product API")

    # Pricing — raw from SerpApi
    price_raw: Optional[str] = Field(default=None, description="Raw price string e.g. '₹ 158'")
    price_inr: Optional[float] = Field(default=None, description="Extracted numeric price in INR")
    old_price_inr: Optional[float] = Field(default=None, description="Original/strikethrough price if present")
    delivery_info: Optional[str] = Field(default=None)
    on_sale: bool = Field(default=False)

    # Product characteristics
    rating: Optional[float] = Field(default=None)
    reviews: Optional[int] = Field(default=None)
    is_small_business: bool = Field(default=False)

    # Normalization outputs — set by product_matcher.py, not this model
    quantity_detected: Optional[float] = Field(default=None)
    unit_detected: Optional[str] = Field(default=None)
    pack_count_detected: int = Field(default=1)
    is_bundle: bool = Field(default=False)
    is_bulk_commercial: bool = Field(default=False)
    unit_price_inr: Optional[float] = Field(
        default=None,
        description="Computed price per base unit (per L, per kg). Set by price_calculator.py"
    )
    comparability_class: Optional[str] = Field(
        default=None,
        description="e.g. 'retail_1L' — items must share this class for direct comparison"
    )
    is_comparable: Optional[bool] = Field(
        default=None,
        description="True if this item passes product matching for the user's product"
    )
    exclusion_reason: Optional[str] = Field(
        default=None,
        description="Why this item was excluded from the comparable set, if applicable"
    )

    # Raw SerpApi payload (for audit/debugging)
    raw_serpapi_data: Optional[Dict[str, Any]] = Field(default=None, exclude=True)


# ---------------------------------------------------------------------------
# Local merchant evidence
# ---------------------------------------------------------------------------

class LocalMerchant(BaseModel):
    """One merchant/business record from Google Local or Search hub local pack."""

    evidence_id: str
    source: EvidenceSource
    retrieved_at: datetime

    # Identity
    title: str
    place_id: Optional[str] = Field(default=None, description="SerpApi place_id for Maps Reviews API")
    data_id: Optional[str] = Field(default=None, description="SerpApi data_id for Maps Reviews API")

    # Contact/location
    address: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    coordinates: Optional[Dict[str, float]] = Field(
        default=None,
        description="{'lat': float, 'lng': float} when available from SerpApi"
    )

    # Business classification
    type: Optional[str] = Field(default=None, description="Primary merchant type from SerpApi")
    types: List[str] = Field(
        default_factory=list,
        description="All type tags. Used for relevance scoring, NOT for inventory inference."
    )
    description: Optional[str] = Field(default=None)

    # Availability
    is_open: Optional[bool] = Field(default=None)
    hours: Optional[Dict[str, Any]] = Field(default=None)

    # Quality signals — displayed to user as context, NOT used as inventory proxy
    rating: Optional[float] = Field(default=None)
    reviews: Optional[int] = Field(default=None)
    price_level: Optional[str] = Field(default=None, description="e.g. '$', '$$' if present")

    # Relevance scoring — set by merchant_ranker.py
    type_relevance_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="How relevant this merchant type is to the product category [0-1]"
    )
    is_wholesaler_or_distributor: bool = Field(
        default=False,
        description="True if merchant type indicates wholesale/distribution (not just retail)"
    )

    # IMPORTANT: Never claim inventory from Local results
    inventory_claimed: bool = Field(
        default=False,
        description="Always False in v1 — Google Local CANNOT confirm physical inventory"
    )

    raw_serpapi_data: Optional[Dict[str, Any]] = Field(default=None, exclude=True)


# ---------------------------------------------------------------------------
# News article evidence
# ---------------------------------------------------------------------------

class NewsArticle(BaseModel):
    """One news article from Google News or Search hub news/top-stories block."""

    evidence_id: str
    source: EvidenceSource
    retrieved_at: datetime

    title: str
    snippet: Optional[str] = Field(default=None)
    source_name: Optional[str] = Field(default=None, description="Publisher name e.g. 'Economic Times'")
    link: Optional[str] = Field(default=None)
    published_date: Optional[str] = Field(default=None, description="As returned by SerpApi")
    published_datetime: Optional[datetime] = Field(default=None, description="Parsed when possible")

    # Relevance classification — set by news_processor.py
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    signal_direction: Optional[str] = Field(
        default=None,
        description="cost_pressure | supply_pressure | demand_boost | regulatory | neutral"
    )
    # Never assign a probability. Direction is a classification, not a forecast.
    classified_by: str = Field(default="keyword_heuristic")

    raw_serpapi_data: Optional[Dict[str, Any]] = Field(default=None, exclude=True)


# ---------------------------------------------------------------------------
# Finance/external market evidence
# ---------------------------------------------------------------------------

class FinanceSignal(BaseModel):
    """One financial instrument observation from Google Finance.
    IMPORTANT: A finance signal is an external market indicator, NOT a direct product price driver."""

    evidence_id: str
    source: EvidenceSource
    retrieved_at: datetime

    instrument: str = Field(description="e.g. 'USDINR', 'NSE:NIFTY' etc.")
    instrument_label: str = Field(description="Human-readable label for the UI")
    current_value: Optional[float] = Field(default=None)
    change_value: Optional[float] = Field(default=None)
    change_percent: Optional[float] = Field(default=None)
    time_window: Optional[str] = Field(default=None)

    # Signal classification
    relevance: str = Field(
        default="low",
        description="high | medium | low — relevance to this product category"
    )
    interpretation: Optional[str] = Field(
        default=None,
        description="Plain-language explanation of what this signal means for this category. "
                    "Never states 'price will rise by X%'. States possible cost pressure only."
    )

    raw_serpapi_data: Optional[Dict[str, Any]] = Field(default=None, exclude=True)


# ---------------------------------------------------------------------------
# Google Trends evidence
# ---------------------------------------------------------------------------

class TrendsDataPoint(BaseModel):
    """One data point in the Trends timeseries."""
    date: str
    value: int  # Interest index 0-100 as returned by Google Trends


class TrendsRegionPoint(BaseModel):
    """Regional breakdown — search interest by Indian state/UT."""
    location: str
    max_value_index: int  # Relative interest index


class TrendsEvidence(BaseModel):
    """Search-interest signal from Google Trends for the product/category."""

    evidence_id: str
    source: EvidenceSource
    retrieved_at: datetime

    query: str = Field(description="The query that was trended")
    geo: str = Field(default="IN")

    # Timeseries
    interest_over_time: List[TrendsDataPoint] = Field(default_factory=list)

    # Regional breakdown
    interest_by_region: List[TrendsRegionPoint] = Field(default_factory=list)

    # Derived signals — set by trend_processor.py
    trend_direction: Optional[str] = Field(
        default=None,
        description="rising | stable | falling — computed from recent timeseries slope"
    )
    peak_region: Optional[str] = Field(
        default=None,
        description="Indian state with highest search interest"
    )
    seller_city_region_rank: Optional[int] = Field(
        default=None,
        description="Rank of seller's state in regional interest (lower = more interest)"
    )

    # IMPORTANT: This is search-interest data, NOT sales data.
    disclaimer: str = Field(
        default="Google Trends shows search interest, not actual sales volumes. "
                "A rising trend suggests growing consumer attention, not guaranteed demand."
    )

    raw_serpapi_data: Optional[Dict[str, Any]] = Field(default=None, exclude=True)


# ---------------------------------------------------------------------------
# GST reference evidence (LOCAL — zero SerpApi calls)
# ---------------------------------------------------------------------------

class GSTReference(BaseModel):
    """GST slab reference for the product category.
    Sourced from a versioned local reference file — NOT from a live API call."""

    evidence_id: str
    source: EvidenceSource = EvidenceSource.GST_REFERENCE

    hsn_code: Optional[str] = Field(default=None)
    description: str
    gst_rate_percent: Optional[float] = Field(default=None)
    cgst_rate: Optional[float] = Field(default=None)
    sgst_rate: Optional[float] = Field(default=None)
    igst_rate: Optional[float] = Field(default=None)

    # Versioning — mandatory so users know how current this reference is
    source_name: str = Field(default="CBIC GST Rate Schedule")
    source_date: str = Field(description="Date of the schedule this rate is drawn from")
    verification_date: str = Field(description="Date this entry was last verified by the project team")
    confidence: str = Field(
        description="high | medium | low — how confident we are in this classification"
    )

    # If classification is uncertain, display this instead of guessing
    unverified_note: Optional[str] = Field(
        default=None,
        description="Shown to user when HSN classification could not be confidently determined"
    )


# ---------------------------------------------------------------------------
# Aggregated evidence bundle — the complete picture for one analysis
# ---------------------------------------------------------------------------

class EvidenceBundle(BaseModel):
    """All evidence collected for one analysis run.
    Passed to the fusion engine which reads ONLY from this bundle —
    it never calls SerpApi directly."""

    analysis_id: str
    normalized_query_cache_key: str
    collected_at: datetime

    # Evidence collections
    shopping_items: List[ShoppingItem] = Field(default_factory=list)
    local_merchants: List[LocalMerchant] = Field(default_factory=list)
    news_articles: List[NewsArticle] = Field(default_factory=list)
    finance_signals: List[FinanceSignal] = Field(default_factory=list)
    trends_evidence: Optional[TrendsEvidence] = None
    gst_reference: Optional[GSTReference] = None

    # Comparable-product subset (set by product_matcher after filtering)
    comparable_items: List[ShoppingItem] = Field(
        default_factory=list,
        description="Filtered subset of shopping_items that are truly comparable to the user's product"
    )

    # Metadata
    searches_consumed: int = Field(default=0, description="Number of actual SerpApi calls made")
    searches_from_cache: int = Field(default=0, description="Number served from local cache")
    mock_mode: bool = Field(default=False)
    engines_used: List[str] = Field(default_factory=list)
    engines_failed: List[str] = Field(default_factory=list)
    partial_failure: bool = Field(
        default=False,
        description="True if one or more engines failed but the analysis continued with remaining evidence"
    )
