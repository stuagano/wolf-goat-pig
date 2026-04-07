"""
Signups Router

Legacy player lookup and daily sign-up management.
"""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query

from .. import database, models, schemas
from ..services.legacy_player_service import (
    get_legacy_players,
    validate_player_for_legacy,
)
from ..services.legacy_signup_service import get_legacy_signup_service

logger = logging.getLogger("app.routers.signups")

router = APIRouter(tags=["signups"])


@router.get("/legacy-players")
def list_legacy_players():
    """Get all players known to the legacy tee sheet system.

    These are the only player names that will sync successfully
    to the thousand-cranes.com tee sheet.
    """
    players = get_legacy_players()
    return {"count": len(players), "players": players}


@router.get("/legacy-players/validate/{name}")
def validate_legacy_player(name: str):
    """Validate a player name against the legacy system.

    Returns whether the name is valid, the canonical spelling if found,
    and suggestions for similar names if not found.
    """
    return validate_player_for_legacy(name)


@router.get("/legacy-players/search")
def search_legacy_players(q: str = Query(description="Search query for player name")):
    """Search for legacy players by partial name match.

    Returns players whose names contain the search query (case-insensitive).
    """
    players = get_legacy_players()
    query_lower = q.lower()
    matches = [p for p in players if query_lower in p.lower()]
    return {"query": q, "count": len(matches), "players": matches}


@router.get("/signups/weekly", response_model=schemas.WeeklySignupView)
def get_weekly_signups(week_start: str = Query(description="YYYY-MM-DD format for Monday of the week")):  # type: ignore
    """Get sign-ups for a rolling 7-day period starting from specified Monday."""
    try:
        db = database.SessionLocal()

        # Parse the week start date
        start_date = datetime.strptime(week_start, "%Y-%m-%d")

        # Get all 7 days
        daily_summaries = []
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")

            signups = (
                db.query(models.DailySignup)
                .filter(
                    models.DailySignup.date == date_str,
                    models.DailySignup.status != "cancelled",
                )
                .all()
            )

            daily_summaries.append(
                schemas.DailySignupSummary(
                    date=date_str,
                    signups=[schemas.DailySignupResponse.from_orm(signup) for signup in signups],
                    total_count=len(signups),
                )
            )

        return schemas.WeeklySignupView(week_start=week_start, daily_summaries=daily_summaries)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e!s}")
    except Exception as e:
        logger.error(f"Error getting weekly signups: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get weekly signups: {e!s}")
    finally:
        db.close()


@router.get("/signups")
def get_signups(limit: int = Query(50, description="Maximum number of signups to return")):  # type: ignore
    """Get recent signups with basic information"""
    try:
        db = database.SessionLocal()

        # Get recent signups
        signups = (
            db.query(models.DailySignup)
            .filter(models.DailySignup.status != "cancelled")
            .order_by(models.DailySignup.created_at.desc())
            .limit(limit)
            .all()
        )

        return {
            "signups": [
                {
                    "id": signup.id,
                    "date": signup.date,
                    "player_name": signup.player_name,
                    "player_profile_id": signup.player_profile_id,
                    "status": signup.status,
                    "signup_time": signup.signup_time,
                    "preferred_start_time": signup.preferred_start_time,
                    "notes": signup.notes,
                    "created_at": signup.created_at if signup.created_at else None,
                }
                for signup in signups
            ],
            "total": len(signups),
        }

    except Exception as e:
        logger.error(f"Error getting signups: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get signups: {e!s}")
    finally:
        db.close()


