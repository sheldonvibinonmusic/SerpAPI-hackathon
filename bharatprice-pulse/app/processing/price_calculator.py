"""
price_calculator.py — BharatPrice Pulse
Deterministic market price statistics computed from the comparable product set.

All functions are pure Python using the statistics standard library.
NEVER call an LLM or SerpApi from this module.
NEVER approximate or invent values.
"""
from __future__ import annotations

import logging
import statistics
from typing import List, Optional

from app.config.settings import get_settings
from app.models.decision_models import MarketMetrics, MarketPosition
from app.models.evidence_models import ShoppingItem
from app.processing.unit_normalizer import compute_unit_price, unit_label_for_display

logger = logging.getLogger(__name__)


def compute_market_metrics(
    comparable_items: List[ShoppingItem],
    all_items: List[ShoppingItem],
    seller_price: float,
    landed_cost: Optional[float],
    product_quantity: Optional[float],
    product_unit: Optional[str],
    settings=None,
) -> MarketMetrics:
    """
    Compute all market price statistics from the comparable product set.

    Parameters
    ----------
    comparable_items : items passing the product-matching filter
    all_items        : total retrieved from SerpApi (before filtering)
    seller_price     : seller's current selling price in INR
    landed_cost      : seller's procurement cost (optional)
    product_quantity : product quantity (for unit price)
    product_unit     : product unit (for unit price)

    Returns
    -------
    MarketMetrics with all fields populated where calculable.
    """
    if settings is None:
        settings = get_settings()

    excluded_count = len(all_items) - len(comparable_items)

    # Base metrics structure
    metrics = MarketMetrics(
        total_retrieved=len(all_items),
        comparable_count=len(comparable_items),
        excluded_count=excluded_count,
        seller_price=seller_price,
        market_position=MarketPosition.INSUFFICIENT_DATA,
    )

    # Extract valid prices from comparable items
    prices = [
        item.price_inr
        for item in comparable_items
        if item.price_inr is not None and item.price_inr > 0
    ]

    if len(prices) < settings.min_comparable_items:
        logger.info(
            f"Insufficient comparable prices: {len(prices)} found, "
            f"minimum {settings.min_comparable_items} required. "
            f"Returning INSUFFICIENT_DATA."
        )
        return metrics  # market_position already INSUFFICIENT_DATA

    # --- Price distribution (all deterministic via statistics module) ---
    metrics.price_min = round(min(prices), 2)
    metrics.price_max = round(max(prices), 2)
    metrics.price_mean = round(statistics.mean(prices), 2)
    metrics.price_median = round(statistics.median(prices), 2)

    if len(prices) >= 4:
        # Quartiles need at least 4 data points for meaningful calculation
        metrics.price_q1 = round(_quartile(prices, 0.25), 2)
        metrics.price_q3 = round(_quartile(prices, 0.75), 2)
    else:
        # With 3 items, use min and max as Q1/Q3 approximations
        # Document this explicitly as a conservative approximation
        sorted_prices = sorted(prices)
        metrics.price_q1 = sorted_prices[0]
        metrics.price_q3 = sorted_prices[-1]
        logger.info(
            f"Small sample ({len(prices)} items): using min/max as Q1/Q3 approximations"
        )

    # --- Unit price distribution ---
    if product_quantity and product_unit:
        unit_prices = []
        for item in comparable_items:
            if item.price_inr and item.quantity_detected and item.unit_detected:
                up = compute_unit_price(
                    item.price_inr,
                    item.quantity_detected,
                    item.unit_detected,
                )
                if up:
                    unit_prices.append(up)

        if len(unit_prices) >= settings.min_comparable_items:
            metrics.unit_price_min = round(min(unit_prices), 2)
            metrics.unit_price_max = round(max(unit_prices), 2)
            metrics.unit_price_median = round(statistics.median(unit_prices), 2)
            metrics.unit_label = unit_label_for_display(product_unit)

    # --- Seller price gap ---
    if metrics.price_median and metrics.price_median > 0:
        gap = (seller_price - metrics.price_median) / metrics.price_median * 100
        metrics.price_gap_percent = round(gap, 2)
        metrics.seller_vs_q1 = round(
            (seller_price - metrics.price_q1) / metrics.price_q1 * 100, 2
        ) if metrics.price_q1 else None
        metrics.seller_vs_q3 = round(
            (seller_price - metrics.price_q3) / metrics.price_q3 * 100, 2
        ) if metrics.price_q3 else None

        # --- Market position (configurable heuristics — not universal economic laws) ---
        metrics.market_position = _determine_market_position(
            gap_percent=gap,
            q1=metrics.price_q1,
            q3=metrics.price_q3,
            seller_price=seller_price,
            settings=settings,
        )

    # --- Gross margin (only if landed cost supplied by seller) ---
    if landed_cost is not None and landed_cost > 0:
        if seller_price > 0:
            margin = (seller_price - landed_cost) / seller_price * 100
            metrics.gross_margin_percent = round(margin, 2)

        # Estimated margin at market median (illustrative, not a guarantee)
        if metrics.price_median and metrics.price_median > 0 and landed_cost > 0:
            margin_at_median = (metrics.price_median - landed_cost) / metrics.price_median * 100
            metrics.margin_vs_market_median = round(margin_at_median, 2)

    return metrics


