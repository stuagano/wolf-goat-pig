"""Game setup routes — create, join, lobby, tee order."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from .. import database, models, schemas
from ..utils.handicap_resolve import find_course, resolve_player_handicap, to_course_handicap
from ..utils.time import utc_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])


class SetTeeOrderRequest(BaseModel):
    player_order: list[str] = Field(..., min_length=1)


@router.post("/create")
async def create_game_with_join_code(
    course_name: str | None = None,
    player_count: int = 4,
    user_id: str | None = None,
    db: Session = Depends(database.get_db),
) -> dict[str, Any]:
    """Create a new game with a join code for authenticated players"""
    if player_count not in (4, 5, 6):
        raise HTTPException(status_code=400, detail="Wolf Goat Pig requires 4, 5, or 6 players")
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
        current_time = utc_now().isoformat()

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
        current_time = utc_now().isoformat()

        # Explicit handicap always wins. Otherwise fill from the roster — never
        # let a silent 18 stand in for a rostered scratch player.
        handicap_was_omitted = request.handicap is None
        player_handicap, profile = resolve_player_handicap(
            db,
            name=request.player_name,
            handicap=request.handicap,
            player_profile_id=request.player_profile_id,
        )
        resolved_profile_id = int(profile.id) if profile is not None else request.player_profile_id
        handicap_source = "manual" if not handicap_was_omitted else ("profile" if profile else "manual")

        # GHIN sync only when the client omitted a handicap — an explicit course
        # handicap for the round must not be overwritten by a GHIN index.
        if handicap_was_omitted and profile is not None and profile.ghin_id:
            try:
                from ..services.ghin_service import GHINService

                ghin = GHINService(db)
                if await ghin.initialize():
                    result = await ghin.sync_player_handicap(int(profile.id))
                    if result and result.get("handicap_index") is not None:
                        player_handicap = float(result["handicap_index"])
                        handicap_source = "ghin"
                        logger.info("GHIN handicap for %s: %.1f", request.player_name, player_handicap)
            except Exception as ghin_err:
                logger.warning("GHIN lookup failed for %s: %s", request.player_name, ghin_err)

        # A roster/GHIN index plays off the course handicap (strokes use it); a
        # typed handicap is already the course handicap and stays as-is.
        handicap_index = None
        if handicap_was_omitted and (
            handicap_source == "ghin" or (profile is not None and profile.handicap is not None)
        ):
            handicap_index = player_handicap
            player_handicap = to_course_handicap(handicap_index, find_course(game.state.get("course_name")))

        # Create GamePlayer record
        game_player = models.GamePlayer(
            game_id=game.game_id,
            player_slot_id=player_slot_id,
            user_id=request.user_id,
            player_profile_id=resolved_profile_id,
            player_name=request.player_name,
            handicap=player_handicap,
            join_status="joined",
            joined_at=current_time,
            created_at=current_time,
        )
        db.add(game_player)

        # Update game state with new player. Build the list and reassign the
        # top-level key (not .append on the nested list) so MutableDict tracks it.
        players = list(game.state.get("players", []))
        players.append(
            {
                "id": player_slot_id,
                "name": request.player_name,
                "handicap": player_handicap,
                "handicap_index": handicap_index,
                "user_id": request.user_id,
                "player_profile_id": resolved_profile_id,
            }
        )
        game.state["players"] = players
        game.updated_at = current_time

        flag_modified(game, "state")
        db.commit()
        db.refresh(game_player)

        return {
            "status": "joined",
            "game_id": game.game_id,
            "player_slot_id": player_slot_id,
            "handicap": player_handicap,
            "handicap_index": handicap_index,
            "handicap_source": handicap_source,
            "player_profile_id": resolved_profile_id,
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
    game_id: str, request: SetTeeOrderRequest, db: Session = Depends(database.get_db)
) -> dict[str, Any]:
    """Set or update the tee order for the game at any time during gameplay"""
    try:
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        player_order = request.player_order

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
        game.updated_at = utc_now()

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
