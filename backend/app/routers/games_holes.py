"""Hole operations — quarters-only scoring, per-player corrections, logs, validation."""

import json
import logging
import traceback
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from .. import database, models
from ..utils.time import utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class HoleScore(BaseModel):
    hole_number: int
    quarters: dict[str, float]  # { player_id: quarters_won_or_lost }
    gross_scores: dict[str, int] | None = None
    notes: str | None = None
    teams: Any | None = None
    winner: str | None = None
    wager: float | None = None
    phase: str | None = None


class ScoresRequest(BaseModel):
    holes: list[HoleScore]
    current_hole: int = 18


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.delete("/{game_id}/holes/{hole_number}")
async def delete_hole(game_id: str, hole_number: int, db: Session = Depends(database.get_db)):  # type: ignore
    """
    Delete a hole's data. Removes from hole_events (source of truth) and from
    the game state hole_history blob. Recalculates standings from what remains.
    """
    game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    events = (
        db.query(models.HoleEvent)
        .filter(models.HoleEvent.game_id == game_id, models.HoleEvent.hole_number == hole_number)
        .all()
    )
    if not events:
        raise HTTPException(status_code=404, detail=f"Hole {hole_number} not found")

    for row in events:
        db.delete(row)

    # Keep hole_history blob in sync
    state = game.state or {}
    state["hole_history"] = [h for h in state.get("hole_history", []) if h.get("hole") != hole_number]

    # Recalculate standings from remaining hole_history
    standings: dict[str, float] = {}
    for entry in state["hole_history"]:
        for pid, q in entry.get("points_delta", {}).items():
            standings[pid] = standings.get(pid, 0) + q
    state["standings"] = standings
    for p in state.get("players", []):
        p["total_points"] = standings.get(p.get("id"), 0)

    flag_modified(game, "state")
    game.updated_at = utc_now().isoformat()
    db.commit()

    logger.info(f"Deleted hole {hole_number} from game {game_id}")
    return {"success": True, "game_id": game_id, "hole_number": hole_number}


