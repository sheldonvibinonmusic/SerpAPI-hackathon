"""
search_planner.py — BharatPrice Pulse
Constructs the controlled, category-driven SerpApi search plan.

Enforces:
- Quick Check: max 3 uncached searches (Search Hub + Shopping + Trends)
- Standard Check: max 4 uncached searches (Quick + Local or News or Finance)
- Deep Check: max 6 uncached searches (user-triggered deep enrichment)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List

from app.config.category_drivers import get_driver
from app.config.search_budget import AnalysisBudget
from app.models.request_models import AnalysisMode, NormalizedQuery

logger = logging.getLogger(__name__)


@dataclass
class SearchPlan:
    analysis_id: str
    mode: AnalysisMode
    max_budget: int
    engines_to_call: List[str] = field(default_factory=list)
    reasoning: List[str] = field(default_factory=list)


def create_search_plan(
    query: NormalizedQuery,
    budget: AnalysisBudget,
) -> SearchPlan:
    """Build the search plan adhering strictly to mode budget limits."""
    mode = query.analysis_mode
    driver = get_driver(query.category)
    plan = SearchPlan(
        analysis_id=budget.analysis_id,
        mode=mode,
        max_budget=budget.max_allowed,
    )

    # 1. Primary engine: Google Search Hub (broad multi-block evidence in 1 call)
    plan.engines_to_call.append("google_search")
    plan.reasoning.append("Google Search Hub: multi-block baseline evidence")

    # 2. Google Shopping: structured price comparison
    if driver.use_shopping and len(plan.engines_to_call) < plan.max_budget:
        plan.engines_to_call.append("google_shopping")
        plan.reasoning.append("Google Shopping: structured competitor pricing")

    # 3. Google Trends: demand / interest signal
    if driver.use_trends and len(plan.engines_to_call) < plan.max_budget:
        plan.engines_to_call.append("google_trends")
        plan.reasoning.append("Google Trends: consumer search interest & regional demand")

    # 4. Standard Mode Adaptive Enrichment: Local or News or Finance
    if mode in (AnalysisMode.STANDARD, AnalysisMode.DEEP):
        if driver.use_google_local and len(plan.engines_to_call) < plan.max_budget:
            plan.engines_to_call.append("google_local")
            plan.reasoning.append("Google Local: local merchant & wholesaler discovery")

        if driver.use_news and len(plan.engines_to_call) < plan.max_budget:
            plan.engines_to_call.append("google_news")
            plan.reasoning.append("Google News: category supply & regulatory events")

        if driver.use_finance and driver.finance_instrument and len(plan.engines_to_call) < plan.max_budget:
            plan.engines_to_call.append("google_finance")
            plan.reasoning.append(f"Google Finance: currency/macro indicator ({driver.finance_instrument})")

    # 5. Deep Mode Extra Enrichments (max 6 calls total)
    if mode == AnalysisMode.DEEP:
        if query.raw_request.image_id and len(plan.engines_to_call) < plan.max_budget:
            plan.engines_to_call.append("google_lens")
            plan.reasoning.append("Google Lens: photo product identification")

        if driver.amazon_relevant and len(plan.engines_to_call) < plan.max_budget:
            plan.engines_to_call.append("amazon")
            plan.reasoning.append("Amazon India: direct marketplace benchmark")

    logger.info(
        f"Search Plan created for {budget.analysis_id} ({mode.value} mode, limit {plan.max_budget}): "
        f"{plan.engines_to_call}"
    )
    return plan
