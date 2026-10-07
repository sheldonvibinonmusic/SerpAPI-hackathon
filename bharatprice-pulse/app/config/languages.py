"""
languages.py — BharatPrice Pulse
Language configuration for SerpApi engine-specific hl (host language) parameters.

Key design decisions:
1. Not all SerpApi engines support every Indian language. This module encodes exactly
   which languages each engine supports, based on SerpApi documentation.
2. Fallback rules are explicit and documented — we never silently pass an unsupported code.
3. UILanguage (what the user sees in the UI) is SEPARATE from the search language (hl param
   sent to SerpApi). A user can select Assamese UI while we search in Hindi — both are tracked.
4. The get_search_language() function is the single source of truth for hl codes.

Reference: SerpApi engine docs, Google Search supported language codes
"""
from __future__ import annotations

import logging
from typing import Dict, FrozenSet, List

from app.models.request_models import UILanguage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# UILanguage enum → SerpApi hl code string
#
# WHY a separate mapping instead of using the enum value directly:
# The UILanguage enum uses 'as_' (with underscore) to avoid clashing with Python's
# 'as' keyword. The actual SerpApi hl code is 'as' (no underscore).
# ---------------------------------------------------------------------------

UI_LANGUAGE_TO_HL: Dict[UILanguage, str] = {
    UILanguage.EN: "en",   # English — universally supported by all SerpApi engines
    UILanguage.HI: "hi",   # Hindi — widely supported by Google engines
    UILanguage.MR: "mr",   # Marathi — supported by Google Search
    UILanguage.TA: "ta",   # Tamil — supported by Google Search
    UILanguage.TE: "te",   # Telugu — supported by Google Search
    UILanguage.KN: "kn",   # Kannada — supported by Google Search
    UILanguage.BN: "bn",   # Bengali — supported by Google Search
    UILanguage.AS: "as",   # Assamese — limited support; see fallback rules
}

# ---------------------------------------------------------------------------
# Engine classification by language support breadth
#
# WHY explicit sets: We need deterministic fallback logic per engine.
# Guessing which engines support which languages leads to garbage results.
# Better to return English (always correct) than to pass an unsupported code.
# ---------------------------------------------------------------------------

# Engines that support most Indian language hl codes via Google's infrastructure
_ENGINES_BROAD_LANG: FrozenSet[str] = frozenset({
    "google",           # Google Search hub — broadest language support
    "google_shopping",  # Shares Google's language infrastructure
    "google_local",     # Shares Google's language infrastructure
    "google_news",      # Shares Google's language infrastructure
})

# Engines where English-only queries return the most reliable results.
# For finance/trends, using a vernacular hl can produce garbled instrument names.
# For Amazon India, English search terms match the product catalog more accurately.
_ENGINES_ENGLISH_ONLY: FrozenSet[str] = frozenset({
    "google_finance",       # Financial instruments are named in English
    "google_trends",        # Trend keywords work best in English for IN geo
    "amazon",               # Amazon India product search: English matches catalog best
    "google_maps_reviews",  # Reviews API: English queries return broadest set
    "google_lens",          # Image-based search: language-agnostic
})

# ---------------------------------------------------------------------------
# Language-specific support status
#
# hl codes that are NOT in the standard Google Search language list:
# These are passed by UILanguage but need a fallback for actual search use.
# ---------------------------------------------------------------------------

_LIMITED_SUPPORT_HLS: FrozenSet[str] = frozenset({
    "as",   # Assamese — not in Google's hl parameter list (as of 2025)
            # See: https://developers.google.com/custom-search/docs/ref_languages
})

# ---------------------------------------------------------------------------
# Fallback rules (search-level)
#
# WHY Hindi for Assamese: Assamese and Bengali are linguistically close,
# but Hindi is the more widely-indexed and supported language in Google's Indian
# infrastructure. Hindi search results for FMCG/grocery products in India are
# richer than Bengali. This is a practical, not linguistic, choice.
# ---------------------------------------------------------------------------

