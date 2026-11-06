"""Pending capture queue for golfers not yet on the legacy dropdown.

Self-signed-up golfers with no canonical roster match are queued in
``pending_legacy_players``. An admin promotes a row into the canonical roster
(``legacy_player_service.add_legacy_player``) once the golfer is on Jeff's
dropdown, or dismisses it. These functions are re-exported from
``legacy_player_service`` for existing callers.

Canonical roster helpers are imported inside the functions that use them:
``legacy_player_service`` imports this module, so a module-level import back
would be circular.
"""

from __future__ import annotations

import logging
from typing import Any

from ..database import SessionLocal
from ..models import PendingLegacyPlayer
from ..utils.time import utc_now
from .pending_signup_service import resolve_stale_pending

logger = logging.getLogger(__name__)


def capture_pending_player(
    name: str,
    *,
    email: str | None = None,
    player_profile_id: int | None = None,
    db: Any = None,
) -> dict:
    """Capture a self-signed-up golfer who has no canonical match yet.

    No-op when the name is already canonical or already queued. Returns a dict
    describing what happened (``captured`` flag + reason).
    """
    from .legacy_player_service import get_canonical_name

    name = (name or "").strip()
    if not name or name == "Unknown Player":
        return {"captured": False, "reason": "blank_or_unknown"}

    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        if get_canonical_name(name, db):
            return {"captured": False, "reason": "already_canonical"}

        already = (
            db.query(PendingLegacyPlayer)
            .filter(PendingLegacyPlayer.name == name, PendingLegacyPlayer.status == "pending")
            .first()
        )
        if already:
            return {"captured": False, "reason": "already_pending", "pending_id": already.id}

        row = PendingLegacyPlayer(
            name=name,
            email=email,
            player_profile_id=player_profile_id,
            status="pending",
            created_at=utc_now().isoformat(),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        logger.info(f"Captured pending legacy player '{name}' (id={row.id})")
        return {"captured": True, "pending_id": row.id, "name": name}
    finally:
        if own_session:
            db.close()


def list_pending_players(status: str = "pending", db: Any = None) -> list[dict]:
    """List capture-queue rows for the given status (default: pending)."""
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        if status == "pending":
            # Self-heal rows already handled elsewhere so they never show as tasks.
            resolve_stale_pending(db)
        rows = (
            db.query(PendingLegacyPlayer)
            .filter(PendingLegacyPlayer.status == status)
            .order_by(PendingLegacyPlayer.created_at.desc())
            .all()
        )
        return [
            {
                "id": r.id,
                "name": r.name,
                "email": r.email,
                "player_profile_id": r.player_profile_id,
                "status": r.status,
                "created_at": r.created_at,
                "resolved_at": r.resolved_at,
            }
            for r in rows
        ]
    finally:
        if own_session:
            db.close()


def promote_pending_player(pending_id: int, db: Any = None, *, name: str | None = None) -> dict:
    """Promote a pending capture into the canonical roster.

    Call this once the player has been added to Jeff's legacy dropdown. When
    the capture came from an authenticated profile, link that same profile to
    the newly canonical name. Never overwrite a different existing link.

    ``name`` overrides the captured name. Sign-ups whose Auth0 profile had no
    display name are captured under their email, so the admin supplies the
    golfer's roster name here. An existing roster name links to that player.
    """
    from .legacy_player_service import add_legacy_player, link_profile_to_canonical_name

    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        row = db.query(PendingLegacyPlayer).filter(PendingLegacyPlayer.id == pending_id).first()
        if not row:
            return {"promoted": False, "message": f"No pending player with id={pending_id}"}
        if row.status != "pending":
            return {"promoted": False, "message": f"Pending player id={pending_id} is already {row.status}"}

        roster_name = (name or "").strip() or row.name
        roster_result = add_legacy_player(roster_name, source="promoted", db=db)
        if roster_result.get("invalid"):
            message = roster_result["message"]
            if "@" in roster_name:
                message = f"{message}. Enter the golfer's name to promote this sign-up."
            return {"promoted": False, "invalid": True, "message": message}
        canonical_name = str(roster_result.get("canonical_name") or roster_name)

        profile_link_status = "no_profile"
        if row.player_profile_id is not None:
            link_result = link_profile_to_canonical_name(db, row.player_profile_id, canonical_name)
            profile_link_status = link_result["status"]
            if profile_link_status == "missing_profile":
                logger.warning(
                    "Promoted pending player '%s', but player profile id=%s no longer exists",
                    row.name,
                    row.player_profile_id,
                )
            elif not link_result["linked"]:
                logger.warning(
                    "Promoted pending player '%s' without linking profile id=%s (status=%s)",
                    row.name,
                    row.player_profile_id,
                    profile_link_status,
                )

        row.status = "promoted"
        row.resolved_at = utc_now().isoformat()
        db.commit()
        logger.info(f"Promoted pending player id={pending_id} to canonical roster as '{canonical_name}'")
        return {
            "promoted": True,
            "canonical_name": canonical_name,
            "profile_linked": profile_link_status in {"linked", "already_linked"},
            "profile_link_status": profile_link_status,
        }
    finally:
        if own_session:
            db.close()


def dismiss_pending_player(pending_id: int, db: Any = None) -> dict:
    """Dismiss a pending capture (e.g. a misspelling of an existing player)."""
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        row = db.query(PendingLegacyPlayer).filter(PendingLegacyPlayer.id == pending_id).first()
        if not row:
            return {"dismissed": False, "message": f"No pending player with id={pending_id}"}

        row.status = "dismissed"
        row.resolved_at = utc_now().isoformat()
        db.commit()
        logger.info(f"Dismissed pending player '{row.name}' (id={pending_id})")
        return {"dismissed": True, "name": row.name}
    finally:
        if own_session:
            db.close()
