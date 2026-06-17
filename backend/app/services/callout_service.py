"""
Callout Service — "we're short for a game" headcount notifications.

When signups for a game date fall short of a full foursome, email the players
who have opted into the callout list (EmailPreferences.callout_list_enabled)
so they get first dibs before anyone resorts to a mass text.

Designed to be driven by the email scheduler (day-before evening + morning-of),
calling these functions DIRECTLY against the DB — no self-HTTP, no deadlock risk.
"""

import logging

from sqlalchemy.orm import Session

from ..models import CalloutNotification, DailySignup, EmailPreferences, PlayerProfile
from ..utils.time import utc_now
from .email_service import get_email_service
from .pairing_scheduler_service import PairingSchedulerService

logger = logging.getLogger(__name__)

# Golf is played in foursomes; a game is only "forming" once a full group exists.
FOURSOME_SIZE = 4


def foursome_target(signup_count: int) -> int:
    """Round signups up to the next full foursome.

    11 -> 12, 13 -> 16, 12 -> 12 (already full). Returns 0 for no signups.
    """
    if signup_count <= 0:
        return 0
    return ((signup_count + FOURSOME_SIZE - 1) // FOURSOME_SIZE) * FOURSOME_SIZE


def compute_shortfall(signup_count: int) -> int:
    """How many more players are needed to complete the next foursome.

    Returns 0 when no callout should fire: an empty/partial day below one full
    foursome (no real game forming yet) or an exact multiple of four.
    """
    if signup_count < FOURSOME_SIZE:
        return 0
    return foursome_target(signup_count) - signup_count


def _already_called(db: Session, game_date: str, window: str) -> bool:
    return (
        db.query(CalloutNotification)
        .filter(CalloutNotification.game_date == game_date, CalloutNotification.callout_window == window)
        .first()
        is not None
    )


def get_callout_recipients(db: Session, game_date: str) -> list[PlayerProfile]:
    """Opt-in players who should be called for a date.

    On the list, have an email, haven't globally paused emails, and aren't
    already signed up for that date.
    """
    signed_up_ids = {
        row.player_profile_id
        for row in db.query(DailySignup.player_profile_id)
        .filter(DailySignup.date == game_date, DailySignup.status == "signed_up")
        .all()
        if row.player_profile_id is not None
    }

    opted_in = (
        db.query(PlayerProfile)
        .join(EmailPreferences, EmailPreferences.player_profile_id == PlayerProfile.id)
        .filter(
            EmailPreferences.callout_list_enabled == 1,
            EmailPreferences.email_frequency != "never",
            PlayerProfile.is_active == 1,
        )
        .all()
    )

    return [p for p in opted_in if p.email and p.id not in signed_up_ids]


def run_callout(db: Session, game_date: str, window: str) -> dict:
    """Evaluate a game date and, if short, email the callout list.

    Args:
        db: Database session
        game_date: Date in YYYY-MM-DD format
        window: "pre_pairing" or "morning_of" (for once-per-window dedup)

    Returns:
        Dict describing what happened (fired/skipped, counts).
    """
    signups = PairingSchedulerService.get_signups_for_date(db, game_date)
    signup_count = len(signups)
    shortfall = compute_shortfall(signup_count)

    if shortfall == 0:
        return {
            "fired": False,
            "reason": "not_short",
            "game_date": game_date,
            "window": window,
            "signup_count": signup_count,
        }

    if _already_called(db, game_date, window):
        return {
            "fired": False,
            "reason": "already_called",
            "game_date": game_date,
            "window": window,
            "signup_count": signup_count,
        }

    email_service = get_email_service()
    if not email_service.is_configured():
        logger.warning("Callout for %s skipped: email service not configured", game_date)
        return {
            "fired": False,
            "reason": "email_not_configured",
            "game_date": game_date,
            "window": window,
            "signup_count": signup_count,
        }

    target = foursome_target(signup_count)
    recipients = get_callout_recipients(db, game_date)

    sent = 0
    for player in recipients:
        try:
            ok = email_service.send_callout_notification(
                to_email=player.email,
                player_name=player.name or "Golfer",
                game_date=game_date,
                signup_count=signup_count,
                needed=shortfall,
            )
            if ok:
                sent += 1
        except Exception as exc:  # one bad address shouldn't sink the rest
            logger.error("Callout email to %s failed: %s", player.email, exc)

    # Record the callout so this window never fires twice for this date.
    db.add(
        CalloutNotification(
            game_date=game_date,
            callout_window=window,
            signup_count=signup_count,
            target=target,
            shortfall=shortfall,
            recipient_count=sent,
            sent_at=utc_now().isoformat(),
        )
    )
    db.commit()

    logger.info(
        "Callout fired for %s (%s): %d signed up, %d short, %d players emailed",
        game_date,
        window,
        signup_count,
        shortfall,
        sent,
    )

    return {
        "fired": True,
        "game_date": game_date,
        "window": window,
        "signup_count": signup_count,
        "target": target,
        "shortfall": shortfall,
        "recipient_count": sent,
    }


def run_callout_for_next_sunday(db: Session, window: str) -> dict:
    """Convenience wrapper: run the callout for the upcoming Sunday game."""
    next_sunday = PairingSchedulerService.get_next_sunday()
    return run_callout(db, next_sunday, window)
