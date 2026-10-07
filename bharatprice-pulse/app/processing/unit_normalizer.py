"""
unit_normalizer.py — BharatPrice Pulse
Pure Python unit conversion and pack detection utilities.

All functions are deterministic and have no external dependencies.
Never call SerpApi or an LLM from this module.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# Core conversion functions
# ---------------------------------------------------------------------------

def normalize_to_base_unit(quantity: float, unit: str) -> Tuple[float, str]:
    """Convert quantity to canonical base unit: L (liquid) or kg (weight).

    Returns (normalized_quantity, base_unit).
    For non-convertible units (pcs), returns as-is.
    """
    unit_lower = unit.lower().strip()

    # Volume: everything → L
    if unit_lower in ('ml', 'milliliter', 'millilitre', 'milliliters', 'millilitres'):
        return round(quantity / 1000, 6), 'L'
    if unit_lower in ('l', 'litre', 'liter', 'litres', 'liters', 'lt', 'ltr'):
        return float(quantity), 'L'
    if unit_lower in ('cl', 'centiliter'):
        return round(quantity / 100, 6), 'L'

    # Weight: everything → kg
    if unit_lower in ('g', 'gram', 'grams', 'gm', 'gms'):
        return round(quantity / 1000, 6), 'kg'
    if unit_lower in ('kg', 'kilogram', 'kilograms', 'kilo', 'kilos'):
        return float(quantity), 'kg'
    if unit_lower in ('mg', 'milligram', 'milligrams'):
        return round(quantity / 1_000_000, 9), 'kg'
    if unit_lower in ('quintal', 'q'):
        return float(quantity * 100), 'kg'
    if unit_lower in ('ton', 'tonne', 'mt'):
        return float(quantity * 1000), 'kg'

    # Count units — no conversion
    if unit_lower in ('pcs', 'pc', 'piece', 'pieces', 'unit', 'units',
                      'nos', 'no', 'item', 'items', 'tablet', 'tablets',
                      'sachet', 'sachets', 'packet', 'packets'):
        return float(quantity), 'pcs'

    # Unknown unit — return as-is
    return float(quantity), unit


def compute_unit_price(price_inr: float, quantity: float, unit: str) -> Optional[float]:
    """Compute price per base unit (per L or per kg).

    Returns None if computation is not meaningful (e.g. pcs without known quantity).
    """
    if quantity <= 0:
        return None
    normalized_qty, base_unit = normalize_to_base_unit(quantity, unit)
    if normalized_qty <= 0:
        return None
    return round(price_inr / normalized_qty, 2)


def unit_label_for_display(unit: str) -> str:
    """Return human-friendly unit label for display in the UI."""
    mapping = {
        'L': 'per Liter',
        'kg': 'per Kilogram',
        'pcs': 'per Piece',
        'ml': 'per mL',
        'g': 'per gram',
    }
    return mapping.get(unit, f'per {unit}')


# ---------------------------------------------------------------------------
# Unit extraction from product titles (for SerpApi Shopping results)
# ---------------------------------------------------------------------------

# Ordered by specificity — more specific patterns first
_TITLE_UNIT_PATTERNS: list[Tuple[re.Pattern, str]] = [
    # Volume
    (re.compile(r'(\d+(?:\.\d+)?)\s*(?:litre|liter|litres|liters|lt|ltr)\b', re.IGNORECASE), 'L'),
    (re.compile(r'(\d+(?:\.\d+)?)\s*(?:ml|millilitre|milliliter)\b', re.IGNORECASE), 'ml'),
    (re.compile(r'(\d+(?:\.\d+)?)\s*L\b'), 'L'),  # Capital L without space
    # Weight
    (re.compile(r'(\d+(?:\.\d+)?)\s*(?:kilogram|kilograms|kilo|kg)\b', re.IGNORECASE), 'kg'),
    (re.compile(r'(\d+(?:\.\d+)?)\s*(?:gram|grams|gm|gms|g)\b', re.IGNORECASE), 'g'),
    # Count
    (re.compile(r'(\d+)\s*(?:pieces|piece|pcs|tablets|tablet|sachets|sachet|items|nos)\b', re.IGNORECASE), 'pcs'),
]


def detect_unit_from_title(title: str) -> Tuple[Optional[float], Optional[str]]:
    """Extract quantity and unit from a product title string (SerpApi shopping result title).

    Examples:
      'Fortune Mustard Oil 1L' → (1.0, 'L')
      'Fortune Mustard Oil 1000ml' → (1.0, 'L')  # normalized
      'India Gate Basmati Rice 5 Kg' → (5.0, 'kg')
      'Samsung Galaxy M14 5G 6GB/128GB' → (None, None)

    Returns (quantity, unit) or (None, None) if not detectable.
    """
    for pattern, unit in _TITLE_UNIT_PATTERNS:
        m = pattern.search(title)
        if m:
            qty = float(m.group(1))
            # Normalize immediately
            normalized_qty, normalized_unit = normalize_to_base_unit(qty, unit)
            return normalized_qty, normalized_unit
    return None, None


# ---------------------------------------------------------------------------
# Pack/bundle detection
# ---------------------------------------------------------------------------

_PACK_PATTERNS: list[Tuple[re.Pattern, str]] = [
    (re.compile(r'\bpack\s+of\s+(\d+)\b', re.IGNORECASE), 'pack_of'),
    (re.compile(r'\bset\s+of\s+(\d+)\b', re.IGNORECASE), 'set_of'),
    (re.compile(r'\bbox\s+of\s+(\d+)\b', re.IGNORECASE), 'box_of'),
    (re.compile(r'\bcombo\s+of\s+(\d+)\b', re.IGNORECASE), 'combo_of'),
    (re.compile(r'\b(\d+)\s*x\s*\d+\s*(?:ml|l|g|kg)\b', re.IGNORECASE), 'multiplier_x'),
    (re.compile(r'\bdozen\b', re.IGNORECASE), 'dozen'),
    (re.compile(r'\b(\d+)\s*(?:bottles?|cans?|packs?|pouches?|units?)\b', re.IGNORECASE), 'count'),
]

_BUNDLE_KEYWORDS = re.compile(
    r'\b(combo|bundle|kit|pack\s+of|set\s+of|box\s+of|carton|case|assorted|variety)\b',
    re.IGNORECASE
)


def detect_pack_count(title: str) -> int:
    """Detect how many individual units are in this product.

    Returns 1 for single-unit products, >1 for multi-packs.
    """
    for pattern, kind in _PACK_PATTERNS:
        m = pattern.search(title)
        if m:
            if kind == 'dozen':
                return 12
            if kind == 'multiplier_x':
                # e.g. "3x500ml" → 3
                # The first capture group is the multiplier
                try:
                    return int(m.group(1))
                except (IndexError, ValueError):
                    return 1
            try:
                count = int(m.group(1))
                if 2 <= count <= 100:  # Sanity bounds
                    return count
            except (IndexError, ValueError):
                pass
    return 1


def detect_is_bundle(title: str) -> bool:
    """Return True if the product appears to be a multi-item bundle/combo."""
    if _BUNDLE_KEYWORDS.search(title):
        return True
    count = detect_pack_count(title)
    return count > 1


def detect_is_bulk_commercial(
    title: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
) -> bool:
    """Return True if this appears to be a bulk/commercial-grade product.

    Bulk products (15L tins, 50kg sacks) are not directly comparable to
    retail consumer packs. They should be excluded from retail price comparison.

    Rules (configurable heuristics):
    - Volume: > 5L → likely commercial/restaurant bulk
    - Weight: > 10kg → likely commercial bulk
    - Title keywords suggesting commercial grade
    """
    BULK_TITLE_KEYWORDS = re.compile(
        r'\b(commercial|industrial|bulk|wholesale|restaurant|catering|tin|drum|barrel|sack|jute bag)\b',
        re.IGNORECASE
    )
    if BULK_TITLE_KEYWORDS.search(title):
        return True

    if quantity is not None and unit is not None:
        normalized_qty, normalized_unit = normalize_to_base_unit(quantity, unit)
        if normalized_unit == 'L' and normalized_qty > 5.0:
            return True
        if normalized_unit == 'kg' and normalized_qty > 10.0:
            return True

    return False


def are_quantities_comparable(
    q1: Optional[float],
    u1: Optional[str],
    q2: Optional[float],
    u2: Optional[str],
    tolerance_percent: float = 25.0,
) -> bool:
    """Return True if two product quantities are directly comparable.

    Direct comparability: same unit family (both volume OR both weight OR both count),
    and quantity within tolerance. Different sizes compute unit price differently,
    but the question here is whether they are the same commercial offer.

    For price-band comparison: we compare unit prices, so technically all
    same-category-unit products can contribute. This function is for
    "same commercial offer" detection (used for exact comparisons).

    For unit-price comparison, use compute_unit_price() on both.
    """
    if q1 is None or u1 is None or q2 is None or u2 is None:
        return False

    n1, base_u1 = normalize_to_base_unit(q1, u1)
    n2, base_u2 = normalize_to_base_unit(q2, u2)

    # Must be in the same unit family
    if base_u1 != base_u2:
        return False

    # Check if quantities are within tolerance
    if n1 == 0:
        return False
    diff_percent = abs(n1 - n2) / n1 * 100
    return diff_percent <= tolerance_percent
