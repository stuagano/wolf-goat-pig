"""
API Routes for Achievement Badge System
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from .badge_engine import BadgeEngine
from .database import get_db
from .models import (
    Badge,
    BadgeProgress,
    BadgeSeries,
    GamePlayerResult,
    PlayerBadgeEarned,
    PlayerProfile,
    PlayerSeriesProgress,
)

router = APIRouter(prefix="/api/badges", tags=["badges"])


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


class BadgeProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    badge: BadgeResponse
    current_progress: int
    target_progress: int
    progress_percentage: float
    last_progress_date: str | None


class SeriesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    badge_count: int
    badges_earned: int
    is_completed: bool
    completion_badge: BadgeResponse | None


class BadgeLeaderboardEntry(BaseModel):
    player_id: int
    player_name: str
    serial_number: int
    earned_at: str


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
        # Sort by rarity tier, then by name
        func.case(
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


@router.get("/player/{player_id}/progress", response_model=list[BadgeProgressResponse])
def get_player_badge_progress(
    player_id: int, include_completed: bool = False, db: Session = Depends(get_db)
) -> list[dict[str, Any]]:
    """
    Get player's progress toward unearned badges.
    - include_completed: Include badges already earned
    """
    # Get all progression badges
    progress_records = db.query(BadgeProgress).filter(BadgeProgress.player_profile_id == player_id).all()

    result = []
    for progress in progress_records:
        # Check if already earned
        if not include_completed:
            has_badge = (
                db.query(PlayerBadgeEarned)
                .filter(
                    and_(
                        PlayerBadgeEarned.player_profile_id == player_id,
                        PlayerBadgeEarned.badge_id == progress.badge_id,
                    )
                )
                .first()
            )
            if has_badge:
                continue

        badge = db.query(Badge).filter_by(id=progress.badge_id).first()
        if badge:
            result.append(
                {
                    "badge": badge,
                    "current_progress": progress.current_progress,
                    "target_progress": progress.target_progress,
                    "progress_percentage": progress.progress_percentage,
                    "last_progress_date": progress.last_progress_date,
                }
            )

    return result


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
# SERIES / COLLECTION ENDPOINTS
# ====================================================================================


@router.get("/series", response_model=list[SeriesResponse])
def get_badge_series(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Get all badge series/collections"""
    series_list = db.query(BadgeSeries).filter(BadgeSeries.is_active == True).all()

    result = []
    for series in series_list:
        # Get completion badge if exists
        completion_badge = None
        if series.completion_badge_id:
            completion_badge = db.query(Badge).filter_by(id=series.completion_badge_id).first()

        result.append(
            {
                **series.__dict__,
                "badges_earned": 0,  # Will be filled by player-specific endpoint
                "is_completed": False,
                "completion_badge": completion_badge,
            }
        )

    return result


@router.get("/series/player/{player_id}", response_model=list[SeriesResponse])
def get_player_series_progress(player_id: int, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Get player's progress on all badge series"""
    series_list = db.query(BadgeSeries).filter(BadgeSeries.is_active == True).all()

    result = []
    for series in series_list:
        # Get player's progress
        progress = (
            db.query(PlayerSeriesProgress)
            .filter(
                and_(
                    PlayerSeriesProgress.player_profile_id == player_id,
                    PlayerSeriesProgress.series_id == series.id,
                )
            )
            .first()
        )

        # Get completion badge
        completion_badge = None
        if series.completion_badge_id:
            completion_badge = db.query(Badge).filter_by(id=series.completion_badge_id).first()

        result.append(
            {
                **series.__dict__,
                "badges_earned": progress.badges_earned if progress else 0,
                "is_completed": progress.is_completed if progress else False,
                "completion_badge": completion_badge,
            }
        )

    return result


# ====================================================================================
# LEADERBOARD ENDPOINTS
# ====================================================================================


@router.get("/leaderboard/badge/{badge_id}", response_model=list[BadgeLeaderboardEntry])
def get_badge_leaderboard(badge_id: int, limit: int = 100, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """
    Get leaderboard for a specific badge (who has it, serial numbers).
    Useful for rare badges to see who the elite owners are.
    """
    badge = db.query(Badge).filter_by(id=badge_id).first()
    if not badge:
        raise HTTPException(status_code=404, detail="Badge not found")

    earned_records = (
        db.query(PlayerBadgeEarned, PlayerProfile.name)
        .join(PlayerProfile, PlayerBadgeEarned.player_profile_id == PlayerProfile.id)
        .filter(PlayerBadgeEarned.badge_id == badge_id)
        .order_by(PlayerBadgeEarned.serial_number.asc())
        .limit(limit)
        .all()
    )

    result = []
    for earned, player_name in earned_records:
        result.append(
            {
                "player_id": earned.player_profile_id,
                "player_name": player_name,
                "serial_number": earned.serial_number,
                "earned_at": earned.earned_at,
            }
        )

    return result


@router.get("/leaderboard/top-collectors")
def get_top_collectors(limit: int = 50, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Get players with most badges earned"""
    top_collectors = (
        db.query(
            PlayerProfile.id,
            PlayerProfile.name,
            func.count(PlayerBadgeEarned.id).label("badge_count"),
        )
        .join(PlayerBadgeEarned, PlayerProfile.id == PlayerBadgeEarned.player_profile_id)
        .group_by(PlayerProfile.id, PlayerProfile.name)
        .order_by(desc("badge_count"))
        .limit(limit)
        .all()
    )

    result = []
    for player_id, player_name, badge_count in top_collectors:
        # Get rarity breakdown
        rarity_counts = (
            db.query(Badge.rarity, func.count(PlayerBadgeEarned.id))
            .join(PlayerBadgeEarned, Badge.id == PlayerBadgeEarned.badge_id)
            .filter(PlayerBadgeEarned.player_profile_id == player_id)
            .group_by(Badge.rarity)
            .all()
        )

        result.append(
            {
                "player_id": player_id,
                "player_name": player_name,
                "total_badges": badge_count,
                "by_rarity": {r: c for r, c in rarity_counts},
            }
        )

    return result


# ====================================================================================
# ADMIN ENDPOINTS (Badge Management)
# ====================================================================================


@router.post("/admin/check-achievements/{player_id}")
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


@router.get("/admin/badge/{badge_id}/holders")
def get_badge_holders(badge_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get detailed information about who holds a specific badge"""
    holders = (
        db.query(PlayerBadgeEarned, PlayerProfile.name, PlayerProfile.email)
        .join(PlayerProfile, PlayerBadgeEarned.player_profile_id == PlayerProfile.id)
        .filter(PlayerBadgeEarned.badge_id == badge_id)
        .order_by(PlayerBadgeEarned.serial_number.asc())
        .all()
    )

    return {
        "badge_id": badge_id,
        "total_holders": len(holders),
        "holders": [
            {
                "player_id": h[0].player_profile_id,
                "player_name": h[1],
                "player_email": h[2],
                "serial_number": h[0].serial_number,
                "earned_at": h[0].earned_at,
            }
            for h in holders
        ],
    }
