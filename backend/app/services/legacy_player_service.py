"""Service for managing and validating players against the legacy tee sheet system.

The legacy system at thousand-cranes.com/WolfGoatPig only accepts signups for
players that exist in its dropdown list. This service is the app-side mirror of
that canonical roster, plus a capture queue for golfers who sign up in the app
before they exist on the legacy dropdown.

Two stores, one invariant:

1. ``legacy_roster`` (canonical) — the names that are valid on the legacy
   dropdown. ALL canonical reads come from here: the onboarding dropdown,
   fuzzy matching, and validation. Seeded from ``data/legacy_players.json``.
2. ``pending_legacy_players`` (capture queue) — self-signed-up golfers with no
   canonical match yet. Kept structurally separate so a pending name can NEVER
   validate as canonical (which would let their signups silently fail at the
   legacy CGI). An admin promotes a pending row into the canonical roster once
   the player has been added to Jeff's dropdown.

The canonical reads fall back to the JSON seed file only when the roster table
is empty (e.g. a fresh dev DB before the startup seed runs), so behaviour is
stable everywhere.
"""

from __future__ import annotations

import json
import logging
from difflib import get_close_matches
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from ..database import SessionLocal
from ..models import LegacyRosterPlayer, PendingLegacyPlayer
from ..utils.time import utc_now

logger = logging.getLogger(__name__)

# Path to the static seed list (mirrors the legacy dropdown at first deploy).
_PLAYERS_FILE = Path(__file__).parent.parent / "data" / "legacy_players.json"


def _seed_names() -> list[str]:
    """Read the static seed player list from the JSON file."""
    try:
        with open(_PLAYERS_FILE) as f:
            data = json.load(f)
            return list(data.get("players", []))
    except FileNotFoundError:
        logger.warning(f"Legacy players seed file not found: {_PLAYERS_FILE}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in legacy players seed file: {e}")
        return []


def seed_roster_if_empty(db: Any) -> int:
    """Populate ``legacy_roster`` from the JSON seed when the table is empty.

    Idempotent: a no-op once the table has any rows. Returns the number of
    names inserted.
    """
    existing = db.query(LegacyRosterPlayer).count()
    if existing:
        return 0

    names = _seed_names()
    now = utc_now().isoformat()
    for name in names:
        db.add(LegacyRosterPlayer(name=name, source="seed", added_at=now))
    db.commit()
    logger.info(f"Seeded {len(names)} canonical players into legacy_roster")
    return len(names)


def _canonical_names(db: Any = None) -> list[str]:
    """Return canonical player names from the roster table.

    Falls back to the JSON seed (read-only) when the table is empty so reads
    are stable before the startup seed has run.
    """
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        names = [row[0] for row in db.query(LegacyRosterPlayer.name).all()]
        if not names:
            return _seed_names()
        return names
    except SQLAlchemyError as exc:
        # Roster table missing/unavailable (e.g. pre-migration) — degrade to the
        # static seed rather than 500 the login/onboarding read path.
        logger.warning(f"Legacy roster read failed, falling back to JSON seed: {exc}")
        if own_session:
            db.rollback()
        return _seed_names()
    finally:
        if own_session:
            db.close()


def get_legacy_players(db: Any = None) -> list[str]:
    """Return the sorted list of all canonical legacy players."""
    return sorted(_canonical_names(db))


def is_valid_legacy_player(name: str, db: Any = None) -> bool:
    """Check if a player name exists in the canonical roster (case-insensitive)."""
    lowered = name.lower()
    return any(p.lower() == lowered for p in _canonical_names(db))


def get_canonical_name(name: str, db: Any = None) -> str | None:
    """Get the canonical (correctly cased) name for a player, or None."""
    lowered = name.lower()
    for p in _canonical_names(db):
        if p.lower() == lowered:
            return p
    return None


def find_similar_players(name: str, max_results: int = 5, db: Any = None) -> list[str]:
    """Find canonical players with names similar to the given name."""
    players = _canonical_names(db)
    if not players:
        return []

    lower_to_original = {p.lower(): p for p in players}
    matches = get_close_matches(name.lower(), list(lower_to_original.keys()), n=max_results, cutoff=0.6)
    return [lower_to_original[m] for m in matches]


