"""Game lifecycle routes — create, join, lobby, start, list, delete, complete, state, action, history, details."""

import json
import logging
import traceback
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import database, models, schemas
from ..managers.websocket_manager import manager as websocket_manager
from ..schemas import ActionRequest, ActionResponse
from ..services.game_lifecycle_service import get_game_lifecycle_service
from ..services.notification_service import get_notification_service
from ..state.course_manager import CourseManager
from ..validators import GameStateValidator, HandicapValidator
from ..wolf_goat_pig import Player, WolfGoatPigGame

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])


# ---------------------------------------------------------------------------
# Legacy-to-unified action mapping (used by POST /games/{game_id}/action)
# ---------------------------------------------------------------------------

def _get_current_captain_id() -> str | None:
    """Best-effort lookup for the active captain id across legacy and unified state."""
    try:
        simulation_state = game.get_game_state()  # type: ignore
        if isinstance(simulation_state, dict):
            captain = simulation_state.get("captain_id") or simulation_state.get("captain")
            if captain:
                return captain  # type: ignore
    except Exception:
        # If the simulation hasn't been initialized yet, fall back to legacy state
        pass

    try:
        legacy_state = {"message": "Legacy game_state.get_state() is deprecated"}
        if isinstance(legacy_state, dict):
            return legacy_state.get("captain_id")
    except Exception:
        pass

    return None


LEGACY_TO_UNIFIED_ACTIONS = {
    "next_hole": ("ADVANCE_HOLE", lambda payload: {}),
    "request_partner": ("REQUEST_PARTNERSHIP", lambda payload: payload or {}),
    "accept_partner": ("RESPOND_PARTNERSHIP", lambda payload: {"accepted": True}),
    "decline_partner": ("RESPOND_PARTNERSHIP", lambda payload: {"accepted": False}),
    "go_solo": ("DECLARE_SOLO", lambda payload: {}),
    "offer_double": (
        "OFFER_DOUBLE",
        lambda payload: {
            "player_id": payload.get("player_id")
            or payload.get("captain_id")
            or payload.get("offering_player_id")
            or payload.get("offering_team_id")
            or _get_current_captain_id(),
        },
    ),
    "accept_double": ("ACCEPT_DOUBLE", lambda payload: {"accepted": True}),
    "decline_double": ("ACCEPT_DOUBLE", lambda payload: {"accepted": False}),
    "concede_putt": ("CONCEDE_PUTT", lambda payload: payload or {}),
    "INITIALIZE_GAME": ("INITIALIZE_GAME", lambda payload: payload or {}),
}

