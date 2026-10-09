"""Compare the app's canonical roster with Jeff's live legacy dropdown.

The legacy tee sheet (thousand-cranes.com) only accepts sign-ups for names on
its player dropdown, so the app roster should match it. This reads the dropdown
read-only, reports drift, and lets an admin remove junk entries (emails,
nicknames) that no active profile uses.
"""

from __future__ import annotations

import html
import re
from typing import Any

import httpx
from sqlalchemy import func, or_

from ..models import LegacyRosterPlayer, PlayerProfile

DROPDOWN_URL = "https://thousand-cranes.com/WolfGoatPig/wgp_tee_sheet.cgi"
_PLAYER_SELECT = re.compile(r'<select[^>]*name="player"[^>]*>(.*?)</select>', re.S | re.I)
_OPTION = re.compile(r"<option[^>]*>(.*?)(?=<option|$)", re.S | re.I)
_PLACEHOLDERS = ("select", "--", "choose")


def parse_dropdown(page: str) -> list[str]:
    """Player names from the tee sheet's ``<select name="player">`` (options may be unclosed)."""
    match = _PLAYER_SELECT.search(page)
    if not match:
        return []
    names = (html.unescape(re.sub(r"<[^>]+>", "", option)).strip() for option in _OPTION.findall(match.group(1)))
    return [name for name in names if name and not name.lower().startswith(_PLACEHOLDERS)]


def fetch_dropdown_names() -> list[str]:
    """Read the live dropdown. Raises httpx.HTTPError or ValueError if it can't be read."""
    resp = httpx.get(DROPDOWN_URL, headers={"Referer": DROPDOWN_URL}, timeout=10.0)
    resp.raise_for_status()
    names = parse_dropdown(resp.text)
    if not names:
        raise ValueError("No player dropdown found on the legacy tee sheet")
    return names


def is_junk_name(name: str) -> bool:
    """An email or a single word — never a real dropdown name."""
    return "@" in name or len(name.split()) < 2


def _profiles_using(db: Any, name: str) -> list[PlayerProfile]:
    low = name.lower()
    return (
        db.query(PlayerProfile)
        .filter(
            PlayerProfile.is_active == 1,
            or_(func.lower(PlayerProfile.legacy_name) == low, func.lower(PlayerProfile.name) == low),
        )
        .order_by(PlayerProfile.id)
        .all()
    )


def compute_drift(db: Any, dropdown: list[str]) -> dict[str, Any]:
    roster = sorted(row[0] for row in db.query(LegacyRosterPlayer.name).all())
    roster_lower = {name.lower() for name in roster}
    dropdown_lower = {name.lower() for name in dropdown}
    extra = [name for name in roster if name.lower() not in dropdown_lower]
    return {
        "dropdown_count": len(dropdown),
        "roster_count": len(roster),
        "missing": sorted(name for name in dropdown if name.lower() not in roster_lower),
        "junk": [
            {"name": name, "used_by": [p.id for p in _profiles_using(db, name)]} for name in extra if is_junk_name(name)
        ],
        "not_on_dropdown": [name for name in extra if not is_junk_name(name)],
    }


def remove_roster_name(db: Any, name: str) -> dict[str, Any]:
    """Delete a roster entry unless an active profile still uses it."""
    row = db.query(LegacyRosterPlayer).filter(func.lower(LegacyRosterPlayer.name) == name.strip().lower()).first()
    if not row:
        return {"removed": False, "status": 404, "message": f"'{name}' is not on the roster"}
    users = _profiles_using(db, row.name)
    if users:
        ids = ", ".join(f"#{p.id}" for p in users)
        return {"removed": False, "status": 409, "message": f"'{row.name}' is used by profile {ids}. Relink it first."}
    db.delete(row)
    db.commit()
    return {"removed": True, "name": row.name}
