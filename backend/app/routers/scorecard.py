"""
Scorecard Router

Scorecard photo scanning via Gemini Vision.
"""

import json as _json
import logging
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

logger = logging.getLogger("app.routers.scorecard")

router = APIRouter(prefix="/scorecard", tags=["scorecard"])


@router.post("/scan")
async def scan_scorecard_photo(
    file: UploadFile = File(...),
    players: str | None = Form(None),
) -> dict[str, Any]:
    """
    Upload a scorecard photo and extract running quarter totals via Gemini Vision.
    Returns extracted running totals and computed per-hole quarter deltas.
    Phase 1: no image persistence, process and return immediately.

    Optional form field:
    - players: JSON array of player name strings (e.g. '["CK","SS","SG"]').
      When provided, passed to the scan service as expected_players to guide
      tiled/guided scanning.
    """
    from ..services.scorecard_scan_service import scan_scorecard

    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
    content_type = file.content_type or "image/jpeg"
    if content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported image type: {content_type}. Use JPEG, PNG, or WebP.")

    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:  # 20MB limit
        raise HTTPException(status_code=400, detail="Image too large. Maximum size is 20MB.")

    # NOTE: we intentionally do NOT downscale here. Phone pics are ~4000px and the
    # dense handwritten cells need that detail. The scan service does the
    # preprocessing at full res and then sizes the image to the HIGHEST resolution
    # that fits Groq's ~4MB request budget (see _fit_image_to_budget) right before
    # the call — so the model gets maximum legible detail instead of a pre-shrunk 2048px.

    expected_players = None
    if players:
        try:
            parsed = _json.loads(players)
            if isinstance(parsed, list) and parsed:
                expected_players = [str(p) for p in parsed]
        except (ValueError, TypeError):
            expected_players = None

    try:
        result = await scan_scorecard(image_bytes, content_type, expected_players=expected_players)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Scorecard scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {e}")
