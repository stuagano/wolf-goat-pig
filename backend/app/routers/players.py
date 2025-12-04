"""
Players Router (Refactored)

Player profile management, statistics, analytics, availability, and preferences.

This is a refactored version demonstrating the new utility patterns:
- @handle_api_errors decorator for consistent error handling
- Dependency injection for database sessions
- require_not_none helper for 404 handling
- Cleaner, more maintainable code

To migrate: Replace players.py with this file after testing.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, cast

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services.auth_service import get_current_user
from ..services.player_service import PlayerService
from ..utils.api_helpers import handle_api_errors, require_not_none, ApiResponse

logger = logging.getLogger("app.routers.players")

router = APIRouter(
    prefix="/players",
    tags=["players"]
)


# ============================================================================
# Player Profile CRUD Endpoints
# ============================================================================

@router.post("", response_model=schemas.PlayerProfileResponse)
@handle_api_errors(operation_name="create player profile")
def create_player_profile(
    profile: schemas.PlayerProfileCreate,
    db: Session = Depends(get_db)
) -> schemas.PlayerProfileResponse:
    """Create a new player profile."""
    player_service = PlayerService(db)
    result = player_service.create_player_profile(profile)
    logger.info(f"Created player profile: {result.name}")
    return result


@router.get("", response_model=List[schemas.PlayerProfileResponse])
@handle_api_errors(operation_name="get player profiles")
def get_all_player_profiles(
    active_only: bool = Query(True, description="Return only active profiles"),
    db: Session = Depends(get_db)
) -> List[schemas.PlayerProfileResponse]:
    """Get all player profiles."""
    player_service = PlayerService(db)
    profiles = player_service.get_all_player_profiles(active_only=active_only)
    logger.info(f"Retrieved {len(profiles)} player profiles")
    return profiles


@router.get("/{player_id}", response_model=schemas.PlayerProfileResponse)
@handle_api_errors(operation_name="get player profile")
def get_player_profile(
    player_id: int,
    db: Session = Depends(get_db)
) -> schemas.PlayerProfileResponse:
    """Get a specific player profile."""
    player_service = PlayerService(db)
    profile = player_service.get_player_profile(player_id)
    return require_not_none(profile, "Player", player_id)


@router.put("/{player_id}", response_model=schemas.PlayerProfileResponse)
@handle_api_errors(operation_name="update player profile")
def update_player_profile(
    player_id: int,
    profile_update: schemas.PlayerProfileUpdate,
    db: Session = Depends(get_db)
) -> schemas.PlayerProfileResponse:
    """Update a player profile."""
    player_service = PlayerService(db)
    updated_profile = player_service.update_player_profile(player_id, profile_update)
    result = require_not_none(updated_profile, "Player", player_id)
    logger.info(f"Updated player profile {player_id}")
    return result


@router.delete("/{player_id}")
@handle_api_errors(operation_name="delete player profile")
def delete_player_profile(
    player_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Delete (deactivate) a player profile."""
    player_service = PlayerService(db)
    success = player_service.delete_player_profile(player_id)
    if not success:
        require_not_none(None, "Player", player_id)  # Raises 404
    logger.info(f"Deleted player profile {player_id}")
    return {"message": f"Player {player_id} has been deleted"}


# ============================================================================
# Player Search Endpoints
# ============================================================================

@router.get("/all", response_model=List[schemas.PlayerProfileResponse])
@handle_api_errors(operation_name="get all players")
def get_all_players(
    active_only: bool = Query(True, description="Only return active players"),
    db: Session = Depends(get_db)
) -> List[schemas.PlayerProfileResponse]:
    """Get all player profiles."""
    player_service = PlayerService(db)
    return player_service.get_all_player_profiles(active_only=active_only)


@router.get("/name/{player_name}", response_model=schemas.PlayerProfileResponse)
@handle_api_errors(operation_name="get player by name")
def get_player_profile_by_name(
    player_name: str,
    db: Session = Depends(get_db)
) -> schemas.PlayerProfileResponse:
    """Get a player profile by name."""
    player_service = PlayerService(db)
    profile = player_service.get_player_profile_by_name(player_name)
    return require_not_none(profile, "Player", player_name)


# ============================================================================
# Player Statistics Endpoints
# ============================================================================

