"""
errors.py — BharatPrice Pulse
Custom application exceptions for controlled, graceful error propagation.
"""
from __future__ import annotations

from typing import Optional, Dict, Any


class BharatPricePulseError(Exception):
    """Base exception for all domain errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class BudgetExceededError(BharatPricePulseError):
    """Raised when an operation would exceed the configured search budget."""
    pass


class SerpApiError(BharatPricePulseError):
    """Raised when an external SerpApi call fails or returns an error."""
    pass


class NormalizationError(BharatPricePulseError):
    """Raised when user input cannot be parsed or normalized safely."""
    pass


class InsufficientDataError(BharatPricePulseError):
    """Raised when evidence is inadequate to make a reliable recommendation."""
    pass


class CacheError(BharatPricePulseError):
    """Raised when local database or cache fails."""
    pass


class ConfigurationError(BharatPricePulseError):
    """Raised when environment or settings are misconfigured."""
    pass
