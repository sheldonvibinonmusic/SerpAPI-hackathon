"""
quota_models.py — BharatPrice Pulse
Pydantic v2 schemas for SerpApi Account API usage telemetry and history summary.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from app.utils.datetime_utils import utc_now
from pydantic import BaseModel, Field


class QuotaTelemetry(BaseModel):
    """Sanitized account telemetry safe to expose to browser.
    NEVER includes the API key or raw account details."""
    monthly_limit: int = Field(default=250, description="Monthly search allowance")
    monthly_used: int = Field(default=0, description="Searches used this month")
    monthly_remaining: int = Field(default=250, description="Searches remaining this month")
    hourly_limit: int = Field(default=50, description="Hourly rate limit")
    hourly_used: int = Field(default=0, description="Estimated searches used in current hour")
    mock_mode: bool = Field(default=True, description="True if running in mock/demo mode")
    cache_hit_rate_pct: float = Field(default=0.0, description="Percentage of queries served from cache")
    timestamp: datetime = Field(default_factory=utc_now)


class HistoryItemSummary(BaseModel):
    """Summary of a past analysis for the history list view."""
    analysis_id: str
    timestamp: datetime
    product: str
    city: str
    selling_price: float
    action: str
    action_label: str
    confidence: str
    searches_consumed: int
    mock_mode: bool
    user_email: Optional[str] = None
    product_description: Optional[str] = None


class HistoryListResponse(BaseModel):
    """List of past analyses."""
    items: List[HistoryItemSummary] = Field(default_factory=list)
    total_count: int = 0
