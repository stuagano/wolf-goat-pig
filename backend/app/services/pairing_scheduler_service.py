"""
Pairing Scheduler Service for Sunday Games RNG Calculator

Handles generating random pairings for Sunday games and notifying players.
Designed to run as a Saturday afternoon cron job.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..models import DailySignup, GeneratedPairing, PlayerProfile
from .email_service import get_email_service
from .team_formation_service import TeamFormationService

logger = logging.getLogger(__name__)

# Golf course email for tee time reservations
TEE_TIME_REQUEST_EMAIL = "stuagano@gmail.com"


class PairingSchedulerService:
    """Service for generating and distributing Sunday game pairings."""

    @staticmethod
    def get_next_sunday(from_date: Optional[datetime] = None) -> str:
        """Get the next Sunday's date in YYYY-MM-DD format.

        If from_date is already Sunday, returns that Sunday.
        """
        if from_date is None:
            from_date = datetime.now()

        days_until_sunday = (6 - from_date.weekday()) % 7
        if days_until_sunday == 0 and from_date.weekday() != 6:
            days_until_sunday = 7

        next_sunday = from_date + timedelta(days=days_until_sunday)
        return next_sunday.strftime("%Y-%m-%d")

    @staticmethod
    def get_signups_for_date(db: Session, game_date: str) -> List[DailySignup]:
        """Get all active signups for a specific date."""
        return (
            db.query(DailySignup)
            .filter(DailySignup.date == game_date)
            .filter(DailySignup.status == "signed_up")
            .all()
        )

    @staticmethod
    def get_existing_pairing(db: Session, game_date: str) -> Optional[GeneratedPairing]:
        """Check if pairings already exist for a date."""
        return (
            db.query(GeneratedPairing)
            .filter(GeneratedPairing.game_date == game_date)
            .first()
        )

    @staticmethod
    def build_player_list(
        db: Session, signups: List[DailySignup]
    ) -> List[Dict]:
        """Convert signups to player dicts with handicap info."""
        players = []
        for signup in signups:
            player_data = {
                "player_name": signup.player_name,
                "player_profile_id": signup.player_profile_id,
                "handicap": 18.0,  # Default
            }

            # Try to get actual handicap from profile
            if signup.player_profile_id:
                profile = (
                    db.query(PlayerProfile)
                    .filter(PlayerProfile.id == signup.player_profile_id)
                    .first()
                )
                if profile and profile.handicap is not None:
                    player_data["handicap"] = profile.handicap

            players.append(player_data)

        return players

    @staticmethod
    def generate_pairings(
        db: Session,
        game_date: str,
        generated_by: str = "scheduler",
        force_regenerate: bool = False
    ) -> Tuple[Optional[GeneratedPairing], str]:
        """Generate random pairings for a game date.

        Args:
            db: Database session
            game_date: Date in YYYY-MM-DD format
            generated_by: Who triggered the generation ("scheduler" or username)
            force_regenerate: If True, overwrites existing pairings

        Returns:
            Tuple of (GeneratedPairing or None, status message)
        """
        # Check for existing pairings
        existing = PairingSchedulerService.get_existing_pairing(db, game_date)
        if existing and not force_regenerate:
            return existing, "Pairings already exist for this date"

        # Get signups
        signups = PairingSchedulerService.get_signups_for_date(db, game_date)
        if len(signups) < 4:
            return None, f"Not enough players signed up ({len(signups)}). Need at least 4."

        # Build player list
        players = PairingSchedulerService.build_player_list(db, signups)

        # Generate random teams (returns list directly)
        teams = TeamFormationService.generate_random_teams(players)

        if not teams:
            return None, "Failed to generate teams"

        now = datetime.now().isoformat()

        # Calculate remaining players (those not in complete teams of 4)
        players_in_teams = sum(len(t.get("players", [])) for t in teams)
        remaining = len(players) - players_in_teams

        # Prepare pairing data
        pairings_data = {
            "teams": teams,
            "players": players,
            "generation_method": "random",
            "remaining_players": [
                p for p in players
                if not any(
                    p["player_name"] in [tp.get("player_name") for tp in t.get("players", [])]
                    for t in teams
                )
            ],
        }

        # Delete existing if regenerating
        if existing and force_regenerate:
            db.delete(existing)
            db.flush()

        # Create new pairing record
        pairing = GeneratedPairing(
            game_date=game_date,
            generated_at=now,
            generated_by=generated_by,
            random_seed=None,  # Pure random
            player_count=len(players),
            team_count=len(teams),
            remaining_players=remaining,
            pairings_data=pairings_data,
            notification_sent=False,
            created_at=now,
        )

        db.add(pairing)
        db.commit()
        db.refresh(pairing)

        logger.info(
            "Generated pairings for %s: %d players -> %d teams",
            game_date,
            len(players),
            len(teams),
        )

        return pairing, f"Generated {len(teams)} teams from {len(players)} players"

    @staticmethod
    def find_player_team(player_name: str, teams: List[Dict]) -> Optional[int]:
        """Find which team (1-indexed) a player is in."""
        for i, team in enumerate(teams, 1):
            team_players = team.get("players", [])
            for p in team_players:
                if p.get("player_name") == player_name:
                    return i
        return None

    @staticmethod
    def send_pairing_notifications(
        db: Session,
        pairing: GeneratedPairing
    ) -> Tuple[int, int]:
        """Send email notifications to all signed-up players and the golf course.

        Returns:
            Tuple of (emails_sent, emails_failed)
        """
        email_service = get_email_service()
        if not email_service.is_configured():
            logger.warning("Email service not configured, skipping notifications")
            return 0, 0

        teams = pairing.pairings_data.get("teams", [])
        players = pairing.pairings_data.get("players", [])

        emails_sent = 0
        emails_failed = 0

        # Send tee time request to the golf course
        try:
            tee_time_success = email_service.send_tee_time_request(
                to_email=TEE_TIME_REQUEST_EMAIL,
                game_date=pairing.game_date,
                teams=teams,
                player_count=pairing.player_count,
                remaining_players=pairing.remaining_players,
            )
            if tee_time_success:
                emails_sent += 1
                logger.info("Tee time request sent to %s", TEE_TIME_REQUEST_EMAIL)
            else:
                emails_failed += 1
                logger.error("Failed to send tee time request to %s", TEE_TIME_REQUEST_EMAIL)
        except Exception as e:
            logger.error("Failed to send tee time request: %s", e)
            emails_failed += 1

        # Get email addresses for all players
        for player in players:
            profile_id = player.get("player_profile_id")
            if not profile_id:
                continue

            profile = (
                db.query(PlayerProfile)
                .filter(PlayerProfile.id == profile_id)
                .first()
            )

            if not profile or not profile.email:
                logger.debug("No email for player %s", player.get("player_name"))
                continue

            # Find which team they're on
            team_number = PairingSchedulerService.find_player_team(
                player.get("player_name", ""),
                teams
            )

            try:
                success = email_service.send_pairing_notification(
                    to_email=profile.email,
                    player_name=player.get("player_name", "Golfer"),
                    game_date=pairing.game_date,
                    teams=teams,
                    player_team_number=team_number,
                )
                if success:
                    emails_sent += 1
                else:
                    emails_failed += 1
            except Exception as e:
                logger.error("Failed to send pairing email to %s: %s", profile.email, e)
                emails_failed += 1

        # Update pairing record
        if emails_sent > 0:
            pairing.notification_sent = True
            pairing.notification_sent_at = datetime.now().isoformat()
            db.commit()

        logger.info(
            "Pairing notifications for %s: %d sent, %d failed (includes tee time request)",
            pairing.game_date,
            emails_sent,
            emails_failed,
        )

        return emails_sent, emails_failed

    @staticmethod
    def run_saturday_job(db: Session) -> Dict:
        """Run the Saturday afternoon pairing job.

        Generates pairings for the next Sunday and sends notifications.

        Returns:
            Dict with job results
        """
        next_sunday = PairingSchedulerService.get_next_sunday()
        logger.info("Running Saturday pairing job for Sunday %s", next_sunday)

        # Generate pairings
        pairing, message = PairingSchedulerService.generate_pairings(
            db,
            next_sunday,
            generated_by="scheduler",
            force_regenerate=False,
        )

        if not pairing:
            return {
                "success": False,
                "game_date": next_sunday,
                "message": message,
                "emails_sent": 0,
                "emails_failed": 0,
            }

        # Send notifications
        emails_sent, emails_failed = PairingSchedulerService.send_pairing_notifications(
            db, pairing
        )

        return {
            "success": True,
            "game_date": next_sunday,
            "message": message,
            "team_count": pairing.team_count,
            "player_count": pairing.player_count,
            "emails_sent": emails_sent,
            "emails_failed": emails_failed,
        }
