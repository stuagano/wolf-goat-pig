"""Weekly league highlights email.

Sent Monday midday (GitHub Actions cron → /internal/jobs/weekly-summaries) to
every active player with an email unless they opted out. Covers the Mon–Sun
week (Pacific) that just ended, so Sunday's games are always included. The
same highlights go to everyone; a per-(week, player) log makes reruns safe.
"""

import logging
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..models import EmailPreferences, GamePlayerResult, GameRecord, PlayerProfile, WeeklyHighlightSend
from ..utils.time import CLUB_TZ, utc_now
from .email_service import get_email_service

logger = logging.getLogger(__name__)


def week_window(now_utc: datetime) -> tuple[datetime, datetime, str]:
    """Most recent fully completed Mon–Sun club week, as naive-UTC [start, end) + its Monday date."""
    today = now_utc.replace(tzinfo=UTC).astimezone(CLUB_TZ).date()
    monday = today - timedelta(days=today.weekday() + 7)

    def to_utc(d) -> datetime:
        local = datetime(d.year, d.month, d.day, tzinfo=CLUB_TZ)
        return local.astimezone(UTC).replace(tzinfo=None)

    return to_utc(monday), to_utc(monday + timedelta(days=7)), monday.isoformat()


def _parse_utc(value: str | None) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value) if value else None
    except ValueError:
        return None
    if parsed and parsed.tzinfo:
        parsed = parsed.astimezone(UTC).replace(tzinfo=None)
    return parsed


def compute_highlights(db: Session, start: datetime, end: datetime) -> dict[str, Any] | None:
    """League-wide highlights for games completed in [start, end), or None if no rounds."""
    # ponytail: parses every completed record's timestamp in Python (formats vary by writer);
    # fine at club scale, push the date filter into SQL if game_records grows large.
    games = [
        g
        for g in db.query(GameRecord).filter(GameRecord.completed_at.isnot(None))
        if start <= (_parse_utc(g.completed_at) or end) < end
    ]
    if not games:
        return None

    course_by_id = {g.id: g.course_name or "Unknown course" for g in games}
    results = db.query(GamePlayerResult).filter(GamePlayerResult.game_record_id.in_(course_by_id)).all()
    if not results:
        return None

    net: dict[str, float] = defaultdict(float)
    rounds: dict[str, int] = defaultdict(int)
    biggest_round = None
    biggest_hole = None
    for r in results:
        name = r.player_name or f"Player {r.player_profile_id}"
        earnings = r.total_earnings or 0
        net[name] += earnings
        rounds[name] += 1
        course = course_by_id[r.game_record_id]
        if biggest_round is None or earnings > biggest_round["quarters"]:
            biggest_round = {"player": name, "quarters": earnings, "course": course}
        for hole in r.hole_scores or []:
            quarters = hole.get("quarters") if isinstance(hole, dict) else None
            if isinstance(quarters, int | float) and (biggest_hole is None or quarters > biggest_hole["quarters"]):
                biggest_hole = {"player": name, "hole": hole.get("hole"), "quarters": quarters, "course": course}

    top = max(net, key=lambda n: net[n])
    most = max(rounds.values())
    return {
        "rounds": len(games),
        "courses": sorted(set(course_by_id.values())),
        "players": sorted(rounds),
        "biggest_round": biggest_round,
        "top_earner": {"player": top, "quarters": net[top], "rounds": rounds[top]},
        "biggest_hole": biggest_hole if biggest_hole and biggest_hole["quarters"] > 0 else None,
        "ironman": {"players": sorted(n for n, c in rounds.items() if c == most), "rounds": most} if most > 1 else None,
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
    start, end, week_start = week_window(now or utc_now())
    highlights = compute_highlights(db, start, end)
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
