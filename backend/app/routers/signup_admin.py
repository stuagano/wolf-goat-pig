"""Admin: put a linked player on an upcoming day's sign-up sheet.

For players who ask an organizer to sign them up (e.g. by text). The sign-up is
created exactly as the player's own would be — same roster name, duplicate
check, confirmation email and legacy-sync hook — and the adding admin is logged.
Removing uses the existing cancel endpoint, which admins may call on any sign-up.
"""

import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services.legacy_signup_service import get_legacy_signup_service
from ..utils.admin_auth import require_admin
from ..utils.time import club_today, utc_now
from .signups import _send_signup_confirmation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/signups/admin", tags=["signups"])


class AdminSignupCreate(BaseModel):
    date: date
    player_profile_id: int = Field(..., gt=0)
    notes: str | None = Field(None, max_length=500)


@router.get("/players", dependencies=[Depends(require_admin)])
def list_signup_players(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Active profiles linked to a club roster name — the only players an admin can add."""
    players = (
        db.query(models.PlayerProfile)
        .filter(models.PlayerProfile.is_active == 1, models.PlayerProfile.legacy_name.isnot(None))
        .order_by(func.lower(models.PlayerProfile.legacy_name))
        .all()
    )
    return {"players": [{"id": p.id, "legacy_name": p.legacy_name} for p in players if (p.legacy_name or "").strip()]}


@router.post("", response_model=schemas.DailySignupResponse)
def admin_add_signup(
    body: AdminSignupCreate,
    admin: dict[str, Any] = Depends(require_admin),
    db: Session = Depends(get_db),
) -> schemas.DailySignupResponse:
    if body.date < club_today():
        raise HTTPException(status_code=400, detail="Pick today or a future date.")
    player = db.get(models.PlayerProfile, body.player_profile_id)
    if player is None or not player.is_active or not (player.legacy_name or "").strip():
        raise HTTPException(status_code=400, detail="That player isn't linked to a club roster name yet.")

    signup_date = body.date.isoformat()
    existing = (
        db.query(models.DailySignup)
        .filter(
            models.DailySignup.date == signup_date,
            models.DailySignup.player_profile_id == player.id,
            models.DailySignup.status != "cancelled",
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Player already signed up for this date")

    now = utc_now().isoformat()
    signup = models.DailySignup(
        date=signup_date,
        player_profile_id=player.id,
        player_name=player.legacy_name,
        signup_time=now,
        notes=body.notes,
        status="signed_up",
        created_at=now,
        updated_at=now,
    )
    db.add(signup)
    db.commit()
    db.refresh(signup)
    logger.info(
        "Admin %s signed up %s (profile %s) for %s", admin.get("email"), player.legacy_name, player.id, signup_date
    )

    try:
        get_legacy_signup_service().sync_signup_created(signup)
    except Exception:
        logger.exception("Legacy signup sync failed for admin create id=%s", signup.id)
    _send_signup_confirmation(signup.id, player.email, player.legacy_name, signup_date)
    return schemas.DailySignupResponse.from_orm(signup)
