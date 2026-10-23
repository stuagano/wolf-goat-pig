"""Opt-in email alerts to players already signed up for the same day."""

import logging
import threading

from sqlalchemy import or_

from ..database import SessionLocal
from ..models import DailySignup, EmailPreferences, PlayerProfile, SameDaySignupNotification
from ..observability.report import report_exception, report_message
from ..utils.time import utc_now
from .email_service import get_email_service

logger = logging.getLogger(__name__)


def deliver_same_day_signup_notifications(signup_id: int) -> None:
    """Best-effort delivery; accepted recipients are recorded to prevent repeats.

    Lock the source signup until delivery completes so concurrent dispatches for
    the same signup serialize on PostgreSQL. A failed recipient remains eligible
    for a later retry. Provider acceptance and our DB commit are not atomic.
    """
    db = SessionLocal()
    try:
        signup = db.query(DailySignup).filter(DailySignup.id == signup_id).with_for_update().first()
        if signup is None or signup.status != "signed_up":
            return
        sender = get_email_service()
        if not sender.is_configured():
            logger.warning("Same-day signup alerts skipped: email provider not configured (signup %s)", signup_id)
            return
        recipients = (
            db.query(PlayerProfile)
            .join(EmailPreferences, EmailPreferences.player_profile_id == PlayerProfile.id)
            .join(DailySignup, DailySignup.player_profile_id == PlayerProfile.id)
            .filter(
                EmailPreferences.same_day_signups_enabled == 1,
                EmailPreferences.email_frequency != "never",
                PlayerProfile.is_active == 1,
                DailySignup.date == signup.date,
                DailySignup.status == "signed_up",
                DailySignup.id != signup.id,
                or_(
                    DailySignup.signup_time < signup.signup_time,
                    (DailySignup.signup_time == signup.signup_time) & (DailySignup.id < signup.id),
                ),
            )
            .order_by(PlayerProfile.id)
            .all()
        )
        for player in recipients:
            if not player.email or player.id == signup.player_profile_id:
                continue
            delivered = (
                db.query(SameDaySignupNotification)
                .filter_by(signup_id=signup.id, recipient_profile_id=player.id)
                .first()
            )
            if delivered:
                continue
            try:
                accepted = sender.send_same_day_signup_notification(
                    to_email=player.email,
                    player_name=player.name or "Golfer",
                    joining_player_name=signup.player_name,
                    signup_date=signup.date,
                )
                if accepted:
                    db.add(
                        SameDaySignupNotification(
                            signup_id=signup.id,
                            recipient_profile_id=player.id,
                            sent_at=utc_now().isoformat(),
                        )
                    )
                    db.flush()
                else:
                    report_message(f"Same-day signup alert rejected (signup_id={signup_id}, recipient_id={player.id})")
            except Exception as exc:
                logger.warning("Same-day signup alert failed for player %s", player.id, exc_info=True)
                report_exception(exc)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.exception("Same-day signup alerts failed for signup %s", signup_id)
        report_exception(exc)
    finally:
        db.close()


def send_same_day_signup_notifications(signup_id: int) -> None:
    """Send outside the request, independently of the player's confirmation."""
    threading.Thread(
        target=deliver_same_day_signup_notifications,
        args=(signup_id,),
        daemon=True,
        name="same-day-signup-alerts",
    ).start()
