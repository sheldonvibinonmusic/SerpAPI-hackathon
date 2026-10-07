"""
archive.py — BharatPrice Pulse
SerpApi Search Archive Access (GET https://serpapi.com/searches/{search_id}.json).
Allows inspecting or replaying past search responses without consuming search credits.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


async def get_archived_search(search_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve archived search results from SerpApi (retained for 31 days)."""
    settings = get_settings()
    if not settings.serpapi_key_is_set:
        return None

    try:
        url = f"{settings.serpapi_base_url}/searches/{search_id}.json?api_key={settings.serpapi_key}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.warning(f"Search Archive retrieval failed: {e}")
    return None
