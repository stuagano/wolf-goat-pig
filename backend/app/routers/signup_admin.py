"""Admin: put a player on an upcoming day's sign-up sheet.

For players who ask an organizer to sign them up (e.g. by text). The sign-up is
created exactly as the player's own would be — roster name when linked, otherwise
the profile name — with the same duplicate check, confirmation email and
legacy-sync hook. The adding admin is logged. Removing uses the existing cancel
endpoint, which admins may call on any sign-up.
"""

import logging
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services.legacy_signup_service import get_legacy_signup_service
from ..services.signup_identity import roster_link, signup_display_name
from ..utils.admin_auth import require_admin
from ..utils.time import club_today, utc_now
from .signups import notify_signup_joined

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/signups/admin", tags=["signups"])


class AdminSignupCreate(BaseModel):
    date: date
    player_profile_id: int = Field(..., gt=0)
    notes: str | None = Field(None, max_length=500)


@router.get("/players", dependencies=[Depends(require_admin)])
def list_signup_players(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Active profiles an admin can add. ``name`` is what the sheet will show."""
    players = db.query(models.PlayerProfile).filter(models.PlayerProfile.is_active == 1).all()
    choices = []
    for player in players:
        display = signup_display_name(player)
        if not display:
            continue
        choices.append({"id": player.id, "name": display, "legacy_name": roster_link(player.legacy_name)})
    choices.sort(key=lambda row: row["name"].casefold())
    return {"players": choices}


@router.post("", response_model=schemas.DailySignupResponse)
def admin_add_signup(
    body: AdminSignupCreate,
    admin: dict[str, Any] = Depends(require_admin),
    db: Session = Depends(get_db),
) -> schemas.DailySignupResponse:
    if body.date < club_today():
        raise HTTPException(status_code=400, detail="Pick today or a future date.")
    player = db.get(models.PlayerProfile, body.player_profile_id)
    display_name = signup_display_name(player) if player is not None and player.is_active else None
    if not display_name:
        raise HTTPException(status_code=400, detail="That player needs a name before they can be signed up.")

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
        player_name=display_name,
        signup_time=now,
        notes=body.notes,
        status="signed_up",
        created_at=now,
        updated_at=now,
    )
    db.add(signup)
    db.commit()
    db.refresh(signup)
    logger.info("Admin %s signed up %s (profile %s) for %s", admin.get("email"), display_name, player.id, signup_date)

    if roster_link(player.legacy_name):
        try:
            get_legacy_signup_service().sync_signup_created(signup)
        except Exception:
            logger.exception("Legacy signup sync failed for admin create id=%s", signup.id)
    notify_signup_joined(signup.id, player.email, display_name, signup_date)
    return schemas.DailySignupResponse.from_orm(signup)
