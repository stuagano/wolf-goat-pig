"""HTTP API for the scorecard vision agent."""

from __future__ import annotations

import json as _json
import logging
from typing import Any

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile

from .agent import scan_scorecard
from .config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("scorecard_agent")

app = FastAPI(title="WGP Scorecard Vision Agent", version="0.1.0")


def _check_auth(authorization: str | None) -> None:
    secret = get_settings().scorecard_service_secret
    if not secret:
        return
    if authorization != f"Bearer {secret}":
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.on_event("startup")
async def _startup() -> None:
    settings = get_settings()
    logger.info(
        "scorecard-agent starting model=%s project=%s",
        settings.vision_model,
        settings.gcp_project_id,
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/scan")
async def scan_scorecard_photo(
    file: UploadFile = File(...),
    players: str | None = Form(None),
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    """Extract running quarter totals from a scorecard photo via Vertex Gemini."""
    _check_auth(authorization)

    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}
    content_type = file.content_type or "image/jpeg"
    if content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported image type: {content_type}. Use JPEG, PNG, or WebP.")

    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large. Maximum size is 20MB.")

    expected_players = None
    if players:
        try:
            parsed = _json.loads(players)
            if isinstance(parsed, list) and parsed:
                expected_players = [str(p) for p in parsed]
        except (ValueError, TypeError):
            expected_players = None

    try:
        return await scan_scorecard(image_bytes, content_type, expected_players)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Scorecard scan failed")
        raise HTTPException(status_code=500, detail=f"Scan failed: {exc}") from exc
