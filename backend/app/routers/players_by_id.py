"""Players router — avatar, public profile and admin CRUD by ``player_id``."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services.player_service import PlayerService
from ..services.unified_data_service import get_unified_data_service
from ..utils.admin_auth import require_admin
from ..utils.api_helpers import handle_api_errors, require_not_none
from .players_avatar import (
    _avatar_jpeg_for_player,
)

logger = logging.getLogger("app.routers.players")

router = APIRouter(prefix="/players", tags=["players"])


# ============================================================================
# Player Profile CRUD by ID (parameterized - must be after static paths)
# ============================================================================


@router.get("/{player_id}/avatar")
@handle_api_errors(operation_name="get player avatar")
def get_player_avatar(player_id: int, db: Session = Depends(get_db)) -> Response:
    """Serve a player's uploaded avatar image. Public — used directly as an <img> src."""
    player = db.query(models.PlayerProfile).filter(models.PlayerProfile.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="No uploaded avatar for this player")
    image_bytes = _avatar_jpeg_for_player(player)
    if not image_bytes:
        raise HTTPException(status_code=404, detail="No uploaded avatar for this player")
    return Response(content=image_bytes, media_type="image/jpeg")


@router.get("/{player_id}/public-profile")
@handle_api_errors(operation_name="get public player profile")
def get_public_player_profile(
    player_id: int,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Public profile — no auth required. Returns only non-sensitive fields
    (no email, venmo, or GHIN id)."""
    player = db.query(models.PlayerProfile).filter(models.PlayerProfile.id == player_id).first()
    if not player:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Player not found")

    # Availability days (which days, no times)
    availability_rows = (
        db.query(models.PlayerAvailability).filter(models.PlayerAvailability.player_profile_id == player_id).all()
    )
    available_days = [a.day_of_week for a in availability_rows if a.is_available]

    # Stats
    stats = PlayerService(db).get_player_statistics(player_id)

    # Badges — showcased (equipped) ones first, in their chosen order, then
    # the rest by most-recently-earned.
    badge_rows = (
        db.query(models.PlayerBadgeEarned, models.Badge)
        .join(models.Badge, models.PlayerBadgeEarned.badge_id == models.Badge.id)
        .filter(models.PlayerBadgeEarned.player_profile_id == player_id)
        .order_by(
            models.PlayerBadgeEarned.showcase_position.is_(None),
            models.PlayerBadgeEarned.showcase_position,
            models.PlayerBadgeEarned.earned_at.desc(),
        )
        .limit(12)
        .all()
    )
    badges = [
        {
            "id": pbe.id,
            "name": b.name,
            "description": b.description,
            "rarity": b.rarity,
            "category": b.category,
            "emoji": b.emoji,
            "earned_at": pbe.earned_at,
            "showcased": pbe.showcase_position is not None,
        }
        for pbe, b in badge_rows
    ]
    total_badges = db.query(models.Badge).count()

    # Game history — actual played/scored rounds (sheet-synced + in-app).
    game_history = []
    if player.legacy_name or player.name:
        from ..services.canonical_round_reads import canonical_mode

        service = get_unified_data_service(db=db)
        rounds = (
            service.get_profile_history(player_id)
            if canonical_mode(db)
            else service.get_player_history(player.legacy_name or player.name)
        )
        game_history = [
            {
                "date": r.date_sortable,
                "location": r.location,
                "group": r.group,
                "score": r.score,
                "duration": r.duration,
                "source": r.source,
                "game_id": r.game_id,
                "participant_id": r.participant_id,
                "score_eligible": r.score_eligible,
                "detail_coverage": r.detail_coverage,
                # Only ever present for rounds scored live in the app or via
                # scorecard scan — legacy sheet rounds are a total only.
                "holes": (
                    [
                        {"hole": h.get("hole"), "quarters": h.get("quarters"), "gross_score": h.get("gross_score")}
                        for h in sorted(r.hole_scores, key=lambda h: h.get("hole") or 0)
                    ]
                    if r.hole_scores
                    else None
                ),
            }
            for r in rounds[:20]
        ]

    return {
        "id": player.id,
        "name": player.name,
        "handicap": player.handicap,
        "description": player.description,
        "avatar_url": player.avatar_url,
        "has_avatar_image": bool(player.has_avatar_image),
        "last_played": player.last_played,
        "created_at": player.created_at,
        "available_days": available_days,
        "game_history": game_history,
        "badges": badges,
        "total_badges": total_badges,
        "stats": {
            "games_played": stats.games_played if stats else 0,
            "known_participation_count": stats.known_participation_count if stats else 0,
            "incomplete_round_count": stats.incomplete_round_count if stats else 0,
            "games_won": stats.games_won if stats else 0,
            "total_earnings": stats.total_earnings if stats else 0.0,
            "solo_wins": stats.solo_wins if stats else 0,
        },
    }


@router.get("/{player_id}", response_model=schemas.PlayerProfileResponse, dependencies=[Depends(require_admin)])
@handle_api_errors(operation_name="get player profile")
def get_player_profile(player_id: int, db: Session = Depends(get_db)) -> schemas.PlayerProfileResponse:
    """Get a specific player profile."""
    player_service = PlayerService(db)
    profile = player_service.get_player_profile(player_id)
    return require_not_none(profile, "Player", player_id)


@router.put("/{player_id}", response_model=schemas.PlayerProfileResponse, dependencies=[Depends(require_admin)])
@handle_api_errors(operation_name="update player profile")
def update_player_profile(
    player_id: int,
    profile_update: schemas.PlayerProfileUpdate,
    db: Session = Depends(get_db),
) -> schemas.PlayerProfileResponse:
    """Update a player profile."""
    player_service = PlayerService(db)
    updated_profile = player_service.update_player_profile(player_id, profile_update)
    result = require_not_none(updated_profile, "Player", player_id)
    logger.info(f"Updated player profile {player_id}")
    return result


@router.delete("/{player_id}", dependencies=[Depends(require_admin)])
@handle_api_errors(operation_name="delete player profile")
def delete_player_profile(player_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    """Delete (deactivate) a player profile."""
    player_service = PlayerService(db)
    success = player_service.delete_player_profile(player_id)
    if not success:
        require_not_none(None, "Player", player_id)  # Raises 404
    logger.info(f"Deleted player profile {player_id}")
    return {"message": f"Player {player_id} has been deleted"}