@router.post("/signups", response_model=schemas.DailySignupResponse)
def create_signup(signup: schemas.DailySignupCreate):  # type: ignore
    """Create a daily sign-up for a player."""
    try:
        db = database.SessionLocal()

        # Check if player already signed up for this date
        existing = (
            db.query(models.DailySignup)
            .filter(
                models.DailySignup.date == signup.date,
                models.DailySignup.player_profile_id == signup.player_profile_id,
                models.DailySignup.status != "cancelled",
            )
            .first()
        )

        if existing:
            raise HTTPException(status_code=400, detail="Player already signed up for this date")

        # Create new signup
        db_signup = models.DailySignup(
            date=signup.date,
            player_profile_id=signup.player_profile_id,
            player_name=signup.player_name,
            signup_time=datetime.now().isoformat(),
            preferred_start_time=signup.preferred_start_time,
            notes=signup.notes,
            status="signed_up",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

        db.add(db_signup)
        db.commit()
        db.refresh(db_signup)

        logger.info(f"Created signup for player {signup.player_name} on {signup.date}")

        # Mirror the signup to the legacy CGI sheet when configured.
        try:
            legacy_service = get_legacy_signup_service()
            legacy_service.sync_signup_created(db_signup)
        except Exception:
            logger.exception("Legacy signup sync failed for create id=%s", db_signup.id)

        return schemas.DailySignupResponse.from_orm(db_signup)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating signup: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create signup: {e!s}")
    finally:
        db.close()


@router.put("/signups/{signup_id}", response_model=schemas.DailySignupResponse)
def update_signup(signup_id: int, signup_update: schemas.DailySignupUpdate):  # type: ignore
    """Update a daily sign-up."""
    try:
        db = database.SessionLocal()

        db_signup = db.query(models.DailySignup).filter(models.DailySignup.id == signup_id).first()
        if not db_signup:
            raise HTTPException(status_code=404, detail="Sign-up not found")

        # Update fields
        if signup_update.preferred_start_time is not None:
            db_signup.preferred_start_time = signup_update.preferred_start_time  # type: ignore
        if signup_update.notes is not None:
            db_signup.notes = signup_update.notes  # type: ignore
        if signup_update.status is not None:
            db_signup.status = signup_update.status  # type: ignore

        db_signup.updated_at = datetime.now().isoformat()  # type: ignore

        db.commit()
        db.refresh(db_signup)

        logger.info(f"Updated signup {signup_id}")

        try:
            legacy_service = get_legacy_signup_service()
            legacy_service.sync_signup_updated(db_signup)
        except Exception:
            logger.exception("Legacy signup sync failed for update id=%s", db_signup.id)

        return schemas.DailySignupResponse.from_orm(db_signup)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating signup {signup_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update signup: {e!s}")
    finally:
        db.close()


@router.delete("/signups/{signup_id}")
def cancel_signup(signup_id: int):  # type: ignore
    """Cancel a daily sign-up."""
    try:
        db = database.SessionLocal()

        db_signup = db.query(models.DailySignup).filter(models.DailySignup.id == signup_id).first()
        if not db_signup:
            raise HTTPException(status_code=404, detail="Sign-up not found")

        db_signup.status = "cancelled"  # type: ignore
        db_signup.updated_at = datetime.now().isoformat()  # type: ignore

        db.commit()

        logger.info(f"Cancelled signup {signup_id}")

        try:
            legacy_service = get_legacy_signup_service()
            legacy_service.sync_signup_cancelled(db_signup)
        except Exception:
            logger.exception("Legacy signup sync failed for cancel id=%s", db_signup.id)

        return {"message": "Sign-up cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling signup {signup_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel signup: {e!s}")
    finally:
        db.close()


@router.post("/signups/{signup_id}/replicate-legacy")
def replicate_signup_to_legacy(signup_id: int):  # type: ignore
    """Manually replicate a signup to the legacy CGI tee sheet for testing."""
    try:
        db = database.SessionLocal()

        db_signup = db.query(models.DailySignup).filter(models.DailySignup.id == signup_id).first()
        if not db_signup:
            raise HTTPException(status_code=404, detail="Sign-up not found")

        legacy_service = get_legacy_signup_service()
        success = legacy_service.sync_signup_created(db_signup)

        if success:
            return {"message": "Successfully replicated to legacy signup page", "success": True}
        config = legacy_service.config
        if not config.enabled:
            return {
                "message": "Legacy sync is not enabled. Set LEGACY_SIGNUP_SYNC_ENABLED=true in environment.",
                "success": False,
            }
        if not config.create_url:
            return {
                "message": "No legacy URL configured. Set LEGACY_SIGNUP_CREATE_URL in environment.",
                "success": False,
            }
        return {
            "message": "Legacy replication attempted but was not successful. Check server logs.",
            "success": False,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error replicating signup {signup_id} to legacy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to replicate to legacy: {e!s}")
    finally:
        db.close()


@router.get("/signups/weekly-with-messages", response_model=schemas.WeeklySignupWithMessagesView)
def get_weekly_signups_with_messages(week_start: str = Query(description="YYYY-MM-DD format for Monday of the week")):  # type: ignore
    """Get sign-ups and messages for a rolling 7-day period starting from specified Monday."""
    try:
        db = database.SessionLocal()

        # Parse the week start date
        start_date = datetime.strptime(week_start, "%Y-%m-%d")

        # Get all 7 days
        daily_summaries = []
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")

            # Get signups
            signups = (
                db.query(models.DailySignup)
                .filter(
                    models.DailySignup.date == date_str,
                    models.DailySignup.status != "cancelled",
                )
                .all()
            )

            # Get messages
            messages = (
                db.query(models.DailyMessage)
                .filter(
                    models.DailyMessage.date == date_str,
                    models.DailyMessage.is_active == 1,
                )
                .order_by(models.DailyMessage.message_time)
                .all()
            )

            daily_summaries.append(
                schemas.DailySignupWithMessages(
                    date=date_str,
                    signups=[schemas.DailySignupResponse.from_orm(signup) for signup in signups],
                    total_count=len(signups),
                    messages=[schemas.DailyMessageResponse.from_orm(message) for message in messages],
                    message_count=len(messages),
                )
            )

        return schemas.WeeklySignupWithMessagesView(week_start=week_start, daily_summaries=daily_summaries)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e!s}")
    except Exception as e:
        logger.error(f"Error getting weekly data with messages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get weekly data: {e!s}")
    finally:
        db.close()
