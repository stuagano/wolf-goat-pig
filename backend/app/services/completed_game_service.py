"""Build + persist a completed Wolf Goat Pig game.

Shared by the live game-completion endpoint and the scorecard-scan
"record a finished round" endpoint so both produce identical
GameRecord / GamePlayerResult rows.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

REQUIRED_HOLES = frozenset(range(1, 19))


def round_played_at(record: Any, game: Any = None) -> str | None:
    """Keep round dates separate from completion audit timestamps."""
    settings = record.game_settings
    if isinstance(settings, dict) and settings.get("played_at"):
        return settings["played_at"]
    # Older scorecard posts stored the played date only in created_at.
    if game is not None and (game.state or {}).get("source") == "scorecard_scan":
        return game.created_at
    return record.completed_at or record.created_at


def validate_round_players(players: list[dict]) -> None:
    """Reject repeated identities and names that cannot distinguish guests."""
    slots: set[str] = set()
    profiles: set[int] = set()
    names: dict[str, int | None] = {}
    for player in players:
        slot = player.get("id")
        profile = player.get("player_profile_id")
        name = " ".join((player.get("name") or "").casefold().split())
        if not slot or slot in slots or not name:
            raise HTTPException(status_code=400, detail="Round requires distinct players with nonblank names")
        if profile is not None and profile in profiles:
            raise HTTPException(status_code=400, detail="Round contains a duplicate player profile")
        if name in names and (profile is None or names[name] is None):
            raise HTTPException(status_code=400, detail="Duplicate player names require distinct player profiles")
        slots.add(slot)
        if profile is not None:
            profiles.add(profile)
        names[name] = profile


def validate_round_scores(players: list[dict], hole_history: list[dict], *, complete: bool = True) -> None:
    """Require explicit quarters for the roster; missing scores are not zeroes."""
    player_ids = {p.get("id") for p in players}
    if not player_ids or None in player_ids or len(player_ids) != len(players):
        raise HTTPException(status_code=400, detail="Round requires a valid player roster")
    holes = {entry.get("hole") for entry in hole_history}
    if not holes.issubset(REQUIRED_HOLES) or (complete and holes != REQUIRED_HOLES):
        raise HTTPException(status_code=400, detail="Completion requires all holes 1-18")
    for entry in hole_history:
        quarters = entry.get("points_delta") or {}
        if set(quarters) != player_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Hole {entry.get('hole')}: scores must include every roster player and no unknown players",
            )
        if any(not isinstance(q, (int, float)) or not math.isfinite(q) for q in quarters.values()):
            raise HTTPException(status_code=400, detail="Quarter scores must be finite numbers")


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
    hole_history, hole_quarters and standings. Matches linked players by profile
    and guests by name when correcting results. Returns the number created.
    """
    from app import models  # local import: router imports this module
    from app.utils.time import utc_now  # match existing helper used in games.py

    state = game.state or {}
    players = state.get("players", [])
    validate_round_players(players)
    hole_history = state.get("hole_history", [])
    hole_quarters = state.get("hole_quarters", {})

    standings = state.get("standings", {})
    if not standings and hole_history:
        for entry in hole_history:
            for pid, q in entry.get("points_delta", {}).items():
                standings[pid] = standings.get(pid, 0) + q

    now = utc_now().isoformat()

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
    record.final_scores = standings
    record.total_holes_played = len(hole_history)
    if state.get("source") == "scorecard_scan":
        record.game_settings = {
            **(record.game_settings or {}),
            "played_at": state.get("played_at") or game.created_at,
        }
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

        result_query = db.query(models.GamePlayerResult).filter_by(
            game_record_id=record_id, player_profile_id=player.get("player_profile_id")
        )
        if player.get("player_profile_id") is None:
            result_query = result_query.filter_by(player_name=player_name)
        result = result_query.one_or_none()
        if result is None:
            result = models.GamePlayerResult(game_record_id=record_id, player_name=player_name, created_at=now)
            db.add(result)
            results_created += 1
        result.player_profile_id = player.get("player_profile_id")
        result.player_name = player_name
        result.final_position = rank
        result.total_earnings = total_earnings
        result.holes_won = holes_won
        result.hole_scores = holes_data
        result.performance_metrics = {
            "handicap": player.get("handicap"),
            "holes_played": len(holes_data),
            "avg_quarters_per_hole": round(total_earnings / max(len(holes_data), 1), 2),
        }
        db.flush()

    # Read the id BEFORE commit: with expire_on_commit=True, touching any
    # attribute afterwards re-queries, so a post-commit read failure would turn
    # an already-durable save into a 500.
    game_id = game.game_id
    db.commit()
    logger.info("Persisted completed game %s: %d results", game_id, results_created)
    return results_created
