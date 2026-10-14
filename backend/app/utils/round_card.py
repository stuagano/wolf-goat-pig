"""Who may change a finished round's card: the players in that round, plus admins."""

from typing import Any

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..services.auth_service import get_current_user
from .admin_auth import is_admin_profile
from .time import utc_now


def can_edit_round(db: Session, game: models.GameStateModel, profile: Any) -> bool:
    """Admin, or a player in this round by profile id (state or GamePlayer) or Auth0 sub."""
    if is_admin_profile(profile):
        return True
    profile_id = getattr(profile, "id", None)
    auth0_id = (getattr(profile, "preferences", None) or {}).get("auth0_id")
    # Scanned rounds have no GamePlayer rows; their roster lives in state.
    if profile_id is not None and any(
        p.get("player_profile_id") == profile_id for p in (game.state or {}).get("players", [])
    ):
        return True
    rows = db.query(models.GamePlayer).filter(models.GamePlayer.game_id == game.game_id).all()
    return any(
        (profile_id is not None and r.player_profile_id == profile_id) or (auth0_id and r.user_id == auth0_id)
        for r in rows
    )


def require_round_member_or_admin(
    game_id: str,
    profile: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.PlayerProfile:
    game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Round not found")
    if not can_edit_round(db, game, profile):
        raise HTTPException(status_code=403, detail="Only players in this round or an admin can change its card")
    return profile


def mark_card_edited(state: dict, profile: Any) -> None:
    """Last edit only; full history is out of scope."""
    state["card_edited_by"] = getattr(profile, "name", None) or getattr(profile, "email", None)
    state["card_edited_at"] = utc_now().isoformat()
