"""
gst_rules.py — BharatPrice Pulse
HSN-aware GST reference module.

Design principle: This module loads GST rate data from a versioned JSON file on disk.
It NEVER calls any external API — GST rates are local reference data only.
It returns None rather than guessing when a category is not in our reference.

Source: CBIC GST Rate Schedule (Central Board of Indirect Taxes and Customs)
Users must verify current rates at https://cbic-gst.gov.in/ before relying on these values.

IMPORTANT: GST rates change via government notifications. Every entry is versioned with
source_date and verification_date so users know exactly how current it is.
This module contributes ZERO SerpApi calls.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from app.models.evidence_models import EvidenceSource, GSTReference
from app.models.request_models import ProductCategory

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default source metadata (applied when individual entries don't override)
# ---------------------------------------------------------------------------

SOURCE_NAME = "CBIC GST Rate Schedule"
SOURCE_DATE = "2025-09-22"
VERIFICATION_DATE = "2025-10-07"
CONFIDENCE = "high"

# ---------------------------------------------------------------------------
# ProductCategory → JSON category_tags mapping
#
# WHY: Our ProductCategory enum is a broad business concept. The JSON file uses
# fine-grained category_tags arrays. This mapping bridges them.
# When tags list is empty → category has no safe/confident GST mapping → returns None.
# We NEVER guess a GST rate — returning None is correct behaviour.
# ---------------------------------------------------------------------------

_CATEGORY_TAG_MAP: Dict[ProductCategory, List[str]] = {
    # Edible oils: HSN 1514, 5% GST (e.g. mustard oil, sunflower oil)
    ProductCategory.EDIBLE_OIL_FMCG: ["edible_oil_fmcg", "mustard_oil"],

    # Mobile phones / smartphones: HSN 8517, 18% GST
    ProductCategory.ELECTRONICS_MOBILES: ["electronics_mobiles", "smartphones"],

    # Packaged staples default to branded rice (5%) as representative
    # The caller should ideally pass a more specific sub-query; this is a safe default
    ProductCategory.PACKAGED_STAPLES: ["packaged_staples", "rice", "branded"],

    # Home hardware: GST varies enormously (tools, fixtures, paint = different slabs)
    # Returning None is safer than misclassifying
    ProductCategory.HOME_HARDWARE: [],

    # Personal care: HSN 3304 cosmetics / HSN 3401 soap — both 18%
    ProductCategory.PERSONAL_CARE: ["personal_care", "cosmetics"],

    # Dairy / beverages: highly variable (milk is 5%, carbonated = 28%, juice = 12%)
    # Returning None avoids a misleading rate
    ProductCategory.DAIRY_BEVERAGES: [],

    # Seasonal/festival goods: extremely varied
    ProductCategory.SEASONAL_FESTIVAL: [],

    # General: no specific mapping
    ProductCategory.GENERAL: [],

    # Unknown: definitely no mapping
    ProductCategory.UNKNOWN: [],
}

# Module-level cache so disk reads happen only once per process lifetime
_gst_data_cache: Optional[List[dict]] = None


def _resolve_json_path() -> Optional[Path]:
    """Locate data/gst_rules.json by searching up from this module's directory.
    
    WHY: The module may be run from different working directories (dev, tests, uvicorn),
    so we walk up the directory tree rather than using a hard-coded relative path.
    """
    this_file = Path(__file__).resolve()
    # Try: project_root/data/gst_rules.json
    # Walk up: config/ → app/ → project root
    for ancestor in this_file.parents:
        candidate = ancestor / "data" / "gst_rules.json"
        if candidate.exists():
            return candidate
    return None


def _load_gst_json() -> List[dict]:
    """Load and cache the GST rules JSON file from disk.
    
    Returns an empty list (not None) on error so callers don't need to
    handle None — they just won't find any entries.
    """
    global _gst_data_cache
    if _gst_data_cache is not None:
        # Already loaded — return the cached result immediately
        return _gst_data_cache

    json_path = _resolve_json_path()
    if json_path is None:
        logger.warning(
            "data/gst_rules.json not found anywhere in directory tree. "
            "GST reference module will return None for all lookups."
        )
        _gst_data_cache = []
        return _gst_data_cache

    try:
        with open(json_path, encoding="utf-8") as f:
            raw = json.load(f)
        entries = raw.get("entries", [])
        _gst_data_cache = entries
        logger.info(
            f"GST rules loaded: {len(entries)} entries from {json_path} "
            f"(source: {raw.get('source', 'unknown')}, version: {raw.get('version', 'unknown')})"
        )
        return _gst_data_cache
    except (json.JSONDecodeError, OSError, KeyError) as exc:
        logger.error(f"Failed to load GST rules from {json_path}: {exc}")
        _gst_data_cache = []  # Cache empty list to avoid repeated failed reads
        return _gst_data_cache


def _find_entry_by_tags(tags: List[str]) -> Optional[dict]:
    """Find the first JSON entry whose category_tags contain ALL specified tags.
    
    WHY ALL tags: We want precise matching. "rice" alone could match unbranded rice
    (0%) when we mean branded rice (5%). Requiring all tags makes the match specific.
    
    Returns the first match, or None if no entry satisfies all tags.
    """
    if not tags:
        # Empty tags list → caller explicitly wants None (no mapping available)
        return None

    entries = _load_gst_json()
    for entry in entries:
        entry_tags: List[str] = entry.get("category_tags", [])
        # Check that every requested tag is present in this entry's tag list
        if all(tag in entry_tags for tag in tags):
            return entry

    # No entry matched all tags → return None (correct, not an error)
    logger.debug(f"No GST entry matched all tags: {tags}")
    return None


def get_gst_for_category(
    category: ProductCategory,
    evidence_id: str = "gst_ref_001",
) -> Optional[GSTReference]:
    """Safe GST lookup for a product category.
    
    This is the primary public API for this module.
    
    Returns:
        GSTReference when we have a confident, verifiable HSN mapping.
        None when the category is unknown, variable, or not in our reference.
    
    Never guesses, never interpolates. None is the correct return value when
    we lack confidence, not an error condition.
    
    Args:
        category: The product category enum value.
        evidence_id: Unique ID to stamp on the returned GSTReference evidence record.
    
    Returns:
        Optional[GSTReference]: The GST reference data, or None.
    """
    # Step 1: Get the tags for this category
    tags = _CATEGORY_TAG_MAP.get(category, [])

    if not tags:
        # This is an intentional design decision, not an error
        logger.info(
            f"ProductCategory.{category.value} has no GST tag mapping — "
            "returning None. This is correct: we don't guess variable GST rates."
        )
        return None

    # Step 2: Find matching entry in the JSON data
    entry = _find_entry_by_tags(tags)
    if entry is None:
        # Tags were defined but no matching entry found — this could indicate
        # the JSON file is missing an entry for a mapped category
        logger.warning(
            f"GST tag mapping exists for '{category.value}' (tags={tags}) "
            "but no matching entry found in gst_rules.json. "
            "Check data/gst_rules.json for completeness."
        )
        return None

    # Step 3: Build and return the typed GSTReference evidence object
    return GSTReference(
        evidence_id=evidence_id,
        source=EvidenceSource.GST_REFERENCE,
        hsn_code=entry.get("hsn"),
        description=entry.get("description", ""),
        gst_rate_percent=entry.get("gst_rate_percent"),
        cgst_rate=entry.get("cgst_rate"),
        sgst_rate=entry.get("sgst_rate"),
        igst_rate=entry.get("igst_rate"),
        source_name=entry.get("source_name", SOURCE_NAME),
        source_date=entry.get("source_date", SOURCE_DATE),
        verification_date=entry.get("verification_date", VERIFICATION_DATE),
        confidence=entry.get("confidence", CONFIDENCE),
        # Notes become the unverified_note for display (e.g. branding caveats)
        unverified_note=entry.get("notes"),
    )


def get_all_entries() -> List[dict]:
    """Return all loaded GST entries — used for admin/debug display only.
    
    Not exposed in the public API response. Safe to call at any time.
    """
    return _load_gst_json()


def reload_cache() -> int:
    """Force-reload the GST JSON from disk. Useful after updating the JSON file.
    
    Returns the number of entries loaded.
    """
    global _gst_data_cache
    _gst_data_cache = None  # Clear cache to force a fresh disk read
    entries = _load_gst_json()
    logger.info(f"GST rules cache reloaded: {len(entries)} entries")
    return len(entries)