@router.get("/{player_id}/statistics", response_model=schemas.PlayerStatisticsResponse)
@handle_api_errors(operation_name="get player statistics")
def get_player_statistics(
    player_id: int,
    db: Session = Depends(get_db)
) -> schemas.PlayerStatisticsResponse:
    """Get player statistics."""
    player_service = PlayerService(db)
    stats = player_service.get_player_statistics(player_id)
    return require_not_none(stats, "Statistics for player", player_id)


@router.get("/{player_id}/analytics", response_model=schemas.PlayerPerformanceAnalytics)
@handle_api_errors(operation_name="get player analytics")
def get_player_analytics(
    player_id: int,
    db: Session = Depends(get_db)
) -> schemas.PlayerPerformanceAnalytics:
    """Get comprehensive player performance analytics."""
    player_service = PlayerService(db)
    analytics = player_service.get_player_performance_analytics(player_id)
    return require_not_none(analytics, "Analytics for player", player_id)


@router.get("/{player_id}/profile-with-stats", response_model=schemas.PlayerProfileWithStats)
@handle_api_errors(operation_name="get player profile with stats")
def get_player_profile_with_stats(
    player_id: int,
    db: Session = Depends(get_db)
) -> schemas.PlayerProfileWithStats:
    """Get player profile combined with statistics and achievements."""
    player_service = PlayerService(db)

    profile_result = player_service.get_player_profile(player_id)
    profile = require_not_none(profile_result, "Player", player_id)

    stats = player_service.get_player_statistics(player_id)
    if not stats:
        # Create empty stats if none exist
        stats = schemas.PlayerStatisticsResponse(
            id=0, player_id=player_id, games_played=0, games_won=0,
            total_earnings=0.0, holes_played=0, holes_won=0,
            avg_earnings_per_hole=0.0, betting_success_rate=0.0,
            successful_bets=0, total_bets=0, partnership_success_rate=0.0,
            partnerships_formed=0, partnerships_won=0, solo_attempts=0,
            solo_wins=0, favorite_game_mode="wolf_goat_pig", preferred_player_count=4,
            best_hole_performance=[], worst_hole_performance=[],
            performance_trends=[], last_updated=datetime.now(timezone.utc).isoformat()
        )

    recent_achievements: List[Any] = []  # Placeholder for future implementation

    return schemas.PlayerProfileWithStats(
        profile=profile,
        statistics=stats,
        recent_achievements=recent_achievements
    )


# ============================================================================
# Advanced Analytics Endpoints
# ============================================================================