@router.post("/{game_id}/scores")
async def save_scores(game_id: str, request: ScoresRequest, db: Session = Depends(database.get_db)):
    """Submit hole scores for a game. Each hole must sum to zero. Upserts — safe to call repeatedly."""
    try:
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Validate zero-sum per hole
        errors = [
            f"Hole {h.hole_number}: sum is {sum(h.quarters.values())}, must be 0"
            for h in request.holes
            if abs(sum(h.quarters.values())) > 0.001
        ]
        if errors:
            raise HTTPException(status_code=400, detail=f"Zero-sum validation failed: {'; '.join(errors)}")

        # Calculate standings
        standings: dict[str, float] = {}
        for h in request.holes:
            for player_id, quarters in h.quarters.items():
                standings[player_id] = standings.get(player_id, 0) + quarters

        # Persist to hole_events (upsert per player per hole)
        now_ts = utc_now().isoformat()
        for h in request.holes:
            for player_id, quarters in h.quarters.items():
                existing = (
                    db.query(models.HoleEvent)
                    .filter(
                        models.HoleEvent.game_id == game_id,
                        models.HoleEvent.hole_number == h.hole_number,
                        models.HoleEvent.player_id == player_id,
                    )
                    .first()
                )
                gross = (h.gross_scores or {}).get(player_id)
                if existing:
                    existing.quarters = quarters
                    if gross is not None:
                        existing.score = gross
                    existing.recorded_at = now_ts
                else:
                    db.add(
                        models.HoleEvent(
                            game_id=game_id,
                            hole_number=h.hole_number,
                            player_id=player_id,
                            score=gross,
                            quarters=quarters,
                            recorded_at=now_ts,
                        )
                    )

        # Keep game state blob in sync for client reads
        game_state = game.state or {}
        game_state["current_hole"] = request.current_hole
        game_state["standings"] = standings
        for player in game_state.get("players", []):
            player["total_points"] = standings.get(player.get("id"), 0)

        hole_history = [
            {
                "hole": h.hole_number,
                "points_delta": h.quarters,
                "gross_scores": h.gross_scores,
                "notes": h.notes,
                "teams": h.teams,
                "winner": h.winner,
                "wager": h.wager,
                "phase": h.phase,
            }
            for h in sorted(request.holes, key=lambda x: x.hole_number)
        ]
        game_state["hole_history"] = hole_history

        holes_with_data = len(request.holes)
        if holes_with_data >= 18:
            game_state["game_status"] = "completed"
            game.game_status = "completed"
        elif holes_with_data > 0:
            game_state["game_status"] = "in_progress"
            game.game_status = "in_progress"

        game.state = game_state
        # game_state is the SAME dict object as game.state (line above:
        # `game.state or {}`), so reassigning it does NOT mark the JSON column
        # dirty — SQLAlchemy can't see in-place mutations of a JSON blob. Without
        # this, hole_history/current_hole/standings never persist (only the
        # separate hole_events rows do), and /state reads back stale-empty state.
        flag_modified(game, "state")
        db.commit()

        logger.info(f"Saved quarters-only data for game {game_id}: {holes_with_data} holes")

        # Persist GameRecord + GamePlayerResult when game is complete
        results_created = 0
        if holes_with_data >= 18:
            try:
                existing_record = db.execute(
                    text("SELECT id FROM game_records WHERE game_id = :gid LIMIT 1"),
                    {"gid": game_id},
                ).first()

                if not existing_record:
                    now = utc_now().isoformat()
                    players = game_state.get("players", [])

                    # Create GameRecord
                    db.execute(
                        text("""
                            INSERT INTO game_records
                                (game_id, course_name, game_mode, player_count,
                                 total_holes_played, created_at, completed_at, final_scores)
                            VALUES
                                (:gid, :course, 'wolf_goat_pig', :pc, :holes, :cat, :comp,
                                 CAST(:scores AS json))
                        """),
                        {
                            "gid": game_id,
                            "course": game_state.get("course_name", "Wing Point"),
                            "pc": len(players),
                            "holes": holes_with_data,
                            "cat": game.created_at or now,
                            "comp": now,
                            "scores": json.dumps(standings),
                        },
                    )
                    record_row = db.execute(
                        text("SELECT id FROM game_records WHERE game_id = :gid"),
                        {"gid": game_id},
                    ).first()
                    record_id = record_row[0]

                    # Build per-player hole data from hole_history
                    player_hole_data = {}
                    for entry in hole_history:
                        pts = entry.get("points_delta", {})
                        gross = entry.get("gross_scores", {})
                        for pid, quarters in pts.items():
                            if pid not in player_hole_data:
                                player_hole_data[pid] = []
                            player_hole_data[pid].append(
                                {
                                    "hole": entry.get("hole"),
                                    "quarters": quarters,
                                    "gross_score": gross.get(pid) if gross else None,
                                    "teams": entry.get("teams"),
                                    "wager": entry.get("wager"),
                                    "phase": entry.get("phase"),
                                }
                            )

                    sorted_players = sorted(
                        players,
                        key=lambda p: standings.get(p.get("id"), 0),
                        reverse=True,
                    )

                    for rank, player in enumerate(sorted_players, 1):
                        pid = player.get("id")
                        holes_data = player_hole_data.get(pid, [])
                        total_earn = standings.get(pid, 0)
                        holes_won = sum(1 for h in holes_data if h.get("quarters", 0) > 0)
                        perf = json.dumps(
                            {
                                "handicap": player.get("handicap"),
                                "holes_played": len(holes_data),
                                "avg_quarters_per_hole": round(total_earn / max(len(holes_data), 1), 2),
                            }
                        )
                        db.execute(
                            text("""
                                INSERT INTO game_player_results
                                    (game_record_id, player_profile_id, player_name,
                                     final_position, total_earnings, holes_won,
                                     hole_scores, performance_metrics, created_at)
                                VALUES
                                    (:rid, :pid, :pname, :pos, :earn, :hw,
                                     CAST(:hs AS json), CAST(:pm AS json), :cat)
                            """),
                            {
                                "rid": record_id,
                                "pid": player.get("player_profile_id"),
                                "pname": player.get("name", "Unknown"),
                                "pos": rank,
                                "earn": total_earn,
                                "hw": holes_won,
                                "hs": json.dumps(holes_data),
                                "pm": perf,
                                "cat": now,
                            },
                        )
                        results_created += 1

                    db.commit()
                    logger.info("Game %s: persisted %d player results", game_id, results_created)

            except Exception as e:
                logger.error("Failed to persist game results for %s: %s", game_id, e)
                # Don't fail the whole request — quarters are already saved

        return {
            "success": True,
            "game_id": game_id,
            "holes_saved": holes_with_data,
            "standings": standings,
            "game_status": game.game_status,
            "results_created": results_created,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving quarters-only data for game {game_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error saving data: {e!s}")


# ---------------------------------------------------------------------------
# Per-player hole event correction and validation
# ---------------------------------------------------------------------------


class HoleEventPatch(BaseModel):
    score: int | None = None  # gross score — omit to leave unchanged
    quarters: float | None = None  # quarters won/lost — omit to leave unchanged


@router.patch("/{game_id}/holes/{hole_number}/players/{player_id}")
async def patch_hole_event(
    game_id: str,
    hole_number: int,
    player_id: str,
    patch: HoleEventPatch,
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """Independently correct a player's score or quarters for a single hole."""
    if patch.score is None and patch.quarters is None:
        raise HTTPException(status_code=400, detail="Provide at least one of: score, quarters")

    existing = (
        db.query(models.HoleEvent)
        .filter(
            models.HoleEvent.game_id == game_id,
            models.HoleEvent.hole_number == hole_number,
            models.HoleEvent.player_id == player_id,
        )
        .first()
    )

    now_ts = utc_now().isoformat()
    if existing:
        if patch.score is not None:
            existing.score = patch.score
        if patch.quarters is not None:
            existing.quarters = patch.quarters
        existing.recorded_at = now_ts
    else:
        db.add(
            models.HoleEvent(
                game_id=game_id,
                hole_number=hole_number,
                player_id=player_id,
                score=patch.score,
                quarters=patch.quarters if patch.quarters is not None else 0.0,
                recorded_at=now_ts,
            )
        )

    db.commit()

    return {
        "game_id": game_id,
        "hole_number": hole_number,
        "player_id": player_id,
        "score": patch.score if patch.score is not None else (existing.score if existing else None),
        "quarters": patch.quarters if patch.quarters is not None else (existing.quarters if existing else 0.0),
    }


@router.get("/{game_id}/holes/validate")
async def validate_hole_quarters(
    game_id: str,
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """Check the zero-sum invariant across all recorded holes.

    Returns a list of holes where SUM(quarters) != 0, so the caller knows
    which holes need correction before finalizing the game.
    """
    events = (
        db.query(models.HoleEvent)
        .filter(models.HoleEvent.game_id == game_id)
        .order_by(models.HoleEvent.hole_number, models.HoleEvent.player_id)
        .all()
    )

    from collections import defaultdict

    by_hole: dict[int, list] = defaultdict(list)
    for e in events:
        by_hole[e.hole_number].append(e)

    errors = []
    for hole_number in sorted(by_hole.keys()):
        total = sum(e.quarters for e in by_hole[hole_number])
        if abs(total) > 0.001:
            errors.append(
                {
                    "hole": hole_number,
                    "sum": round(total, 4),
                    "players": {e.player_id: e.quarters for e in by_hole[hole_number]},
                }
            )

    return {
        "valid": len(errors) == 0,
        "holes_checked": len(by_hole),
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Hole log — narrative record of a hole's betting arc and play
# ---------------------------------------------------------------------------


class HoleLogRequest(BaseModel):
    log_data: dict[str, Any]


@router.put("/{game_id}/holes/{hole_number}/log")
async def put_hole_log(
    game_id: str,
    hole_number: int,
    body: HoleLogRequest,
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """Create or replace the narrative log for a single hole."""
    log = body.log_data
    now_ts = utc_now().isoformat()

    existing = (
        db.query(models.HoleLog)
        .filter(models.HoleLog.game_id == game_id, models.HoleLog.hole_number == hole_number)
        .first()
    )
    if existing:
        existing.log_data = log
        existing.recorded_at = now_ts
    else:
        db.add(
            models.HoleLog(
                game_id=game_id,
                hole_number=hole_number,
                log_data=log,
                recorded_at=now_ts,
            )
        )
    db.commit()

    return {"game_id": game_id, "hole_number": hole_number, "recorded_at": now_ts}


@router.get("/{game_id}/holes/{hole_number}/log")
async def get_hole_log(
    game_id: str,
    hole_number: int,
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """Retrieve the narrative log for a single hole."""
    entry = (
        db.query(models.HoleLog)
        .filter(models.HoleLog.game_id == game_id, models.HoleLog.hole_number == hole_number)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail=f"No log for hole {hole_number}")
    return entry.log_data


@router.get("/{game_id}/log")
async def get_game_log(
    game_id: str,
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """Retrieve all hole logs for a game, ordered by hole number."""
    entries = (
        db.query(models.HoleLog).filter(models.HoleLog.game_id == game_id).order_by(models.HoleLog.hole_number).all()
    )
    return {
        "game_id": game_id,
        "holes_logged": len(entries),
        "log": [e.log_data for e in entries],
    }
