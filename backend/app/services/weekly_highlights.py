"""Weekly league highlights email.

Sent Monday midday (GitHub Actions cron → /internal/jobs/weekly-summaries) to
every active player with an email unless they opted out. Covers the Mon–Sun
week (Pacific) that just ended, so Sunday's games are always included, over the
merged league rounds (sheet + member posts + app games). The
same highlights go to everyone; a per-(week, player) log makes reruns safe.
"""

import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..models import EmailPreferences, PlayerProfile, WeeklyHighlightSend
from ..utils.time import CLUB_TZ, utc_now
from . import email_voice
from .email_service import get_email_service
from .unified_data_service import get_unified_data_service

logger = logging.getLogger(__name__)


def week_window(now_utc: datetime) -> tuple[str, str]:
    """Most recent fully completed Mon–Sun club week (Pacific), as YYYY-MM-DD [start, end)."""
    today = now_utc.replace(tzinfo=UTC).astimezone(CLUB_TZ).date()
    monday = today - timedelta(days=today.weekday() + 7)
    return monday.isoformat(), (monday + timedelta(days=7)).isoformat()


def compute_highlights(db: Session, start: str, end: str) -> dict[str, Any] | None:
    """League-wide highlights for rounds dated in [start, end), or None if there were none.

    Reads the same merged view as the leaderboard: sheet rounds + attested member
    posts (legacy_rounds) + in-app scored games. Only app rounds carry hole detail.
    """
    # ponytail: app games are dated by their UTC completed_at in the unified service,
    # so one finishing after 5pm PT Sunday lands in the next week; fix there if it bites.
    history = [
        r
        for r in get_unified_data_service(db=db).get_season_rounds()
        if r.date_sortable and start <= r.date_sortable < end
    ]
    week = [r for r in history if r.score_eligible and r.score is not None]
    if not history:
        return None

    net = defaultdict(float)
    rounds = defaultdict(int)
    labels = {}
    biggest_round = None
    biggest_hole = None
    for r in week:
        identity = (
            ("profile", r.player_id)
            if r.player_id is not None
            else (("guest", r.game_id, r.participant_id) if r.source == "canonical" else r.member)
        )
        labels[identity] = r.member
        net[identity] += r.score
        rounds[identity] += 1
        if biggest_round is None or r.score > biggest_round["quarters"]:
            biggest_round = {"player": r.member, "quarters": r.score, "course": r.location}
        for hole in r.hole_scores or []:
            quarters = hole.get("quarters") if isinstance(hole, dict) else None
            if isinstance(quarters, int | float) and (biggest_hole is None or quarters > biggest_hole["quarters"]):
                biggest_hole = {
                    "player": r.member,
                    "hole": hole.get("hole"),
                    "quarters": quarters,
                    "course": r.location,
                }

    top = max(net, key=lambda n: net[n]) if net else None
    most = max(rounds.values(), default=0)
    return {
        # A round is one foursome: same grouping as GET /data/leaderboard/rounds.
        # Canonical rounds are one game UUID; the old key merged two same-day games.
        "rounds": len({r.game_id or (r.date_sortable, r.group, r.location) for r in week}),
        "known_participation_count": len(history),
        "scored_participation_count": len(week),
        "incomplete_rounds": len({r.game_id or r.game_key for r in history if not r.score_eligible}),
        "courses": sorted({r.location for r in history if r.location is not None}),
        "players": sorted(
            {
                (
                    ("profile", r.player_id)
                    if r.player_id is not None
                    else (("guest", r.game_id, r.participant_id) if r.source == "canonical" else r.member)
                ): r.member
                for r in history
            }.values()
        ),
        "biggest_round": biggest_round,
        "top_earner": {"player": labels[top], "quarters": net[top], "rounds": rounds[top]} if top is not None else None,
        "biggest_hole": biggest_hole if biggest_hole and biggest_hole["quarters"] > 0 else None,
        "ironman": {"players": sorted(labels[n] for n, c in rounds.items() if c == most), "rounds": most}
        if most > 1
        else None,
    }


def get_recipients(db: Session) -> list[PlayerProfile]:
    """Everyone active with an email, unless they turned weekly summaries off or set frequency never/monthly.
    A player with no preferences row is opted in (the column defaults are on)."""
    return (
        db.query(PlayerProfile)
        .outerjoin(EmailPreferences, EmailPreferences.player_profile_id == PlayerProfile.id)
        .filter(
            PlayerProfile.is_active == 1,
            PlayerProfile.email.isnot(None),
            PlayerProfile.email != "",
            or_(
                EmailPreferences.id.is_(None),
                (EmailPreferences.weekly_summary_enabled == 1)
                & or_(
                    EmailPreferences.email_frequency.is_(None),
                    EmailPreferences.email_frequency.in_(["daily", "weekly"]),
                ),
            ),
        )
        .all()
    )


def run(db: Session, *, now: datetime | None = None, email_service=None, dry_run: bool = False) -> dict[str, Any]:
    """Compute last week's highlights and email everyone who hasn't had them yet."""
    week_start, week_end = week_window(now or utc_now())
    highlights = compute_highlights(db, week_start, week_end)
    if highlights is None:
        return {"week_start": week_start, "sent": 0, "reason": "no_rounds"}

    already = {
        pid
        for (pid,) in db.query(WeeklyHighlightSend.player_profile_id).filter(
            WeeklyHighlightSend.week_start == week_start
        )
    }
    pending = [p for p in get_recipients(db) if p.id not in already]

    if dry_run:
        highlights["intro"] = email_voice.commissioner_intro("weekly league highlights", highlights)
        return {
            "dry_run": True,
            "week_start": week_start,
            "highlights": highlights,
            "recipient_count": len(pending),
            "already_sent": len(already),
        }

    email_service = email_service or get_email_service()
    if not email_service.is_configured():
        logger.warning("Weekly highlights for %s skipped: email service not configured", week_start)
        return {"week_start": week_start, "sent": 0, "reason": "email_not_configured"}

    # One Commissioner-voice intro for everyone; None (plain email) if the AI is unavailable.
    if pending:
        highlights["intro"] = email_voice.commissioner_intro("weekly league highlights", highlights)

    sent = failed = 0
    for player in pending:
        try:
            ok = email_service.send_weekly_highlights(
                to_email=player.email, player_name=player.name or "Golfer", highlights=highlights
            )
        except Exception as e:
            logger.error("Weekly highlights to player %s raised: %s", player.id, e)
            ok = False
        if ok:
            # Commit per send so a crash mid-run never re-emails the ones already done.
            db.add(
                WeeklyHighlightSend(week_start=week_start, player_profile_id=player.id, sent_at=utc_now().isoformat())
            )
            db.commit()
            sent += 1
        else:
            failed += 1

    logger.info("Weekly highlights %s: sent=%d failed=%d already=%d", week_start, sent, failed, len(already))
    return {"week_start": week_start, "sent": sent, "failed": failed, "already_sent": len(already)}