_SEARCH_FALLBACK_HL: Dict[str, str] = {
    "as": "hi",   # Assamese → Hindi for search queries
}

# ---------------------------------------------------------------------------
# Display fallback rules (for explanation template selection)
#
# When we cannot render UI in the requested language (no templates exist),
# fall back to this display language for the explanation text.
# ---------------------------------------------------------------------------

_DISPLAY_FALLBACK: Dict[str, str] = {
    "as": "en",   # Assamese UI → English explanation (no Assamese templates in v1)
}


def get_search_language(ui_language: UILanguage, engine_name: str) -> str:
    """Return the appropriate SerpApi hl code for a given UI language and engine.
    
    Precedence rules (evaluated in order):
    1. If engine is English-only → always return "en" regardless of UI language.
    2. Map UILanguage to its base hl code.
    3. If the hl code has limited support → apply the search fallback.
    4. Unknown engine → return the hl as-is (Google may handle it gracefully).
    
    Args:
        ui_language: The user's selected interface language.
        engine_name: The SerpApi engine identifier (e.g. 'google', 'amazon').
    
    Returns:
        A valid SerpApi hl parameter string (always safe to pass to the API).
    """
    # Rule 1: Some engines only work reliably in English
    if engine_name in _ENGINES_ENGLISH_ONLY:
        logger.debug(
            f"Engine '{engine_name}' is in the English-only set "
            f"— ignoring ui_language='{ui_language.value}', using hl='en'"
        )
        return "en"

    # Rule 2: Map the UI language to its base hl code
    hl = UI_LANGUAGE_TO_HL.get(ui_language, "en")

    # Rule 3: Apply search fallback for languages with limited engine support
    if hl in _LIMITED_SUPPORT_HLS:
        fallback_hl = _SEARCH_FALLBACK_HL.get(hl, "en")
        logger.info(
            f"UI language '{ui_language.value}' maps to hl='{hl}' which has limited "
            f"SerpApi support. Using fallback hl='{fallback_hl}' for engine='{engine_name}'. "
            f"Explanation will still be generated in the selected UI language."
        )
        return fallback_hl

    # Rule 4: Engine not in any known set — pass hl as-is
    if engine_name not in _ENGINES_BROAD_LANG and engine_name not in _ENGINES_ENGLISH_ONLY:
        logger.debug(
            f"Engine '{engine_name}' is not in the known engine sets. "
            f"Passing hl='{hl}' — SerpApi will apply its own fallback if unsupported."
        )

    return hl


def get_display_language(ui_language: UILanguage) -> str:
    """Return the language code to use for rendering explanation text.
    
    This may differ from get_search_language() because:
    - We want to display results in the user's preferred language
    - But we may not have templates for every language yet
    
    Returns the fallback display code when the requested language has no templates.
    """
    hl = UI_LANGUAGE_TO_HL.get(ui_language, "en")
    return _DISPLAY_FALLBACK.get(hl, hl)


def get_supported_ui_languages() -> List[UILanguage]:
    """Return all supported UI languages in a stable order.
    
    Used by the API health/info endpoint to advertise supported languages.
    """
    return list(UILanguage)


def hl_to_ui_language(hl: str) -> UILanguage:
    """Reverse lookup: hl code → UILanguage enum value.
    
    Returns UILanguage.EN as a safe default if the hl code is not recognized.
    """
    reverse_map = {v: k for k, v in UI_LANGUAGE_TO_HL.items()}
    return reverse_map.get(hl, UILanguage.EN)


def get_engine_language_note(ui_language: UILanguage, engine_name: str) -> str:
    """Return a human-readable note about the language used for a specific engine.
    
    Used for debug logging and the search plan display.
    """
    search_hl = get_search_language(ui_language, engine_name)
    base_hl = UI_LANGUAGE_TO_HL.get(ui_language, "en")

    if search_hl != base_hl:
        return (
            f"Language fallback applied: UI='{ui_language.value}' "
            f"→ search hl='{search_hl}' (base would be '{base_hl}')"
        )
    return f"Language: hl='{search_hl}' (from UI language '{ui_language.value}')"
