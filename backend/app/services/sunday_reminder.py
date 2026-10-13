"""Thursday "Sunday's game" signup nudge.

Sent Thursday midday (GitHub Actions cron → /internal/jobs/sunday-reminder) to
every active player with an email who isn't signed up for this Sunday yet,
unless they turned off Sign-up Reminders. Lists who's in so far, links to sign
up. Complements the Friday/Sunday short-a-foursome callouts. A per-(Sunday,
player) log makes reruns safe.
"""

import logging
from datetime import date, timedelta
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..models import DailySignup, EmailPreferences, PlayerProfile, SignupReminderSend
from ..utils.time import club_today, utc_now
from . import email_voice
from .email_service import get_email_service

logger = logging.getLogger(__name__)


def next_sunday(today: date) -> date:
    """The coming Sunday (today, if today is Sunday)."""
    return today + timedelta(days=(6 - today.weekday()) % 7)


def _signups(db: Session, game_date: str):
    return db.query(DailySignup).filter(DailySignup.date == game_date, DailySignup.status == "signed_up")


def signed_up_names(db: Session, game_date: str) -> list[str]:
    return sorted({s.player_name for s in _signups(db, game_date) if s.player_name})


def get_recipients(db: Session, game_date: str) -> list[PlayerProfile]:
    """Active players with an email who aren't signed up for game_date and haven't opted out.
    A player with no preferences row is opted in (the column default is on)."""
    signed_up_ids = {s.player_profile_id for s in _signups(db, game_date) if s.player_profile_id is not None}
    players = (
        db.query(PlayerProfile)
        .outerjoin(EmailPreferences, EmailPreferences.player_profile_id == PlayerProfile.id)
        .filter(
            PlayerProfile.is_active == 1,
            PlayerProfile.email.isnot(None),
            PlayerProfile.email != "",
            or_(
                EmailPreferences.id.is_(None),
                (EmailPreferences.signup_reminders_enabled == 1)
                & or_(EmailPreferences.email_frequency.is_(None), EmailPreferences.email_frequency != "never"),
            ),
        )
        .all()
    )
    return [p for p in players if p.id not in signed_up_ids]


def run(db: Session, *, today: date | None = None, email_service=None, dry_run: bool = False) -> dict[str, Any]:
    """Nudge everyone not yet signed up for the coming Sunday."""
    game_date = next_sunday(today or club_today()).isoformat()
    signed_up = signed_up_names(db, game_date)

    already = {
        pid
        for (pid,) in db.query(SignupReminderSend.player_profile_id).filter(SignupReminderSend.game_date == game_date)
    }
    pending = [p for p in get_recipients(db, game_date) if p.id not in already]

    def intro() -> str | None:
        facts = {"game_date": game_date, "signed_up": signed_up, "signed_up_count": len(signed_up)}
        return email_voice.commissioner_intro("Thursday nudge to sign up for Sunday's game", facts)

    if dry_run:
        return {
            "dry_run": True,
            "game_date": game_date,
            "intro": intro(),
            "signed_up": signed_up,
            "recipient_count": len(pending),
            "already_sent": len(already),
        }

    email_service = email_service or get_email_service()
    if not email_service.is_configured():
        logger.warning("Sunday reminder for %s skipped: email service not configured", game_date)
        return {"game_date": game_date, "sent": 0, "reason": "email_not_configured"}

    # One Commissioner-voice intro for everyone; None (plain email) if the AI is unavailable.
    shared_intro = intro() if pending else None

    sent = failed = 0
    for player in pending:
        try:
            ok = email_service.send_sunday_reminder(
                to_email=player.email,
                player_name=player.name or "Golfer",
                game_date=game_date,
                signed_up=signed_up,
                intro=shared_intro,
            )
        except Exception as e:
            logger.error("Sunday reminder to player %s raised: %s", player.id, e)
            ok = False
        if ok:
            # Commit per send so a crash mid-run never re-emails the ones already done.
            db.add(SignupReminderSend(game_date=game_date, player_profile_id=player.id, sent_at=utc_now().isoformat()))
            db.commit()
            sent += 1
        else:
            failed += 1

    logger.info("Sunday reminder %s: sent=%d failed=%d already=%d", game_date, sent, failed, len(already))
    return {"game_date": game_date, "sent": sent, "failed": failed, "already_sent": len(already)}
