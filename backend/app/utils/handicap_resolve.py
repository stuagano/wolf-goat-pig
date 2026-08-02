"""Resolve a player's course handicap from the roster when the client omits one.

A game stores course handicaps — the numbers the group plays off. Never let the
18.0 placeholder stand in for a rostered player: a scratch golfer silently
entered as an 18 collects strokes on most holes and every net score is wrong.
"""

from __future__ import annotations

import re

from sqlalchemy.orm import Session

from .. import models

UNKNOWN_HANDICAP = 18.0


def normalize_player_name(name: str) -> str:
    """Fold a name for matching: case, punctuation and spacing all ignored."""
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


def resolve_player_handicap(
    db: Session,
    *,
    name: str,
    handicap: float | None = None,
    player_profile_id: int | None = None,
) -> tuple[float, models.PlayerProfile | None]:
    """Return (course_handicap, matched_profile).

    An explicit handicap always wins (one-off override for the round). Otherwise
    match by profile id, then by name, and only fall back to the placeholder
    when there is no profile.
    """
    profile: models.PlayerProfile | None = None

    if player_profile_id is not None:
        profile = db.query(models.PlayerProfile).filter(models.PlayerProfile.id == player_profile_id).first()

    if profile is None and name:
        key = normalize_player_name(name)
        if key:
            for row in db.query(models.PlayerProfile).all():
                if row.name and normalize_player_name(str(row.name)) == key:
                    profile = row
                    break

    if handicap is not None:
        return float(handicap), profile

    if profile is not None and profile.handicap is not None:
        return float(profile.handicap), profile

    return UNKNOWN_HANDICAP, profile
