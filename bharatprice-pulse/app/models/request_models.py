"""
request_models.py — BharatPrice Pulse
Pydantic v2 schemas for user input, normalized queries and analysis configuration.

Design principle: Every user submission must pass through a validated, typed structure
before reaching any business logic or SerpApi layer. Raw user strings are preserved for
auditability but never sent directly to external APIs.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class AnalysisMode(str, Enum):
    """Controls how many SerpApi search credits this analysis may use.

    QUICK  → max 3 uncached searches  (Google Search hub + Shopping + Trends)
    STANDARD → max 4 uncached searches (Quick + one adaptive specialist)
    DEEP   → max 6 uncached searches  (Standard + additional enrichers, user-triggered)
    """
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class ProductCategory(str, Enum):
    """Broad product categories that drive the search plan and category-driver matrix."""
    EDIBLE_OIL_FMCG = "edible_oil_fmcg"
    ELECTRONICS_MOBILES = "electronics_mobiles"
    PACKAGED_STAPLES = "packaged_staples"
    HOME_HARDWARE = "home_hardware"
    SEASONAL_FESTIVAL = "seasonal_festival"
    PERSONAL_CARE = "personal_care"
    DAIRY_BEVERAGES = "dairy_beverages"
    TEXTILES_APPAREL = "textiles_apparel"
    GENERAL = "general"
    UNKNOWN = "unknown"


class UILanguage(str, Enum):
    """UI display language codes. Separate from SerpApi search language (hl)."""
    EN = "en"   # English
    HI = "hi"   # Hindi
    MR = "mr"   # Marathi
    TA = "ta"   # Tamil
    TE = "te"   # Telugu
    KN = "kn"   # Kannada
    BN = "bn"   # Bengali
    AS = "as_"  # Assamese (underscore suffix avoids Python reserved keyword)


class TaxBasis(str, Enum):
    """Whether the supplied prices include or exclude GST."""
    INCLUSIVE = "inclusive"   # Prices include GST (most retail quotes)
    EXCLUSIVE = "exclusive"   # Prices exclude GST (B2B / invoice basis)
    UNKNOWN = "unknown"       # User did not specify — we will not assume


# ---------------------------------------------------------------------------
# Raw user input (pre-normalization)
# ---------------------------------------------------------------------------

class AnalysisRequest(BaseModel):
    """Raw form submission from the seller. Fields are deliberately permissive
    because we validate and normalize downstream rather than rejecting at the edge."""

    # Core required inputs
    product_raw: str = Field(
        ...,
        min_length=2,
        max_length=300,
        description="Raw product name/description as typed by the seller",
        examples=["Fortune mustard oil 1L", "Samsung Galaxy M14 5G", "India Gate Basmati Rice 5kg"],
    )
    city_raw: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="City or location where the seller operates",
        examples=["Jaipur", "Mumbai", "Delhi", "Coimbatore"],
    )
    selling_price: float = Field(
        ...,
        gt=0,
        description="Seller's current selling price in Indian Rupees (INR)",
        examples=[175.0, 12999.0, 420.0],
    )

    # Optional inputs
    landed_cost: Optional[float] = Field(
        default=None,
        gt=0,
        description="Seller's landed/procurement cost in INR. Used for gross margin calculation only if supplied.",
    )
    mrp: Optional[float] = Field(
        default=None,
        gt=0,
        description="Maximum Retail Price as printed on product, if known",
    )
    quantity: Optional[float] = Field(
        default=None,
        gt=0,
        description="Product quantity (numeric part). e.g. 1.0 for '1L', 5.0 for '5kg'",
    )
    unit_raw: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Unit string as supplied. Normalization handles L/ml/g/kg/pcs etc.",
        examples=["L", "ml", "g", "kg", "pcs", "packet"],
    )

    # Analysis configuration
    analysis_mode: AnalysisMode = Field(
        default=AnalysisMode.STANDARD,
        description="Controls search budget for this analysis",
    )
    ui_language: UILanguage = Field(
        default=UILanguage.EN,
        description="Language for UI labels and explanation text",
    )
    tax_basis: TaxBasis = Field(
        default=TaxBasis.UNKNOWN,
        description="Whether supplied prices include or exclude GST",
    )

    # Optional photo-based product scan (Block 11)
    # image_id is the SerpApi Image API upload ID, obtained separately via /api/upload-image
    image_id: Optional[str] = Field(
        default=None,
        max_length=200,
        description="SerpApi Image API upload ID for photo-based product recognition (Deep mode only)",
    )

    # Optional detailed product description for intelligent disambiguation
    description_raw: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional detailed product description from seller for disambiguation",
        examples=["1121 steam basmati rice, 2 years aged, premium long grain"],
    )

    # User identification for personal history scoping
    user_email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Logged-in seller's Gmail/email address for personal history tracking",
    )

    @field_validator("selling_price", "landed_cost", "mrp", mode="before")
    @classmethod
    def coerce_price(cls, v):
        """Strip currency symbols and commas that users commonly paste (e.g. '₹175' → 175.0)."""
        if isinstance(v, str):
            cleaned = v.replace("₹", "").replace(",", "").replace("Rs", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                raise ValueError(f"Could not parse price value: '{v}'")
        return v

    @model_validator(mode="after")
    def validate_cost_vs_price(self) -> "AnalysisRequest":
        """Sanity check: landed cost should not exceed selling price.
        We warn but do not reject — the seller may be operating at a temporary loss."""
        if self.landed_cost and self.selling_price:
            if self.landed_cost > self.selling_price * 1.5:
                # Do not raise; annotate for downstream warning
                pass
        return self

    @model_validator(mode="after")
    def image_mode_requires_deep(self) -> "AnalysisRequest":
        """Photo scanning uses Google Lens which costs one search credit.
        It is only permitted in DEEP analysis mode to protect the budget."""
        if self.image_id and self.analysis_mode != AnalysisMode.DEEP:
            # Silently upgrade to DEEP when photo is supplied
            self.analysis_mode = AnalysisMode.DEEP
        return self


# ---------------------------------------------------------------------------
# Normalized query (post-normalization, pre-search)
# ---------------------------------------------------------------------------

class NormalizedQuery(BaseModel):
    """Structured, canonical form of the user request.
    This is what the search planner, SerpApi layer and processing pipeline operate on.
    Raw user strings are stored for auditability but never sent to external APIs."""

    # Provenance
    raw_request: AnalysisRequest
    normalization_version: str = "1.0"  # Increment when normalization logic changes

    # Normalized product fields
    product_name: str = Field(description="Cleaned product name without brand/quantity")
    brand: Optional[str] = Field(default=None, description="Detected brand name")
    model: Optional[str] = Field(default=None, description="Model/variant identifier")
    quantity: Optional[float] = Field(default=None, description="Numeric quantity in base unit")
    base_unit: Optional[str] = Field(default=None, description="Normalized unit: L, kg, pcs, etc.")
    pack_count: int = Field(default=1, description="Number of items in pack/bundle")
    is_bundle: bool = Field(default=False, description="True if this is a multi-unit bundle/combo")
    search_query: str = Field(description="Canonical search string for SerpApi queries")
    description_raw: Optional[str] = Field(default=None, description="Original description text supplied by user")
    distilled_tokens: List[str] = Field(default_factory=list, description="Distilled high-signal descriptor tokens")

    # Location
    city: str = Field(description="Normalized city name")
    state: Optional[str] = Field(default=None, description="Indian state name if identifiable")
    location_string: str = Field(description="Full location string for SerpApi location param")
    serpapi_location: Optional[str] = Field(
        default=None,
        description="Canonicalized SerpApi Locations API result for this city"
    )

    # Category
    category: ProductCategory = Field(default=ProductCategory.UNKNOWN)
    category_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in category detection [0-1]"
    )

    # Prices (preserved as-is from user input)
    selling_price_inr: float
    landed_cost_inr: Optional[float] = None
    mrp_inr: Optional[float] = None
    tax_basis: TaxBasis

    # Analysis config
    analysis_mode: AnalysisMode
    ui_language: UILanguage
    search_language: str = Field(
        default="en",
        description="SerpApi hl parameter — engine-supported language code"
    )

    # Ambiguity
    is_ambiguous: bool = Field(default=False)
    ambiguity_reason: Optional[str] = Field(default=None)
    clarification_question: Optional[str] = Field(default=None)

    # Cache key — deterministic hash of all result-changing parameters
    cache_key: Optional[str] = Field(default=None)

    model_config = {"arbitrary_types_allowed": True}
