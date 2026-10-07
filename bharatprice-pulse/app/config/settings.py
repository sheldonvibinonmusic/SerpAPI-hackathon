"""
settings.py — BharatPrice Pulse
Central configuration using Pydantic-Settings.

All secrets come from environment variables. Never hard-code SERPAPI_KEY.
All thresholds are documented as heuristics, not economic laws.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env file and environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -----------------------------------------------------------------------
    # SerpApi Configuration
    # -----------------------------------------------------------------------
    serpapi_key: str = ""  # Loaded from SERPAPI_KEY env var. Never hard-coded.

    # Mock mode: when True, all SerpApi calls use fixture JSON files instead of live calls.
    # MUST be True during UI development, unit testing, and fusion testing.
    # Set to False only for live integration tests and the final demo recording.
    serpapi_mock_mode: bool = True

    # Base URL — use current SerpApi endpoint
    serpapi_base_url: str = "https://serpapi.com"

    # Request timeout in seconds for SerpApi HTTP calls
    serpapi_timeout_seconds: int = 30

    # -----------------------------------------------------------------------
    # Search Budget Configuration (architectural constraint, not just a label)
    # -----------------------------------------------------------------------
    # Maximum uncached SerpApi calls permitted per analysis request.
    # These are HARD limits enforced by search_budget.py — the pipeline will
    # abort and return partial results rather than exceed them.
    max_searches_quick: int = 3      # Quick Check mode
    max_searches_standard: int = 4   # Standard Check mode
    max_searches_deep: int = 6       # Deep Check mode (explicit user selection only)

    # Monthly credit reserve: never let the application use credits below this threshold
    # during normal operation. Reserve for final testing and demo recording.
    monthly_reserve_credits: int = 25

    # -----------------------------------------------------------------------
    # Cache TTL Configuration (source-specific freshness rules)
    # -----------------------------------------------------------------------
    # Shopping prices change frequently — short TTL
    cache_ttl_shopping_minutes: int = 45
    # Local merchants change slowly — longer TTL is acceptable
    cache_ttl_local_minutes: int = 360   # 6 hours
    # News is time-sensitive
    cache_ttl_news_minutes: int = 90
    # Finance signals are moderately time-sensitive
    cache_ttl_finance_minutes: int = 60
    # Trends data is less time-sensitive
    cache_ttl_trends_minutes: int = 180  # 3 hours
    # Google Search hub — moderate TTL
    cache_ttl_search_hub_minutes: int = 60

    # -----------------------------------------------------------------------
    # Database Configuration
    # -----------------------------------------------------------------------
    database_path: str = "data/bharatprice_pulse.db"

    # -----------------------------------------------------------------------
    # Application Configuration
    # -----------------------------------------------------------------------
    app_name: str = "BharatPrice Pulse"
    app_version: str = "1.0.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    # -----------------------------------------------------------------------
    # LLM Configuration (optional bounded assistant — Gemini API)
    # The LLM is ONLY used for:
    #   1. Parsing messy natural-language product queries
    #   2. Classifying news article relevance when keyword heuristics are uncertain
    #   3. Generating the plain-language explanation in the selected UI language
    # The LLM is NEVER used for arithmetic, prices, GST rates, or factual invention.
    # -----------------------------------------------------------------------
    gemini_api_key: str = ""  # Loaded from GEMINI_API_KEY. Leave empty to disable LLM.
    gemini_model: str = "gemini-3.8-flash"
    llm_enabled: bool = False  # Disabled by default. Enable only when GEMINI_API_KEY is set.
    llm_max_input_tokens: int = 4096   # Limit context sent to LLM
    llm_timeout_seconds: int = 15

    # -----------------------------------------------------------------------
    # Market Position Thresholds
    # IMPORTANT: These are configurable heuristics, NOT universal economic laws.
    # A +7% gap does not mean the same thing in a commodity FMCG market vs.
    # a branded electronics market. They are starting points that can be tuned.
    # -----------------------------------------------------------------------
    # Price gap thresholds (percentage above/below observed median)
    threshold_well_above_percent: float = 15.0   # > +15% → WELL_ABOVE
    threshold_above_percent: float = 5.0          # > +5% → ABOVE
    threshold_below_percent: float = -5.0         # < -5% → BELOW
    threshold_well_below_percent: float = -15.0   # < -15% → WELL_BELOW

    # Minimum comparable items needed for a reliable price recommendation
    min_comparable_items: int = 3

    # -----------------------------------------------------------------------
    # Local Sourcing Signal Thresholds
    # -----------------------------------------------------------------------
    local_high_merchant_count: int = 4    # >= 4 relevant merchants → HIGH signal
    local_medium_merchant_count: int = 2  # >= 2 relevant merchants → MEDIUM signal

    # -----------------------------------------------------------------------
    # Confidence Score Thresholds
    # -----------------------------------------------------------------------
    confidence_high_threshold: float = 70.0   # >= 70 → HIGH confidence
    confidence_medium_threshold: float = 45.0 # >= 45 → MEDIUM confidence
    confidence_low_threshold: float = 20.0    # >= 20 → LOW confidence
    # Below 20 → VERY_LOW

    # -----------------------------------------------------------------------
    # CORS (for development when frontend and backend are on different ports)
    # -----------------------------------------------------------------------
    cors_origins: list = ["http://localhost:8000", "http://127.0.0.1:8000"]

    # -----------------------------------------------------------------------
    # Localization Defaults
    # -----------------------------------------------------------------------
    default_country: str = "IN"
    default_gl: str = "in"          # SerpApi gl parameter
    default_hl: str = "en"          # SerpApi hl parameter
    default_ui_language: str = "en"

    @property
    def serpapi_key_is_set(self) -> bool:
        """True if a real SerpApi key has been configured."""
        return bool(self.serpapi_key and self.serpapi_key.strip())

    @property
    def llm_is_available(self) -> bool:
        """True if LLM integration is enabled and API key is configured."""
        return self.llm_enabled and bool(self.gemini_api_key and self.gemini_api_key.strip())


@lru_cache()
def get_settings() -> Settings:
    """Return the singleton settings instance. Cached for performance."""
    return Settings()
