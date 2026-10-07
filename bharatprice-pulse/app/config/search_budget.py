"""
search_budget.py — BharatPrice Pulse
Hard search-budget enforcement. This is an architectural constraint, not a UI label.

The SerpApi Free plan provides 250 searches/month and 50/hour.
This module tracks per-request budgets and provides the hard gate that prevents
any analysis from exceeding its configured maximum, regardless of what the LLM
or any other module requests.

NEVER allow this limit to be bypassed. If budget is exceeded, return partial results.
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict

from app.config.settings import get_settings
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


@dataclass
class AnalysisBudget:
    """Tracks search credit consumption for a single analysis request."""
    analysis_id: str
    max_allowed: int
    consumed: int = 0
    from_cache: int = 0
    engines_called: list = field(default_factory=list)
    budget_exceeded: bool = False
    started_at: datetime = field(default_factory=utc_now)

    @property
    def remaining(self) -> int:
        return max(0, self.max_allowed - self.consumed)

    @property
    def can_search(self) -> bool:
        return self.remaining > 0

    def consume(self, engine_name: str) -> bool:
        """Attempt to consume one search credit. Returns True if allowed, False if budget exceeded."""
        if not self.can_search:
            self.budget_exceeded = True
            logger.warning(
                f"[{self.analysis_id}] BUDGET EXCEEDED — attempted to call '{engine_name}' "
                f"but limit of {self.max_allowed} already reached. "
                f"Engines called: {self.engines_called}"
            )
            return False
        self.consumed += 1
        self.engines_called.append(engine_name)
        logger.info(
            f"[{self.analysis_id}] Search credit consumed: {engine_name} "
            f"({self.consumed}/{self.max_allowed})"
        )
        return True

    def record_cache_hit(self, engine_name: str) -> None:
        """Record that a result was served from cache (free — no credit consumed)."""
        self.from_cache += 1
        logger.info(f"[{self.analysis_id}] Cache hit for '{engine_name}' (free)")


class SearchBudgetController:
    """
    Application-wide singleton that:
    1. Maintains per-analysis budgets
    2. Provides budget instances to the orchestrator
    3. Tracks hourly consumption for rate-limit awareness

    This is a HARD gate. The orchestrator must call consume() before every SerpApi call
    and abort if it returns False.
    """

    def __init__(self):
        self._settings = get_settings()
        self._budgets: Dict[str, AnalysisBudget] = {}
        self._lock = threading.Lock()
        # Hourly rolling window tracker
        self._hourly_calls: list = []

    def create_budget(self, analysis_id: str, analysis_mode: str) -> AnalysisBudget:
        """Create a fresh budget for a new analysis request."""
        from app.models.request_models import AnalysisMode
        mode_map = {
            AnalysisMode.QUICK.value: self._settings.max_searches_quick,
            AnalysisMode.STANDARD.value: self._settings.max_searches_standard,
            AnalysisMode.DEEP.value: self._settings.max_searches_deep,
            "quick": self._settings.max_searches_quick,
            "standard": self._settings.max_searches_standard,
            "deep": self._settings.max_searches_deep,
        }
        max_allowed = mode_map.get(analysis_mode, self._settings.max_searches_standard)
        budget = AnalysisBudget(analysis_id=analysis_id, max_allowed=max_allowed)
        with self._lock:
            self._budgets[analysis_id] = budget
        logger.info(f"[{analysis_id}] Budget created: {max_allowed} searches allowed (mode={analysis_mode})")
        return budget

    def get_budget(self, analysis_id: str) -> AnalysisBudget | None:
        return self._budgets.get(analysis_id)

    def record_hourly_call(self) -> None:
        """Track calls in the last 60 minutes for hourly-rate awareness."""
        now = utc_now()
        with self._lock:
            self._hourly_calls.append(now)
            # Clean up calls older than 60 minutes
            cutoff = now - timedelta(hours=1)
            self._hourly_calls = [t for t in self._hourly_calls if t > cutoff]

    def get_hourly_calls_count(self) -> int:
        """Number of searches made in the last 60 minutes (approximate, local tracking)."""
        now = utc_now()
        cutoff = now - timedelta(hours=1)
        return sum(1 for t in self._hourly_calls if t > cutoff)

    def cleanup_budget(self, analysis_id: str) -> None:
        """Remove completed analysis budget from memory."""
        with self._lock:
            self._budgets.pop(analysis_id, None)


# Module-level singleton
_controller: SearchBudgetController | None = None


def get_budget_controller() -> SearchBudgetController:
    global _controller
    if _controller is None:
        _controller = SearchBudgetController()
    return _controller