def validate_player_for_legacy(name: str, db: Any = None) -> dict:
    """Validate a player name for legacy system compatibility.

    Returns a dict with:
    - valid: bool - whether the name is canonical (will sync to the legacy sheet)
    - canonical_name: str or None - the correctly-cased name if valid
    - suggestions: list - similar names if not valid
    - message: str - human-readable explanation
    """
    canonical = get_canonical_name(name, db)

    if canonical:
        return {
            "valid": True,
            "canonical_name": canonical,
            "suggestions": [],
            "message": f"Player '{canonical}' found in legacy system",
        }

    suggestions = find_similar_players(name, db=db)

    if suggestions:
        return {
            "valid": False,
            "canonical_name": None,
            "suggestions": suggestions,
            "message": f"Player '{name}' not found. Did you mean: {', '.join(suggestions)}?",
        }

    return {
        "valid": False,
        "canonical_name": None,
        "suggestions": [],
        "message": f"Player '{name}' not found in legacy system",
    }


# ---------------------------------------------------------------------------
# Canonical roster writes
# ---------------------------------------------------------------------------
def add_legacy_player(name: str, *, source: str = "admin", db: Any = None) -> dict:
    """Add a name to the canonical roster.

    Use this once the player is known to exist on the legacy dropdown.
    Idempotent: returns ``added=False`` if the name is already canonical.
    """
    name = (name or "").strip()
    if not name:
        return {"added": False, "message": "Empty name"}

    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        existing = get_canonical_name(name, db)
        if existing:
            return {"added": False, "canonical_name": existing, "message": f"'{existing}' already in roster"}

        db.add(LegacyRosterPlayer(name=name, source=source, added_at=utc_now().isoformat()))
        db.commit()
        logger.info(f"Added canonical legacy player '{name}' (source={source})")
        return {"added": True, "canonical_name": name, "message": f"Added '{name}' to roster"}
    finally:
        if own_session:
            db.close()


