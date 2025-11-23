"""
Players Router

Player profile management, statistics, analytics, availability, and preferences.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from ..database import get_db, SessionLocal
from .. import models, schemas
from ..services.player_service import PlayerService
from ..services.auth_service import get_current_user

logger = logging.getLogger("app.routers.players")

router = APIRouter(
    prefix="/players",
    tags=["players"]
)


# Player Profile CRUD Endpoints

@router.post("", response_model=schemas.PlayerProfileResponse)
def create_player_profile(profile: schemas.PlayerProfileCreate) -> schemas.PlayerProfileResponse:
    """Create a new player profile."""
    try:
        db = SessionLocal()
        player_service = PlayerService(db)
        result = player_service.create_player_profile(profile)
        
        logger.info(f"Created player profile: {result.name}")
        return result
        
    except ValueError as e:
        logger.error(f"Validation error creating player profile: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating player profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create player profile: {str(e)}")
    finally:
        db.close()


@router.get("", response_model=List[schemas.PlayerProfileResponse])
def get_all_player_profiles(active_only: bool = Query(True, description="Return only active profiles")) -> List[schemas.PlayerProfileResponse]:
    """Get all player profiles."""
    try:
        db = SessionLocal()
        player_service = PlayerService(db)
        profiles = player_service.get_all_player_profiles(active_only=active_only)
        
        logger.info(f"Retrieved {len(profiles)} player profiles")
        return profiles
        
    except Exception as e:
        logger.error(f"Error getting player profiles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get player profiles: {str(e)}")
    finally:
        db.close()


@router.get("/{player_id}", response_model=schemas.PlayerProfileResponse)
def get_player_profile(player_id: int) -> schemas.PlayerProfileResponse:
    """Get a specific player profile."""
    try:
        db = SessionLocal()
        player_service = PlayerService(db)
        profile = player_service.get_player_profile(player_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting player profile {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get player profile: {str(e)}")
    finally:
        db.close()


@router.put("/{player_id}", response_model=schemas.PlayerProfileResponse)
def update_player_profile(player_id: int, profile_update: schemas.PlayerProfileUpdate) -> schemas.PlayerProfileResponse:
    """Update a player profile."""
    try:
        db = SessionLocal()
        player_service = PlayerService(db)
        updated_profile = player_service.update_player_profile(player_id, profile_update)
        
        if not updated_profile:
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
        
        logger.info(f"Updated player profile {player_id}")
        return updated_profile
        
    except ValueError as e:
        logger.error(f"Validation error updating player profile: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating player profile {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update player profile: {str(e)}")
    finally:
        db.close()


@router.delete("/{player_id}")
def delete_player_profile(player_id: int) -> Dict[str, str]:
    """Delete (deactivate) a player profile."""
    try:
        db = SessionLocal()
        player_service = PlayerService(db)
        success = player_service.delete_player_profile(player_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
        
        logger.info(f"Deleted player profile {player_id}")
        return {"message": f"Player {player_id} has been deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting player profile {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete player profile: {str(e)}")
    finally:
        db.close()


# Player Search Endpoints

@router.get("/all", response_model=List[schemas.PlayerProfileResponse])
def get_all_players(
    active_only: bool = Query(True, description="Only return active players"),
    db: Session = Depends(get_db)
):
    """Get all player profiles."""
    player_service = PlayerService(db)
    return player_service.get_all_player_profiles(active_only=active_only)


@router.get("/name/{player_name}", response_model=schemas.PlayerProfileResponse)
def get_player_profile_by_name(player_name: str) -> schemas.PlayerProfileResponse:
    """Get a player profile by name."""
    try:
        db = SessionLocal()
        player_service = PlayerService(db)
        profile = player_service.get_player_profile_by_name(player_name)
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"Player '{player_name}' not found")
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting player profile by name {player_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get player profile: {str(e)}")
    finally:
        db.close()


# Player Statistics Endpoints

@router.get("/{player_id}/statistics", response_model=schemas.PlayerStatisticsResponse)
def get_player_statistics(player_id: int) -> schemas.PlayerStatisticsResponse:
    """Get player statistics."""
    try:
        db = SessionLocal()
        player_service = PlayerService(db)
        stats = player_service.get_player_statistics(player_id)
        
        if not stats:
            raise HTTPException(status_code=404, detail=f"Statistics for player {player_id} not found")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting player statistics {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get player statistics: {str(e)}")
    finally:
        db.close()


@router.get("/{player_id}/analytics", response_model=schemas.PlayerPerformanceAnalytics)
def get_player_analytics(player_id: int) -> schemas.PlayerPerformanceAnalytics:
    """Get comprehensive player performance analytics."""
    try:
        db = SessionLocal()
        player_service = PlayerService(db)
        analytics = player_service.get_player_performance_analytics(player_id)
        
        if not analytics:
            raise HTTPException(status_code=404, detail=f"Analytics for player {player_id} not found")
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting player analytics {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get player analytics: {str(e)}")
    finally:
        db.close()


@router.get("/{player_id}/profile-with-stats", response_model=schemas.PlayerProfileWithStats)
def get_player_profile_with_stats(player_id: int) -> schemas.PlayerProfileWithStats:
    """Get player profile combined with statistics and achievements."""
    try:
        db = SessionLocal()
        player_service = PlayerService(db)
        
        # Get profile
        profile = player_service.get_player_profile(player_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
        
        # Get statistics
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
                performance_trends=[], last_updated=datetime.now().isoformat()
            )
        
        # Get recent achievements (would need to implement this query)
        recent_achievements: List[Any] = []  # Placeholder
        
        return schemas.PlayerProfileWithStats(
            profile=profile,
            statistics=stats,
            recent_achievements=recent_achievements
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting player profile with stats {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get player profile with stats: {str(e)}")
    finally:
        db.close()


# Advanced Analytics Endpoints

@router.get("/{player_id}/advanced-metrics")
def get_player_advanced_metrics(player_id: int) -> Dict[str, Any]:
    """Get advanced performance metrics for a player."""
    try:
        db = SessionLocal()
        from ..services.statistics_service import StatisticsService
        
        stats_service = StatisticsService(db)
        metrics = stats_service.get_advanced_player_metrics(player_id)
        
        return {
            "player_id": player_id,
            "metrics": metrics,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting advanced metrics for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get advanced metrics: {str(e)}")
    finally:
        db.close()


@router.get("/{player_id}/trends")
def get_player_trends(
    player_id: int,
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze")
) -> Dict[str, Any]:
    """Get performance trends for a player."""
    try:
        db = SessionLocal()
        from ..services.statistics_service import StatisticsService
        
        stats_service = StatisticsService(db)
        trends = stats_service.get_performance_trends(player_id, days=days)
        
        return {
            "player_id": player_id,
            "period_days": days,
            "trends": trends,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting trends for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get player trends: {str(e)}")
    finally:
        db.close()


@router.get("/{player_id}/insights")
def get_player_insights(player_id: int) -> Dict[str, Any]:
    """Get personalized insights and recommendations for a player."""
    try:
        db = SessionLocal()
        from ..services.statistics_service import StatisticsService
        
        stats_service = StatisticsService(db)
        insights = stats_service.get_player_insights(player_id)
        
        return {
            "player_id": player_id,
            "insights": [insight.__dict__ for insight in insights],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting insights for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get player insights: {str(e)}")
    finally:
        db.close()


@router.get("/{player_id}/skill-rating")
def get_player_skill_rating(player_id: int) -> Dict[str, Any]:
    """Get skill rating for a player."""
    try:
        db = SessionLocal()
        from ..services.statistics_service import StatisticsService
        
        stats_service = StatisticsService(db)
        rating = stats_service.calculate_skill_rating(player_id)
        
        return {
            "player_id": player_id,
            "skill_rating": rating,
            "calculated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting skill rating for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get skill rating: {str(e)}")
    finally:
        db.close()


# Player Availability Endpoints

@router.get("/me/availability", response_model=List[schemas.PlayerAvailabilityResponse])
async def get_my_availability(current_user: models.PlayerProfile = Depends(get_current_user)) -> List[schemas.PlayerAvailabilityResponse]:
    """Get current user's weekly availability."""
    try:
        db = SessionLocal()
        
        availability = db.query(models.PlayerAvailability).filter(
            models.PlayerAvailability.player_profile_id == current_user.id
        ).all()
        
        return [schemas.PlayerAvailabilityResponse.from_orm(a) for a in availability]
        
    except Exception as e:
        logger.error(f"Error getting availability for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get availability: {str(e)}")
    finally:
        db.close()


