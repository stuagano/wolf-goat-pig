"""Keep the pending sign-up queue free of rows that need no admin action.

A pending row exists so an admin can add a brand-new golfer to the roster.
Once that golfer's profile is linked to a roster name some other way (they
picked their name in onboarding, an admin linked them in Account links, or a
claim moved their login onto an older profile), the row is done and must not
linger as a manual task.
"""

from __future__ import annotations

import logging
from typing import Any

from ..models import PendingLegacyPlayer, PlayerProfile
from ..utils.time import utc_now

logger = logging.getLogger(__name__)


def resolve_pending_for_profile(db: Any, player_profile_id: int, canonical_name: str) -> int:
    """Mark a profile's pending rows resolved because it is now linked. Caller commits."""
    rows = (
        db.query(PendingLegacyPlayer)
        .filter(
            PendingLegacyPlayer.player_profile_id == player_profile_id,
            PendingLegacyPlayer.status == "pending",
        )
        .all()
    )
    for row in rows:
        row.status = "promoted"
        row.resolved_at = utc_now().isoformat()
        row.notes = f"Auto-resolved: profile linked to '{canonical_name}'"
    if rows:
        logger.info(
            "Auto-resolved %d pending sign-up(s) for profile id=%s (linked to '%s')",
            len(rows),
            player_profile_id,
            canonical_name,
        )
    return len(rows)


def _is_real_link(legacy_name: str | None) -> bool:
    name = (legacy_name or "").strip()
    return bool(name) and "@" not in name


def resolve_stale_pending(db: Any) -> int:
    """Resolve pending rows whose profile no longer needs an admin. Commits if anything changed.

    - The profile is linked to a roster name: resolved as promoted.
    - The profile is gone or retired (e.g. a claim moved the login onto an
      older profile): dismissed.
    """
    rows = (
        db.query(PendingLegacyPlayer)
        .filter(
            PendingLegacyPlayer.status == "pending",
            PendingLegacyPlayer.player_profile_id.isnot(None),
        )
        .all()
    )
    changed = 0
    for row in rows:
        profile = db.get(PlayerProfile, row.player_profile_id)
        if profile is None or not profile.is_active:
            row.status = "dismissed"
            row.notes = "Auto-resolved: sign-in profile was retired or merged"
        elif _is_real_link(profile.legacy_name):
            row.status = "promoted"
            row.notes = f"Auto-resolved: profile linked to '{profile.legacy_name}'"
        else:
            continue
        row.resolved_at = utc_now().isoformat()
        changed += 1
    if changed:
        db.commit()
        logger.info("Auto-resolved %d stale pending sign-up(s)", changed)
    return changed
