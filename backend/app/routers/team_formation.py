"""Team formation, pairing generation, and Sunday game routes."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from .. import database, models
from ..utils.admin_auth import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(tags=["team-formation"])


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/signups/{date}/players")
def get_players_for_date(date: str = Path(description="Date in YYYY-MM-DD format")):  # type: ignore
    """Get all players signed up for a specific date."""
    try:
        db = database.SessionLocal()

        # Get all signups for the specified date
        signups = (
            db.query(models.DailySignup)
            .filter(
                models.DailySignup.date == date,
                models.DailySignup.status != "cancelled",
            )
            .all()
        )

        players = []
        for signup in signups:
            # Get player profile for additional info
            player_profile = (
                db.query(models.PlayerProfile).filter(models.PlayerProfile.id == signup.player_profile_id).first()
            )

            player_data = {
                "signup_id": signup.id,
                "player_profile_id": signup.player_profile_id,
                "player_name": signup.player_name,
                "preferred_start_time": signup.preferred_start_time,
                "notes": signup.notes,
                "signup_time": signup.signup_time,
                "handicap": player_profile.handicap if player_profile else None,
                "email": player_profile.email if player_profile else None,
            }
            players.append(player_data)

        return {
            "date": date,
            "total_players": len(players),
            "players": players,
            "can_form_teams": len(players) >= 4,
            "max_complete_teams": len(players) // 4,
            "remaining_players": len(players) % 4,
        }

    except Exception as e:
        logger.error(f"Error getting players for date {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get players: {e!s}")
    finally:
        db.close()


# =============================================================================
# RNG PAIRING CALCULATOR ENDPOINTS
# =============================================================================


@router.get("/pairings/{date}")
def get_generated_pairings(date: str = Path(description="Date in YYYY-MM-DD format")):  # type: ignore
    """Get generated pairings for a specific date if they exist."""
    try:
        db = database.SessionLocal()
        from ..services.pairing_scheduler_service import PairingSchedulerService

        pairing = PairingSchedulerService.get_existing_pairing(db, date)

        if not pairing:
            return {"date": date, "exists": False, "pairings": None}

        return {
            "date": date,
            "exists": True,
            "generated_at": pairing.generated_at,
            "generated_by": pairing.generated_by,
            "player_count": pairing.player_count,
            "team_count": pairing.team_count,
            "remaining_players": pairing.remaining_players,
            "notification_sent": pairing.notification_sent,
            "notification_sent_at": pairing.notification_sent_at,
            "pairings": pairing.pairings_data,
        }

    except Exception as e:
        logger.error(f"Error getting pairings for date {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pairings: {e!s}")
    finally:
        db.close()


@router.post("/pairings/{date}/generate")
def generate_and_save_pairings(  # type: ignore
    date: str = Path(description="Date in YYYY-MM-DD format"),
    force: bool = Query(False, description="Force regenerate even if pairings exist"),
    send_notifications: bool = Query(True, description="Send email notifications to all players"),
    actor: dict[str, Any] = Depends(require_admin),
):
    """Generate and save random pairings for a specific date.

    Admin only. ``force=true`` overwrites official pairings already saved for the day.
    """
    try:
        db = database.SessionLocal()
        from ..services.pairing_scheduler_service import PairingSchedulerService

        generated_by = actor.get("email") or "manual"
        # Generate pairings
        pairing, message = PairingSchedulerService.generate_pairings(
            db, date, generated_by=generated_by, force_regenerate=force
        )

        if not pairing:
            raise HTTPException(status_code=400, detail=message)

        emails_sent = 0
        emails_failed = 0

        # Send notifications if requested
        if send_notifications:
            emails_sent, emails_failed = PairingSchedulerService.send_pairing_notifications(db, pairing)

        return {
            "success": True,
            "date": date,
            "message": message,
            "generated_at": pairing.generated_at,
            "player_count": pairing.player_count,
            "team_count": pairing.team_count,
            "remaining_players": pairing.remaining_players,
            "pairings": pairing.pairings_data,
            "notifications": {
                "sent": emails_sent,
                "failed": emails_failed,
                "enabled": send_notifications,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating pairings for date {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate pairings: {e!s}")
    finally:
        db.close()


@router.post("/pairings/run-saturday-job", dependencies=[Depends(require_admin)])
def run_saturday_pairing_job():  # type: ignore
    """Manually trigger the Saturday pairing job.

    This generates pairings for the next Sunday and sends notifications.
    Designed to be called by a cron job on Saturday afternoons.
    """
    try:
        db = database.SessionLocal()
        from ..services.pairing_scheduler_service import PairingSchedulerService

        result = PairingSchedulerService.run_saturday_job(db)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running Saturday pairing job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run Saturday job: {e!s}")
    finally:
        db.close()


@router.delete("/pairings/{date}", dependencies=[Depends(require_admin)])
def delete_generated_pairings(date: str = Path(description="Date in YYYY-MM-DD format")):  # type: ignore
    """Delete generated pairings for a specific date.

    Use this to clear pairings if you need to regenerate.
    """
    try:
        db = database.SessionLocal()
        from ..services.pairing_scheduler_service import PairingSchedulerService

        pairing = PairingSchedulerService.get_existing_pairing(db, date)

        if not pairing:
            raise HTTPException(status_code=404, detail=f"No pairings found for {date}")

        db.delete(pairing)
        db.commit()

        return {
            "success": True,
            "date": date,
            "message": f"Pairings for {date} deleted",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting pairings for date {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete pairings: {e!s}")
    finally:
        db.close()
