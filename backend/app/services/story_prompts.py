"""Nightly bell prompt: ask each player in a recent round to check the scores and add a story.

GitHub Actions cron → /internal/jobs/story-prompts. One prompt per (player, round),
ever: the existing ``story_prompt`` notifications are the dedup log, so reruns and
the overlapping lookback window never double-prompt. Bell only; no email.
"""

import logging
from datetime import UTC, timedelta
from typing import Any
from urllib.parse import quote

from sqlalchemy.orm import Session

from ..models import Notification, PlayerProfile
from ..utils.time import CLUB_TZ, utc_now
from .player_name_index import profile_id_for_member, profile_ids_by_member
from .unified_data_service import get_unified_data_service

logger = logging.getLogger(__name__)

STORY_PROMPT_TYPE = "story_prompt"
# Sheet rounds can land a day or two after they're played.
LOOKBACK_DAYS = 3


def round_path(r) -> str:
    """Same link the leaderboard builds (frontend roundLink.js)."""
    if r.game_id:
        return f"/game/{quote(r.game_id)}"
    query = f"?location={quote(r.location)}" if r.location else ""
    return f"/rounds/{quote(r.date_sortable or r.date)}/{quote(r.group or '')}{query}"


def run(db: Session, *, now=None, dry_run: bool = False) -> dict[str, Any]:
    today = (now or utc_now()).replace(tzinfo=UTC).astimezone(CLUB_TZ).date()
    since = (today - timedelta(days=LOOKBACK_DAYS)).isoformat()
    rounds = [r for r in get_unified_data_service(db=db).get_season_rounds() if (r.date_sortable or "") >= since]

    names = profile_ids_by_member(db)
    reachable = {
        pid for (pid,) in db.query(PlayerProfile.id).filter(PlayerProfile.is_active == 1, PlayerProfile.is_ai == 0)
    }
    # ponytail: loads every story prompt ever sent; filter by created_at if this grows large.
    already = {
        (n.player_profile_id, (n.data or {}).get("path"))
        for n in db.query(Notification).filter(Notification.notification_type == STORY_PROMPT_TYPE)
    }

    created_at = utc_now().isoformat()
    new = []
    for r in rounds:
        pid = r.player_id if r.player_id is not None else profile_id_for_member(r.member, names)
        path = round_path(r)
        if pid not in reachable or (pid, path) in already:
            continue
        already.add((pid, path))
        where = f"{r.date} at {r.location}" if r.location else r.date
        new.append(
            Notification(
                player_profile_id=pid,
                notification_type=STORY_PROMPT_TYPE,
                message=f"How'd {where} go? Check the scores and add a story.",
                data={"path": path},
                is_read=False,
                created_at=created_at,
            )
        )

    if not dry_run and new:
        db.add_all(new)
        db.commit()
    logger.info("Story prompts since %s: %d new (dry_run=%s)", since, len(new), dry_run)
    return {"since": since, "rounds": len(rounds), "prompted": len(new), "dry_run": dry_run}
