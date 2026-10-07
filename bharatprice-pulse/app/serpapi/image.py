"""
image.py — BharatPrice Pulse
SerpApi Image Upload API (POST https://serpapi.com/uploads).
Used for optional photo scanning mode (BLOCK 11).
Uploads image bytes (< 500 KB) and returns temporary image_id for Google Lens.
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config.settings import get_settings
from app.utils.errors import SerpApiError

logger = logging.getLogger(__name__)


async def upload_product_image(image_bytes: bytes, filename: str = "product.jpg") -> str:
    """Upload product photo to SerpApi and return image_id for Google Lens."""
    settings = get_settings()

    if len(image_bytes) > 500 * 1024:
        raise ValueError("Image exceeds SerpApi maximum allowed size of 500 KB")

    if settings.serpapi_mock_mode or not settings.serpapi_key_is_set:
        return "mock_image_id_12345"

    url = f"{settings.serpapi_base_url}/uploads"
    files = {"file": (filename, image_bytes, "image/jpeg")}
    params = {"api_key": settings.serpapi_key}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, files=files, params=params)
            if resp.status_code in (200, 201):
                data = resp.json()
                image_id = data.get("image_id") or data.get("id")
                if image_id:
                    return str(image_id)
            raise SerpApiError(f"Image upload failed with status {resp.status_code}")
    except Exception as e:
        logger.error(f"Image upload exception: {e}")
        raise SerpApiError(f"Could not upload image to SerpApi: {e}")