UNIFIED_ACTION_TYPES = {
    "INITIALIZE_GAME",
    "PLAY_SHOT",
    "REQUEST_PARTNERSHIP",
    "RESPOND_PARTNERSHIP",
    "DECLARE_SOLO",
    "OFFER_DOUBLE",
    "ACCEPT_DOUBLE",
    "CONCEDE_PUTT",
    "ADVANCE_HOLE",
    "OFFER_BIG_DICK",
    "ACCEPT_BIG_DICK",
    "AARDVARK_JOIN_REQUEST",
    "AARDVARK_TOSS",
    "AARDVARK_GO_SOLO",
    "PING_PONG_AARDVARK",
    "INVOKE_JOES_SPECIAL",
    "GET_POST_HOLE_ANALYSIS",
    "ENTER_HOLE_SCORES",
    "GET_ADVANCED_ANALYTICS",
}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/create")
async def create_game_with_join_code(
    course_name: str | None = None,
    player_count: int = 4,
    user_id: str | None = None,
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """Create a new game with a join code for authenticated players"""
    try:
        import random
        import string
        import uuid

        # Generate 6-character join code
        join_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Ensure uniqueness
        while db.query(models.GameStateModel).filter(models.GameStateModel.join_code == join_code).first():
            join_code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

        # Create game with unique ID
        game_id = str(uuid.uuid4())
        current_time = datetime.now(UTC).isoformat()

        # Initial game state
        initial_state = {
            "current_hole": 1,
            "game_status": "setup",
            "player_count": player_count,
            "course_name": course_name,
            "players": [],
            "hole_history": [],
        }

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
            initial_state["holes_config"] = holes_config

        # Create GameStateModel
        game_state_model = models.GameStateModel(
            game_id=game_id,
            join_code=join_code,
            creator_user_id=user_id,
            game_status="setup",
            state=initial_state,
            created_at=current_time,
            updated_at=current_time,
        )
        db.add(game_state_model)
        db.commit()
        db.refresh(game_state_model)

        return {
            "game_id": game_id,
            "join_code": join_code,
            "status": "setup",
            "player_count": player_count,
            "players_joined": 0,
            "created_at": current_time,
            "join_url": f"/join/{join_code}",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating game: {e!s}")


@router.post("/join/{join_code}")
async def join_game_with_code(  # type: ignore
    join_code: str,
    request: schemas.JoinGameRequest,
    db: Session = Depends(database.get_db),
):
    """Join a game using a join code"""
    try:
        # Find game by join code
        game = db.query(models.GameStateModel).filter(models.GameStateModel.join_code == join_code).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found with that join code")

        if game.game_status != "setup":
            raise HTTPException(status_code=400, detail="Game has already started")

        # Check if user already joined
        if request.user_id:
            existing = (
                db.query(models.GamePlayer)
                .filter(
                    models.GamePlayer.game_id == game.game_id,
                    models.GamePlayer.user_id == request.user_id,
                )
                .first()
            )
            if existing:
                return {
                    "status": "already_joined",
                    "message": "You've already joined this game",
                    "game_id": game.game_id,
                    "player_slot_id": existing.player_slot_id,
                }

        # Get current players
        current_players = db.query(models.GamePlayer).filter(models.GamePlayer.game_id == game.game_id).all()

        # Check player limit
        max_players = game.state.get("player_count", 4)
        if len(current_players) >= max_players:
            raise HTTPException(status_code=400, detail="Game is full")

        # Assign player slot
        player_slot_id = f"p{len(current_players) + 1}"
        current_time = datetime.now(UTC).isoformat()

        # Ensure handicap is valid - use default if None
        player_handicap = request.handicap if request.handicap is not None else 18.0

        # Create GamePlayer record
        game_player = models.GamePlayer(
            game_id=game.game_id,
            player_slot_id=player_slot_id,
            user_id=request.user_id,
            player_profile_id=request.player_profile_id,
            player_name=request.player_name,
            handicap=player_handicap,
            join_status="joined",
            joined_at=current_time,
            created_at=current_time,
        )
        db.add(game_player)

        # Update game state with new player
        game.state["players"] = game.state.get("players", [])
        game.state["players"].append(
            {
                "id": player_slot_id,
                "name": request.player_name,
                "handicap": player_handicap,
                "user_id": request.user_id,
                "player_profile_id": request.player_profile_id,
            }
        )
        game.updated_at = current_time

        db.commit()
        db.refresh(game_player)

        return {
            "status": "joined",
            "game_id": game.game_id,
            "player_slot_id": player_slot_id,
            "players_joined": len(current_players) + 1,
            "max_players": max_players,
            "message": f"Welcome {request.player_name}! Waiting for {max_players - len(current_players) - 1} more player(s)",
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error joining game: {e!s}")


@router.get("/{game_id}/lobby")
async def get_game_lobby(game_id: str, db: Session = Depends(database.get_db)) -> dict[str, Any]:
    """Get game lobby information - who has joined"""
    try:
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        players = (
            db.query(models.GamePlayer)
            .filter(models.GamePlayer.game_id == game_id)
            .order_by(models.GamePlayer.player_slot_id)
            .all()
        )

        max_players = game.state.get("player_count", 4)

        return {
            "game_id": game_id,
            "join_code": game.join_code,
            "status": game.game_status,
            "course_name": game.state.get("course_name"),
            "max_players": max_players,
            "players_joined": len(players),
            "ready_to_start": len(players) >= 2 and len(players) <= max_players,
            "tee_order_set": game.state.get("tee_order_set", False),
            "players": [
                {
                    "player_slot_id": p.player_slot_id,
                    "player_name": p.player_name,
                    "handicap": p.handicap,
                    "is_authenticated": p.user_id is not None,
                    "join_status": p.join_status,
                    "joined_at": p.joined_at,
                    "tee_order": p.tee_order,
                }
                for p in players
            ],
            "created_at": game.created_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving game lobby: {e!s}")


@router.patch("/{game_id}/tee-order")
async def set_tee_order(
    game_id: str, request: dict[str, Any], db: Session = Depends(database.get_db)
) -> dict[str, Any]:
    """Set or update the tee order for the game at any time during gameplay"""
    try:
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        player_order = request.get("player_order", [])
        if not player_order:
            raise HTTPException(status_code=400, detail="player_order is required")

        # Validate all players exist and get them
        players = db.query(models.GamePlayer).filter(models.GamePlayer.game_id == game_id).all()

        player_dict = {p.player_slot_id: p for p in players}

        # Validate that all players in the game are in the order
        if len(player_order) != len(players):
            raise HTTPException(
                status_code=400,
                detail=f"player_order must include all {len(players)} players",
            )

        # Validate all player IDs exist
        for player_slot_id in player_order:
            if player_slot_id not in player_dict:
                raise HTTPException(status_code=400, detail=f"Invalid player_slot_id: {player_slot_id}")

        # Set tee_order field for each player (0 = first to tee, 1 = second, etc.)
        # This preserves player_slot_id and stores the tee order separately
        for tee_position, player_slot_id in enumerate(player_order):
            player = player_dict[player_slot_id]
            player.tee_order = tee_position

        # Mark tee order as set in game state
        game.state["tee_order_set"] = True
        game.updated_at = datetime.now(UTC)

        # Tell SQLAlchemy the JSON field has changed
        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(game, "state")

        db.commit()

        logger.info(f"Tee order set for game {game_id}: {player_order}")

        return {
            "status": "success",
            "message": "Tee order set successfully",
            "player_order": player_order,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error setting tee order: {e!s}")
        raise HTTPException(status_code=500, detail=f"Error setting tee order: {e!s}")


@router.post("/{game_id}/start")
async def start_game_from_lobby(game_id: str, db: Session = Depends(database.get_db)) -> dict[str, Any]:
    """Start a game from the lobby - initializes WGP simulation"""
    # MIGRATED: Using GameLifecycleService instead of global active_games

    try:
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        if game.game_status != "setup":
            raise HTTPException(status_code=400, detail="Game has already been started")

        # Check if tee order has been set
        if not game.state.get("tee_order_set", False):
            raise HTTPException(status_code=400, detail="Tee order must be set before starting the game")

        players = (
            db.query(models.GamePlayer)
            .filter(models.GamePlayer.game_id == game_id)
            .order_by(models.GamePlayer.tee_order)
            .all()
        )

        if len(players) < 2:
            raise HTTPException(status_code=400, detail="Need at least 2 players to start")

        # Create Player objects from database players
        wgp_players = []
        for p in players:
            # Ensure handicap is not None - default to 18.0 if missing
            player_handicap = p.handicap if p.handicap is not None else 18.0

            # Validate handicap range
            if player_handicap < 0 or player_handicap > 54:
                raise HTTPException(
                    status_code=400,
                    detail=f"Player {p.player_name} has invalid handicap {player_handicap}. Handicap must be between 0 and 54.",
                )

            wgp_player = Player(
                id=cast("str", p.player_slot_id),
                name=cast("str", p.player_name),
                handicap=cast("float", player_handicap),
            )
            wgp_players.append(wgp_player)

        # Initialize WolfGoatPigGame for this game
        # Use the configured player_count from game state, not actual number of players joined
        configured_player_count = game.state.get("player_count", 4)
        logger.info(
            f"Initializing WGP simulation for game {game_id} with {len(wgp_players)} players (configured for {configured_player_count})"
        )

        # Initialize course manager with selected course
        course_manager = None
        course_name = game.state.get("course_name")
        try:
            course_manager = CourseManager()
            if course_name:
                available_courses = course_manager.get_courses()
                if course_name in available_courses:
                    course_manager.load_course(course_name)
                    logger.info(f"Loaded course '{course_name}' for game {game_id}")
                else:
                    logger.warning(f"Course '{course_name}' not found. Using default course.")
                    # Do not set course_manager to None, let it use the default
            else:
                logger.info("No course name specified. Using default course.")
        except Exception as course_error:
            logger.error(f"Failed to load course '{course_name}': {course_error}")
            # Initialize a default course manager on error
            course_manager = CourseManager()

        try:
            # Create simulation with configured player count, actual players, and course manager
            simulation = WolfGoatPigGame(
                player_count=configured_player_count,
                players=wgp_players,
                course_manager=course_manager,
            )
            logger.info(f"Simulation initialized for game {game_id}")
        except Exception as init_error:
            logger.error(f"Failed to initialize simulation: {init_error}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize game: {init_error!s}")

        # MIGRATED: Store simulation using GameLifecycleService
        # Add to service cache (note: game was already created in DB, just adding to cache)
        get_game_lifecycle_service()._active_games[game_id] = simulation

        # Get initial game state from simulation
        initial_state = simulation.get_game_state()

        # Update database game state
        game.game_status = "in_progress"  # type: ignore
        game.updated_at = datetime.now(UTC).isoformat()  # type: ignore
        game.state = initial_state  # type: ignore
        game.state["game_status"] = "in_progress"
        game.state["started_at"] = game.updated_at
        game.state["game_id"] = game_id  # Track game_id in state

        db.commit()

        logger.info(f"Game {game_id} started successfully with {len(players)} players")

        # Send game start notifications to all players using NotificationService
        notification_service = get_notification_service()
        for player in players:
            if player.player_profile_id:  # Only send to registered players
                try:
                    notification_service.send_notification(
                        player_id=player.player_profile_id,
                        notification_type="game_start",
                        message=f"Game {game_id[:8]} has started with {len(players)} players!",
                        db=db,
                        data={"game_id": game_id, "player_count": len(players)},
                    )
                except Exception as notif_error:
                    logger.warning(
                        f"Failed to send game start notification to player {player.player_profile_id}: {notif_error}"
                    )

        return {
            "status": "started",
            "game_id": game_id,
            "message": f"Game started with {len(players)} players!",
            "players": [p.player_name for p in players],
            "game_state": initial_state,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error starting game {game_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting game: {e!s}")


@router.get("")
async def get_games(  # type: ignore
    status: str | None = Query(None, description="Filter by game status: setup, in_progress, completed"),
    creator_user_id: str | None = Query(None, description="Filter by creator user ID"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of games to return"),
    offset: int = Query(0, ge=0, description="Number of games to skip"),
    db: Session = Depends(database.get_db),
):
    """
    Get list of all games with optional filters.

    Filters:
    - status: Filter by game_status (setup, in_progress, completed)
    - creator_user_id: Filter by game creator
    - limit: Maximum results (1-100, default 20)
    - offset: Pagination offset (default 0)
    """
    try:
        # Build query
        query = db.query(models.GameStateModel)

        # Apply filters
        if status:
            query = query.filter(models.GameStateModel.game_status == status)

        if creator_user_id:
            query = query.filter(models.GameStateModel.creator_user_id == creator_user_id)

        # Order by created_at descending (newest first)
        query = query.order_by(models.GameStateModel.created_at.desc())

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination
        games = query.offset(offset).limit(limit).all()

        # Format response
        games_list = []
        for game in games:
            # Get player count
            player_count = db.query(models.GamePlayer).filter(models.GamePlayer.game_id == game.game_id).count()

            games_list.append(
                {
                    "game_id": game.game_id,
                    "join_code": game.join_code,
                    "game_status": game.game_status,
                    "creator_user_id": game.creator_user_id,
                    "player_count": player_count,
                    "created_at": game.created_at,
                    "updated_at": game.updated_at,
                }
            )

        return {
            "games": games_list,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count,
        }

    except Exception as e:
        logger.error(f"Error retrieving games: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving games: {e!s}")


@router.delete("/{game_id}")
async def delete_game(game_id: str, db: Session = Depends(database.get_db)):  # type: ignore
    """
    Delete a game and all associated data.

    This will remove:
    - The game state record
    - All player records for this game
    - Any game records and player results
    - The game from active games if it's currently running

    Args:
        game_id: The game ID to delete

    Returns:
        Success message with deletion details
    """
    try:
        # Check if game exists
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Remove from active games service if it's running
        service = get_game_lifecycle_service()
        if game_id in service._active_games:
            del service._active_games[game_id]
            logger.info(f"Removed game {game_id} from active games")

        # Delete all related game players
        players_deleted = db.query(models.GamePlayer).filter(models.GamePlayer.game_id == game_id).delete()

        # Delete game record if it exists
        game_record = db.query(models.GameRecord).filter(models.GameRecord.game_id == game_id).first()

        if game_record:
            # Delete player results for this game record
            db.query(models.GamePlayerResult).filter(models.GamePlayerResult.game_record_id == game_record.id).delete()

            # Delete the game record
            db.delete(game_record)

        # Delete the game state itself
        db.delete(game)
        db.commit()

        logger.info(f"Successfully deleted game {game_id} and {players_deleted} associated players")

        return {
            "success": True,
            "message": "Game deleted successfully",
            "game_id": game_id,
            "players_deleted": players_deleted,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting game {game_id}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error deleting game: {e!s}")


@router.post("/{game_id}/complete")
async def mark_game_complete(game_id: str, db: Session = Depends(database.get_db)):
    """
    Mark a game as completed.

    This endpoint is used to manually mark a game as complete when all 18 holes
    have been played but the status wasn't automatically updated.

    Args:
        game_id: The game ID to mark as complete

    Returns:
        Updated game information
    """
    try:
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        if game.game_status == "completed":
            return {
                "success": True,
                "message": "Game is already marked as completed",
                "game_id": game_id,
                "game_status": "completed",
            }

        if game.game_status == "setup":
            raise HTTPException(status_code=400, detail="Cannot complete a game that hasn't started yet")

        # Update game status to completed
        game.game_status = "completed"
        if game.state:
            game.state["game_status"] = "completed"

        db.commit()

        logger.info(f"Game {game_id} marked as completed")

        return {
            "success": True,
            "message": "Game marked as completed",
            "game_id": game_id,
            "game_status": "completed",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error completing game {game_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error completing game: {e!s}")


@router.get("/{game_id}/state")
async def get_game_state_by_id(game_id: str, db: Session = Depends(database.get_db)) -> dict[str, Any]:
    """Get current game state for a specific multiplayer game"""
    # MIGRATED: Using GameLifecycleService instead of global active_games

    try:
        # Check if game is in active games (in-progress) using service
        service = get_game_lifecycle_service()
        if game_id in service._active_games:
            simulation = service._active_games[game_id]
            state = simulation.get_game_state()
            state["game_id"] = game_id

            # Enrich players with tee_order from database
            db_players = db.query(models.GamePlayer).filter(models.GamePlayer.game_id == game_id).all()

            # Create a mapping of player_slot_id to tee_order
            tee_order_map = {p.player_slot_id: p.tee_order for p in db_players}

            # Add tee_order to each player in the state
            if "players" in state:
                for player in state["players"]:
                    player_id = player.get("id")
                    if player_id in tee_order_map:
                        player["tee_order"] = tee_order_map[player_id]

            return state

        # Otherwise, fetch from database
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # If game is completed, just return the saved state
        if game.game_status == "completed":
            return game.state  # type: ignore

        # If game is in setup, return lobby info
        if game.game_status == "setup":
            players = (
                db.query(models.GamePlayer)
                .filter(models.GamePlayer.game_id == game_id)
                .order_by(models.GamePlayer.player_slot_id)
                .all()
            )

            return {
                "game_id": game_id,
                "game_status": "setup",
                "players": [
                    {
                        "id": p.player_slot_id,
                        "name": p.player_name,
                        "handicap": p.handicap,
                        "tee_order": p.tee_order,
                    }
                    for p in players
                ],
                "message": "Game not started yet. Please start from lobby.",
            }

        # Game is in_progress but not in active_games (server restart?)
        # Return the saved state - SimpleScorekeeper works directly with game.state
        # The full simulation restoration happens lazily when /action is called
        logger.info(f"Game {game_id} is in_progress - returning saved state (simulation will restore on next action)")

        # Enrich with players from database
        saved_state = game.state.copy() if game.state else {}  # type: ignore
        saved_state["game_id"] = game_id
        saved_state["game_status"] = "in_progress"

        # Get players from database to ensure fresh data
        db_players = (
            db.query(models.GamePlayer)
            .filter(models.GamePlayer.game_id == game_id)
            .order_by(models.GamePlayer.tee_order)
            .all()
        )

        # Update players with database info including tee_order
        if db_players:
            player_map = {p.get("id"): p for p in saved_state.get("players", [])}
            enriched_players = []
            for db_player in db_players:
                existing = player_map.get(db_player.player_slot_id, {})
                enriched_players.append(
                    {
                        "id": db_player.player_slot_id,
                        "name": db_player.player_name,
                        "handicap": db_player.handicap,
                        "tee_order": db_player.tee_order,
                        "points": existing.get("points", 0),
                        "float_used": existing.get("float_used", 0),
                    }
                )
            saved_state["players"] = enriched_players

        return saved_state

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game state for {game_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving game state: {e!s}")


@router.post("/{game_id}/action")
async def perform_game_action_by_id(  # type: ignore
    game_id: str, action_request: ActionRequest, db: Session = Depends(database.get_db)
):
    """Perform an action on a specific multiplayer game"""
    # MIGRATED: Using GameLifecycleService instead of global active_games
    service = get_game_lifecycle_service()

    try:
        # Check if game is in active_games using service
        if game_id not in service._active_games:
            # Try to restore/reload game from database
            logger.warning(f"Game {game_id} not in active_games, attempting to restore from database...")

            game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

            if not game:
                raise HTTPException(status_code=404, detail="Game not found")

            if game.game_status == "completed":
                raise HTTPException(status_code=400, detail="Game is already completed")

            if game.game_status == "setup":
                raise HTTPException(status_code=400, detail="Game has not been started yet")

            # Restore game simulation from database
            # Get players from database in tee order
            players = (
                db.query(models.GamePlayer)
                .filter(models.GamePlayer.game_id == game_id)
                .order_by(models.GamePlayer.tee_order)
                .all()
            )

            # Create Player objects
            wgp_players = []
            for p in players:
                # Ensure handicap is not None - default to 18.0 if missing
                player_handicap = p.handicap if p.handicap is not None else 18.0

                wgp_player = Player(
                    id=cast("str", p.player_slot_id),
                    name=cast("str", p.player_name),
                    handicap=cast("float", player_handicap),
                )
                wgp_players.append(wgp_player)

            # Get configured player count from saved state
            configured_player_count = game.state.get("player_count", 4)

            # Initialize course manager with selected course
            course_manager = None
            course_name = game.state.get("course_name")
            if course_name:
                try:
                    course_manager = CourseManager()
                    available_courses = course_manager.get_courses()
                    if course_name in available_courses:
                        course_manager.load_course(course_name)
                        logger.info(f"Loaded course '{course_name}' for restored game {game_id}")
                    else:
                        logger.warning(f"Course '{course_name}' not found during game restoration")
                        course_manager = None
                except Exception as course_error:
                    logger.error(f"Failed to load course during restoration: {course_error}")
                    course_manager = None

            # Create new simulation with course manager
            simulation = WolfGoatPigGame(
                player_count=configured_player_count,
                players=wgp_players,
                course_manager=course_manager,
            )

            # Restore full game state from database
            saved_state = game.state or {}

            # Restore current hole
            simulation.current_hole = saved_state.get("current_hole", 1)

            # Restore player points and float usage
            saved_players = saved_state.get("players", [])
            for saved_player in saved_players:
                player_id = saved_player.get("id")
                sim_player = next((p for p in simulation.players if p.id == player_id), None)
                if sim_player:
                    sim_player.points = saved_player.get("points", 0)
                    sim_player.float_used = saved_player.get("float_used", 0)

            # Restore carry-over state (for push scenarios)
            simulation.carry_over_wager = saved_state.get("carry_over_wager")  # type: ignore
            simulation.carry_over_from_hole = saved_state.get("carry_over_from_hole")  # type: ignore
            simulation.consecutive_push_block = saved_state.get("consecutive_push_block", False)  # type: ignore
            simulation.last_push_hole = saved_state.get("last_push_hole")  # type: ignore
            simulation.base_wager = saved_state.get("base_wager")  # type: ignore

            # Restore hole history for SimpleScorekeeper compatibility
            simulation.scorekeeper_hole_history = saved_state.get("hole_history", [])  # type: ignore

            logger.info(
                f"Restored game {game_id} from database: "
                f"hole={simulation.current_hole}, "
                f"players={len(simulation.players)}, "
                f"hole_history={len(simulation.scorekeeper_hole_history)}"  # type: ignore
            )

            # MIGRATED: Add to active_games using service
            service._active_games[game_id] = simulation

        # MIGRATED: Get simulation from service
        simulation = service._active_games[game_id]

        # Use the existing unified action handler from wgp_actions router
        from .wgp_actions import unified_action

        # Call the unified action endpoint logic
        response = await unified_action(game_id, action_request, db)

        # Save state back to database after action
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if game:
            game.state = simulation.get_game_state()
            game.state["game_id"] = game_id
            game.updated_at = datetime.now(UTC).isoformat()

            # Check if game is completed
            if simulation.current_hole > 18:
                game.game_status = "completed"
                game.state["game_status"] = "completed"

            db.commit()
            logger.info(f"Saved state for game {game_id} after action {action_request.action_type}")

            # Broadcast the updated game state
            await websocket_manager.broadcast(json.dumps({"game_state": game.state}), game_id)

        return response

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error performing action on game {game_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error performing action: {e!s}")


@router.get("/history")
async def get_game_history(limit: int = 10, offset: int = 0, db: Session = Depends(database.get_db)) -> dict[str, Any]:
    """Get list of completed games"""
    try:
        games = (
            db.query(models.GameRecord)
            .order_by(models.GameRecord.completed_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return {
            "games": [
                {
                    "id": game.id,
                    "game_id": game.game_id,
                    "course_name": game.course_name,
                    "player_count": game.player_count,
                    "total_holes_played": game.total_holes_played,
                    "game_duration_minutes": game.game_duration_minutes,
                    "created_at": game.created_at,
                    "completed_at": game.completed_at,
                    "final_scores": game.final_scores,
                }
                for game in games
            ],
            "total": db.query(models.GameRecord).count(),
            "offset": offset,
            "limit": limit,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving game history: {e!s}")


@router.get("/{game_id}/details")
async def get_game_details(game_id: str, db: Session = Depends(database.get_db)) -> dict[str, Any]:
    """Get detailed game results including player performances and hole-by-hole scores"""
    try:
        # Get game record
        game = db.query(models.GameRecord).filter(models.GameRecord.game_id == game_id).first()
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        # Get player results
        player_results = (
            db.query(models.GamePlayerResult)
            .filter(models.GamePlayerResult.game_record_id == game.id)
            .order_by(models.GamePlayerResult.final_position)
            .all()
        )

        return {
            "game": {
                "id": game.id,
                "game_id": game.game_id,
                "course_name": game.course_name,
                "player_count": game.player_count,
                "total_holes_played": game.total_holes_played,
                "game_duration_minutes": game.game_duration_minutes,
                "created_at": game.created_at,
                "completed_at": game.completed_at,
                "game_settings": game.game_settings,
                "final_scores": game.final_scores,
            },
            "player_results": [
                {
                    "player_name": result.player_name,
                    "final_position": result.final_position,
                    "total_earnings": result.total_earnings,
                    "holes_won": result.holes_won,
                    "partnerships_formed": result.partnerships_formed,
                    "partnerships_won": result.partnerships_won,
                    "solo_attempts": result.solo_attempts,
                    "solo_wins": result.solo_wins,
                    "hole_scores": result.hole_scores,
                    "betting_history": result.betting_history,
                    "performance_metrics": result.performance_metrics,
                }
                for result in player_results
            ],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving game details: {e!s}")
