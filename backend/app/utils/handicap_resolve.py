"""Resolve a player's course handicap from the roster when the client omits one.

A game stores course handicaps — the numbers the group plays off. Never let the
18.0 placeholder stand in for a rostered player: a scratch golfer silently
entered as an 18 collects strokes on most holes and every net score is wrong.
"""

from __future__ import annotations

import math
import re
from typing import Any

from sqlalchemy.orm import Session

from .. import models

UNKNOWN_HANDICAP = 18.0


def to_course_handicap(handicap_index: float, course: dict[str, Any] | None) -> float:
    """USGA course handicap: index x slope/113 + (rating - par), rounded half up.

    `course` is a CourseManager course dict (`rating`, `slope`, `holes` or
    `total_par`). Without a rating and slope the index is returned unchanged.
    """
    if not course or not course.get("rating") or not course.get("slope"):
        return handicap_index
    par = sum(h["par"] for h in course.get("holes") or []) or course.get("total_par")
    if not par:
        return handicap_index
    raw = handicap_index * float(course["slope"]) / 113 + (float(course["rating"]) - par)
    return float(math.floor(raw + 0.5))


def find_course(course_name: str | None) -> dict[str, Any] | None:
    """Course details by exact name, else the first whose name contains it
    (lobby games say "Wing Point" for "Wing Point Golf & Country Club")."""
    if not course_name:
        return None
    from ..state.course_manager import CourseManager

    cm = CourseManager()
    details = cm.get_course_details(course_name)
    if details:
        return details
    key = course_name.lower()
    match = next((name for name in cm.get_courses() if key in name.lower()), None)
    return cm.get_course_details(match) if match else None


def resolve_course_handicap(
    db: Session,
    course: dict[str, Any] | None,
    *,
    name: str,
    handicap: float | None = None,
    player_profile_id: int | None = None,
) -> tuple[float, float | None, models.PlayerProfile | None]:
    """Return (course_handicap, handicap_index, matched_profile).

    A typed handicap is the course handicap for the round, used as-is (no
    index). A roster index is converted off the course. The unknown-player
    placeholder is already a course-handicap guess, so it isn't converted.
    """
    resolved, profile = resolve_player_handicap(db, name=name, handicap=handicap, player_profile_id=player_profile_id)
    if handicap is not None or profile is None or profile.handicap is None:
        return resolved, None, profile
    return to_course_handicap(resolved, course), resolved, profile


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
