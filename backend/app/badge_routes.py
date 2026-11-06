"""
API Routes for Achievement Badge System
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from .badge_engine import BadgeEngine
from .database import get_db
from .models import (
    Badge,
    GamePlayerResult,
    PlayerBadgeEarned,
    PlayerProfile,
)
from .services.auth_service import get_current_user
from .utils.admin_auth import require_admin

router = APIRouter(prefix="/api/badges", tags=["badges"])

MAX_SHOWCASE_SLOTS = 6


# ====================================================================================
# PYDANTIC MODELS (Request/Response Schemas)
# ====================================================================================


class BadgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    badge_id: int
    name: str
    description: str
    category: str
    rarity: str
    emoji: str | None
    image_url: str | None
    max_supply: int | None
    current_supply: int
    points_value: int
    tier: int | None
    series_id: int | None


class EarnedBadgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    badge: BadgeResponse
    earned_at: str
    serial_number: int
    game_record_id: int | None


# ====================================================================================
# BADGE DISCOVERY ENDPOINTS
# ====================================================================================


@router.get("/available", response_model=list[BadgeResponse])
def get_available_badges(
    category: str | None = None,
    rarity: str | None = None,
    db: Session = Depends(get_db),
) -> list[Badge]:
    """
    Get all available badges with optional filtering.
    Query params:
    - category: achievement, progression, seasonal, rare_event, collectible_series
    - rarity: common, rare, epic, legendary, mythic
    """
    query = db.query(Badge).filter(Badge.is_active == True)

    if category:
        query = query.filter(Badge.category == category)

    if rarity:
        query = query.filter(Badge.rarity == rarity)

    badges = query.order_by(
        # Sort by rarity tier, then by name. NOTE: sqlalchemy.case, not
        # func.case — the latter emits an invalid SQL function call and
        # 500'd this endpoint since it shipped.
        case(
            (Badge.rarity == "mythic", 5),
            (Badge.rarity == "legendary", 4),
            (Badge.rarity == "epic", 3),
            (Badge.rarity == "rare", 2),
            else_=1,
        ).desc(),
        Badge.name,
    ).all()

    return badges  # type: ignore[no-any-return]


@router.get("/player/{player_id}/earned", response_model=list[EarnedBadgeResponse])
def get_player_earned_badges(player_id: int, showcase_only: bool = False, db: Session = Depends(get_db)) -> Any:
    """
    Get all badges earned by a player.
    - showcase_only: Return only badges in player's showcase (top 6)
    """
    query = db.query(PlayerBadgeEarned).filter(PlayerBadgeEarned.player_profile_id == player_id)

    if showcase_only:
        query = query.filter(PlayerBadgeEarned.showcase_position.isnot(None))

    earned_badges = query.order_by(PlayerBadgeEarned.earned_at.desc()).all()

    # Enrich with badge details
    result = []
    for earned in earned_badges:
        badge = db.query(Badge).filter_by(id=earned.badge_id).first()
        if badge:
            result.append({**earned.__dict__, "badge": badge})

    return result


@router.post("/me/{earned_badge_id}/showcase")
def toggle_showcase_badge(
    earned_badge_id: int,
    current_user: PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Equip/unequip one of the current user's earned badges into their public
    showcase (max 6, shown first on the profile page). Toggles: calling this
    on an already-showcased badge un-equips it."""
    earned = (
        db.query(PlayerBadgeEarned)
        .filter(
            PlayerBadgeEarned.id == earned_badge_id,
            PlayerBadgeEarned.player_profile_id == current_user.id,
        )
        .first()
    )
    if not earned:
        raise HTTPException(status_code=404, detail="Badge not found")

    if earned.showcase_position is not None:
        earned.showcase_position = None
        db.commit()
        return {"showcased": False}

    showcased_count = (
        db.query(PlayerBadgeEarned)
        .filter(
            PlayerBadgeEarned.player_profile_id == current_user.id,
            PlayerBadgeEarned.showcase_position.isnot(None),
        )
        .count()
    )
    if showcased_count >= MAX_SHOWCASE_SLOTS:
        raise HTTPException(status_code=400, detail=f"Showcase is full (max {MAX_SHOWCASE_SLOTS})")

    earned.showcase_position = showcased_count + 1
    db.commit()
    return {"showcased": True, "position": earned.showcase_position}


@router.get("/player/{player_id}/stats")
def get_player_badge_stats(player_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get summary statistics about player's badge collection"""
    earned_count = db.query(PlayerBadgeEarned).filter(PlayerBadgeEarned.player_profile_id == player_id).count()

    # Count by rarity
    rarity_counts = (
        db.query(Badge.rarity, func.count(PlayerBadgeEarned.id))
        .join(PlayerBadgeEarned, Badge.id == PlayerBadgeEarned.badge_id)
        .filter(PlayerBadgeEarned.player_profile_id == player_id)
        .group_by(Badge.rarity)
        .all()
    )

    # Count by category
    category_counts = (
        db.query(Badge.category, func.count(PlayerBadgeEarned.id))
        .join(PlayerBadgeEarned, Badge.id == PlayerBadgeEarned.badge_id)
        .filter(PlayerBadgeEarned.player_profile_id == player_id)
        .group_by(Badge.category)
        .all()
    )

    # Total badges available
    total_available = db.query(Badge).filter(Badge.is_active == True).count()

    return {
        "total_earned": earned_count,
        "total_available": total_available,
        "completion_percentage": ((earned_count / total_available * 100) if total_available > 0 else 0),
        "by_rarity": {r: c for r, c in rarity_counts},
        "by_category": {cat: c for cat, c in category_counts},
    }


# ====================================================================================
# ADMIN ENDPOINTS (Badge Management)
# ====================================================================================


@router.post(
    "/admin/check-achievements/{player_id}",
    dependencies=[Depends(require_admin)],
)
def manually_check_achievements(
    player_id: int, game_record_id: int | None = None, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Trigger badge achievement check for a player.
    If game_record_id is not provided, uses the player's most recent game.
    """
    # If no game_record_id provided, find the most recent game for this player
    if game_record_id is None:
        latest_result = (
            db.query(GamePlayerResult)
            .filter(GamePlayerResult.player_profile_id == player_id)
            .order_by(GamePlayerResult.id.desc())
            .first()
        )
        if latest_result:
            game_record_id = latest_result.game_record_id

    if game_record_id is None:
        return {
            "message": "No game records found for player",
            "badges_earned": [],
        }

    engine = BadgeEngine(db)
    earned_badges = engine.check_post_game_achievements(game_record_id, player_id)

    # Build response with badge names
    badges_earned = []
    for b in earned_badges:
        badge = db.query(Badge).filter_by(id=b.badge_id).first()
        badges_earned.append(
            {
                "badge_id": b.badge_id,
                "name": badge.name if badge else "Unknown",
                "rarity": badge.rarity if badge else "common",
                "description": badge.description if badge else "",
                "serial_number": b.serial_number,
                "earned_at": b.earned_at,
            }
        )

    return {
        "message": f"Found {len(badges_earned)} new badges",
        "badges_earned": badges_earned,
    }