def _determine_market_position(
    gap_percent: float,
    q1: Optional[float],
    q3: Optional[float],
    seller_price: float,
    settings,
) -> MarketPosition:
    """Map price gap and distribution position to a MarketPosition enum value.

    Uses both gap_percent AND distribution position (vs Q1/Q3) for a more
    robust assessment than threshold-only logic.

    IMPORTANT: These thresholds are documented heuristics, not economic universals.
    Different product categories may warrant different thresholds, but these
    serve as reasonable starting points across Indian retail categories.
    """
    # Primary classification by gap percentage
    if gap_percent >= settings.threshold_well_above_percent:
        return MarketPosition.WELL_ABOVE
    elif gap_percent >= settings.threshold_above_percent:
        # Additional check: is seller above Q3?
        if q3 and seller_price > q3:
            return MarketPosition.WELL_ABOVE
        return MarketPosition.ABOVE
    elif gap_percent <= settings.threshold_well_below_percent:
        return MarketPosition.WELL_BELOW
    elif gap_percent <= settings.threshold_below_percent:
        if q1 and seller_price < q1:
            return MarketPosition.WELL_BELOW
        return MarketPosition.BELOW
    else:
        return MarketPosition.AT_MARKET


def _quartile(data: List[float], q: float) -> float:
    """Compute a specific quartile using linear interpolation.

    This replicates numpy's percentile behavior for small lists.
    Pure Python implementation to avoid numpy dependency.
    """
    sorted_data = sorted(data)
    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]

    # Linear interpolation (same as numpy's default method)
    index = q * (n - 1)
    lower = int(index)
    upper = lower + 1
    fraction = index - lower

    if upper >= n:
        return sorted_data[-1]

    return sorted_data[lower] + fraction * (sorted_data[upper] - sorted_data[lower])


def apply_iqr_filtering(
    items: List[ShoppingItem],
    min_sample_for_iqr: int = 6,
) -> List[ShoppingItem]:
    """Apply IQR-based outlier removal ONLY when sample size is adequate.

    For < min_sample_for_iqr items: return as-is (IQR is statistically
    unreliable on tiny samples and would remove too much information).

    For >= min_sample_for_iqr items: remove prices below Q1 - 1.5*IQR
    or above Q3 + 1.5*IQR (Tukey fences).
    """
    prices = [
        item.price_inr for item in items
        if item.price_inr is not None and item.price_inr > 0
    ]

    if len(prices) < min_sample_for_iqr:
        logger.info(
            f"IQR filtering skipped: only {len(prices)} items (min {min_sample_for_iqr} required). "
            f"Using conservative filtering only."
        )
        return items

    q1 = _quartile(prices, 0.25)
    q3 = _quartile(prices, 0.75)
    iqr = q3 - q1

    # Tukey fences
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr

    filtered = []
    for item in items:
        if item.price_inr is None:
            continue
        if lower_fence <= item.price_inr <= upper_fence:
            filtered.append(item)
        else:
            logger.info(
                f"IQR outlier removed: {item.title!r} at ₹{item.price_inr} "
                f"(fences: [{lower_fence:.2f}, {upper_fence:.2f}])"
            )
            item.exclusion_reason = f"Statistical outlier (IQR filter: outside [{lower_fence:.0f}, {upper_fence:.0f}])"

    return filtered
