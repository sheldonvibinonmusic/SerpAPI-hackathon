"""
locations.py — BharatPrice Pulse
SerpApi Locations API (GET https://serpapi.com/locations.json?q={city}&limit=5).
FREE utility — does not count against search credits.
Canonicalizes Indian city and location queries into standardized SerpApi locations.
"""
from __future__ import annotations

import logging
from typing import List, Optional

import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


async def canonicalize_location(city: str) -> str:
    """Find the best matching canonical SerpApi location for an Indian city."""
    settings = get_settings()
    fallback = f"{city.title()}, India"

    if settings.serpapi_mock_mode or not settings.serpapi_key_is_set:
        return fallback

    try:
        url = f"{settings.serpapi_base_url}/locations.json"
        params = {"q": city, "limit": 5}
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                locations = resp.json()
                for loc in locations:
                    # Prefer Indian locations
                    if loc.get("country_code") == "IN" or "India" in loc.get("canonical_name", ""):
                        return loc.get("canonical_name", fallback)
    except Exception as e:
        logger.warning(f"Locations API failed: {e}; using fallback {fallback}")

    return fallback
