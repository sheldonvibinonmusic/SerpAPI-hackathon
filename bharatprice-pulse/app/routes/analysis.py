"""
analysis.py — BharatPrice Pulse
Analysis endpoints: POST /api/analyze, POST /api/upload-image, GET /api/analyze/{id}.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.models.decision_models import AnalysisResponse
from app.models.request_models import AnalysisRequest
from app.serpapi.image import upload_product_image
from app.services.orchestrator import run_analysis
from app.storage.history import get_history_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Analysis"])


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Market Intelligence Analysis",
    description="Takes product, city, selling price and returns evidence-backed market decision.",
)
async def analyze_product(request: AnalysisRequest) -> AnalysisResponse:
    """Execute complete analysis pipeline."""
    try:
        response = await run_analysis(request)
        return response
    except Exception as e:
        logger.exception(f"Unhandled error in analysis endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis pipeline error: {str(e)}",
        )


@router.get(
    "/analyze/{analysis_id}",
    response_model=Dict[str, Any],
    summary="Retrieve Past Analysis by ID",
)
async def get_past_analysis(analysis_id: str) -> Dict[str, Any]:
    """Retrieve full saved analysis result from history."""
    history_repo = get_history_repo()
    result = await history_repo.get_by_id(analysis_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis ID '{analysis_id}' not found in history.",
        )
    return result


@router.post(
    "/upload-image",
    summary="Upload Product Photo for Lens Recognition",
)
async def upload_image(file: UploadFile = File(...)) -> Dict[str, str]:
    """Upload photo to SerpApi Image API and return temporary image_id."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    content = await file.read()
    if len(content) > 500 * 1024:
        raise HTTPException(status_code=400, detail="Image must be under 500 KB.")

    try:
        image_id = await upload_product_image(content, file.filename or "product.jpg")
        return {"image_id": image_id, "status": "uploaded"}
    except Exception as e:
        logger.error(f"Image upload route failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
