"""In-app admin grants on linked player profiles; SUPER_ADMIN_EMAILS stays the floor."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import PlayerProfile
from ..utils.admin_auth import get_super_admin_emails, is_super_admin_email, require_admin
from ..utils.time import utc_now

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/admins", tags=["players"])


def _row(player: PlayerProfile) -> dict[str, Any]:
    return {
        "id": player.id,
        "name": player.name,
        "legacy_name": player.legacy_name,
        "email": player.email,
        "auth0_id": (player.preferences or {}).get("auth0_id"),
        "is_admin": bool(player.admin_granted),
        "admin_granted_by": player.admin_granted_by,
        "admin_granted_at": player.admin_granted_at,
    }


def _get(db: Session, player_id: int) -> PlayerProfile:
    player = db.query(PlayerProfile).filter(PlayerProfile.id == player_id).with_for_update().first()
    if not player:
        raise HTTPException(status_code=404, detail="Player profile not found")
    return player


@router.get("", dependencies=[Depends(require_admin)])
def list_admins(db: Session = Depends(get_db)) -> dict[str, Any]:
    flagged = (
        db.query(PlayerProfile)
        .filter(PlayerProfile.admin_granted == 1, PlayerProfile.is_active == 1)
        .order_by(PlayerProfile.id)
        .all()
    )
    return {"env_admins": sorted(get_super_admin_emails()), "profile_admins": [_row(p) for p in flagged]}


@router.post("/{player_id}")
def grant_admin(
    player_id: int, actor: dict[str, Any] = Depends(require_admin), db: Session = Depends(get_db)
) -> dict[str, Any]:
    player = _get(db, player_id)
    if not player.is_active or not (player.preferences or {}).get("auth0_id"):
        raise HTTPException(
            status_code=400,
            detail="This profile needs to sign in (and be linked) before it can be made an admin.",
        )
    auth0_id = player.preferences["auth0_id"]
    shared = db.query(PlayerProfile).filter(PlayerProfile.preferences["auth0_id"].as_string() == auth0_id).count()
    if shared > 1:
        raise HTTPException(
            status_code=400,
            detail="This login matches multiple profiles. Fix it in Account links before making it an admin.",
        )
    if not player.admin_granted:
        player.admin_granted = 1
        player.admin_granted_by = actor.get("email")
        player.admin_granted_at = utc_now().isoformat()
        db.commit()
        logger.info("Admin granted to profile %s by %s", player.id, actor.get("email"))
    return _row(player)


@router.delete("/{player_id}")
def revoke_admin(
    player_id: int, actor: dict[str, Any] = Depends(require_admin), db: Session = Depends(get_db)
) -> dict[str, Any]:
    player = _get(db, player_id)
    if is_super_admin_email(player.email):
        raise HTTPException(
            status_code=400,
            detail="This admin is set in the deployment config and can't be removed here.",
        )
    actor_is_env = is_super_admin_email(actor.get("email"))
    if not actor_is_env and (player.preferences or {}).get("auth0_id") == actor.get("sub"):
        raise HTTPException(status_code=400, detail="You can't remove your own admin access. Ask another admin.")
    if player.admin_granted:
        player.admin_granted = 0
        player.admin_granted_by = None
        player.admin_granted_at = None
        db.commit()
        logger.info("Admin revoked from profile %s by %s", player.id, actor.get("email"))
    return _row(player)
