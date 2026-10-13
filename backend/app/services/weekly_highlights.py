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
    week = [r for r in get_unified_data_service(db=db).get_season_rounds() if start <= r.date_sortable < end]
    if not week:
        return None

    net: dict[str, int] = defaultdict(int)
    rounds: dict[str, int] = defaultdict(int)
    biggest_round = None
    biggest_hole = None
    for r in week:
        net[r.member] += r.score
        rounds[r.member] += 1
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

    top = max(net, key=lambda n: net[n])
    most = max(rounds.values())
    return {
        # A round is one foursome: same grouping as GET /data/leaderboard/rounds.
        "rounds": len({(r.date_sortable, r.group, r.location) for r in week}),
        "courses": sorted({r.location for r in week}),
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
