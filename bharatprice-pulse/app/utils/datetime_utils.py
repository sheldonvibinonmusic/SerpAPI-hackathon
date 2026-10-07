"""
datetime_utils.py — BharatPrice Pulse
UTC datetime helper compatible with Python 3.11, 3.12, 3.13, and 3.14 without deprecation warnings.
"""
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)
