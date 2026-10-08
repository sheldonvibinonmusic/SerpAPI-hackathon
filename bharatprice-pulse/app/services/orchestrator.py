"""
orchestrator.py — BharatPrice Pulse
Master Pipeline Orchestrator. Coordinates the complete end-to-end flow:
1. Normalization & Category Detection
2. Search Planning & Budget Gate
3. SerpApi Execution (Hub & Spokes)
4. Evidence Aggregation & Matching
5. Deterministic Math & Fusion
6. Decision State Machine & Grounded Explanation
7. Persistence & History Archival
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config.gst_rules import get_gst_for_category
from app.config.search_budget import get_budget_controller
from app.config.settings import get_settings
from app.models.decision_models import (
    AnalysisResponse,
    SourceRecord,
)
from app.models.evidence_models import (
    EvidenceBundle,
    ShoppingItem,
)
from app.models.request_models import AnalysisRequest, NormalizedQuery
from app.processing.merchant_ranker import rank_merchants
from app.processing.news_processor import process_news_articles
from app.processing.price_calculator import compute_market_metrics
from app.processing.product_matcher import match_and_filter_products
from app.processing.query_normalizer import normalize_request
from app.processing.trend_processor import process_trends_data
from app.serpapi.amazon import search_amazon_in
from app.serpapi.finance import search_google_finance
from app.serpapi.google_search import search_google_hub
from app.serpapi.lens import search_google_lens
from app.serpapi.local import search_google_local
from app.serpapi.news import search_google_news
from app.serpapi.shopping import search_google_shopping
from app.serpapi.trends import search_google_trends
from app.services.decision_engine import decide_action
from app.services.evidence_fusion import fuse_evidence
from app.services.explanation import generate_explanation
from app.services.search_planner import create_search_plan
from app.storage.history import get_history_repo

from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


async def run_analysis(request: AnalysisRequest) -> AnalysisResponse:
    """Execute complete BharatPrice Pulse market intelligence pipeline."""
    analysis_id = f"bpp_{uuid.uuid4().hex[:10]}"
    now = utc_now()
    settings = get_settings()
    budget_ctrl = get_budget_controller()
    history_repo = get_history_repo()

    logger.info(f"[{analysis_id}] Starting market analysis for '{request.product_raw}' in '{request.city_raw}'")

    # 1. Normalize query
    query = normalize_request(request)

    # 2. Initialize search budget
    budget = budget_ctrl.create_budget(analysis_id, query.analysis_mode.value)

    try:
        return await _execute_analysis(
            request=request,
            query=query,
            budget=budget,
            analysis_id=analysis_id,
            now=now,
            settings=settings,
            history_repo=history_repo,
        )
    finally:
        budget_ctrl.cleanup_budget(analysis_id)


async def _execute_analysis(
    request: AnalysisRequest,
    query: NormalizedQuery,
    budget: Any,
    analysis_id: str,
    now: datetime,
    settings: Any,
    history_repo: Any,
) -> AnalysisResponse:
    # 3. Create category-driven search plan
    plan = create_search_plan(query, budget)

    # 4. Initialize Evidence Bundle
    bundle = EvidenceBundle(
        analysis_id=analysis_id,
        normalized_query_cache_key=query.cache_key or analysis_id,
        collected_at=now,
        mock_mode=settings.serpapi_mock_mode,
    )

    # 5. Execute SerpApi search engines according to plan
    partial_failure = False
    engines_used: List[str] = []
    engines_failed: List[str] = []

    # Step 5a: Google Search Hub (1 credit)
    if "google_search" in plan.engines_to_call:
        try:
            hub_result = await search_google_hub(query, budget)
            bundle.shopping_items.extend(hub_result.shopping_items)
            bundle.local_merchants.extend(hub_result.local_merchants)
            bundle.news_articles.extend(hub_result.news_articles)
            engines_used.append("google_search_hub")
        except Exception as e:
            logger.error(f"[{analysis_id}] Google Search Hub failed: {e}")
            engines_failed.append("google_search_hub")
            partial_failure = True

    # Step 5b: Specialized Google Shopping (if planned)
    if "google_shopping" in plan.engines_to_call and budget.can_search:
        try:
            shop_items = await search_google_shopping(query, budget)
            bundle.shopping_items.extend(shop_items)
            engines_used.append("google_shopping")
        except Exception as e:
            logger.warning(f"[{analysis_id}] Google Shopping failed: {e}")
            engines_failed.append("google_shopping")
            partial_failure = True

    # Step 5c: Google Trends (if planned)
    if "google_trends" in plan.engines_to_call and budget.can_search:
        try:
            trends_data = await search_google_trends(query, budget)
            bundle.trends_evidence = trends_data
            if trends_data:
                engines_used.append("google_trends")
        except Exception as e:
            logger.warning(f"[{analysis_id}] Google Trends failed: {e}")
            engines_failed.append("google_trends")
            partial_failure = True

    # Step 5d: Google Local (if planned and local merchants needed)
    if "google_local" in plan.engines_to_call and budget.can_search:
        try:
            local_items = await search_google_local(query, budget)
            bundle.local_merchants.extend(local_items)
            engines_used.append("google_local")
        except Exception as e:
            logger.warning(f"[{analysis_id}] Google Local failed: {e}")
            engines_failed.append("google_local")
            partial_failure = True

    # Step 5e: Google News (if planned)
    if "google_news" in plan.engines_to_call and budget.can_search:
        try:
            news_items = await search_google_news(query, budget)
            bundle.news_articles.extend(news_items)
            engines_used.append("google_news")
        except Exception as e:
            logger.warning(f"[{analysis_id}] Google News failed: {e}")
            engines_failed.append("google_news")
            partial_failure = True

    # Step 5f: Google Finance (if planned)
    if "google_finance" in plan.engines_to_call and budget.can_search:
        try:
            fin_sig = await search_google_finance(query, budget)
            if fin_sig:
                bundle.finance_signals.append(fin_sig)
                engines_used.append("google_finance")
        except Exception as e:
            logger.warning(f"[{analysis_id}] Google Finance failed: {e}")
            engines_failed.append("google_finance")
            partial_failure = True

    # Step 5g: Optional Deep Enrichments (Amazon, Lens)
    if "amazon" in plan.engines_to_call and budget.can_search:
        try:
            amz_items = await search_amazon_in(query, budget)
            bundle.shopping_items.extend(amz_items)
            engines_used.append("amazon_in")
        except Exception as e:
            logger.warning(f"[{analysis_id}] Amazon search failed: {e}")

    if "google_lens" in plan.engines_to_call and request.image_id and budget.can_search:
        try:
            lens_items = await search_google_lens(request.image_id, budget)
            bundle.shopping_items.extend(lens_items)
            engines_used.append("google_lens")
        except Exception as e:
            logger.warning(f"[{analysis_id}] Google Lens failed: {e}")

    bundle.searches_consumed = budget.consumed
    bundle.searches_from_cache = budget.from_cache
    bundle.engines_used = engines_used
    bundle.engines_failed = engines_failed
    bundle.partial_failure = partial_failure

    # 6. Process Evidence with Deterministic Code
    # Deduplicate Shopping items by title
    seen_titles = set()
    deduped_items: List[ShoppingItem] = []
    for item in bundle.shopping_items:
        t = (item.title or "").strip().lower()
        if not t:
            continue
        if t not in seen_titles:
            seen_titles.add(t)
            deduped_items.append(item)
    bundle.shopping_items = deduped_items

    # 7. Match & Filter Products
    comparable_items, _ = match_and_filter_products(bundle.shopping_items, query)
    bundle.comparable_items = comparable_items

    # 8. Compute Price Distribution Metrics
    metrics = compute_market_metrics(
        comparable_items=bundle.comparable_items,
        all_items=bundle.shopping_items,
        seller_price=query.selling_price_inr,
        landed_cost=query.landed_cost_inr,
        product_quantity=query.quantity,
        product_unit=query.base_unit,
        settings=settings,
    )

    # 9. Rank & Classify Local Merchants
    bundle.local_merchants = rank_merchants(bundle.local_merchants, query.category)

    # 10. Process News Articles
    bundle.news_articles = process_news_articles(bundle.news_articles, query.category, query.product_name)

    # 11. Process Trends Signals
    bundle.trends_evidence = process_trends_data(bundle.trends_evidence)

    # 12. Local GST Reference Lookup (0 API calls)
    gst_ref = get_gst_for_category(query.category, evidence_id="gst_ref_001")
    bundle.gst_reference = gst_ref

    # 13. Evidence Fusion
    fusion = fuse_evidence(bundle, metrics)

    # 14. Action Decision State Machine
    action, action_label = decide_action(fusion, metrics, query)

    # 15. Plain-Language Explanation
    explanation = generate_explanation(action, fusion, metrics, query, bundle)

    # 16. Compile Clickable Evidence Sources
    sources: List[SourceRecord] = []
    for item in bundle.comparable_items[:6]:
        sources.append(
            SourceRecord(
                evidence_id=item.evidence_id,
                source_type="Shopping Listing",
                title=f"{item.title} — ₹{item.price_inr:.2f}" if item.price_inr else item.title,
                url=item.product_link,
                source_name=item.source_name or "Online Merchant",
                retrieved_at=item.retrieved_at,
                is_mock=bundle.mock_mode,
            )
        )
    for m in bundle.local_merchants[:4]:
        sources.append(
            SourceRecord(
                evidence_id=m.evidence_id,
                source_type="Local Discovery",
                title=f"{m.title} ({m.type or 'Merchant'})",
                url=None,
                source_name=m.address or query.city,
                retrieved_at=m.retrieved_at,
                is_mock=bundle.mock_mode,
                disclaimer="Merchant location discovered on Google Local. Physical inventory not guaranteed.",
            )
        )
    for art in bundle.news_articles[:3]:
        sources.append(
            SourceRecord(
                evidence_id=art.evidence_id,
                source_type="News Event",
                title=art.title,
                url=art.link,
                source_name=art.source_name,
                retrieved_at=art.retrieved_at,
                is_mock=bundle.mock_mode,
            )
        )

    # Format GST display
    gst_display = None
    if gst_ref and gst_ref.gst_rate_percent is not None:
        gst_display = {
            "hsn_code": gst_ref.hsn_code,
            "rate_percent": gst_ref.gst_rate_percent,
            "description": gst_ref.description,
            "source": f"{gst_ref.source_name} ({gst_ref.source_date})",
            "confidence": gst_ref.confidence,
        }

    # 17. Build Final Response
    response = AnalysisResponse(
        analysis_id=analysis_id,
        status="success" if not partial_failure else "partial_success",
        timestamp=now,
        product_display=query.product_name.title(),
        location_display=query.location_string,
        seller_price_display=f"₹{query.selling_price_inr:,.2f}",
        analysis_mode=query.analysis_mode.value,
        ui_language=query.ui_language.value if hasattr(query.ui_language, "value") else str(query.ui_language),
        action=action,
        action_label=action_label,
        explanation=explanation,
        market_metrics=metrics,
        fusion=fusion,
        local_merchants=bundle.local_merchants,
        trends_evidence=bundle.trends_evidence,
        news_articles=bundle.news_articles,
        finance_signals=bundle.finance_signals,
        sources=sources,
        searches_consumed=budget.consumed,
        searches_from_cache=budget.from_cache,
        mock_mode=bundle.mock_mode,
        gst_reference_display=gst_display,
        partial_failure=partial_failure,
        partial_failure_note=(
            f"Some secondary engines failed ({', '.join(engines_failed)}) but core analysis completed."
            if partial_failure else None
        ),
    )

    # 18. Save to persistent SQLite history (async fire-and-forget or await)
    await history_repo.save(response)

    logger.info(f"[{analysis_id}] Analysis completed successfully with action {action.value}")
    return response
