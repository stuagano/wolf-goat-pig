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

    hole_history = [{"hole": h, "points_delta": holes[h]} for h in sorted(holes)]

    standings: dict[str, float] = {}
    for entry in hole_history:
        for pid, q in entry["points_delta"].items():
            standings[pid] = standings.get(pid, 0) + q
    return hole_history, standings


def persist_completed_game(db: Session, game: Any) -> int:
    """Write GameRecord + GamePlayerResult rows for a completed game.

    `game` is a GameStateModel whose `state` already contains players,
    hole_history, hole_quarters and standings. Idempotent on
    (game_record_id, player_name). Returns the number of results created.
    """
    from app import models  # local import: router imports this module
    from app.utils.time import utc_now  # match existing helper used in games.py

    state = game.state or {}
    players = state.get("players", [])
    hole_history = state.get("hole_history", [])
    hole_quarters = state.get("hole_quarters", {})

    standings = state.get("standings", {})
    if not standings and hole_history:
        for entry in hole_history:
            for pid, q in entry.get("points_delta", {}).items():
                standings[pid] = standings.get(pid, 0) + q

    now = utc_now().isoformat()
    is_pg = db.bind.dialect.name == "postgresql"
    hs_expr = "CAST(:hs AS jsonb)" if is_pg else ":hs"
    pm_expr = "CAST(:pm AS jsonb)" if is_pg else ":pm"

    record = db.query(models.GameRecord).filter(models.GameRecord.game_id == game.game_id).first()
    if not record:
        record = models.GameRecord(
            game_id=game.game_id,
            course_name=state.get("course_name", "Wing Point"),
            game_mode="wolf_goat_pig",
            player_count=len(players),
            total_holes_played=len(hole_quarters) or len(hole_history),
            created_at=game.created_at or now,
            completed_at=now,
            final_scores=standings,
        )
        db.add(record)
        db.flush()
    record_id = record.id

    player_hole_data: dict[str, list] = {}
    for entry in hole_history:
        for pid, quarters in entry.get("points_delta", {}).items():
            player_hole_data.setdefault(pid, []).append(
                {
                    "hole": entry.get("hole"),
                    "quarters": quarters,
                    "gross_score": (entry.get("gross_scores") or {}).get(pid),
                    "teams": entry.get("teams"),
                    "wager": entry.get("wager"),
                    "phase": entry.get("phase"),
                }
            )

    sorted_players = sorted(players, key=lambda p: standings.get(p.get("id"), 0), reverse=True)
    results_created = 0
    for rank, player in enumerate(sorted_players, 1):
        pid = player.get("id")
        player_name = player.get("name", "Unknown")
        total_earnings = standings.get(pid, 0)
        holes_data = player_hole_data.get(pid, [])
        holes_won = sum(1 for h in holes_data if h.get("quarters", 0) > 0)

        exists = db.execute(
            text("SELECT 1 FROM game_player_results WHERE game_record_id = :rid AND player_name = :pn LIMIT 1"),
            {"rid": record_id, "pn": player_name},
        ).first()
        if exists:
            continue

        perf = json.dumps(
            {
                "handicap": player.get("handicap"),
                "holes_played": len(holes_data),
                "avg_quarters_per_hole": round(total_earnings / max(len(holes_data), 1), 2),
            }
        )
        db.execute(
            text(f"""
                INSERT INTO game_player_results
                    (game_record_id, player_profile_id, player_name,
                     final_position, total_earnings, holes_won,
                     hole_scores, performance_metrics, created_at)
                VALUES
                    (:rid, :pid, :pname, :pos, :earn, :hw,
                     {hs_expr}, {pm_expr}, :cat)
            """),
            {
                "rid": record_id,
                "pid": player.get("player_profile_id"),
                "pname": player_name,
                "pos": rank,
                "earn": total_earnings,
                "hw": holes_won,
                "hs": json.dumps(holes_data),
                "pm": perf,
                "cat": now,
            },
        )
        results_created += 1

    db.commit()
    logger.info("Persisted completed game %s: %d results", game.game_id, results_created)
    return results_created
