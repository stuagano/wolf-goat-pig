"""Players router — per-player statistics and analytics endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..services.player_service import PlayerService
from ..utils.api_helpers import ApiResponse, handle_api_errors, require_not_none
from ..utils.time import utc_now

router = APIRouter(prefix="/players", tags=["players"])


# ============================================================================
# Player Statistics Endpoints
# ============================================================================


@router.get("/{player_id}/statistics", response_model=schemas.PlayerStatisticsResponse)
@handle_api_errors(operation_name="get player statistics")
def get_player_statistics(player_id: int, db: Session = Depends(get_db)) -> schemas.PlayerStatisticsResponse:
    """Get player statistics."""
    player_service = PlayerService(db)
    stats = player_service.get_player_statistics(player_id)
    return require_not_none(stats, "Statistics for player", player_id)


@router.get("/{player_id}/analytics", response_model=schemas.PlayerPerformanceAnalytics)
@handle_api_errors(operation_name="get player analytics")
def get_player_analytics(player_id: int, db: Session = Depends(get_db)) -> schemas.PlayerPerformanceAnalytics:
    """Get comprehensive player performance analytics."""
    player_service = PlayerService(db)
    analytics = player_service.get_player_performance_analytics(player_id)
    return require_not_none(analytics, "Analytics for player", player_id)


@router.get("/{player_id}/profile-with-stats", response_model=schemas.PlayerProfileWithStats)
@handle_api_errors(operation_name="get player profile with stats")
def get_player_profile_with_stats(player_id: int, db: Session = Depends(get_db)) -> schemas.PlayerProfileWithStats:
    """Get player profile combined with statistics and achievements."""
    player_service = PlayerService(db)

    profile_result = player_service.get_player_profile(player_id)
    profile = require_not_none(profile_result, "Player", player_id)

    stats = player_service.get_player_statistics(player_id)
    if not stats:
        # Create empty stats if none exist
        stats = schemas.PlayerStatisticsResponse(
            id=0,
            player_id=player_id,
            games_played=0,
            games_won=0,
            total_earnings=0.0,
            holes_played=0,
            holes_won=0,
            avg_earnings_per_hole=0.0,
            betting_success_rate=0.0,
            successful_bets=0,
            total_bets=0,
            partnership_success_rate=0.0,
            partnerships_formed=0,
            partnerships_won=0,
            solo_attempts=0,
            solo_wins=0,
            favorite_game_mode="wolf_goat_pig",
            preferred_player_count=4,
            best_hole_performance=[],
            worst_hole_performance=[],
            performance_trends=[],
            last_updated=utc_now().isoformat(),
        )

    recent_achievements: list[Any] = []  # Placeholder for future implementation

    return schemas.PlayerProfileWithStats(profile=profile, statistics=stats, recent_achievements=recent_achievements)


# ============================================================================
# Advanced Analytics Endpoints
# ============================================================================


@router.get("/{player_id}/advanced-metrics")
@handle_api_errors(operation_name="get advanced metrics")
def get_player_advanced_metrics(player_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get advanced performance metrics for a player."""
    from ..services.statistics_service import StatisticsService

    stats_service = StatisticsService(db)
    metrics = stats_service.get_advanced_player_metrics(player_id)

    return ApiResponse.success(
        data={"player_id": player_id, "metrics": metrics},
        message="Advanced metrics retrieved",
    )


@router.get("/{player_id}/trends")
@handle_api_errors(operation_name="get player trends")
def get_player_trends(
    player_id: int,
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Get performance trends for a player."""
    from ..services.statistics_service import StatisticsService

    stats_service = StatisticsService(db)
    trends = stats_service.get_performance_trends(player_id, days=days)

    return ApiResponse.success(
        data={"player_id": player_id, "period_days": days, "trends": trends},
        message="Trends retrieved",
    )


@router.get("/{player_id}/insights")
@handle_api_errors(operation_name="get player insights")
def get_player_insights(player_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get personalized insights and recommendations for a player."""
    from ..services.statistics_service import StatisticsService

    stats_service = StatisticsService(db)
    insights = stats_service.get_player_insights(player_id)

    return ApiResponse.success(
        data={
            "player_id": player_id,
            "insights": [insight.__dict__ for insight in insights],
        },
        message="Insights generated",
    )


@router.get("/{player_id}/skill-rating")
@handle_api_errors(operation_name="get skill rating")
def get_player_skill_rating(player_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get skill rating for a player."""
    from ..services.statistics_service import StatisticsService

    stats_service = StatisticsService(db)
    rating = stats_service.calculate_skill_rating(player_id)

    return ApiResponse.success(
        data={"player_id": player_id, "skill_rating": rating},
        message="Skill rating calculated",
    )


@router.get("/{player_id}/head-to-head/{opponent_id}")
@handle_api_errors(operation_name="get head-to-head")
def get_head_to_head(player_id: int, opponent_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get head-to-head record between two players."""
    from ..services.statistics_service import StatisticsService

    stats_service = StatisticsService(db)
    h2h = stats_service.get_head_to_head(player_id, opponent_id)

    return ApiResponse.success(
        data={"player_id": player_id, "opponent_id": opponent_id, "head_to_head": h2h},
        message="Head-to-head record retrieved",
    )


@router.get("/{player_id}/head-to-head")
@handle_api_errors(operation_name="get all head-to-head records")
def get_all_head_to_head(player_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get head-to-head records against all opponents."""
    from ..services.statistics_service import StatisticsService

    stats_service = StatisticsService(db)
    h2h_records = stats_service.get_all_head_to_head(player_id)

    return ApiResponse.success(
        data={"player_id": player_id, "opponents": h2h_records},
        message="All head-to-head records retrieved",
    )


@router.get("/{player_id}/streaks")
@handle_api_errors(operation_name="get streak analysis")
def get_streak_analysis(player_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get detailed streak analysis for a player."""
    from ..services.statistics_service import StatisticsService

    stats_service = StatisticsService(db)
    streaks = stats_service.get_streak_analysis(player_id)

    return ApiResponse.success(
        data={"player_id": player_id, "streaks": streaks},
        message="Streak analysis retrieved",
    )


@router.get("/{player_id}/special-events")
@handle_api_errors(operation_name="get special event analytics")
def get_special_event_analytics(player_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get analytics for special events (ping pong, invisible aardvark, etc.)."""
    from ..services.statistics_service import StatisticsService

    stats_service = StatisticsService(db)
    special_events = stats_service.get_special_event_analytics(player_id)

    return ApiResponse.success(
        data={"player_id": player_id, "special_events": special_events},
        message="Special event analytics retrieved",
    )


@router.get("/{player_id}/score-performance")
@handle_api_errors(operation_name="get score performance analytics")
def get_score_performance_analytics(player_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get detailed score performance analytics (eagles, birdies, pars, etc.)."""
    from ..services.statistics_service import StatisticsService

    stats_service = StatisticsService(db)
    score_performance = stats_service.get_score_performance_analytics(player_id)

    return ApiResponse.success(
        data={"player_id": player_id, "score_performance": score_performance},
        message="Score performance analytics retrieved",
    )
