"""
history.py — BharatPrice Pulse
GET /api/history and DELETE /api/history endpoints for viewing past analyses.
"""
from __future__ import annotations

import logging
from typing import Dict, Any

from fastapi import APIRouter

from app.models.quota_models import HistoryListResponse
from app.storage.history import get_history_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["History"])


@router.get(
    "/history",
    response_model=HistoryListResponse,
    summary="List Past Market Analyses",
)
async def list_history() -> HistoryListResponse:
    """Return recent analyses for the history list page."""
    repo = get_history_repo()
    items = await repo.list_recent(limit=30)
    return HistoryListResponse(items=items, total_count=len(items))


@router.delete(
    "/history",
    summary="Clear Analysis History",
)
async def clear_history() -> Dict[str, Any]:
    """Delete all past saved analyses."""
    repo = get_history_repo()
    count = await repo.clear_all()
    return {"status": "cleared", "records_removed": count}
