"""
query_normalizer.py — BharatPrice Pulse
Converts raw user input into a structured, canonical NormalizedQuery.

Design principles:
1. Never guess missing details — mark ambiguous and ask or return controlled state
2. Normalize units FIRST before category detection
3. Build deterministic, reproducible cache keys
4. Preserve raw input for auditability
5. LLM assistance is optional and bounded — only for messy text parsing
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import unicodedata
from typing import Optional, Tuple

from app.config.settings import get_settings
from app.models.request_models import (
    AnalysisMode,
    AnalysisRequest,
    NormalizedQuery,
    ProductCategory,
    TaxBasis,
    UILanguage,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Indian city → state mapping (common cities)
# ---------------------------------------------------------------------------

CITY_TO_STATE: dict[str, str] = {
    # North India
    "delhi": "Delhi", "new delhi": "Delhi",
    "jaipur": "Rajasthan", "jodhpur": "Rajasthan", "udaipur": "Rajasthan", "kota": "Rajasthan",
    "lucknow": "Uttar Pradesh", "kanpur": "Uttar Pradesh", "agra": "Uttar Pradesh",
    "varanasi": "Uttar Pradesh", "ghaziabad": "Uttar Pradesh", "noida": "Uttar Pradesh",
    "chandigarh": "Chandigarh", "amritsar": "Punjab", "ludhiana": "Punjab",
    "dehradun": "Uttarakhand",
    # West India
    "mumbai": "Maharashtra", "pune": "Maharashtra", "nagpur": "Maharashtra",
    "nashik": "Maharashtra", "aurangabad": "Maharashtra",
    "ahmedabad": "Gujarat", "surat": "Gujarat", "vadodara": "Gujarat", "rajkot": "Gujarat",
    "bhopal": "Madhya Pradesh", "indore": "Madhya Pradesh", "gwalior": "Madhya Pradesh",
    # South India
    "bengaluru": "Karnataka", "bangalore": "Karnataka", "mysuru": "Karnataka", "mysore": "Karnataka",
    "hubli": "Karnataka", "mangaluru": "Karnataka",
    "chennai": "Tamil Nadu", "coimbatore": "Tamil Nadu", "madurai": "Tamil Nadu",
    "tirupur": "Tamil Nadu", "salem": "Tamil Nadu",
    "hyderabad": "Telangana", "secunderabad": "Telangana", "warangal": "Telangana",
    "visakhapatnam": "Andhra Pradesh", "vijayawada": "Andhra Pradesh",
    "kochi": "Kerala", "thiruvananthapuram": "Kerala", "kozhikode": "Kerala",
    # East India
    "kolkata": "West Bengal", "howrah": "West Bengal", "siliguri": "West Bengal",
    "patna": "Bihar", "gaya": "Bihar",
    "bhubaneswar": "Odisha", "cuttack": "Odisha",
    "ranchi": "Jharkhand", "jamshedpur": "Jharkhand",
    # Northeast India
    "guwahati": "Assam", "dibrugarh": "Assam",
    "shillong": "Meghalaya",
    "aizawl": "Mizoram",
    "imphal": "Manipur",
    "agartala": "Tripura",
    "gangtok": "Sikkim",
    "itanagar": "Arunachal Pradesh",
    "kohima": "Nagaland",
}

# ---------------------------------------------------------------------------
# Unit normalization patterns
# ---------------------------------------------------------------------------

UNIT_PATTERNS: list[Tuple[re.Pattern, str]] = [
    (re.compile(r'\b(\d+(?:\.\d+)?)\s*(?:litre|liter|liters|litres|lt|ltr)\b', re.IGNORECASE), 'L'),
    (re.compile(r'\b(\d+(?:\.\d+)?)\s*(?:ml|milliliter|millilitre|milliliters|millilitres)\b', re.IGNORECASE), 'ml'),
    (re.compile(r'\b(\d+(?:\.\d+)?)\s*(?:kg|kilogram|kilograms|kilo|kilos)\b', re.IGNORECASE), 'kg'),
    (re.compile(r'\b(\d+(?:\.\d+)?)\s*(?:g|gram|grams|gm|gms)\b', re.IGNORECASE), 'g'),
    (re.compile(r'\b(\d+(?:\.\d+)?)\s*(?:l)\b', re.IGNORECASE), 'L'),  # bare 'L'
]

# Fractional quantity patterns
HALF_PATTERNS = re.compile(r'\bhalf\s*(?:kilo|kg|liter|litre|L)?\b', re.IGNORECASE)
QUARTER_PATTERNS = re.compile(r'\bquarter\s*(?:kilo|kg|liter|litre|L)?\b', re.IGNORECASE)

# Pack count patterns
PACK_PATTERNS = [
    re.compile(r'\bpack\s+of\s+(\d+)\b', re.IGNORECASE),
    re.compile(r'\bset\s+of\s+(\d+)\b', re.IGNORECASE),
    re.compile(r'\bbox\s+of\s+(\d+)\b', re.IGNORECASE),
    re.compile(r'\bcarton\s+of\s+(\d+)\b', re.IGNORECASE),
    re.compile(r'\bdozen\b', re.IGNORECASE),  # → 12
    re.compile(r'\b(\d+)\s*(?:pieces|pcs|pc|units|nos)\b', re.IGNORECASE),
]

# ---------------------------------------------------------------------------
# Category detection keywords
# ---------------------------------------------------------------------------

CATEGORY_KEYWORDS: dict[ProductCategory, list[str]] = {
    ProductCategory.EDIBLE_OIL_FMCG: [
        "oil", "tel", "mustard", "sarso", "sarson", "sunflower", "palm", "refined",
        "groundnut", "coconut", "narial", "vegetable oil", "cooking oil", "edible",
        "fortune", "dhara", "saffola", "kachi ghani",
    ],
    ProductCategory.ELECTRONICS_MOBILES: [
        "mobile", "phone", "smartphone", "samsung", "iphone", "oneplus", "realme",
        "redmi", "poco", "vivo", "oppo", "motorola", "nokia", "laptop", "tablet",
        "earphone", "headphone", "charger", "cable", "powerbank", "gadget",
        "5g", "4g", "electronics",
    ],
    ProductCategory.PACKAGED_STAPLES: [
        "rice", "chawal", "wheat", "atta", "maida", "dal", "pulse", "daal",
        "basmati", "india gate", "aashirvaad", "tata", "lentil", "flour",
        "poha", "semolina", "suji", "chana", "rajma", "masoor", "moong",
    ],
    ProductCategory.PERSONAL_CARE: [
        "soap", "shampoo", "toothpaste", "cream", "lotion", "face wash",
        "hair oil", "moisturizer", "powder", "deodorant", "deo", "perfume",
        "dove", "lux", "pantene", "colgate", "dettol", "lifebuoy", "fair",
        "sunscreen", "lipstick", "cosmetic",
    ],
    ProductCategory.DAIRY_BEVERAGES: [
        "milk", "doodh", "yogurt", "curd", "dahi", "butter", "ghee",
        "cheese", "paneer", "amul", "mother dairy", "juice", "drink",
        "cold drink", "soft drink", "tea", "chai", "coffee", "biscuit",
    ],
    ProductCategory.HOME_HARDWARE: [
        "hardware", "tool", "pipe", "wire", "cement", "paint",
        "lock", "hinge", "screw", "nut", "bolt", "electrical", "switch",
        "plug", "bulb", "fan", "pump",
    ],
    ProductCategory.SEASONAL_FESTIVAL: [
        "diwali", "holi", "eid", "christmas", "puja", "pooja", "festival",
        "gift", "sweet", "mithai", "firework", "cracker", "decoration",
        "lantern", "rangoli",
    ],
}


def normalize_text(text: str) -> str:
    """Lowercase, strip accents, normalize whitespace."""
    text = unicodedata.normalize('NFC', text)
    return re.sub(r'\s+', ' ', text.strip().lower())


def extract_quantity_and_unit(text: str) -> Tuple[Optional[float], Optional[str]]:
    """Extract quantity and unit from product text. Returns (quantity, unit)."""
    # Guard against cellular technology (2G, 3G, 4G, 5G, 6G) and storage (GB, TB, MB, GHz)
    clean_text = re.sub(r'\b[2-6][gG]\b', ' ', text)
    clean_text = re.sub(r'\b\d+\s*(?:gb|mb|tb|ghz|mhz)\b', ' ', clean_text, flags=re.IGNORECASE)

    # Handle "half" patterns
    if HALF_PATTERNS.search(clean_text):
        for pat, unit in UNIT_PATTERNS[2:4]:  # kg/g patterns
            m = pat.search(clean_text)
            if m:
                return 0.5, unit
        return 0.5, 'kg'  # Default for "half" without unit

    # Handle "quarter" patterns
    if QUARTER_PATTERNS.search(clean_text):
        return 0.25, 'kg'

    # Handle "dozen"
    if re.search(r'\bdozen\b', clean_text, re.IGNORECASE):
        return 12.0, 'pcs'

    # Standard unit patterns
    for pattern, unit in UNIT_PATTERNS:
        m = pattern.search(clean_text)
        if m:
            qty = float(m.group(1))
            # Convert ml to L, g to kg for canonical representation
            if unit == 'ml':
                return round(qty / 1000, 4), 'L'
            if unit == 'g':
                return round(qty / 1000, 4), 'kg'
            return qty, unit

    # Fallback: look for bare number + pcs/pieces
    m = re.search(r'\b(\d+)\s*(?:pieces?|pcs?|units?|nos?|item)\b', clean_text, re.IGNORECASE)
    if m:
        return float(m.group(1)), 'pcs'

    return None, None


def extract_pack_count(text: str) -> int:
    """Extract how many individual units are in this product listing."""
    for pat in PACK_PATTERNS:
        m = pat.search(text)
        if m:
            if 'dozen' in pat.pattern:
                return 12
            try:
                return int(m.group(1))
            except (IndexError, ValueError):
                pass
    return 1


def detect_brand(product_text: str, known_brands: list[str] | None = None) -> Optional[str]:
    """Attempt to detect a brand name from the product text."""
    KNOWN_BRANDS = [
        "Fortune", "Dhara", "Saffola", "Sundrop", "Krishi", "Emami",
        "Samsung", "Apple", "OnePlus", "Realme", "Redmi", "POCO", "Vivo", "Oppo",
        "Motorola", "Nokia", "Xiaomi", "Nothing", "iQOO",
        "India Gate", "Aashirvaad", "Tata", "Patanjali", "Rajdhani",
        "Amul", "Mother Dairy", "Nestlé", "Nestle", "Britannia", "Parle",
        "Dove", "Lux", "Pantene", "Colgate", "Dettol", "Lifebuoy", "HUL",
    ]
    if known_brands:
        KNOWN_BRANDS.extend(known_brands)

    text_lower = product_text.lower()
    for brand in KNOWN_BRANDS:
        if brand.lower() in text_lower:
            return brand
    return None


def detect_category(product_text: str, brand: Optional[str] = None) -> Tuple[ProductCategory, float]:
    """Keyword-based category detection. Returns (category, confidence)."""
    text_lower = normalize_text(product_text)
    scores: dict[ProductCategory, int] = {cat: 0 for cat in ProductCategory}

    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                scores[category] += 1

    best_cat = max(scores, key=lambda c: scores[c])
    best_score = scores[best_cat]

    if best_score == 0:
        return ProductCategory.UNKNOWN, 0.0
    if best_score == 1:
        return best_cat, 0.5
    return best_cat, min(0.9, 0.5 + best_score * 0.1)


def build_search_query(
    product_name: str,
    brand: Optional[str],
    quantity: Optional[float],
    unit: Optional[str],
    city: str,
) -> str:
    """Build the canonical SerpApi search query string."""
    parts = []
    if brand and brand.lower() not in product_name.lower():
        parts.append(brand)
    parts.append(product_name)
    if quantity and unit:
        if unit == 'L':
            parts.append(f"{quantity}L")
        elif unit == 'kg':
            parts.append(f"{quantity}kg")
        elif unit == 'pcs':
            if quantity > 1:
                parts.append(f"{int(quantity)} pieces")
        else:
            parts.append(f"{quantity} {unit}")
    return " ".join(parts).strip()


def build_cache_key(
    engine: str,
    query: str,
    city: str,
    language: str,
    country: str = "in",
    **extra_params,
) -> str:
    """Build a deterministic, reproducible cache key from all result-changing parameters."""
    key_data = {
        "engine": engine,
        "query": normalize_text(query),
        "city": normalize_text(city),
        "language": language,
        "country": country,
        **{k: str(v).lower() for k, v in sorted(extra_params.items())},
    }
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(key_str.encode()).hexdigest()[:32]


def normalize_request(request: AnalysisRequest) -> NormalizedQuery:
    """
    Main normalization entry point.
    Converts raw AnalysisRequest into a structured NormalizedQuery.

    Never invents missing information. If ambiguous, sets is_ambiguous=True.
    """
    settings = get_settings()
    product_raw = request.product_raw.strip()
    city_raw = request.city_raw.strip()

    # --- Product normalization ---
    qty_from_req = request.quantity
    unit_from_req = request.unit_raw

    # Try to extract from the product text if not explicitly provided
    if qty_from_req is None or unit_from_req is None:
        extracted_qty, extracted_unit = extract_quantity_and_unit(product_raw)
        if qty_from_req is None:
            qty_from_req = extracted_qty
        if unit_from_req is None:
            unit_from_req = extracted_unit

    # Normalize unit (ml→L, g→kg)
    if qty_from_req and unit_from_req:
        if unit_from_req.lower() == 'ml':
            qty_from_req = round(qty_from_req / 1000, 4)
            unit_from_req = 'L'
        elif unit_from_req.lower() == 'g':
            qty_from_req = round(qty_from_req / 1000, 4)
            unit_from_req = 'kg'

    pack_count = extract_pack_count(product_raw)
    is_bundle = pack_count > 1

    # Brand detection
    brand = detect_brand(product_raw)

    # Clean product name: remove city, remove quantity/unit phrases
    product_name = product_raw
    # Strip detected quantity phrases from product name
    for pat, _ in UNIT_PATTERNS:
        product_name = pat.sub('', product_name)
    product_name = re.sub(r'\bpack\s+of\s+\d+\b', '', product_name, flags=re.IGNORECASE)
    product_name = re.sub(r'\bdozen\b', '', product_name, flags=re.IGNORECASE)
    # Strip city from product name if it crept in
    product_name = re.sub(re.escape(city_raw), '', product_name, flags=re.IGNORECASE)
    product_name = ' '.join(product_name.split()).strip()

    # Category detection
    category, category_confidence = detect_category(product_raw, brand=brand)

    # --- City normalization ---
    city_normalized = city_raw.strip().title()
    city_lower = city_raw.lower().strip()
    state = CITY_TO_STATE.get(city_lower)
    location_string = f"{city_normalized}, India"
    if state and state not in city_normalized:
        location_string = f"{city_normalized}, {state}, India"

    # --- Language mapping ---
    from app.config.languages import get_search_language
    search_language = get_search_language(request.ui_language, "google_search")

    # --- Build canonical search query ---
    search_query = build_search_query(
        product_name=product_name,
        brand=brand,
        quantity=qty_from_req,
        unit=unit_from_req,
        city=city_normalized,
    )

    # --- Ambiguity detection ---
    is_ambiguous = False
    ambiguity_reason = None
    clarification_question = None

    if len(product_name) < 3:
        is_ambiguous = True
        ambiguity_reason = "Product name is too short to identify"
        clarification_question = "Could you provide a more specific product name or brand?"
    elif category == ProductCategory.UNKNOWN and category_confidence == 0.0:
        # Not necessarily ambiguous — just an uncommon product. Log but don't block.
        logger.info(f"Category unknown for product: '{product_name}'")

    # --- Build master cache key ---
    master_cache_key = build_cache_key(
        engine="multi",
        query=search_query,
        city=city_normalized,
        language=search_language,
        analysis_mode=request.analysis_mode.value,
    )

    return NormalizedQuery(
        raw_request=request,
        product_name=product_name,
        brand=brand,
        model=None,  # TODO: extract model from electronics products
        quantity=qty_from_req,
        base_unit=unit_from_req,
        pack_count=pack_count,
        is_bundle=is_bundle,
        search_query=search_query,
        city=city_normalized,
        state=state,
        location_string=location_string,
        serpapi_location=None,  # Set later by Locations API
        category=category,
        category_confidence=category_confidence,
        selling_price_inr=request.selling_price,
        landed_cost_inr=request.landed_cost,
        mrp_inr=request.mrp,
        tax_basis=request.tax_basis,
        analysis_mode=request.analysis_mode,
        ui_language=request.ui_language,
        search_language=search_language,
        is_ambiguous=is_ambiguous,
        ambiguity_reason=ambiguity_reason,
        clarification_question=clarification_question,
        cache_key=master_cache_key,
    )
