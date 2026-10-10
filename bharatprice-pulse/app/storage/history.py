"""
history.py — BharatPrice Pulse
Analysis history repository for tracking and retrieving past seller decisions.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiosqlite

from app.config.settings import get_settings
from app.models.decision_models import AnalysisResponse
from app.models.quota_models import HistoryItemSummary
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


class HistoryRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_settings().database_path

    async def save(self, response: AnalysisResponse, user_email: Optional[str] = None) -> None:
        """Save a completed analysis response to persistent history, scoped to user."""
        try:
            resp_dict = response.model_dump(mode="json")
            resp_json = json.dumps(resp_dict)
            landed_cost = (
                response.market_metrics.gross_margin_percent
                if response.market_metrics and response.market_metrics.gross_margin_percent is not None
                else None
            )

            selling_price = (
                response.market_metrics.seller_price
                if response.market_metrics and response.market_metrics.seller_price is not None
                else float(re.sub(r"[^\d.]", "", response.seller_price_display) or 0.0)
            )

            email_to_save = user_email or response.user_email or "guest@bharatprice.local"
            desc_to_save = response.product_description

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO analysis_history (
                        analysis_id, timestamp, product, city, selling_price, landed_cost,
                        action, action_label, confidence, confidence_score, searches_consumed,
                        mock_mode, full_response_json, user_email, product_description
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        response.analysis_id,
                        response.timestamp.isoformat(),
                        response.product_display,
                        response.location_display,
                        selling_price,
                        landed_cost,
                        response.action.value,
                        response.action_label,
                        response.fusion.confidence.value if response.fusion else "unknown",
                        response.fusion.confidence_score if response.fusion else 0.0,
                        response.searches_consumed,
                        1 if response.mock_mode else 0,
                        resp_json,
                        email_to_save,
                        desc_to_save,
                    )
                )
                await db.commit()
        except Exception as e:
            if "no such table" in str(e) or "has no column" in str(e):
                from app.storage.database import init_db
                await init_db()
                try:
                    async with aiosqlite.connect(self.db_path) as db:
                        await db.execute(
                            """
                            INSERT OR REPLACE INTO analysis_history (
                                analysis_id, timestamp, product, city, selling_price, landed_cost,
                                action, action_label, confidence, confidence_score, searches_consumed,
                                mock_mode, full_response_json, user_email, product_description
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                response.analysis_id,
                                response.timestamp.isoformat(),
                                response.product_display,
                                response.location_display,
                                selling_price,
                                landed_cost,
                                response.action.value,
                                response.action_label,
                                response.fusion.confidence.value if response.fusion else "unknown",
                                response.fusion.confidence_score if response.fusion else 0.0,
                                response.searches_consumed,
                                1 if response.mock_mode else 0,
                                resp_json,
                                email_to_save,
                                desc_to_save,
                            )
                        )
                        await db.commit()
                except Exception as inner_e:
                    logger.error(f"Failed to save analysis history after init: {inner_e}")
            else:
                logger.error(f"Failed to save analysis history: {e}")

    async def list_recent(self, limit: int = 30, user_email: Optional[str] = None) -> List[HistoryItemSummary]:
        """Fetch list of recent analyses scoped to the specific user."""
        results: List[HistoryItemSummary] = []
        try:
            async with aiosqlite.connect(self.db_path) as db:
                if user_email and user_email.strip():
                    sql = """
                        SELECT analysis_id, timestamp, product, city, selling_price,
                               action, action_label, confidence, searches_consumed, mock_mode,
                               user_email, product_description
                        FROM analysis_history
                        WHERE user_email = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """
                    params = (user_email.strip().lower(), limit)
                else:
                    sql = """
                        SELECT analysis_id, timestamp, product, city, selling_price,
                               action, action_label, confidence, searches_consumed, mock_mode,
                               user_email, product_description
                        FROM analysis_history
                        WHERE user_email = 'guest@bharatprice.local' OR user_email IS NULL
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """
                    params = (limit,)

                async with db.execute(sql, params) as cursor:
                    rows = await cursor.fetchall()
                    for r in rows:
                        results.append(
                            HistoryItemSummary(
                                analysis_id=r[0],
                                timestamp=datetime.fromisoformat(r[1]) if isinstance(r[1], str) else r[1],
                                product=r[2],
                                city=r[3],
                                selling_price=float(r[4]),
                                action=r[5],
                                action_label=r[6],
                                confidence=r[7],
                                searches_consumed=int(r[8]),
                                mock_mode=bool(r[9]),
                                user_email=r[10],
                                product_description=r[11],
                            )
                        )
        except Exception as e:
            logger.error(f"Error fetching history list: {e}")
        return results

    async def get_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full past analysis response by ID."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT full_response_json FROM analysis_history WHERE analysis_id = ?",
                    (analysis_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return json.loads(row[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching analysis by id {analysis_id}: {e}")
            return None

    async def clear_all(self, user_email: Optional[str] = None) -> int:
        """Clear stored history records for a specific user (or guest)."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                if user_email and user_email.strip():
                    cursor = await db.execute(
                        "DELETE FROM analysis_history WHERE user_email = ?",
                        (user_email.strip().lower(),)
                    )
                else:
                    cursor = await db.execute(
                        "DELETE FROM analysis_history WHERE user_email = 'guest@bharatprice.local' OR user_email IS NULL"
                    )
                await db.commit()
                return cursor.rowcount
            return 0
        except Exception as e:
            logger.error(f"Error clearing history: {e}")
            return 0

    async def save_user(
        self, email: str, name: str, provider: str = "google", avatar_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register or update a user on login."""
        clean_email = email.strip().lower()
        clean_name = name.strip() or clean_email.split("@")[0].title()
        now_str = utc_now().isoformat()
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT INTO users (email, name, provider, avatar_url, created_at, last_login)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(email) DO UPDATE SET
                        name = excluded.name,
                        last_login = excluded.last_login,
                        avatar_url = COALESCE(excluded.avatar_url, users.avatar_url)
                    """,
                    (clean_email, clean_name, provider, avatar_url, now_str, now_str)
                )
                await db.commit()
            return {
                "email": clean_email,
                "name": clean_name,
                "provider": provider,
                "avatar_url": avatar_url,
                "last_login": now_str,
            }
        except Exception as e:
            if "no such table" in str(e):
                from app.storage.database import init_db
                await init_db()
                try:
                    async with aiosqlite.connect(self.db_path) as db:
                        await db.execute(
                            """
                            INSERT INTO users (email, name, provider, avatar_url, created_at, last_login)
                            VALUES (?, ?, ?, ?, ?, ?)
                            ON CONFLICT(email) DO UPDATE SET
                                name = excluded.name,
                                last_login = excluded.last_login,
                                avatar_url = COALESCE(excluded.avatar_url, users.avatar_url)
                            """,
                            (clean_email, clean_name, provider, avatar_url, now_str, now_str)
                        )
                        await db.commit()
                    return {
                        "email": clean_email,
                        "name": clean_name,
                        "provider": provider,
                        "avatar_url": avatar_url,
                        "last_login": now_str,
                    }
                except Exception as inner_e:
                    logger.error(f"Failed to save user after init: {inner_e}")
            else:
                logger.error(f"Error saving user {email}: {e}")
            return {
                "email": clean_email,
                "name": clean_name,
                "provider": provider,
                "avatar_url": avatar_url,
            }

    async def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """Fetch user profile by email."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT email, name, provider, avatar_url, created_at, last_login FROM users WHERE email = ?",
                    (email.strip().lower(),)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return {
                            "email": row[0],
                            "name": row[1],
                            "provider": row[2],
                            "avatar_url": row[3],
                            "created_at": row[4],
                            "last_login": row[5],
                        }
            return None
        except Exception as e:
            if "no such table" in str(e):
                from app.storage.database import init_db
                await init_db()
            else:
                logger.error(f"Error fetching user {email}: {e}")
            return None


_history_repo: Optional[HistoryRepository] = None

def get_history_repo() -> HistoryRepository:
    global _history_repo
    if _history_repo is None:
        _history_repo = HistoryRepository()
    return _history_repo
