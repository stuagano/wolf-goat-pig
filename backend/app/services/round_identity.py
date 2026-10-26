"""Conservative associations between sheet summaries and saved scorecards.

Score suppression is deliberately separate: historical imports can be approximate,
whereas a link or per-hole detail must never be borrowed from a guessed game.
"""

from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .unified_data_service import UnifiedRound


def normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def course_name(value: str) -> str:
    value = normalized(value)
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
