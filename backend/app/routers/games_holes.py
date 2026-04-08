"""Hole operations routes — complete, update, delete holes; rotation; wagers; quarters-only scoring."""

import json
import logging
import traceback
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import database, models, schemas
from ..managers.websocket_manager import manager as websocket_manager
from ..schemas import CompleteHoleRequest, RotationSelectionRequest
from ..services.game_lifecycle_service import get_game_lifecycle_service
from ..services.hole_completion_service import (
    process_complete_hole,
    process_update_hole,
    replay_player_totals,
    run_complete_hole_validations,
    run_update_hole_validations,
    sync_simulation,
)
from ..services.notification_service import get_notification_service
from ..wolf_goat_pig import Player, WolfGoatPigGame

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class QuartersOnlyRequest(BaseModel):
    """Simplified scoring request - just quarters per hole per player"""

    hole_quarters: dict[str, dict[str, float]]  # { "1": { "player1": 2, "player2": -2 }, ... }
    optional_details: dict[str, dict[str, Any]] | None = None  # { "1": { "notes": "..." }, ... }
    current_hole: int = 18


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/{game_id}/holes/complete", deprecated=True)
async def complete_hole(  # type: ignore
    game_id: str, request: CompleteHoleRequest, db: Session = Depends(database.get_db)
):
    """
    DEPRECATED: Use POST /games/{game_id}/quarters-only instead.

    This endpoint has complex validation for special rules (Joe's Special, Big Dick,
    Aardvark, Float, carry-over). For simplified scoring, use the quarters-only endpoint
    which only validates that each hole sums to zero.

    Complete a hole with all data at once - simplified scorekeeper mode.
    No state machine validation, just direct data storage.
    """
    try:
        # Get game from database
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state or {}

        # Validate request
        run_complete_hole_validations(request, game_state)

        # Process hole completion (scoring, state updates)
        hole_result, game_state = process_complete_hole(request, game_state)

        # Persist to database
        game.state = game_state
        game.updated_at = datetime.now(UTC).isoformat()

        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(game, "state")

        db.commit()
        db.refresh(game)

        # Sync to in-memory simulation if present
        sync_simulation(game_id, game_state, request)

        logger.info(f"Completed hole {request.hole_number} for game {game_id}")

        await websocket_manager.broadcast(json.dumps({"game_state": game_state}), game_id)

        # Send game end notifications when final hole (18) is completed
        if request.hole_number == 18:
            try:
                notification_service = get_notification_service()
                final_standings = sorted(
                    game_state.get("players", []),
                    key=lambda p: p.get("points", 0),
                    reverse=True,
                )
                winner_name = final_standings[0].get("id", "Unknown") if final_standings else "Unknown"
                winner_points = final_standings[0].get("points", 0) if final_standings else 0

                notification_service.broadcast_to_game(
                    game_id=game_id,
                    notification_type="game_end",
                    message=f"Game completed! Winner: {winner_name} with {winner_points:+.0f}Q",
                    db=db,
                    data={
                        "game_id": game_id,
                        "final_standings": [{"id": p.get("id"), "points": p.get("points", 0)} for p in final_standings],
                    },
                )
                logger.info(f"Sent game_end notifications for game {game_id}")
            except Exception as notify_error:
                # Don't fail the hole completion if notifications fail
                logger.warning(f"Failed to send game_end notifications: {notify_error}")

        return {
            "success": True,
            "game_state": game_state,
            "hole_result": hole_result,
            "message": f"Hole {request.hole_number} completed successfully",
        }

    except HTTPException:
        # Re-raise HTTPException without wrapping
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error completing hole: {e}")
        raise HTTPException(status_code=500, detail=f"Error completing hole: {e!s}")


@router.patch("/{game_id}/holes/{hole_number}")
async def update_hole(  # type: ignore
    game_id: str,
    hole_number: int,
    request: CompleteHoleRequest,
    db: Session = Depends(database.get_db),
):
    """
    Update an existing hole's data. Uses same validation as complete_hole.
    Recalculates all player totals from scratch after update.
    """
    try:
        # Validate hole_number matches request
        if request.hole_number != hole_number:
            raise HTTPException(
                status_code=400,
                detail=f"Hole number in URL ({hole_number}) must match request body ({request.hole_number})",
            )

        # Get game from database
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state or {}

        # Check if hole exists
        if "hole_history" not in game_state:
            raise HTTPException(status_code=404, detail="No holes recorded for this game")

        existing_hole_index = next(
            (i for i, h in enumerate(game_state["hole_history"]) if h.get("hole") == hole_number),
            None,
        )

        if existing_hole_index is None:
            raise HTTPException(status_code=404, detail=f"Hole {hole_number} not found in game history")

        # Validate request
        run_update_hole_validations(request, hole_number)

        # Process hole update (scoring, replay totals)
        hole_result, game_state = process_update_hole(request, game_state, hole_number, existing_hole_index)

        # Persist to database
        game.state = game_state
        game.updated_at = datetime.now(UTC).isoformat()

        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(game, "state")

        db.commit()
        db.refresh(game)

        logger.info(f"Updated hole {hole_number} for game {game_id}")

        await websocket_manager.broadcast(json.dumps({"game_state": game_state}), game_id)
        return {
            "success": True,
            "game_state": game_state,
            "hole_result": hole_result,
            "message": f"Hole {hole_number} updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating hole: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating hole: {e!s}")


