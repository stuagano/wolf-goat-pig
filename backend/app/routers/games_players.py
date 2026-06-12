"""Player management in games — create-test, update name, remove player, update handicap."""

import logging
import random
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .. import database, models
from ..services.game_lifecycle_service import get_game_lifecycle_service
from ..state.course_manager import CourseManager
from ..utils.time import utc_now
from ..wolf_goat_pig import Player, WolfGoatPigGame

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])


# ---------------------------------------------------------------------------
# Test seed models (used only by create-test)
# ---------------------------------------------------------------------------


class BallSeed(BaseModel):
    """Testing helper payload for manually positioning a ball."""

    player_id: str = Field(..., description="Unique player identifier")
    distance_to_pin: float = Field(..., ge=0, description="Distance remaining in yards")
    lie_type: str = Field("fairway", description="Current lie type for the ball")
    shot_count: int = Field(1, ge=0, description="Number of strokes taken on the hole")
    holed: bool = Field(False, description="Whether the ball is in the hole")
    conceded: bool = Field(False, description="If the putt has been conceded")
    penalty_strokes: int = Field(0, ge=0, description="Penalty strokes assessed on the shot")


class BettingSeed(BaseModel):
    """Testing helper payload for adjusting betting metadata."""

    base_wager: int | None = Field(None, ge=0)
    current_wager: int | None = Field(None, ge=0)
    doubled: bool | None = None
    redoubled: bool | None = None
    carry_over: bool | None = None
    float_invoked: bool | None = None
    option_invoked: bool | None = None
    duncan_invoked: bool | None = None
    tunkarri_invoked: bool | None = None
    big_dick_invoked: bool | None = None
    joes_special_value: int | None = None
    line_of_scrimmage: str | None = None
    ping_pong_count: int | None = Field(None, ge=0)


class UpdatePlayerNameRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)


class UpdateHittingOrderRequest(BaseModel):
    hitting_order: list[str] = Field(..., min_length=4, max_length=6)
    hole_number: int | None = Field(None, ge=1, le=18, description="Hole to update; defaults to current hole")


class SimulationSeedRequest(BaseModel):
    """Parameters accepted by the test seeding endpoint."""

    current_hole: int | None = Field(None, description="Hole number to switch the active simulation to")
    shot_order: list[str] | None = Field(None, description="Explicit hitting order for the active hole")
    ball_positions: list[BallSeed] = Field(default_factory=list)
    ball_positions_replace: bool = Field(False, description="Replace all ball positions when True")
    line_of_scrimmage: str | None = None
    next_player_to_hit: str | None = None
    current_order_of_play: list[str] | None = None
    wagering_closed: bool | None = None
    betting: BettingSeed | None = None
    team_formation: dict[str, Any] | None = Field(None, description="Override the current TeamFormation dataclass")
    clear_balls_in_hole: bool = Field(False, description="Clear recorded holed balls before applying seed")
    reset_doubles_history: bool = Field(True, description="Clear double-offer history to avoid stale offers")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/create-test")
