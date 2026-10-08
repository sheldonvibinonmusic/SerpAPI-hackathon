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

logger = logging.getLogger(__name__)


class HistoryRepository:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_settings().database_path

    async def save(self, response: AnalysisResponse) -> None:
        """Save a completed analysis response to persistent history."""
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

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO analysis_history (
                        analysis_id, timestamp, product, city, selling_price, landed_cost,
                        action, action_label, confidence, confidence_score, searches_consumed,
                        mock_mode, full_response_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    )
                )
                await db.commit()
        except Exception as e:
            if "no such table" in str(e):
                from app.storage.database import init_db
                await init_db()
                try:
                    async with aiosqlite.connect(self.db_path) as db:
                        await db.execute(
                            """
                            INSERT OR REPLACE INTO analysis_history (
                                analysis_id, timestamp, product, city, selling_price, landed_cost,
                                action, action_label, confidence, confidence_score, searches_consumed,
                                mock_mode, full_response_json
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                            )
                        )
                        await db.commit()
                except Exception as inner_e:
                    logger.error(f"Failed to save analysis history after init: {inner_e}")
            else:
                logger.error(f"Failed to save analysis history: {e}")

    async def list_recent(self, limit: int = 30) -> List[HistoryItemSummary]:
        """Fetch list of recent analyses for the history UI view."""
        results: List[HistoryItemSummary] = []
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    """
                    SELECT analysis_id, timestamp, product, city, selling_price,
                           action, action_label, confidence, searches_consumed, mock_mode
                    FROM analysis_history
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (limit,)
                ) as cursor:
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

    async def clear_all(self) -> int:
        """Clear all stored history records."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("DELETE FROM analysis_history")
                await db.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Error clearing history: {e}")
            return 0


_history_repo: Optional[HistoryRepository] = None

def get_history_repo() -> HistoryRepository:
    global _history_repo
    if _history_repo is None:
        _history_repo = HistoryRepository()
    return _history_repo