@router.delete("/{game_id}/holes/{hole_number}")
async def delete_hole(game_id: str, hole_number: int, db: Session = Depends(database.get_db)):  # type: ignore
    """
    Delete a hole from hole_history.
    Recalculates all player totals and updates current_hole if needed.
    """
    try:
        # Get game from database
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state or {}

        # Check if hole exists
        if "hole_history" not in game_state or not game_state["hole_history"]:
            raise HTTPException(status_code=404, detail="No holes recorded for this game")

        existing_hole_index = next(
            (i for i, h in enumerate(game_state["hole_history"]) if h.get("hole") == hole_number),
            None,
        )

        if existing_hole_index is None:
            raise HTTPException(status_code=404, detail=f"Hole {hole_number} not found in game history")

        # Remove the hole from history
        deleted_hole = game_state["hole_history"].pop(existing_hole_index)

        # Replay all player totals from scratch
        replay_player_totals(game_state)

        # Update current_hole if the deleted hole was the last one played
        max_hole_played = max([h.get("hole", 0) for h in game_state["hole_history"]], default=0)
        game_state["current_hole"] = max_hole_played + 1

        # Update game state in database
        game.state = game_state
        game.updated_at = datetime.now(UTC).isoformat()

        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(game, "state")

        db.commit()
        db.refresh(game)

        logger.info(f"Deleted hole {hole_number} from game {game_id}")

        return {
            "success": True,
            "game_state": game_state,
            "deleted_hole": deleted_hole,
            "message": f"Hole {hole_number} deleted successfully",
            "remaining_holes": len(game_state["hole_history"]),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting hole: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting hole: {e!s}")


@router.get("/{game_id}/next-rotation", deprecated=True)
async def get_next_rotation(game_id: str, db: Session = Depends(database.get_db)):  # type: ignore
    """
    DEPRECATED: Not needed for quarters-only scoring.

    Calculate the next rotation order based on current hole.
    Handles normal rotation and Hoepfinger special selection.
    Only needed if tracking complex game mechanics (rotation, Hoepfinger, etc).
    """
    try:
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state or {}
        player_count = len(game_state.get("players", []))

        # Use game_state.get("current_hole", 1) for current_hole
        current_hole = game_state.get("current_hole", 1)

        # Determine Hoepfinger start based on player count
        hoepfinger_start = {4: 17, 5: 16, 6: 13}.get(player_count, 17)

        is_hoepfinger = current_hole >= hoepfinger_start

        # Get last hole's rotation
        hole_history = game_state.get("hole_history", [])
        is_first_hole = len(hole_history) == 0

        if hole_history:
            last_hole = hole_history[-1]
            last_rotation = last_hole.get("rotation_order", [p["id"] for p in game_state["players"]])
        else:
            # First hole - use player order (sorted by tee_order)
            last_rotation = [p["id"] for p in game_state["players"]]

        if is_hoepfinger:
            # Hoepfinger: Goat (furthest down) selects position
            # Calculate current standings
            standings = {}
            for player in game_state["players"]:
                standings[player["id"]] = player.get("points", 0)

            goat_id = min(standings, key=standings.get)  # type: ignore

            return {
                "is_hoepfinger": True,
                "goat_id": goat_id,
                "goat_selects_position": True,
                "available_positions": list(range(player_count)),
                "current_rotation": last_rotation,
                "message": "Goat selects hitting position",
            }
        if is_first_hole:
            # First hole - use initial tee order without rotation
            new_rotation = last_rotation
        else:
            # Normal rotation: shift left by 1 from previous hole
            new_rotation = last_rotation[1:] + [last_rotation[0]]

        return {
            "is_hoepfinger": False,
            "rotation_order": new_rotation,
            "captain_index": 0,
            "captain_id": new_rotation[0],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating next rotation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{game_id}/next-hole-wager", deprecated=True)
async def get_next_hole_wager(  # type: ignore
    game_id: str,
    current_hole: int | None = None,
    db: Session = Depends(database.get_db),
):
    """
    DEPRECATED: Not needed for quarters-only scoring.

    Calculate the base wager for the next hole.
    Accounts for carry-over, Vinnie's Variation, and Hoepfinger rules.
    Only needed if tracking complex game mechanics (wager escalation, carry-over, etc).
    """
    try:
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state or {}
        player_count = len(game_state.get("players", []))

        # Use provided current_hole or get from game state
        if current_hole is None:
            current_hole = game_state.get("current_hole", 1)

        base_wager = game_state.get("base_wager", 1)

        # Check for carry-over
        if game_state.get("carry_over_wager"):
            carry_over_wager = game_state["carry_over_wager"]
            from_hole = game_state.get("carry_over_from_hole", current_hole - 1)

            if game_state.get("consecutive_push_block"):
                return {
                    "base_wager": carry_over_wager,
                    "carry_over": False,
                    "message": f"Consecutive carry-over blocked. Base wager remains {carry_over_wager}Q from hole {from_hole}",
                }
            return {
                "base_wager": carry_over_wager,
                "carry_over": True,
                "message": f"Carry-over from hole {from_hole} push",
            }

        # Check for The Option (Captain is Goat)
        if not game_state.get("carry_over_wager"):  # Option doesn't stack with carry-over
            # Calculate current standings to find Goat
            standings = {}
            for player in game_state.get("players", []):
                standings[player["id"]] = player.get("points", 0)

            if standings:
                goat_id = min(standings, key=standings.get)  # type: ignore
                goat_points = standings[goat_id]

                # Option applies if Captain (first in rotation) is the Goat AND has negative points
                hole_history = game_state.get("hole_history", [])
                if hole_history:
                    last_hole = hole_history[-1]
                    next_rotation_order = last_hole.get("rotation_order", [])[1:] + [
                        last_hole.get("rotation_order", [])[0]
                    ]
                    next_captain_id = next_rotation_order[0] if next_rotation_order else None

                    if next_captain_id == goat_id and goat_points < 0:
                        # Check if last hole turned off Option
                        if not last_hole.get("option_turned_off", False):
                            return {
                                "base_wager": base_wager * 2,
                                "option_active": True,
                                "goat_id": goat_id,
                                "carry_over": False,
                                "vinnies_variation": False,
                                "message": f"The Option: Captain is Goat ({goat_points}Q), wager doubled",
                            }

        # Check for Vinnie's Variation (holes 13-16 in 4-player)
        if player_count == 4 and 13 <= current_hole <= 16:
            return {
                "base_wager": base_wager * 2,
                "vinnies_variation": True,
                "carry_over": False,
                "message": f"Vinnie's Variation: holes 13-16 doubled (hole {current_hole})",
            }

        # Normal base wager
        return {
            "base_wager": base_wager,
            "carry_over": False,
            "vinnies_variation": False,
            "message": "Normal base wager",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating next hole wager: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{game_id}/select-rotation", deprecated=True)
async def select_rotation(  # type: ignore
    game_id: str,
    request: RotationSelectionRequest,
    db: Session = Depends(database.get_db),
):
    """
    DEPRECATED: Not needed for quarters-only scoring.

    Phase 5: Dynamic rotation selection for 5-man games on holes 16-18.
    The Goat (lowest points player) selects their position in the rotation.
    Only needed for complex 5-man game Hoepfinger mechanics.
    """
    # Get game state (follow same pattern as get_game_state_by_id)
    service = get_game_lifecycle_service()
    simulation = None
    game = None
    game_state = None

    if game_id in service._active_games:
        simulation = service._active_games[game_id]
        game_state = simulation.get_game_state()
    else:
        # Fetch from database
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        game_state = game.state

    if not game_state:
        raise HTTPException(status_code=404, detail="Game state not found")

    player_count = len(game_state.get("players", []))

    # Validate: Only 5-man games
    if player_count != 5:
        raise HTTPException(
            status_code=400,
            detail="Dynamic rotation selection only applies to 5-player games",
        )

    # Validate: Only holes 16, 17, 18
    if request.hole_number not in [16, 17, 18]:
        raise HTTPException(
            status_code=400,
            detail="Rotation selection only allowed on holes 16, 17, and 18",
        )

    # Validate: Position must be 1-5 for 5-man game
    if request.selected_position < 1 or request.selected_position > 5:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid position {request.selected_position}. Must be 1-5 for 5-player games",
        )

    # Identify current Goat (player with lowest total points)
    players = game_state.get("players", [])
    if not players:
        raise HTTPException(status_code=404, detail="No players found in game")

    # Find player with lowest points
    goat_player = min(players, key=lambda p: p.get("points", 0))
    actual_goat_id = goat_player["id"]

    # Validate: Request must be from actual Goat
    if request.goat_player_id != actual_goat_id:
        raise HTTPException(
            status_code=400,
            detail=f"Only the Goat (player with lowest points) can select rotation. Current Goat is {actual_goat_id}, not {request.goat_player_id}",
        )

    # Get current rotation order (or use default player order)
    current_rotation = game_state.get("current_rotation_order") or [p["id"] for p in players]

    # Reorder rotation: Goat at selected position, others maintain relative order
    goat_id = request.goat_player_id
    selected_index = request.selected_position - 1  # Convert to 0-indexed

    # Remove Goat from current rotation
    rotation_without_goat = [pid for pid in current_rotation if pid != goat_id]

    # Insert Goat at selected position
    new_rotation = rotation_without_goat[:selected_index] + [goat_id] + rotation_without_goat[selected_index:]

    # Store new rotation in game state
    game_state["current_rotation_order"] = new_rotation

    # Save updated rotation
    if simulation:
        # Update simulation state for in-progress games
        simulation._game_state = game_state  # type: ignore
    else:
        # Update database for stored games
        assert game is not None  # game is guaranteed non-None here (we returned 404 if None)
        game.state = game_state
        db.commit()

    return {
        "message": f"Rotation updated for hole {request.hole_number}",
        "rotation_order": new_rotation,
        "goat_id": goat_id,
        "selected_position": request.selected_position,
    }


@router.post("/{game_id}/quarters-only")
async def save_quarters_only(game_id: str, request: QuartersOnlyRequest, db: Session = Depends(database.get_db)):
    """
    Simplified scoring endpoint - just quarters per hole per player.
    Only validation: each hole must sum to zero (zero-sum game).

    This replaces the complex hole completion flow with a simple:
    1. Enter quarters (+/-) for each player per hole
    2. Validate sum is zero
    3. Save
    """
    try:
        # Get game from database
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Validate: Each hole must sum to zero
        validation_errors = []
        for hole_str, player_quarters in request.hole_quarters.items():
            hole_sum = sum(player_quarters.values())
            if abs(hole_sum) > 0.001:  # Allow small floating point errors
                validation_errors.append(f"Hole {hole_str}: sum is {hole_sum}, must be 0")

        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail=f"Zero-sum validation failed: {'; '.join(validation_errors)}",
            )

        # Calculate standings
        standings = {}
        for hole_str, player_quarters in request.hole_quarters.items():
            for player_id, quarters in player_quarters.items():
                if player_id not in standings:
                    standings[player_id] = 0
                standings[player_id] += quarters

        # Update game state with simplified data
        game_state = game.state or {}
        game_state["quarters_only_mode"] = True
        game_state["hole_quarters"] = request.hole_quarters
        game_state["optional_details"] = request.optional_details or {}
        game_state["current_hole"] = request.current_hole
        game_state["standings"] = standings

        # Update player points in game state
        for player in game_state.get("players", []):
            player_id = player.get("id")
            if player_id in standings:
                player["total_points"] = standings[player_id]

        # Convert hole_quarters to hole_history format for compatibility
        # Include all optional details (teams, winner, wager, gross_scores, phase, notes)
        hole_history = []
        for hole_num in range(1, 19):
            hole_str = str(hole_num)
            if hole_str in request.hole_quarters:
                # Get all optional details for this hole
                hole_details = (request.optional_details or {}).get(hole_str, {})
                hole_entry = {
                    "hole": hole_num,
                    "points_delta": request.hole_quarters[hole_str],
                    "quarters_only": True,
                    "notes": hole_details.get("notes", ""),
                    # Include all other fields from optional_details
                    "teams": hole_details.get("teams"),
                    "winner": hole_details.get("winner"),
                    "wager": hole_details.get("wager"),
                    "gross_scores": hole_details.get("gross_scores"),
                    "phase": hole_details.get("phase"),
                }
                hole_history.append(hole_entry)
        game_state["hole_history"] = hole_history

        # Mark game status based on holes completed
        holes_with_data = len([h for h in request.hole_quarters.values() if h])
        if holes_with_data >= 18:
            game_state["game_status"] = "completed"
            game.game_status = "completed"
        elif holes_with_data > 0:
            game_state["game_status"] = "in_progress"
            game.game_status = "in_progress"

        game.state = game_state
        db.commit()

        logger.info(f"Saved quarters-only data for game {game_id}: {holes_with_data} holes")

        return {
            "success": True,
            "game_id": game_id,
            "holes_saved": holes_with_data,
            "standings": standings,
            "game_status": game.game_status,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving quarters-only data for game {game_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error saving data: {e!s}")