async def create_test_game(
    course_name: str | None = None,
    player_count: int = 4,
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """
    Create a test game with mock players and immediately start it - for single-device testing

    Supports fallback mode: if database operations fail, the game is created in memory only.
    """
    import string
    import uuid

    from ..fallback_game_manager import get_fallback_manager

    # Generate 6-character join code
    join_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    game_id = str(uuid.uuid4())
    current_time = utc_now().isoformat()

    # Create mock players (supports up to 6 players)
    mock_players = [
        {
            "id": "test-player-1",
            "name": "Test Player 1",
            "handicap": 18,
            "is_human": True,
        },
        {
            "id": "test-player-2",
            "name": "Test Player 2",
            "handicap": 15,
            "is_human": False,
        },
        {
            "id": "test-player-3",
            "name": "Test Player 3",
            "handicap": 12,
            "is_human": False,
        },
        {
            "id": "test-player-4",
            "name": "Test Player 4",
            "handicap": 20,
            "is_human": False,
        },
        {
            "id": "test-player-5",
            "name": "Test Player 5",
            "handicap": 16,
            "is_human": False,
        },
        {
            "id": "test-player-6",
            "name": "Test Player 6",
            "handicap": 14,
            "is_human": False,
        },
    ][:player_count]

    # Initialize WolfGoatPigGame for this game
    wgp_players = [
        Player(
            id=p["id"],  # type: ignore
            name=p["name"],  # type: ignore
            handicap=p["handicap"],  # type: ignore
        )
        for p in mock_players
    ]

    # Initialize course manager with selected course
    test_course_manager = None
    if course_name:
        try:
            test_course_manager = CourseManager()
            available_courses = test_course_manager.get_courses()
            if course_name in available_courses:
                test_course_manager.load_course(course_name)
                logger.info(f"Loaded course '{course_name}' for test game {game_id}")
            else:
                logger.warning(f"Course '{course_name}' not found for test game")
                test_course_manager = None
        except Exception as course_error:
            logger.error(f"Failed to load course for test game: {course_error}")
            test_course_manager = None

    simulation = WolfGoatPigGame(
        player_count=player_count,
        players=wgp_players,
        course_manager=test_course_manager,
    )

    # Get the game state (game is already started in __init__)
    game_state = simulation.get_game_state()
    game_state["game_status"] = "in_progress"
    game_state["test_mode"] = True

    # Add holes_config for Wing Point course
    if course_name and "wing point" in course_name.lower():
        from ..data.wing_point_course_data import WING_POINT_COURSE_DATA

        holes_config = []
        for hole_data in WING_POINT_COURSE_DATA["holes"]:
            holes_config.append(
                {
                    "hole_number": hole_data["hole_number"],
                    "par": hole_data["par"],
                    "handicap": hole_data["handicap_men"],
                }
            )
        game_state["holes_config"] = holes_config

    # Add simulation to active_games for test mode
    service = get_game_lifecycle_service()
    service._active_games[game_id] = simulation

    # Try to save to database first
    fallback_mode = False

    try:
        # Ensure uniqueness of join code
        existing = db.query(models.GameStateModel).filter(models.GameStateModel.join_code == join_code).first()

        if existing:
            join_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Create GameStateModel
        game_state_model = models.GameStateModel(
            game_id=game_id,
            join_code=join_code,
            creator_user_id="test-user",
            game_status="in_progress",
            state=game_state,
            created_at=current_time,
            updated_at=current_time,
        )
        db.add(game_state_model)

        # Create GamePlayer records for each mock player
        for i, player in enumerate(mock_players):
            game_player = models.GamePlayer(
                game_id=game_id,
                player_slot_id=player["id"],
                user_id=f"test-user-{i + 1}",
                player_name=player["name"],
                handicap=player["handicap"],
                join_status="joined",
                joined_at=current_time,
                created_at=current_time,
            )
            db.add(game_player)

        db.commit()
        db.refresh(game_state_model)

        logger.info(f"Created test game {game_id} in database with {player_count} mock players")

    except Exception as db_error:
        db.rollback()
        logger.warning(f"Database save failed: {db_error}")
        logger.info("Attempting fallback mode...")

        # Try fallback mode
        try:
            fallback = get_fallback_manager()
            fallback.enable()

            fallback.create_game(
                game_id=game_id,
                join_code=join_code,
                creator_user_id="test-user",
                game_status="in_progress",
                state=game_state,
            )

            fallback_mode = True
            logger.warning(f"Created test game {game_id} in FALLBACK MODE (memory only)")

        except Exception as fallback_error:
            logger.error(f"Both database and fallback mode failed: {fallback_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create game. Database error: {db_error!s}. Fallback error: {fallback_error!s}",
            )

    # Build response
    response = {
        "game_id": game_id,
        "join_code": join_code,
        "status": "in_progress",
        "player_count": player_count,
        "players": mock_players,
        "test_mode": True,
        "created_at": current_time,
        "message": "Test game created and started successfully",
    }

    # Add warnings if in fallback mode
    if fallback_mode:
        response["warning"] = "Game created in memory only - will be lost on server restart"
        response["fallback_mode"] = True
        response["persistence"] = "memory"
    else:
        response["persistence"] = "database"

    return response


@router.patch("/{game_id}/players/{player_id}/name")
async def update_player_name(
    game_id: str,
    player_id: str,
    name_update: UpdatePlayerNameRequest,
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """Update a player's display name. Writes to DB; evicts cache so next load is fresh."""
    new_name = name_update.name.strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="Name cannot be blank")

    game_player = (
        db.query(models.GamePlayer)
        .filter(models.GamePlayer.game_id == game_id, models.GamePlayer.player_slot_id == player_id)
        .first()
    )
    if not game_player:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found in game {game_id}")

    game_player.player_name = new_name

    # Keep the denormalized copy in the state blob in sync
    game_record = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()
    if game_record:
        from sqlalchemy.orm.attributes import flag_modified

        state = game_record.state or {}
        for p in state.get("players", []):
            if p.get("id") == player_id:
                p["name"] = new_name
                break
        flag_modified(game_record, "state")
        game_record.updated_at = utc_now().isoformat()

    db.commit()
    get_game_lifecycle_service().cleanup_game(game_id)

    logger.info(f"Updated player {player_id} name to '{new_name}' in game {game_id}")
    return {"success": True, "game_id": game_id, "player_id": player_id, "name": new_name}


@router.delete("/{game_id}/players/{player_slot_id}")
async def remove_player(game_id: str, player_slot_id: str, db: Session = Depends(database.get_db)):  # type: ignore
    """
    Remove a player from a game in setup/lobby status.
    Only allowed before game starts.

    Args:
        game_id: The game ID
        player_slot_id: The player's slot ID (e.g., "p1", "p2")
    """
    try:
        # Get game from database
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Only allow removing players if game hasn't started
        if game.game_status not in ["setup", "lobby"]:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove players from a game that has already started",
            )

        # Remove from game_players table
        game_player = (
            db.query(models.GamePlayer)
            .filter(
                models.GamePlayer.game_id == game_id,
                models.GamePlayer.player_slot_id == player_slot_id,
            )
            .first()
        )

        if not game_player:
            raise HTTPException(status_code=404, detail=f"Player {player_slot_id} not found in game")

        player_name = game_player.player_name
        db.delete(game_player)

        # Remove from game state players array
        state = game.state or {}
        players = state.get("players", [])
        state["players"] = [p for p in players if p.get("id") != player_slot_id]
        game.state = state
        game.updated_at = utc_now().isoformat()

        db.commit()

        logger.info(f"Removed player {player_slot_id} ({player_name}) from game {game_id}")

        return {
            "success": True,
            "game_id": game_id,
            "player_slot_id": player_slot_id,
            "message": f"Player {player_name} removed from game",
            "players_remaining": len(state["players"]),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing player: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to remove player: {e!s}")


@router.patch("/{game_id}/players/{player_slot_id}/handicap")
async def update_player_handicap(  # type: ignore
    game_id: str,
    player_slot_id: str,
    handicap_update: dict,
    db: Session = Depends(database.get_db),
):
    """
    Update a player's handicap in a game in setup/lobby status.
    Only allowed before game starts.

    Args:
        game_id: The game ID
        player_slot_id: The player's slot ID (e.g., "p1", "p2")
        handicap_update: Dict with "handicap" key containing the new handicap
    """
    try:
        new_handicap = handicap_update.get("handicap")
        if new_handicap is None:
            raise HTTPException(status_code=400, detail="Handicap not provided")

        try:
            new_handicap = float(new_handicap)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid handicap value")

        if new_handicap < 0 or new_handicap > 54:
            raise HTTPException(status_code=400, detail="Handicap must be between 0 and 54")

        # Get game from database
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Only allow updating handicap if game hasn't started
        if game.game_status not in ["setup", "lobby"]:
            raise HTTPException(status_code=400, detail="Cannot update handicap after game has started")

        # Update in game_players table
        game_player = (
            db.query(models.GamePlayer)
            .filter(
                models.GamePlayer.game_id == game_id,
                models.GamePlayer.player_slot_id == player_slot_id,
            )
            .first()
        )

        if not game_player:
            raise HTTPException(status_code=404, detail=f"Player {player_slot_id} not found in game")

        game_player.handicap = new_handicap

        # Update in game state players array
        state = game.state or {}
        players = state.get("players", [])
        for player in players:
            if player.get("id") == player_slot_id:
                player["handicap"] = new_handicap
                break

        game.state = state
        game.updated_at = utc_now().isoformat()

        db.commit()

        logger.info(f"Updated player {player_slot_id} handicap to {new_handicap} in game {game_id}")

        return {
            "success": True,
            "game_id": game_id,
            "player_slot_id": player_slot_id,
            "handicap": new_handicap,
            "message": f"Handicap updated to {new_handicap}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating player handicap: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update handicap: {e!s}")


@router.patch("/{game_id}/hitting-order")
async def update_hitting_order(
    game_id: str,
    body: UpdateHittingOrderRequest,
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """Update the hitting order for any hole (defaults to current hole).

    Writes to hole_orders table (source of truth), then evicts the game from
    cache so the next load replays the stored order via get_game().
    """
    try:
        game = get_game_lifecycle_service().get_game(db, game_id)

        player_ids = {p.id for p in game.players}
        if set(body.hitting_order) != player_ids or len(body.hitting_order) != len(player_ids):
            raise HTTPException(
                status_code=400,
                detail="hitting_order must be an exact permutation of all player IDs",
            )

        target_hole = body.hole_number if body.hole_number is not None else game.current_hole
        current_time = utc_now().isoformat()

        # Persist to hole_orders (upsert — last write wins)
        existing = (
            db.query(models.HoleOrder)
            .filter(models.HoleOrder.game_id == game_id, models.HoleOrder.hole_number == target_hole)
            .first()
        )
        if existing:
            existing.hitting_order = list(body.hitting_order)
            existing.captain_id = body.hitting_order[0]
            existing.recorded_at = current_time
        else:
            db.add(
                models.HoleOrder(
                    game_id=game_id,
                    hole_number=target_hole,
                    hitting_order=list(body.hitting_order),
                    captain_id=body.hitting_order[0],
                    recorded_at=current_time,
                )
            )
        db.commit()

        # Evict from cache so the next get_game() reloads with the stored order applied
        get_game_lifecycle_service().cleanup_game(game_id)

        logger.info(f"Updated hitting order for game {game_id} hole {target_hole}: {body.hitting_order}")

        return {
            "status": "ok",
            "game_id": game_id,
            "hole": target_hole,
            "hitting_order": body.hitting_order,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating hitting order: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update hitting order: {e!s}")