# ---------------------------------------------------------------------------
# Pending capture queue
# ---------------------------------------------------------------------------
def capture_pending_player(
    name: str,
    *,
    email: str | None = None,
    player_profile_id: int | None = None,
    db: Any = None,
) -> dict:
    """Capture a self-signed-up golfer who has no canonical match yet.

    No-op when the name is already canonical or already queued. Returns a dict
    describing what happened (``captured`` flag + reason).
    """
    name = (name or "").strip()
    if not name or name == "Unknown Player":
        return {"captured": False, "reason": "blank_or_unknown"}

    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        if get_canonical_name(name, db):
            return {"captured": False, "reason": "already_canonical"}

        already = (
            db.query(PendingLegacyPlayer)
            .filter(PendingLegacyPlayer.name == name, PendingLegacyPlayer.status == "pending")
            .first()
        )
        if already:
            return {"captured": False, "reason": "already_pending", "pending_id": already.id}

        row = PendingLegacyPlayer(
            name=name,
            email=email,
            player_profile_id=player_profile_id,
            status="pending",
            created_at=utc_now().isoformat(),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        logger.info(f"Captured pending legacy player '{name}' (id={row.id})")
        return {"captured": True, "pending_id": row.id, "name": name}
    finally:
        if own_session:
            db.close()


def list_pending_players(status: str = "pending", db: Any = None) -> list[dict]:
    """List capture-queue rows for the given status (default: pending)."""
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        rows = (
            db.query(PendingLegacyPlayer)
            .filter(PendingLegacyPlayer.status == status)
            .order_by(PendingLegacyPlayer.created_at.desc())
            .all()
        )
        return [
            {
                "id": r.id,
                "name": r.name,
                "email": r.email,
                "player_profile_id": r.player_profile_id,
                "status": r.status,
                "created_at": r.created_at,
                "resolved_at": r.resolved_at,
            }
            for r in rows
        ]
    finally:
        if own_session:
            db.close()


def promote_pending_player(pending_id: int, db: Any = None) -> dict:
    """Promote a pending capture into the canonical roster.

    Call this once the player has been added to Jeff's legacy dropdown.
    """
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        row = db.query(PendingLegacyPlayer).filter(PendingLegacyPlayer.id == pending_id).first()
        if not row:
            return {"promoted": False, "message": f"No pending player with id={pending_id}"}
        if row.status != "pending":
            return {"promoted": False, "message": f"Pending player id={pending_id} is already {row.status}"}

        add_legacy_player(row.name, source="promoted", db=db)
        row.status = "promoted"
        row.resolved_at = utc_now().isoformat()
        db.commit()
        logger.info(f"Promoted pending player '{row.name}' (id={pending_id}) to canonical roster")
        return {"promoted": True, "canonical_name": row.name}
    finally:
        if own_session:
            db.close()


def dismiss_pending_player(pending_id: int, db: Any = None) -> dict:
    """Dismiss a pending capture (e.g. a misspelling of an existing player)."""
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        row = db.query(PendingLegacyPlayer).filter(PendingLegacyPlayer.id == pending_id).first()
        if not row:
            return {"dismissed": False, "message": f"No pending player with id={pending_id}"}

        row.status = "dismissed"
        row.resolved_at = utc_now().isoformat()
        db.commit()
        logger.info(f"Dismissed pending player '{row.name}' (id={pending_id})")
        return {"dismissed": True, "name": row.name}
    finally:
        if own_session:
            db.close()


def _looks_like_dropdown_name(name: str) -> bool:
    """Heuristic: does this look like a canonical 'First Last' dropdown name?

    The legacy CGI dropdown uses full first-and-last names. We refuse to inject
    round-history member strings that diverge from that shape ("Last, First",
    "Mike S.") as canonical, because a name the dropdown does not actually have
    would let that player's sign-ups silently fail at the CGI. Format-divergent
    members fall through to the pending-capture queue instead (safe).
    """
    if "," in name:
        return False
    tokens = name.split()
    if len(tokens) < 2:
        return False
    # Reject a trailing single-letter initial like "Mike S" / "Mike S.".
    return len(tokens[-1].rstrip(".")) >= 2


def sync_roster_from_members(names: Any, db: Any = None) -> dict:
    """Additively reconcile the canonical roster with names seen in round history.

    Round history is synced from the Google Sheet every 2h; the distinct member
    names are players who have signed up and played, i.e. real dropdown members.
    This adds any new dropdown-shaped name to the canonical roster and resolves
    any matching pending capture. It is an *additive reconcile*, not a full
    mirror: names are never removed (a player dropped from the sheet but still
    linked to a profile must persist). Returns a summary dict.
    """
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        added: list[str] = []
        skipped_format: list[str] = []
        resolved: list[str] = []
        seen_lower: set[str] = set()
        confirmed_lower: set[str] = set()

        for raw in names:
            name = (raw or "").strip()
            if not name or name == "Unknown Player":
                continue
            low = name.lower()
            if low in seen_lower:
                continue
            seen_lower.add(low)

            existing = get_canonical_name(name, db)
            if existing:
                confirmed_lower.add(existing.lower())
                continue
            if not _looks_like_dropdown_name(name):
                skipped_format.append(name)
                continue

            db.add(LegacyRosterPlayer(name=name, source="sheet_sync", added_at=utc_now().isoformat()))
            added.append(name)
            confirmed_lower.add(low)

        # Resolve pending captures whose name is now confirmed canonical.
        pending = db.query(PendingLegacyPlayer).filter(PendingLegacyPlayer.status == "pending").all()
        for p in pending:
            if (p.name or "").strip().lower() in confirmed_lower:
                p.status = "promoted"
                p.resolved_at = utc_now().isoformat()
                resolved.append(p.name)

        db.commit()
        if added or resolved or skipped_format:
            logger.info(
                "Roster sync from rounds: +%d canonical, %d pending resolved, %d skipped (format divergence)",
                len(added),
                len(resolved),
                len(skipped_format),
            )
        return {"added": added, "resolved": resolved, "skipped_format": skipped_format}
    except SQLAlchemyError as exc:
        logger.warning(f"Roster sync from rounds failed: {exc}")
        db.rollback()
        return {"added": [], "resolved": [], "skipped_format": [], "error": str(exc)}
    finally:
        if own_session:
            db.close()


def reload_players() -> int:
    """Return the current canonical roster size (kept for API compatibility)."""
    return len(get_legacy_players())
