"""
product_matcher.py — BharatPrice Pulse
Deterministic product matching, comparability classification, and bundle/bulk filtering.

Design principle: A 1L bottle, 2L bottle, 15L commercial tin, and a 3-pack bundle
are NOT directly comparable offers. This module filters and groups retrieved Shopping items
before computing price statistics.
"""
from __future__ import annotations

import logging
import re
from typing import List, Tuple

from app.models.evidence_models import ShoppingItem
from app.models.request_models import NormalizedQuery
from app.processing.price_calculator import apply_iqr_filtering
from app.processing.unit_normalizer import (
    are_quantities_comparable,
    compute_unit_price,
    detect_is_bulk_commercial,
    detect_is_bundle,
    detect_pack_count,
    detect_unit_from_title,
    normalize_to_base_unit,
)

logger = logging.getLogger(__name__)


def match_and_filter_products(
    items: List[ShoppingItem],
    query: NormalizedQuery,
) -> Tuple[List[ShoppingItem], List[ShoppingItem]]:
    """
    Filter retrieved Shopping items to find genuine retail comparables.

    Returns:
        (comparable_items, excluded_items)
    """
    comparable: List[ShoppingItem] = []
    excluded: List[ShoppingItem] = []

    user_brand = query.brand.lower() if query.brand else None
    user_tokens = set(re.findall(r'\b[a-zA-Z0-9]{3,}\b', query.product_name.lower()))

    # Remove unit/city words from token set
    stop_tokens = {"oil", "tel", "pack", "litre", "liter", "bottle", "pouch", query.city.lower()}
    user_core_tokens = user_tokens - stop_tokens

    for item in items:
        # Require price
        if item.price_inr is None or item.price_inr <= 0:
            item.is_comparable = False
            item.exclusion_reason = "Missing or unparseable price"
            excluded.append(item)
            continue

        title_lower = item.title.lower()

        # 1. Detect unit and quantity from item title
        qty, unit = detect_unit_from_title(item.title)
        item.quantity_detected = qty
        item.unit_detected = unit
        item.pack_count_detected = detect_pack_count(item.title)
        item.is_bundle = detect_is_bundle(item.title) or item.pack_count_detected > 1
        item.is_bulk_commercial = detect_is_bulk_commercial(item.title, qty, unit)

        # 2. Reject commercial bulk lots (e.g. 15L tins, 50kg bags)
        if item.is_bulk_commercial and (query.quantity is None or query.quantity <= 5):
            item.is_comparable = False
            item.exclusion_reason = "Bulk or commercial packaging (not consumer retail)"
            excluded.append(item)
            continue

        # 3. Reject multi-pack bundles if user requested a single unit
        if query.pack_count == 1 and item.is_bundle:
            item.is_comparable = False
            item.exclusion_reason = f"Multi-pack or bundle ({item.pack_count_detected} units)"
            excluded.append(item)
            continue

        # 4. Brand matching check
        if user_brand and user_brand not in title_lower:
            # Check if title explicitly mentions a different major brand
            other_brands = ["dhara", "saffola", "gemini", "sundrop", "dalda", "engine", "bail kolhu"]
            if any(b in title_lower for b in other_brands if b != user_brand):
                item.is_comparable = False
                item.exclusion_reason = f"Different brand than requested ({user_brand.title()})"
                excluded.append(item)
                continue

        # 5. Core product token overlap check
        item_tokens = set(re.findall(r'\b[a-zA-Z0-9]{3,}\b', title_lower))
        if user_core_tokens and not (user_core_tokens & item_tokens):
            item.is_comparable = False
            item.exclusion_reason = "Product title does not match core search terms"
            excluded.append(item)
            continue

        # 6. Size/volume comparability check
        if query.quantity and query.base_unit and qty and unit:
            # Check if sizes are directly comparable
            if not are_quantities_comparable(query.quantity, query.base_unit, qty, unit, tolerance_percent=30.0):
                # Check if price per unit makes sense, but reject from direct pack comparison
                item.is_comparable = False
                item.exclusion_reason = f"Different pack size ({qty}{unit} vs user {query.quantity}{query.base_unit})"
                excluded.append(item)
                continue

        # 7. Compute unit price where possible
        if qty and unit:
            item.unit_price_inr = compute_unit_price(item.price_inr, qty, unit)
            item.comparability_class = f"retail_{qty}{unit}"
        else:
            item.comparability_class = "retail_standard"

        item.is_comparable = True
        comparable.append(item)

    # 8. Apply IQR filtering if sample size is sufficient (>= 6)
    if len(comparable) >= 6:
        comparable = apply_iqr_filtering(comparable, min_sample_for_iqr=6)

    logger.info(
        f"Product matching: {len(comparable)} comparable items retained, "
        f"{len(excluded)} items excluded"
    )
    return comparable, excluded
