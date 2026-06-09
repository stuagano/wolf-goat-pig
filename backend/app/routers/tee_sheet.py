"""
Tee Sheet Integration Router

Pushes game players to the thousand-cranes.com WGP tee sheet.
Endpoint: POST https://thousand-cranes.com/WolfGoatPig/wgp_add_tee_sheet_ajax.cgi
Params:   date=YYYY-MM-DD, name=<player name>, type=member
"""

import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

logger = logging.getLogger("app.routers.tee_sheet")

router = APIRouter(prefix="/tee-sheet", tags=["tee-sheet"])

TEE_SHEET_URL = "https://thousand-cranes.com/WolfGoatPig/wgp_add_tee_sheet_ajax.cgi"
TEE_SHEET_REFERER = "https://thousand-cranes.com/WolfGoatPig/wgp_tee_sheet.cgi"


class TeeSheetPushRequest(BaseModel):
    game_id: str
    date: str  # YYYY-MM-DD


def _tee_sheet_name(profile: models.PlayerProfile | None, fallback: str) -> str:
    if profile and profile.legacy_name:
        return str(profile.legacy_name)
    return fallback


@router.post("/push")
async def push_game_to_tee_sheet(
    request: TeeSheetPushRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Push all players in a game to the thousand-cranes.com tee sheet."""
    game = db.query(models.GameStateModel).filter(
        models.GameStateModel.game_id == request.game_id
    ).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    players = (
        db.query(models.GamePlayer)
        .filter(models.GamePlayer.game_id == request.game_id)
        .order_by(models.GamePlayer.player_slot_id)
        .all()
    )
    if not players:
        raise HTTPException(status_code=400, detail="No players in game")

    pushed = []
    skipped = []
    errors = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        for gp in players:
            profile = None
            if gp.player_profile_id:
                profile = db.query(models.PlayerProfile).filter(
                    models.PlayerProfile.id == gp.player_profile_id
                ).first()

            name = _tee_sheet_name(profile, gp.player_name or "")
            if not name:
                skipped.append({"player": gp.player_name, "reason": "no name"})
                continue

            try:
                resp = await client.post(
                    TEE_SHEET_URL,
                    data={"date": request.date, "name": name, "type": "member"},
                    headers={"Referer": TEE_SHEET_REFERER},
                )
                if resp.status_code == 200:
                    pushed.append({"player": gp.player_name, "tee_sheet_name": name})
                    logger.info("Pushed %s to tee sheet for %s", name, request.date)
                else:
                    errors.append({"player": gp.player_name, "reason": f"HTTP {resp.status_code}"})
            except Exception as e:
                logger.error("Failed to push %s: %s", name, e)
                errors.append({"player": gp.player_name, "reason": str(e)})

    return {"date": request.date, "pushed": pushed, "skipped": skipped, "errors": errors}
