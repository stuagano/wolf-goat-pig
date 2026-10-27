"""Persisted source identity and globally serialized candidate discovery.

Legacy summary helpers below remain pre-cutover compatibility only. They are
never evidence for canonical binding and are retired with the legacy readers.
"""

import re
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .unified_data_service import UnifiedRound

_CLUB_SUFFIX = re.compile(r"(\s+(golf|country|club|course|&|and|g&cc|gcc|gc|cc))+$")


def acquire_reconciliation_lock(db) -> None:
    """One application transaction lock, before fresh candidate reads.

    SQLite test fixtures serialize transactions themselves; this is not a
    substitute for PostgreSQL concurrency verification.
    """
    from sqlalchemy import text

    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": 870284190311})


def resolve_round_alias(db, date_key: str, group: str, location: str) -> list[str]:
    from app.models import RoundAlias

    return sorted(
        {r.game_id for r in db.query(RoundAlias).filter_by(date_key=date_key, group=group, location=location).all()}
    )


def candidate_games(db, draft) -> list[str]:
    """Conservative identity candidates, never score matching or auto-binding."""
    from app import models

    candidates = set()
    for record in db.query(models.GameRecord).populate_existing().all():
        if draft.played_on and record.played_on and draft.played_on != record.played_on:
            continue
        if (
            draft.course_name
            and record.course_name
            and course_name(draft.course_name) != course_name(record.course_name)
        ):
            continue
        candidates.add(record.game_id)
    # Include live containers and orphan UUIDs lacking a record. Unknown dates
    # cannot evade coordination, and no total signature grants identity.
    for game in db.query(models.GameStateModel).populate_existing().all():
        if db.query(models.GameRecord).filter_by(game_id=game.game_id).first() is None:
            candidates.add(game.game_id)
    return sorted(candidates)


def retain_alias(db, game_id, draft):
    from app.models import RoundAlias

    for key in {draft.raw_date, draft.played_on.isoformat() if draft.played_on else None} - {None}:
        values = {"date_key": key, "group": draft.group or "", "location": draft.course_name or "", "game_id": game_id}
        if db.query(RoundAlias).filter_by(**values).first() is None:
            db.add(RoundAlias(**values, evidence={"kind": "accepted_projection"}))
    db.flush()


def normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def course_name(value: str) -> str:
    # The sheet says "Wing Point"; saved games say "Wing Point Golf & Country Club".
    value = _CLUB_SUFFIX.sub("", normalized(value))
    return "" if value in {"", "unknown", "n/a"} else value


def round_day(rows: list["UnifiedRound"]) -> date | None:
    try:
        return date.fromisoformat(rows[0].date_sortable)
    except ValueError:
        return None


def group_rounds(rows: list["UnifiedRound"]) -> list[list["UnifiedRound"]]:
    groups: dict[tuple, list[UnifiedRound]] = {}
    for row in rows:
        groups.setdefault(row.game_key or (row.source, id(row)), []).append(row)
    return list(groups.values())


def _signature(rows: list["UnifiedRound"]) -> tuple | None:
    day = round_day(rows)
    course = course_name(rows[0].location)
    players = [(normalized(row.member), row.score) for row in rows]
    # Repeated names cannot establish individual hole ownership. Missing names,
    # dates, courses and mixed game metadata cannot establish identity either.
    if (
        not day
        or not course
        or any(not name for name, _ in players)
        or len({name for name, _ in players}) != len(players)
        or any(row.date_sortable != rows[0].date_sortable or course_name(row.location) != course for row in rows)
    ):
        return None
    return day, course, tuple(sorted(players))


def link_saved_cards(sheet_games: list[list["UnifiedRound"]], other_games: list[list["UnifiedRound"]]) -> None:
    """Copy identity only for a mutual one-to-one whole-game match.

    Count even orphan app records without reachable state, so a missing UUID
    cannot make an ambiguous match appear unique. App group A is a placeholder,
    not evidence; sheet groups remain distinct candidates.
    """
    sheets: dict[tuple, list[list[UnifiedRound]]] = {}
    apps: dict[tuple, list[list[UnifiedRound]]] = {}
    for groups, index in ((sheet_games, sheets), (other_games, apps)):
        for rows in groups:
            if index is apps and rows[0].source != "database":
                continue
            signature = _signature(rows)
            if signature is not None:
                index.setdefault(signature, []).append(rows)
    for signature, candidates in sheets.items():
        matches = apps.get(signature, [])
        if len(candidates) != 1 or len(matches) != 1:
            continue
        sheet, app = candidates[0], matches[0]
        ids = {row.game_id for row in app}
        if len(ids) != 1 or None in ids:
            continue
        game_id = app[0].game_id
        holes = {normalized(row.member): row.hole_scores for row in app}
        for row in sheet:
            row.game_id = game_id
            if not row.hole_scores:
                row.hole_scores = holes[normalized(row.member)]
