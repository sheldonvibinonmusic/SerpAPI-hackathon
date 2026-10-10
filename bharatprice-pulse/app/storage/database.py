"""
database.py — BharatPrice Pulse
SQLite database connection and schema initialization using aiosqlite.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
import aiosqlite

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Initialize SQLite database tables for cache, history, and telemetry."""
    settings = get_settings()
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(str(db_path)) as db:
        # 1. Cache table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                engine TEXT NOT NULL,
                data_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ttl_minutes INTEGER NOT NULL,
                expires_at TIMESTAMP NOT NULL
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_cache_engine ON cache(engine)")

        # 2. History table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS analysis_history (
                analysis_id TEXT PRIMARY KEY,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                product TEXT NOT NULL,
                city TEXT NOT NULL,
                selling_price REAL NOT NULL,
                landed_cost REAL,
                action TEXT NOT NULL,
                action_label TEXT NOT NULL,
                confidence TEXT NOT NULL,
                confidence_score REAL,
                searches_consumed INTEGER NOT NULL,
                mock_mode INTEGER NOT NULL,
                full_response_json TEXT NOT NULL,
                user_email TEXT DEFAULT 'guest@bharatprice.local',
                product_description TEXT
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_history_timestamp ON analysis_history(timestamp DESC)")

        # Migration: Ensure user_email and product_description columns exist if table existed before
        try:
            async with db.execute("PRAGMA table_info(analysis_history)") as cursor:
                columns = [row[1] for row in await cursor.fetchall()]
                if "user_email" not in columns:
                    await db.execute("ALTER TABLE analysis_history ADD COLUMN user_email TEXT DEFAULT 'guest@bharatprice.local'")
                if "product_description" not in columns:
                    await db.execute("ALTER TABLE analysis_history ADD COLUMN product_description TEXT")
        except Exception as e:
            logger.warning(f"Could not check/migrate analysis_history schema: {e}")

        await db.execute("CREATE INDEX IF NOT EXISTS idx_history_user ON analysis_history(user_email, timestamp DESC)")

        # 3. Users table for deployable multi-tenant authentication
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                provider TEXT DEFAULT 'google',
                avatar_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 4. Telemetry log (tracks search usage locally)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS telemetry_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                analysis_id TEXT,
                engine TEXT NOT NULL,
                was_cached INTEGER NOT NULL,
                mock_mode INTEGER NOT NULL
            )
        """)
        await db.commit()
    logger.info(f"Database initialized at {db_path}")


async def get_db_connection() -> aiosqlite.Connection:
    """Return an active connection to the SQLite database."""
    settings = get_settings()
    return await aiosqlite.connect(settings.database_path)
