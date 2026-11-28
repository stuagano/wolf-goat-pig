"""How a signup names a player when the old tee-sheet roster is incomplete.

Existing members keep their ``legacy_name`` so history and the live sheet stay
aligned. New members have no row on that roster; their profile name is enough
to sign up, pair, and settle inside this app.
"""


def roster_link(legacy_name: str | None) -> str | None:
    """Return a real tee-sheet name.

    An email stored in ``legacy_name`` is a signup placeholder, not a roster link.
    """
    name = (legacy_name or "").strip()
    if not name or "@" in name:
        return None
    return name


def signup_display_name(player: object) -> str | None:
    """Name written on a signup: roster link when present, otherwise profile name."""
    linked = roster_link(getattr(player, "legacy_name", None))
    if linked:
        return linked
    name = (getattr(player, "name", None) or "").strip()
    return name or None
