"""Hole operations — quarters-only scoring, per-player corrections, logs, validation."""

import logging
import math
from copy import deepcopy
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from .. import database, models
from ..observability.score_save import log_score_commit
from ..services.completed_game_service import (
    REQUIRED_HOLES,
    merge_hole_history,
    persist_completed_game,
    validate_round_scores,
)
from ..services.round_writes import check_revision, propose_completed, writer_mode
from ..utils.round_card import require_round_member_or_admin
from ..utils.time import utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


# A standard round is complete only when every hole 1-18 has score data.


class HoleScore(BaseModel):
    hole_number: int
    quarters: dict[str, float]  # { player_id: quarters_won_or_lost }
    gross_scores: dict[str, int] | None = None
    notes: str | None = None
    teams: Any | None = None
    winner: str | None = None
    wager: float | None = None
    phase: str | None = None
    # Betting / special-action flags — without these a reload loses float-once
    # and Duncan/aardvark context the scorekeeper needs mid-round.
    float_invoked_by: str | None = None
    option_invoked_by: str | None = None
    duncan_invoked: bool | None = None
    joes_special_wager: int | float | None = None
    aardvark_requested_team: str | None = None
    aardvark_tossed: bool | None = None
    aardvark_solo: bool | None = None
    aardvark_ping_ponged: bool | None = None
    carry_over_applied: bool | None = None


class ScoresRequest(BaseModel):
    holes: list[HoleScore]
    current_hole: int = 18
    expected_revision: int | None = None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.delete("/{game_id}/holes/{hole_number}", dependencies=[Depends(require_round_member_or_admin)])
async def delete_hole(game_id: str, hole_number: int, db: Session = Depends(database.get_db)):  # type: ignore
    """
    Delete a hole's data. Removes from hole_events (source of truth) and from
    the game state hole_history blob. Recalculates standings from what remains.
    """
    game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.game_status == "completed":
        raise HTTPException(
            status_code=400, detail="Correct completed rounds through scores; a completed round cannot lose a hole"
        )

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


