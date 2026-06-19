"""Build + persist a completed Wolf Goat Pig game.

Shared by the live game-completion endpoint and the scorecard-scan
"record a finished round" endpoint so both produce identical
GameRecord / GamePlayerResult rows.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def build_hole_history(
    players: list[dict[str, Any]],
    per_hole_quarters: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    """Convert per-(index, hole) quarter deltas into hole_history + standings.

    player_index refers to the position of the player in `players`.
    """
    id_by_index = {i: p["id"] for i, p in enumerate(players)}
    holes: dict[int, dict[str, float]] = {}
    for entry in per_hole_quarters:
        pid = id_by_index.get(entry["player_index"])
        if pid is None:
            continue
        holes.setdefault(entry["hole"], {})[pid] = entry["quarters"]

    hole_history = [
        {"hole": h, "points_delta": holes[h]} for h in sorted(holes)
    ]

    standings: dict[str, float] = {}
    for entry in hole_history:
        for pid, q in entry["points_delta"].items():
            standings[pid] = standings.get(pid, 0) + q
    return hole_history, standings
