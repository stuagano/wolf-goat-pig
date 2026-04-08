"""
Analytics Router

Game statistics, player performance, and analytics overview endpoints.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import and_

from .. import database, models
from ..services.statistics_service import StatisticsService
from ..state.app_state import get_course_manager

logger = logging.getLogger("app.routers.analytics")

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/game-stats")
def get_game_stats():
    """Get game statistics analytics"""
    try:
        db = database.SessionLocal()

        # Get basic game statistics
        total_games = db.query(models.GameRecord).count() if hasattr(models, "GameRecord") else 0
        # SimulationResult model removed — simulation mode deprecated
        total_simulations = 0

        # Get course usage
        course_manager = get_course_manager()
        courses = course_manager.get_courses()
        course_names = list(courses.keys()) if courses else []

        return {
            "total_games": total_games,
            "total_simulations": total_simulations,
            "available_courses": len(course_names),
            "course_names": course_names,
            "game_modes": ["4-man", "5-man", "6-man"],
            "betting_types": ["Wolf", "Goat", "Pig", "Aardvark"],
            "last_updated": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting game stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get game stats: {e!s}")
    finally:
        db.close()


@router.get("/player-performance")
def get_player_performance():
    """Get player performance analytics"""
    try:
        db = database.SessionLocal()

        # Get basic player statistics
        total_players = db.query(models.PlayerProfile).filter(models.PlayerProfile.is_active == 1).count()
        active_players = total_players  # For now, assume all active players are active

        # Get recent signups
        recent_signups = db.query(models.DailySignup).filter(models.DailySignup.status != "cancelled").count()

        return {
            "total_players": total_players,
            "active_players": active_players,
            "recent_signups": recent_signups,
            "average_handicap": 15.5,  # Placeholder calculation
            "performance_metrics": {
                "games_played": 0,
                "average_score": 0,
                "best_round": 0,
                "worst_round": 0,
            },
            "last_updated": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting player performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get player performance: {e!s}")
    finally:
        db.close()


@router.get("/overview")
def get_analytics_overview():
    """Get overall analytics overview."""
    try:
        db = database.SessionLocal()

        stats_service = StatisticsService(db)

        # Get game mode analytics
        game_mode_analytics = stats_service.get_game_mode_analytics()

        # Get basic statistics
        total_players = db.query(models.PlayerProfile).filter(models.PlayerProfile.is_active == 1).count()
        total_games = db.query(models.GameRecord).count()
        active_players = (
            db.query(models.PlayerProfile)
            .filter(
                and_(models.PlayerProfile.is_active == 1, models.PlayerProfile.last_played.isnot(None))  # type: ignore
            )
            .count()
        )

        return {
            "total_players": total_players,
            "active_players": active_players,
            "total_games": total_games,
            "game_mode_analytics": game_mode_analytics,
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics overview: {e!s}")
    finally:
        db.close()
