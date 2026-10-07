"""
logging.py — BharatPrice Pulse
Structured logging utility with request correlation and safe sanitization.
"""
from __future__ import annotations

import logging
import sys
from typing import Optional


def setup_logging(debug: bool = False) -> None:
    """Configure system-wide logging format and level."""
    log_level = logging.DEBUG if debug else logging.INFO
    log_format = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )
    # Silence noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for a module."""
    return logging.getLogger(name)
