"""Player management in games — create-test, update name, remove player, update handicap."""

import logging
import random
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .. import database, models
from ..services.game_lifecycle_service import get_game_lifecycle_service
from ..state.course_manager import CourseManager
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
    current_time = datetime.now(UTC).isoformat()

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
async def update_player_name(  # type: ignore
    game_id: str,
    player_id: str,
    name_update: dict,
    db: Session = Depends(database.get_db),
):
    """
    Update a player's name in an active game.
    Allows editing player names in the game scorer without requiring PlayerProfile records.

    Args:
        game_id: The game ID
        player_id: The player's ID (e.g., "test-player-1")
        name_update: Dict with "name" key containing the new name
    """
    try:
        new_name = name_update.get("name")
        if not new_name or not isinstance(new_name, str) or not new_name.strip():
            raise HTTPException(status_code=400, detail="Invalid name provided")

        new_name = new_name.strip()

        # Try to get game from lifecycle service (active games in memory)
        service = get_game_lifecycle_service()
        simulation = service._active_games.get(game_id)

        if simulation:
            # Update player name in simulation
            player_found = False
            for player in simulation.players:
                if player.id == player_id:
                    player.name = new_name
                    player_found = True
                    break

            if not player_found:
                raise HTTPException(status_code=404, detail=f"Player {player_id} not found in game")

            # Update player name in game state
            game_state = simulation.get_game_state()
            for player in game_state.get("players", []):
                if player.get("id") == player_id:
                    player["name"] = new_name
                    break

            logger.info(f"Updated player {player_id} name to '{new_name}' in game {game_id}")

        # Try to update in database as well (if game exists in DB)
        try:
            # Update GameStateModel
            game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

            if game:
                state = game.state or {}
                players = state.get("players", [])
                for player in players:
                    if player.get("id") == player_id:
                        player["name"] = new_name
                        break

                game.state = state  # type: ignore
                game.updated_at = datetime.now(UTC).isoformat()  # type: ignore

                # Also update GamePlayer record
                game_player = (
                    db.query(models.GamePlayer)
                    .filter(
                        models.GamePlayer.game_id == game_id,
                        models.GamePlayer.player_slot_id == player_id,
                    )
                    .first()
                )

                if game_player:
                    game_player.player_name = new_name

                db.commit()
                logger.info(f"Updated player {player_id} name to '{new_name}' in database for game {game_id}")

        except Exception as db_error:
            # Log but don't fail - game can continue in memory
            logger.warning(f"Failed to update player name in database: {db_error}")
            try:
                db.rollback()
            except Exception as rollback_error:
                logger.debug(f"Rollback failed (may be expected): {rollback_error}")

        return {
            "success": True,
            "game_id": game_id,
            "player_id": player_id,
            "name": new_name,
            "message": f"Player name updated to '{new_name}'",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating player name: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update player name: {e!s}")


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
        if game.status not in ["setup", "lobby"]:
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
        game.updated_at = datetime.now(UTC).isoformat()

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
        if game.status not in ["setup", "lobby"]:
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
        game.updated_at = datetime.now(UTC).isoformat()

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
