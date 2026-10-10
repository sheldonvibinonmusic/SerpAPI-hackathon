"""
history.py — BharatPrice Pulse
GET /api/history and DELETE /api/history endpoints for viewing past analyses.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Query

from app.models.quota_models import HistoryListResponse
from app.storage.history import get_history_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["History"])


@router.get(
    "/history",
    response_model=HistoryListResponse,
    summary="List Past Market Analyses",
)
async def list_history(
    user_email: Optional[str] = Query(default=None, description="Filter history by user email")
) -> HistoryListResponse:
    """Return recent analyses for the history list page, scoped to user."""
    repo = get_history_repo()
    items = await repo.list_recent(limit=30, user_email=user_email)
    return HistoryListResponse(items=items, total_count=len(items))


@router.delete(
    "/history",
    summary="Clear Analysis History",
)
async def clear_history(
    user_email: Optional[str] = Query(default=None, description="Clear history for user email")
) -> Dict[str, Any]:
    """Delete past saved analyses for user."""
    repo = get_history_repo()
    count = await repo.clear_all(user_email=user_email)
    return {"status": "cleared", "records_removed": count}
