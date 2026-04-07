"""Team formation, pairing generation, and Sunday game routes."""

import logging
from typing import Any, cast

from fastapi import APIRouter, HTTPException, Path, Query
from sqlalchemy.orm import Session

from .. import database, models
from ..services.sunday_game_service import generate_sunday_pairings
from ..services.team_formation_service import TeamFormationService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["team-formation"])


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _get_active_signups_for_date(db: Session, date: str) -> list[models.DailySignup]:
    """Fetch non-cancelled signups for the requested date."""
    return (
        db.query(models.DailySignup)
        .filter(models.DailySignup.date == date, models.DailySignup.status != "cancelled")
        .all()
    )


def _build_player_payload(
    signups: list[models.DailySignup],
    *,
    include_handicap: bool = False,
    db: Session | None = None,
) -> list[dict[str, Any]]:
    """Convert signup records into the player dictionaries used by formation services."""
    if include_handicap and db is None:
        raise ValueError("Database session is required when include_handicap=True")

    players: list[dict[str, Any]] = []
    handicap_lookup: dict[int, float] = {}

    if include_handicap:
        profile_ids = [s.player_profile_id for s in signups if s.player_profile_id is not None]
        if profile_ids:
            profiles = (
                db.query(models.PlayerProfile).filter(models.PlayerProfile.id.in_(profile_ids)).all()  # type: ignore
            )
            handicap_lookup = {profile.id: profile.handicap for profile in profiles}

    for signup in signups:
        player_data: dict[str, Any] = {
            "id": signup.id,
            "player_profile_id": signup.player_profile_id,
            "player_name": signup.player_name,
            "preferred_start_time": signup.preferred_start_time,
            "notes": signup.notes,
            "signup_time": signup.signup_time,
        }

        if include_handicap:
            player_data["handicap"] = handicap_lookup.get(cast("Any", signup.player_profile_id), 18.0)

        players.append(player_data)

    return players


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/signups/{date}/team-formation/random")
def generate_random_teams_for_date(  # type: ignore
    date: str = Path(description="Date in YYYY-MM-DD format"),
    seed: int | None = Query(None, description="Random seed for reproducible results"),
    max_teams: int | None = Query(None, description="Maximum number of teams to create"),
):
    """Generate random 4-player teams from players signed up for a specific date."""
    try:
        db = database.SessionLocal()

        # Get all signups for the specified date
        signups = _get_active_signups_for_date(db, date)

        if len(signups) < 4:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough players signed up for {date}. Need at least 4 players, found {len(signups)}",
            )

        # Convert signups to player dictionaries
        players = _build_player_payload(signups)

        # Generate random teams
        teams = TeamFormationService.generate_random_teams(players=players, seed=seed, max_teams=max_teams)

        # Create summary
        summary = TeamFormationService.create_team_summary(teams)
        summary["date"] = date
        summary["total_signups"] = len(signups)

        # Validate results
        validation = TeamFormationService.validate_team_formation(teams)

        logger.info(f"Generated {len(teams)} random teams for date {date}")

        return {
            "summary": summary,
            "teams": teams,
            "validation": validation,
            "remaining_players": len(signups) % 4,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating random teams for date {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate teams: {e!s}")
    finally:
        db.close()


@router.post("/signups/{date}/team-formation/balanced")
def generate_balanced_teams_for_date(  # type: ignore
    date: str = Path(description="Date in YYYY-MM-DD format"),
    seed: int | None = Query(None, description="Random seed for reproducible results"),
):
    """Generate skill-balanced 4-player teams from players signed up for a specific date."""
    try:
        db = database.SessionLocal()

        # Get all signups for the specified date
        signups = _get_active_signups_for_date(db, date)

        if len(signups) < 4:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough players signed up for {date}. Need at least 4 players, found {len(signups)}",
            )

        # Get player profiles with handicap information
        players = _build_player_payload(signups, include_handicap=True, db=db)

        # Generate balanced teams
        teams = TeamFormationService.generate_balanced_teams(players=players, skill_key="handicap", seed=seed)

        # Create summary
        summary = TeamFormationService.create_team_summary(teams)
        summary["date"] = date
        summary["total_signups"] = len(signups)

        # Validate results
        validation = TeamFormationService.validate_team_formation(teams)

        logger.info(f"Generated {len(teams)} balanced teams for date {date}")

        return {
            "summary": summary,
            "teams": teams,
            "validation": validation,
            "remaining_players": len(signups) % 4,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating balanced teams for date {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate balanced teams: {e!s}")
    finally:
        db.close()


@router.post("/signups/{date}/team-formation/rotations")
def generate_team_rotations_for_date(  # type: ignore
    date: str = Path(description="Date in YYYY-MM-DD format"),
    num_rotations: int = Query(3, description="Number of different team rotations to create"),
    seed: int | None = Query(None, description="Random seed for reproducible results"),
):
    """Generate multiple team rotation options for variety throughout the day."""
    try:
        db = database.SessionLocal()

        # Get all signups for the specified date
        signups = _get_active_signups_for_date(db, date)

        if len(signups) < 4:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough players signed up for {date}. Need at least 4 players, found {len(signups)}",
            )

        # Convert signups to player dictionaries
        players = _build_player_payload(signups)

        # Generate team rotations
        rotations = TeamFormationService.create_team_pairings_with_rotations(
            players=players, num_rotations=num_rotations, seed=seed
        )

        logger.info(f"Generated {len(rotations)} team rotations for date {date}")

        return {
            "date": date,
            "total_signups": len(signups),
            "num_rotations": len(rotations),
            "rotations": rotations,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating team rotations for date {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate rotations: {e!s}")
    finally:
        db.close()


@router.post("/signups/{date}/sunday-game/pairings")
def generate_sunday_game_pairings(  # type: ignore
    date: str = Path(description="Date in YYYY-MM-DD format"),
    num_rotations: int = Query(3, description="Number of Sunday pairing options to generate"),
    seed: int | None = Query(None, description="Override random seed for reproducible results"),
):
    """Generate randomized Sunday game pairings with optional deterministic seeding."""
    try:
        db = database.SessionLocal()

        signups = _get_active_signups_for_date(db, date)

        if len(signups) < 4:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough players signed up for {date}. Need at least 4 players, found {len(signups)}",
            )

        players = _build_player_payload(signups)

        pairing_result = generate_sunday_pairings(players, num_rotations=num_rotations, seed=seed)

        return {
            "date": date,
            "total_signups": len(signups),
            "player_count": pairing_result["player_count"],
            "pairing_sets_available": pairing_result["total_rotations"],
            "selected_rotation": pairing_result["selected_rotation"],
            "rotations": pairing_result["rotations"],
            "random_seed": pairing_result["random_seed"],
            "remaining_players": pairing_result["remaining_players"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Sunday game pairings for {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate Sunday pairings: {e!s}")
    finally:
        db.close()


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
):
    """Generate and save random pairings for a specific date.

    This is the endpoint to call manually or from a cron job.
    """
    try:
        db = database.SessionLocal()
        from ..services.pairing_scheduler_service import PairingSchedulerService

        # Generate pairings
        pairing, message = PairingSchedulerService.generate_pairings(
            db, date, generated_by="manual", force_regenerate=force
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


@router.post("/pairings/{date}/notify")
def resend_pairing_notifications(date: str = Path(description="Date in YYYY-MM-DD format")):  # type: ignore
    """Resend pairing notifications for an existing pairing.

    Use this if some emails failed or you need to notify again.
    """
    try:
        db = database.SessionLocal()
        from ..services.pairing_scheduler_service import PairingSchedulerService

        pairing = PairingSchedulerService.get_existing_pairing(db, date)

        if not pairing:
            raise HTTPException(status_code=404, detail=f"No pairings found for {date}")

        emails_sent, emails_failed = PairingSchedulerService.send_pairing_notifications(db, pairing)

        return {
            "success": True,
            "date": date,
            "emails_sent": emails_sent,
            "emails_failed": emails_failed,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending pairing notifications for {date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send notifications: {e!s}")
    finally:
        db.close()


@router.post("/pairings/run-saturday-job")
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


@router.delete("/pairings/{date}")
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
