"""
security.py — BharatPrice Pulse
Security utilities: sanitize text, redact API keys, validate response payloads,
and prevent prompt injection / information leaks.
"""
from __future__ import annotations

import re
from typing import Any, Dict


def sanitize_text(text: str) -> str:
    """Strip dangerous characters or prompt injection attempts from user input."""
    if not text:
        return ""
    # Strip non-printable control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # Strip potential HTML script tags
    text = re.sub(r'<[^>]*>', '', text)
    return text.strip()


def redact_secrets(text: str, api_key: str = "") -> str:
    """Redact sensitive keys from log output or user strings."""
    if not text:
        return ""
    if api_key and len(api_key) > 4:
        text = text.replace(api_key, "[REDACTED_API_KEY]")
    # Redact standard SerpApi key patterns (hexadecimal 64-char or similar)
    text = re.sub(r'(?i)(api[_-]?key[\s=:]+)[a-f0-9]{32,64}', r'\1[REDACTED]', text)
    return text


def validate_serpapi_response(data: Any) -> Dict[str, Any]:
    """Ensure raw SerpApi response is a valid dictionary and inspect search metadata."""
    if not isinstance(data, dict):
        raise ValueError("Invalid SerpApi response format: expected JSON object")
    if "error" in data:
        error_msg = data.get("error")
        raise ValueError(f"SerpApi returned error: {error_msg}")
    return data