@router.get("/{player_id}/advanced-metrics")
@handle_api_errors(operation_name="get advanced metrics")
def get_player_advanced_metrics(
    player_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get advanced performance metrics for a player."""
    from ..services.statistics_service import StatisticsService

    stats_service = StatisticsService(db)
    metrics = stats_service.get_advanced_player_metrics(player_id)

    return ApiResponse.success(
        data={"player_id": player_id, "metrics": metrics},
        message="Advanced metrics retrieved"
    )


@router.get("/{player_id}/trends")
@handle_api_errors(operation_name="get player trends")
def get_player_trends(
    player_id: int,
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get performance trends for a player."""
    from ..services.statistics_service import StatisticsService

    stats_service = StatisticsService(db)
    trends = stats_service.get_performance_trends(player_id, days=days)

    return ApiResponse.success(
        data={"player_id": player_id, "period_days": days, "trends": trends},
        message="Trends retrieved"
    )


@router.get("/{player_id}/insights")
@handle_api_errors(operation_name="get player insights")
def get_player_insights(
    player_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get personalized insights and recommendations for a player."""
    from ..services.statistics_service import StatisticsService

    stats_service = StatisticsService(db)
    insights = stats_service.get_player_insights(player_id)

    return ApiResponse.success(
        data={
            "player_id": player_id,
            "insights": [insight.__dict__ for insight in insights]
        },
        message="Insights generated"
    )


@router.get("/{player_id}/skill-rating")
@handle_api_errors(operation_name="get skill rating")
def get_player_skill_rating(
    player_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get skill rating for a player."""
    from ..services.statistics_service import StatisticsService

    stats_service = StatisticsService(db)
    rating = stats_service.calculate_skill_rating(player_id)

    return ApiResponse.success(
        data={"player_id": player_id, "skill_rating": rating},
        message="Skill rating calculated"
    )


@router.get("/{player_id}/head-to-head/{opponent_id}")
@handle_api_errors(operation_name="get head-to-head")
def get_head_to_head(
    player_id: int,
    opponent_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get head-to-head record between two players."""
    from ..services.statistics_service import StatisticsService

    stats_service = StatisticsService(db)
    h2h = stats_service.get_head_to_head(player_id, opponent_id)

    return ApiResponse.success(
        data={"player_id": player_id, "opponent_id": opponent_id, "head_to_head": h2h},
        message="Head-to-head record retrieved"
    )


@router.get("/{player_id}/head-to-head")
@handle_api_errors(operation_name="get all head-to-head records")
def get_all_head_to_head(
    player_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get head-to-head records against all opponents."""
    from ..services.statistics_service import StatisticsService

    stats_service = StatisticsService(db)
    h2h_records = stats_service.get_all_head_to_head(player_id)

    return ApiResponse.success(
        data={"player_id": player_id, "opponents": h2h_records},
        message="All head-to-head records retrieved"
    )


@router.get("/{player_id}/streaks")
@handle_api_errors(operation_name="get streak analysis")
def get_streak_analysis(
    player_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed streak analysis for a player."""
    from ..services.statistics_service import StatisticsService

    stats_service = StatisticsService(db)
    streaks = stats_service.get_streak_analysis(player_id)

    return ApiResponse.success(
        data={"player_id": player_id, "streaks": streaks},
        message="Streak analysis retrieved"
    )


@router.get("/{player_id}/special-events")
@handle_api_errors(operation_name="get special event analytics")
def get_special_event_analytics(
    player_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get analytics for special events (ping pong, invisible aardvark, etc.)."""
    from ..services.statistics_service import StatisticsService

    stats_service = StatisticsService(db)
    special_events = stats_service.get_special_event_analytics(player_id)

    return ApiResponse.success(
        data={"player_id": player_id, "special_events": special_events},
        message="Special event analytics retrieved"
    )


@router.get("/{player_id}/score-performance")
@handle_api_errors(operation_name="get score performance analytics")
def get_score_performance_analytics(
    player_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed score performance analytics (eagles, birdies, pars, etc.)."""
    from ..services.statistics_service import StatisticsService

    stats_service = StatisticsService(db)
    score_performance = stats_service.get_score_performance_analytics(player_id)

    return ApiResponse.success(
        data={"player_id": player_id, "score_performance": score_performance},
        message="Score performance analytics retrieved"
    )


# ============================================================================
# Player Availability Endpoints
# ============================================================================

@router.get("/me/availability", response_model=List[schemas.PlayerAvailabilityResponse])
@handle_api_errors(operation_name="get my availability")
async def get_my_availability(
    current_user: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[schemas.PlayerAvailabilityResponse]:
    """Get current user's weekly availability."""
    availability = db.query(models.PlayerAvailability).filter(
        models.PlayerAvailability.player_profile_id == current_user.id
    ).all()
    return [schemas.PlayerAvailabilityResponse.from_orm(a) for a in availability]


@router.post("/me/availability", response_model=schemas.PlayerAvailabilityResponse)
@handle_api_errors(operation_name="set my availability")
async def set_my_availability(
    availability: schemas.PlayerAvailabilityCreate,
    current_user: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> schemas.PlayerAvailabilityResponse:
    """Set or update current user's availability for a specific day."""
    # Override the player_profile_id with the current user's ID
    availability.player_profile_id = cast(int, current_user.id)

    existing = db.query(models.PlayerAvailability).filter(
        models.PlayerAvailability.player_profile_id == current_user.id,
        models.PlayerAvailability.day_of_week == availability.day_of_week
    ).first()

    now = datetime.now(timezone.utc).isoformat()

    if existing:
        existing.available_from_time = availability.available_from_time
        existing.available_to_time = availability.available_to_time
        existing.is_available = availability.is_available
        existing.notes = availability.notes
        existing.updated_at = now
        db.commit()
        db.refresh(existing)
        logger.info(f"Updated availability for user {current_user.id}, day {availability.day_of_week}")
        return schemas.PlayerAvailabilityResponse.from_orm(existing)

    # Create new
    db_availability = models.PlayerAvailability(
        player_profile_id=current_user.id,
        day_of_week=availability.day_of_week,
        available_from_time=availability.available_from_time,
        available_to_time=availability.available_to_time,
        is_available=availability.is_available,
        notes=availability.notes,
        created_at=now,
        updated_at=now
    )
    db.add(db_availability)
    db.commit()
    db.refresh(db_availability)

    logger.info(f"Created availability for user {current_user.id}, day {availability.day_of_week}")
    return schemas.PlayerAvailabilityResponse.from_orm(db_availability)


@router.get("/{player_id}/availability", response_model=List[schemas.PlayerAvailabilityResponse])
@handle_api_errors(operation_name="get player availability")
def get_player_availability(
    player_id: int,
    db: Session = Depends(get_db)
) -> List[schemas.PlayerAvailabilityResponse]:
    """Get a player's weekly availability."""
    availability = db.query(models.PlayerAvailability).filter(
        models.PlayerAvailability.player_profile_id == player_id
    ).order_by(models.PlayerAvailability.day_of_week).all()
    return [schemas.PlayerAvailabilityResponse.from_orm(avail) for avail in availability]


@router.get("/availability/all", response_model=List[Dict])
@handle_api_errors(operation_name="get all players availability")
def get_all_players_availability(
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Get all players' weekly availability with their names."""
    players_with_availability = db.query(models.PlayerProfile).all()

    result: List[Dict[str, Any]] = []
    for player in players_with_availability:
        player_data: Dict[str, Any] = {
            "player_id": player.id,
            "player_name": player.name,
            "email": player.email,
            "availability": []
        }

        availability = db.query(models.PlayerAvailability).filter(
            models.PlayerAvailability.player_profile_id == player.id
        ).all()

        for avail in availability:
            player_data["availability"].append({
                "day_of_week": avail.day_of_week,
                "is_available": avail.is_available,
                "available_from_time": avail.available_from_time,
                "available_to_time": avail.available_to_time,
                "notes": avail.notes
            })

        result.append(player_data)

    return result


@router.post("/{player_id}/availability", response_model=schemas.PlayerAvailabilityResponse)
@handle_api_errors(operation_name="set player availability")
def set_player_availability(
    player_id: int,
    availability: schemas.PlayerAvailabilityCreate,
    db: Session = Depends(get_db)
) -> schemas.PlayerAvailabilityResponse:
    """Set or update a player's availability for a specific day."""
    existing = db.query(models.PlayerAvailability).filter(
        models.PlayerAvailability.player_profile_id == player_id,
        models.PlayerAvailability.day_of_week == availability.day_of_week
    ).first()

    now = datetime.now(timezone.utc).isoformat()

    if existing:
        existing.available_from_time = availability.available_from_time  # type: ignore
        existing.available_to_time = availability.available_to_time  # type: ignore
        existing.is_available = availability.is_available  # type: ignore
        existing.notes = availability.notes  # type: ignore
        existing.updated_at = now  # type: ignore
        db.commit()
        db.refresh(existing)
        logger.info(f"Updated availability for player {player_id}, day {availability.day_of_week}")
        return schemas.PlayerAvailabilityResponse.from_orm(existing)

    # Create new
    db_availability = models.PlayerAvailability(
        player_profile_id=player_id,
        day_of_week=availability.day_of_week,
        available_from_time=availability.available_from_time,
        available_to_time=availability.available_to_time,
        is_available=availability.is_available,
        notes=availability.notes,
        created_at=now,
        updated_at=now
    )
    db.add(db_availability)
    db.commit()
    db.refresh(db_availability)

    logger.info(f"Created availability for player {player_id}, day {availability.day_of_week}")
    return schemas.PlayerAvailabilityResponse.from_orm(db_availability)


# ============================================================================
# Email Preferences Endpoints
# ============================================================================

@router.get("/{player_id}/email-preferences", response_model=schemas.EmailPreferencesResponse)
@handle_api_errors(operation_name="get email preferences")
def get_email_preferences(
    player_id: int,
    db: Session = Depends(get_db)
) -> schemas.EmailPreferencesResponse:
    """Get a player's email preferences."""
    now = datetime.now(timezone.utc).isoformat()

    preferences = db.query(models.EmailPreferences).filter(
        models.EmailPreferences.player_profile_id == player_id
    ).first()

    if not preferences:
        preferences = models.EmailPreferences(
            player_profile_id=player_id,
            created_at=now,
            updated_at=now
        )
        db.add(preferences)
        db.commit()
        db.refresh(preferences)

    return schemas.EmailPreferencesResponse.from_orm(preferences)


@router.put("/{player_id}/email-preferences", response_model=schemas.EmailPreferencesResponse)
@handle_api_errors(operation_name="update email preferences")
def update_email_preferences(
    player_id: int,
    preferences_update: schemas.EmailPreferencesUpdate,
    db: Session = Depends(get_db)
) -> schemas.EmailPreferencesResponse:
    """Update a player's email preferences."""
    preferences_result = db.query(models.EmailPreferences).filter(
        models.EmailPreferences.player_profile_id == player_id
    ).first()

    preferences = require_not_none(preferences_result, "Email preferences for player", player_id)

    # Update fields that are provided
    update_data = preferences_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(preferences, field):
            setattr(preferences, field, value)

    preferences.updated_at = datetime.now(timezone.utc).isoformat()  # type: ignore
    db.commit()
    db.refresh(preferences)

    logger.info(f"Updated email preferences for player {player_id}")
    return schemas.EmailPreferencesResponse.from_orm(preferences)


@router.get("/me/email-preferences", response_model=schemas.EmailPreferencesResponse)
@handle_api_errors(operation_name="get my email preferences")
async def get_my_email_preferences(
    current_user: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> schemas.EmailPreferencesResponse:
    """Get current user's email preferences."""
    now = datetime.now(timezone.utc).isoformat()

    prefs = db.query(models.EmailPreferences).filter(
        models.EmailPreferences.player_profile_id == current_user.id
    ).first()

    if not prefs:
        prefs = models.EmailPreferences(
            player_profile_id=current_user.id,
            created_at=now,
            updated_at=now
        )
        db.add(prefs)
        db.commit()
        db.refresh(prefs)

    return schemas.EmailPreferencesResponse(
        id=cast(int, prefs.id),
        player_profile_id=cast(int, prefs.player_profile_id),
        daily_signups_enabled=bool(prefs.daily_signups_enabled),
        signup_confirmations_enabled=bool(prefs.signup_confirmations_enabled),
        signup_reminders_enabled=bool(prefs.signup_reminders_enabled),
        game_invitations_enabled=bool(prefs.game_invitations_enabled),
        weekly_summary_enabled=bool(prefs.weekly_summary_enabled),
        email_frequency=cast(str, prefs.email_frequency),
        preferred_notification_time=cast(str, prefs.preferred_notification_time),
        created_at=cast(str, prefs.created_at),
        updated_at=cast(str, prefs.updated_at)
    )


@router.put("/me/email-preferences", response_model=schemas.EmailPreferencesResponse)
@handle_api_errors(operation_name="update my email preferences")
async def update_my_email_preferences(
    preferences_update: schemas.EmailPreferencesUpdate,
    current_user: models.PlayerProfile = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> schemas.EmailPreferencesResponse:
    """Update current user's email preferences."""
    now = datetime.now(timezone.utc).isoformat()

    prefs = db.query(models.EmailPreferences).filter(
        models.EmailPreferences.player_profile_id == current_user.id
    ).first()

    if not prefs:
        prefs = models.EmailPreferences(
            player_profile_id=current_user.id,
            created_at=now
        )
        db.add(prefs)

    update_data = preferences_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(prefs, field):
            # Convert bool to int for SQLite
            if isinstance(value, bool):
                value = 1 if value else 0
            setattr(prefs, field, value)

    prefs.updated_at = now  # type: ignore
    db.commit()
    db.refresh(prefs)

    logger.info(f"Updated email preferences for user {current_user.id}")

    return schemas.EmailPreferencesResponse(
        id=cast(int, prefs.id),
        player_profile_id=cast(int, prefs.player_profile_id),
        daily_signups_enabled=bool(prefs.daily_signups_enabled),
        signup_confirmations_enabled=bool(prefs.signup_confirmations_enabled),
        signup_reminders_enabled=bool(prefs.signup_reminders_enabled),
        game_invitations_enabled=bool(prefs.game_invitations_enabled),
        weekly_summary_enabled=bool(prefs.weekly_summary_enabled),
        email_frequency=cast(str, prefs.email_frequency),
        preferred_notification_time=cast(str, prefs.preferred_notification_time),
        created_at=cast(str, prefs.created_at),
        updated_at=cast(str, prefs.updated_at)
    )
