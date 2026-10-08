"""
client.py — BharatPrice Pulse
Base SerpApi client and execution gateway.

Design rules:
1. All SerpApi searches MUST pass through this module.
2. Checks local cache first; if fresh hit, returns without consuming API credit.
3. In mock mode (SERPAPI_MOCK_MODE=True), loads realistic JSON fixtures from fixtures/.
4. Checks budget limit via SearchBudgetController before calling live API.
5. Never hardcodes or exposes SERPAPI_KEY.
"""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
import serpapi
from app.config.search_budget import AnalysisBudget, get_budget_controller
from app.config.settings import get_settings
from app.storage.cache import get_cache_repo
from app.utils.errors import BudgetExceededError, SerpApiError
from app.utils.security import redact_secrets, validate_serpapi_response

logger = logging.getLogger(__name__)


class SerpApiClient:
    """Gateway client for all SerpApi queries."""

    def __init__(self):
        self.settings = get_settings()
        self.cache_repo = get_cache_repo()
        self.budget_controller = get_budget_controller()

    async def execute(
        self,
        engine: str,
        params: Dict[str, Any],
        cache_key: str,
        ttl_minutes: int,
        budget: Optional[AnalysisBudget] = None,
        fixture_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a search with caching, budget enforcement, and mock mode support.
        """
        # 1. Check local cache
        cached_result = await self.cache_repo.get(cache_key, engine)
        if cached_result is not None:
            if budget:
                budget.record_cache_hit(engine)
            return cached_result

        # 2. Check if Mock Mode is active
        if self.settings.serpapi_mock_mode:
            logger.info(f"[MOCK MODE] Loading fixture for {engine} (query: {params.get('q', params.get('query', ''))})")
            data = self._load_fixture(engine, fixture_path, params)
            await self.cache_repo.set(cache_key, engine, data, ttl_minutes)
            if budget:
                budget.consume(f"{engine} (mock)")
            return data

        # 3. Live search: Check budget allowance
        if budget and not budget.consume(engine):
            raise BudgetExceededError(
                f"Analysis search budget of {budget.max_allowed} exceeded when attempting {engine}"
            )

        # 4. Enforce API key configuration
        if not self.settings.serpapi_key_is_set:
            raise SerpApiError("SERPAPI_KEY is not set. Enable mock mode or provide a valid key in .env.")

        # 5. Call live SerpApi via official package
        try:
            # Prepare search parameters
            search_params = {
                "engine": engine,
                "api_key": self.settings.serpapi_key,
                **params,
            }
            logger.info(f"[LIVE SERPAPI] Calling {engine} with q={params.get('q', params.get('query', ''))}")
            
            # Execute asynchronously in thread pool to prevent blocking event loop
            sp_client = serpapi.Client(api_key=self.settings.serpapi_key)
            results = await asyncio.to_thread(sp_client.search, search_params)
            raw_result = results.as_dict() if hasattr(results, "as_dict") else dict(results)
            validated = validate_serpapi_response(raw_result)

            # Record hourly usage telemetry
            self.budget_controller.record_hourly_call()

            # Save in local SQLite cache
            await self.cache_repo.set(cache_key, engine, validated, ttl_minutes)
            return validated

        except Exception as e:
            redacted_msg = redact_secrets(str(e), self.settings.serpapi_key)
            logger.error(f"SerpApi {engine} request failed: {redacted_msg}")
            raise SerpApiError(f"SerpApi {engine} search failed: {redacted_msg}")

    def _load_fixture(
        self,
        engine: str,
        fixture_path: Optional[str],
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Load fixture JSON file from disk based on engine or explicit path."""
        # Check explicit path
        if fixture_path and Path(fixture_path).exists():
            with open(fixture_path, "r", encoding="utf-8") as f:
                return json.load(f)

        # Default fixtures directory inspection
        base_dir = Path("fixtures")
        q = str(params.get("q", params.get("query", ""))).lower()

        # Route to mustard_oil, electronics, or staples
        target_sub = "mustard_oil"
        if "samsung" in q or "phone" in q or "mobile" in q:
            target_sub = "electronics"
        elif "rice" in q or "staple" in q or "grain" in q:
            target_sub = "staples"

        engine_file_map = {
            "google": "google_search.json",
            "google_shopping": "shopping.json",
            "google_local": "local.json",
            "google_news": "news.json",
            "google_trends": "trends.json",
            "google_finance": "finance.json",
        }

        filename = engine_file_map.get(engine, f"{engine}.json")
        candidate = base_dir / target_sub / filename
        if candidate.exists():
            with open(candidate, "r", encoding="utf-8") as f:
                return json.load(f)

        # Fallback to mustard_oil fixture if target fixture is missing
        fallback_candidate = base_dir / "mustard_oil" / filename
        if fallback_candidate.exists():
            with open(fallback_candidate, "r", encoding="utf-8") as f:
                return json.load(f)

        # Minimal stub if no fixture exists
        logger.warning(f"No fixture found for {engine} at {candidate}; returning empty payload")
        return {"engine": engine, "mock_data": True}


_client: Optional[SerpApiClient] = None

def get_serpapi_client() -> SerpApiClient:
    global _client
    if _client is None:
        _client = SerpApiClient()
    return _client