@router.post("/{game_id}/scores", dependencies=[Depends(require_round_member_or_admin)])
async def save_scores(game_id: str, request: ScoresRequest, db: Session = Depends(database.get_db)):
    """Replace the full scored-hole snapshot (not a one-hole patch)."""
    try:
        mode = writer_mode(db)
        game = (
            db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).populate_existing().first()
        )
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Replays are safe across requests, but competing entries within one
        # request are ambiguous and must be rejected rather than last-write-wins.
        holes = request.holes
        validate_round_scores(
            (game.state or {}).get("players", []),
            [{"hole": h.hole_number, "points_delta": h.quarters} for h in holes],
            complete=game.game_status == "completed",
        )

        # Validate zero-sum per hole
        errors = [
            f"Hole {h.hole_number}: sum is {sum(h.quarters.values())}, must be 0"
            for h in holes
            if abs(sum(h.quarters.values())) > 0.001
        ]
        if errors:
            raise HTTPException(status_code=400, detail=f"Zero-sum validation failed: {'; '.join(errors)}")

        check_revision(
            db, game, request.expected_revision, required=mode == "canonical" and game.game_status == "completed"
        )
        if mode == "canonical" and game.game_status == "completed":
            proposed_history = merge_hole_history(
                (game.state or {}).get("hole_history", []),
                [
                    {
                        "hole": h.hole_number,
                        "points_delta": h.quarters,
                        **h.model_dump(exclude={"hole_number", "quarters"}, exclude_none=True),
                    }
                    for h in holes
                ],
            )
            detail = propose_completed(db, game, proposed_history)
            db.commit()
            if detail["issue_ids"]:
                raise HTTPException(409, detail)
            return {
                "success": True,
                "game_id": game_id,
                "revision": detail["revision"],
                "status": "unchanged",
                "issue_ids": [],
                "game_status": "completed",
            }

        # Calculate standings
        standings: dict[str, float] = {}
        for h in holes:
            for player_id, quarters in h.quarters.items():
                standings[player_id] = standings.get(player_id, 0) + quarters

        # Persist to hole_events (upsert per player per hole)
        now_ts = utc_now().isoformat()
        for h in holes:
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
                "float_invoked_by": h.float_invoked_by,
                "option_invoked_by": h.option_invoked_by,
                "duncan_invoked": h.duncan_invoked,
                "joes_special_wager": h.joes_special_wager,
                "aardvark_requested_team": h.aardvark_requested_team,
                "aardvark_tossed": h.aardvark_tossed,
                "aardvark_solo": h.aardvark_solo,
                "aardvark_ping_ponged": h.aardvark_ping_ponged,
                "carry_over_applied": h.carry_over_applied,
            }
            for h in sorted(holes, key=lambda x: x.hole_number)
        ]
        submitted_holes = {h["hole"] for h in hole_history}
        hole_history = merge_hole_history(
            [h for h in game_state.get("hole_history", []) if h["hole"] in submitted_holes], hole_history
        )
        game_state["hole_history"] = hole_history

        holes_with_data = len(holes)
        # Gate completion on the DISTINCT set of holes 1-18 actually played, not
        # the raw entry count. Counting raw entries let 18 rows that skip a real
        # hole (or duplicate one) trip completion before hole 18 was played.
        distinct_holes = {h.hole_number for h in holes}
        game_complete = REQUIRED_HOLES.issubset(distinct_holes)
        if game_complete:
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
        # Snapshot the response value BEFORE commit. With expire_on_commit=True
        # a post-commit attribute read re-queries the row, so a dropped
        # connection there raised 500 for a save that had already landed —
        # the client then retried or showed "save failed" over durable data.
        saved_status = game.game_status
        results_created = 0
        if game_complete:
            results_created = persist_completed_game(db, game)
            standings = dict(game.state["standings"])
        if "hole_quarters" in game.state:
            game.state["hole_quarters"] = {str(h["hole"]): dict(h["points_delta"]) for h in game.state["hole_history"]}
        if not game_complete:
            game.revision = (game.revision or 0) + 1
        revision = game.revision
        db.commit()
        # Only now is the write provable.
        log_score_commit()

        return {
            "success": True,
            "game_id": game_id,
            "holes_saved": holes_with_data,
            "standings": standings,
            "game_status": saved_status,
            "results_created": results_created,
            "revision": revision,
            "status": "accepted",
            "issue_ids": [],
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        # Log the failure class and location, never the message: SQLAlchemy
        # errors embed the bound score values, and the message previously went
        # to the client as well.
        logger.error("Score save failed for game %s: %s", game_id, type(e).__name__)
        raise HTTPException(status_code=500, detail="Unable to save scores. Please retry.") from None


# ---------------------------------------------------------------------------
# Per-player hole event correction and validation
# ---------------------------------------------------------------------------


class HoleEventPatch(BaseModel):
    score: int | None = None  # gross score — omit to leave unchanged
    quarters: float | None = None  # quarters won/lost — omit to leave unchanged
    expected_revision: int | None = None


@router.patch(
    "/{game_id}/holes/{hole_number}/players/{player_id}", dependencies=[Depends(require_round_member_or_admin)]
)
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

    mode = writer_mode(db)
    game = db.query(models.GameStateModel).filter_by(game_id=game_id).populate_existing().first()
    if game is None:
        raise HTTPException(404, "Game not found")
    check_revision(db, game, patch.expected_revision, required=mode == "canonical" and game.game_status == "completed")
    state = deepcopy(game.state or {})
    if player_id not in {p.get("id") for p in state.get("players", [])} or hole_number not in REQUIRED_HOLES:
        raise HTTPException(status_code=400, detail="Unknown player or hole")
    if patch.quarters is not None and not math.isfinite(patch.quarters):
        raise HTTPException(status_code=400, detail="Quarter scores must be finite numbers")

    history = state.setdefault("hole_history", [])
    entry = next((h for h in history if h.get("hole") == hole_number), None)
    if entry is None:
        entry = {"hole": hole_number, "points_delta": {}}
        history.append(entry)

    if mode == "canonical" and game.game_status == "completed":
        if patch.quarters is not None:
            entry.setdefault("points_delta", {})[player_id] = patch.quarters
        if patch.score is not None:
            entry["gross_scores"] = {**(entry.get("gross_scores") or {}), player_id: patch.score}
        validate_round_scores(state["players"], history)
        detail = propose_completed(db, game, history)
        db.commit()
        raise HTTPException(409, detail)

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
        existing = models.HoleEvent(
            game_id=game_id,
            hole_number=hole_number,
            player_id=player_id,
            score=patch.score,
            quarters=patch.quarters
            if patch.quarters is not None
            else entry.get("points_delta", {}).get(player_id, 0.0),
            recorded_at=now_ts,
        )
        db.add(existing)

    if patch.quarters is not None:
        entry.setdefault("points_delta", {})[player_id] = patch.quarters
    if patch.score is not None:
        entry["gross_scores"] = {**(entry.get("gross_scores") or {}), player_id: patch.score}
    standings = {}
    for hole in history:
        for pid, quarters in hole.get("points_delta", {}).items():
            standings[pid] = standings.get(pid, 0) + quarters
    state["standings"] = standings
    state["hole_quarters"] = {str(h["hole"]): h["points_delta"] for h in history}
    for player in state.get("players", []):
        player["total_points"] = standings.get(player["id"], 0)
    game.state = state
    flag_modified(game, "state")
    saved_score = existing.score
    saved_quarters = existing.quarters
    try:
        if game.game_status == "completed":
            validate_round_scores(state["players"], history)
            persist_completed_game(db, game)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "game_id": game_id,
        "hole_number": hole_number,
        "player_id": player_id,
        "score": saved_score,
        "quarters": saved_quarters,
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
