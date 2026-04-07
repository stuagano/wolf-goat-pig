"""
Scorecard Router

Scorecard photo scanning via Gemini Vision.
"""

import logging
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

logger = logging.getLogger("app.routers.scorecard")

router = APIRouter(prefix="/scorecard", tags=["scorecard"])


@router.post("/scan")
async def scan_scorecard_photo(file: UploadFile = File(...)) -> dict[str, Any]:
    """
    Upload a scorecard photo and extract running quarter totals via Gemini Vision.
    Returns extracted running totals and computed per-hole quarter deltas.
    Phase 1: no image persistence, process and return immediately.
    """
    from ..services.scorecard_scan_service import scan_scorecard

    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
    content_type = file.content_type or "image/jpeg"
    if content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported image type: {content_type}. Use JPEG, PNG, or WebP.")

    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:  # 20MB limit
        raise HTTPException(status_code=400, detail="Image too large. Maximum size is 20MB.")

    try:
        result = await scan_scorecard(image_bytes, content_type)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Scorecard scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {e}")
