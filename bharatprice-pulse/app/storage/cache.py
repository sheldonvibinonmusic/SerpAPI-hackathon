"""
cache.py — BharatPrice Pulse
Two-tier SQLite caching repository with source-specific TTLs.
Saves scarce SerpApi credits (250/month) by preventing redundant queries.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import aiosqlite

from app.config.settings import get_settings
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class CacheRepository:
    """Async cache operations against SQLite."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_settings().database_path

    async def get(self, key: str, engine: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached JSON payload if present and not expired."""
        now = utc_now().isoformat()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT data_json FROM cache WHERE key = ? AND engine = ? AND expires_at > ?",
                    (key, engine, now)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        logger.info(f"Local cache HIT: {engine} [{key[:8]}...]")
                        return json.loads(row[0])
        except Exception as e:
            if "no such table" in str(e):
                from app.storage.database import init_db
                await init_db()
            else:
                logger.warning(f"Cache get error: {e}")
            return None

    async def set(self, key: str, engine: str, data: Dict[str, Any], ttl_minutes: int) -> None:
        """Store data in cache with engine-specific expiration."""
        now = utc_now()
        expires = (now + timedelta(minutes=ttl_minutes)).isoformat()
        data_json = json.dumps(data)

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO cache (key, engine, data_json, created_at, ttl_minutes, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (key, engine, data_json, now.isoformat(), ttl_minutes, expires)
                )
                await db.commit()
            logger.info(f"Local cache SET: {engine} [{key[:8]}...] (TTL: {ttl_minutes}m)")
        except Exception as e:
            if "no such table" in str(e):
                from app.storage.database import init_db
                await init_db()
                try:
                    async with aiosqlite.connect(self.db_path) as db:
                        await db.execute(
                            """
                            INSERT OR REPLACE INTO cache (key, engine, data_json, created_at, ttl_minutes, expires_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (key, engine, data_json, now.isoformat(), ttl_minutes, expires)
                        )
                        await db.commit()
                except Exception:
                    pass
            else:
                logger.warning(f"Cache set error: {e}")

    async def clear_expired(self) -> int:
        """Purge all expired cache entries."""
        now = utc_now().isoformat()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("DELETE FROM cache WHERE expires_at <= ?", (now,))
                await db.commit()
                deleted = cursor.rowcount
                if deleted > 0:
                    logger.info(f"Purged {deleted} expired cache records")
                return deleted
        except Exception as e:
            logger.warning(f"Cache purge error: {e}")
            return 0


# Singleton instance
_cache_repo: Optional[CacheRepository] = None

def get_cache_repo() -> CacheRepository:
    global _cache_repo
    if _cache_repo is None:
        _cache_repo = CacheRepository()
    return _cache_repo