@router.post("/me/availability", response_model=schemas.PlayerAvailabilityResponse)
async def set_my_availability(
    availability: schemas.PlayerAvailabilityCreate,
    current_user: models.PlayerProfile = Depends(get_current_user)
) -> schemas.PlayerAvailabilityResponse:
    """Set or update current user's availability for a specific day."""
    try:
        db = SessionLocal()
        
        # Override the player_profile_id with the current user's ID
        availability.player_profile_id = current_user.id
        
        # Check if availability already exists for this day
        existing = db.query(models.PlayerAvailability).filter(
            models.PlayerAvailability.player_profile_id == current_user.id,
            models.PlayerAvailability.day_of_week == availability.day_of_week
        ).first()
        
        if existing:
            # Update existing
            existing.available_from_time = availability.available_from_time
            existing.available_to_time = availability.available_to_time
            existing.is_available = availability.is_available
            existing.notes = availability.notes
            existing.updated_at = datetime.now().isoformat()
            
            db.commit()
            db.refresh(existing)
            
            logger.info(f"Updated availability for user {current_user.id}, day {availability.day_of_week}")
            return schemas.PlayerAvailabilityResponse.from_orm(existing)
        else:
            # Create new
            db_availability = models.PlayerAvailability(
                player_profile_id=current_user.id,
                day_of_week=availability.day_of_week,
                available_from_time=availability.available_from_time,
                available_to_time=availability.available_to_time,
                is_available=availability.is_available,
                notes=availability.notes,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            db.add(db_availability)
            db.commit()
            db.refresh(db_availability)
            
            logger.info(f"Created availability for user {current_user.id}, day {availability.day_of_week}")
            return schemas.PlayerAvailabilityResponse.from_orm(db_availability)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error setting availability for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set availability: {str(e)}")
    finally:
        db.close()


@router.get("/{player_id}/availability", response_model=List[schemas.PlayerAvailabilityResponse])
def get_player_availability(player_id: int) -> List[schemas.PlayerAvailabilityResponse]:
    """Get a player's weekly availability."""
    try:
        db = SessionLocal()
        
        availability = db.query(models.PlayerAvailability).filter(
            models.PlayerAvailability.player_profile_id == player_id
        ).order_by(models.PlayerAvailability.day_of_week).all()
        
        return [schemas.PlayerAvailabilityResponse.from_orm(avail) for avail in availability]
        
    except Exception as e:
        logger.error(f"Error getting availability for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get availability: {str(e)}")
    finally:
        db.close()


@router.get("/availability/all", response_model=List[Dict])
def get_all_players_availability() -> List[Dict[str, Any]]:
    """Get all players' weekly availability with their names."""
    try:
        db = SessionLocal()
        
        # Get all players with their availability
        players_with_availability = db.query(models.PlayerProfile).all()
        
        result = []
        for player in players_with_availability:
            player_data = {
                "player_id": player.id,
                "player_name": player.name,
                "email": player.email,
                "availability": []
            }
            
            # Get this player's availability
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
        
    except Exception as e:
        logger.error(f"Error getting all players availability: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get availability: {str(e)}")
    finally:
        db.close()


@router.post("/{player_id}/availability", response_model=schemas.PlayerAvailabilityResponse)
def set_player_availability(player_id: int, availability: schemas.PlayerAvailabilityCreate) -> schemas.PlayerAvailabilityResponse:
    """Set or update a player's availability for a specific day."""
    try:
        db = SessionLocal()
        
        # Check if availability already exists for this day
        existing = db.query(models.PlayerAvailability).filter(
            models.PlayerAvailability.player_profile_id == player_id,
            models.PlayerAvailability.day_of_week == availability.day_of_week
        ).first()
        
        if existing:
            # Update existing
            existing.available_from_time = availability.available_from_time
            existing.available_to_time = availability.available_to_time
            existing.is_available = availability.is_available
            existing.notes = availability.notes
            existing.updated_at = datetime.now().isoformat()
            
            db.commit()
            db.refresh(existing)
            
            logger.info(f"Updated availability for player {player_id}, day {availability.day_of_week}")
            return schemas.PlayerAvailabilityResponse.from_orm(existing)
        else:
            # Create new
            db_availability = models.PlayerAvailability(
                player_profile_id=player_id,
                day_of_week=availability.day_of_week,
                available_from_time=availability.available_from_time,
                available_to_time=availability.available_to_time,
                is_available=availability.is_available,
                notes=availability.notes,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            db.add(db_availability)
            db.commit()
            db.refresh(db_availability)
            
            logger.info(f"Created availability for player {player_id}, day {availability.day_of_week}")
            return schemas.PlayerAvailabilityResponse.from_orm(db_availability)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error setting availability for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set availability: {str(e)}")
    finally:
        db.close()


# Email Preferences Endpoints

@router.get("/{player_id}/email-preferences", response_model=schemas.EmailPreferencesResponse)
def get_email_preferences(player_id: int) -> schemas.EmailPreferencesResponse:
    """Get a player's email preferences."""
    try:
        db = SessionLocal()
        
        preferences = db.query(models.EmailPreferences).filter(
            models.EmailPreferences.player_profile_id == player_id
        ).first()
        
        if not preferences:
            # Create default preferences
            preferences = models.EmailPreferences(
                player_profile_id=player_id,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            db.add(preferences)
            db.commit()
            db.refresh(preferences)
            
        return schemas.EmailPreferencesResponse.from_orm(preferences)
        
    except Exception as e:
        logger.error(f"Error getting email preferences for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get email preferences: {str(e)}")
    finally:
        db.close()


@router.put("/{player_id}/email-preferences", response_model=schemas.EmailPreferencesResponse)
def update_email_preferences(player_id: int, preferences_update: schemas.EmailPreferencesUpdate) -> schemas.EmailPreferencesResponse:
    """Update a player's email preferences."""
    try:
        db = SessionLocal()
        
        preferences = db.query(models.EmailPreferences).filter(
            models.EmailPreferences.player_profile_id == player_id
        ).first()
        
        if not preferences:
            raise HTTPException(status_code=404, detail="Email preferences not found")
        
        # Update fields
        if preferences_update.daily_signups_enabled is not None:
            preferences.daily_signups_enabled = preferences_update.daily_signups_enabled
        if preferences_update.signup_confirmations_enabled is not None:
            preferences.signup_confirmations_enabled = preferences_update.signup_confirmations_enabled
        if preferences_update.signup_reminders_enabled is not None:
            preferences.signup_reminders_enabled = preferences_update.signup_reminders_enabled
        if preferences_update.game_invitations_enabled is not None:
            preferences.game_invitations_enabled = preferences_update.game_invitations_enabled
        if preferences_update.weekly_summary_enabled is not None:
            preferences.weekly_summary_enabled = preferences_update.weekly_summary_enabled
        if preferences_update.email_frequency is not None:
            preferences.email_frequency = preferences_update.email_frequency
        if preferences_update.preferred_notification_time is not None:
            preferences.preferred_notification_time = preferences_update.preferred_notification_time
            
        preferences.updated_at = datetime.now().isoformat()
        
        db.commit()
        db.refresh(preferences)
        
        logger.info(f"Updated email preferences for player {player_id}")
        return schemas.EmailPreferencesResponse.from_orm(preferences)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating email preferences for player {player_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update email preferences: {str(e)}")
    finally:
        db.close()


@router.get("/me/email-preferences", response_model=schemas.EmailPreferencesResponse)
async def get_my_email_preferences(current_user: models.PlayerProfile = Depends(get_current_user)) -> schemas.EmailPreferencesResponse:
    """Get current user's email preferences"""
    db = SessionLocal()
    try:
        # Try to find existing preferences
        prefs = db.query(models.EmailPreferences).filter(
            models.EmailPreferences.player_profile_id == current_user.id
        ).first()
        
        if not prefs:
            # Create default preferences
            prefs = models.EmailPreferences(
                player_profile_id=current_user.id,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            db.add(prefs)
            db.commit()
            db.refresh(prefs)
        
        return schemas.EmailPreferencesResponse(
            id=prefs.id,
            player_profile_id=prefs.player_profile_id,
            daily_signups_enabled=bool(prefs.daily_signups_enabled),
            signup_confirmations_enabled=bool(prefs.signup_confirmations_enabled),
            signup_reminders_enabled=bool(prefs.signup_reminders_enabled),
            game_invitations_enabled=bool(prefs.game_invitations_enabled),
            weekly_summary_enabled=bool(prefs.weekly_summary_enabled),
            email_frequency=prefs.email_frequency,
            preferred_notification_time=prefs.preferred_notification_time
        )
    except Exception as e:
        logger.error(f"Error getting email preferences for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get email preferences: {str(e)}")
    finally:
        db.close()


@router.put("/me/email-preferences", response_model=schemas.EmailPreferencesResponse)
async def update_my_email_preferences(
    preferences_update: schemas.EmailPreferencesUpdate,
    current_user: models.PlayerProfile = Depends(get_current_user)
) -> schemas.EmailPreferencesResponse:
    """Update current user's email preferences"""
    db = SessionLocal()
    try:
        # Find or create preferences
        prefs = db.query(models.EmailPreferences).filter(
            models.EmailPreferences.player_profile_id == current_user.id
        ).first()
        
        if not prefs:
            prefs = models.EmailPreferences(
                player_profile_id=current_user.id,
                created_at=datetime.now().isoformat()
            )
            db.add(prefs)
        
        # Update preferences
        update_data = preferences_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(prefs, field):
                # Convert bool to int for SQLite
                if isinstance(value, bool):
                    value = 1 if value else 0
                setattr(prefs, field, value)
        
        prefs.updated_at = datetime.now().isoformat()
        db.commit()
        db.refresh(prefs)
        
        logger.info(f"Updated email preferences for user {current_user.id}")
        
        return schemas.EmailPreferencesResponse(
            id=prefs.id,
            player_profile_id=prefs.player_profile_id,
            daily_signups_enabled=bool(prefs.daily_signups_enabled),
            signup_confirmations_enabled=bool(prefs.signup_confirmations_enabled),
            signup_reminders_enabled=bool(prefs.signup_reminders_enabled),
            game_invitations_enabled=bool(prefs.game_invitations_enabled),
            weekly_summary_enabled=bool(prefs.weekly_summary_enabled),
            email_frequency=prefs.email_frequency,
            preferred_notification_time=prefs.preferred_notification_time
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating email preferences for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update email preferences: {str(e)}")
    finally:
        db.close()

