"""Exact, case-insensitive links from a sheet name to a player profile.

legacy_name wins over the display name. An ambiguous name (two profiles
sharing it) stays unlinked rather than pointing at the wrong person.
"""

from sqlalchemy.orm import Session

from ..models import PlayerProfile


def profile_ids_by_member(db: Session) -> dict[str, int]:
    rows = db.query(PlayerProfile.id, PlayerProfile.name, PlayerProfile.legacy_name).all()
    by_name: dict[str, int | None] = {}
    claimed_by_legacy: set[str] = set()

    def claim(raw: str | None, profile_id: int) -> None:
        key = (raw or "").strip().casefold()
        if not key:
            return
        current = by_name.get(key, profile_id)
        by_name[key] = profile_id if current == profile_id else None

    # A confirmed legacy link owns that sheet name, so the display name is not
    # also claimed by the same profile.
    for profile_id, _name, legacy_name in rows:
        if (legacy_name or "").strip():
            claim(legacy_name, profile_id)
            claimed_by_legacy.add(profile_id)
    for profile_id, name, _legacy_name in rows:
        if profile_id not in claimed_by_legacy:
            claim(name, profile_id)

    return {key: profile_id for key, profile_id in by_name.items() if profile_id is not None}


def profile_id_for_member(member: str | None, index: dict[str, int]) -> int | None:
    return index.get((member or "").strip().casefold())
