"""Game read routes — list games, game state, history, details."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import database, models
from ..schemas.round_identity import RoundSummary
from ..services.completed_game_service import round_played_at

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])


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

        # Resolve persisted round dates in one query for the current page.
        records = (
            db.query(models.GameRecord).filter(models.GameRecord.game_id.in_([game.game_id for game in games])).all()
            if games
            else []
        )
        records_by_game = {record.game_id: record for record in records}

        # Format response
        games_list = []
        for game in games:
            # Get player count
            player_count = db.query(models.GamePlayer).filter(models.GamePlayer.game_id == game.game_id).count()
            record = records_by_game.get(game.game_id)
            played_at = (
                round_played_at(record, game)
                if record is not None
                else (game.state or {}).get("played_at") or game.created_at
            )

            games_list.append(
                {
                    "game_id": game.game_id,
                    "join_code": game.join_code,
                    "game_status": game.game_status,
                    "creator_user_id": game.creator_user_id,
                    "player_count": player_count,
                    "created_at": game.created_at,
                    "updated_at": game.updated_at,
                    "played_at": played_at,
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


@router.get("/{game_id}/round-summary", response_model=RoundSummary)
def get_round_summary(game_id: str, db: Session = Depends(database.get_db)):
    """Accepted final results and actual detail on the permanent UUID."""
    from ..services.round_review import round_summary

    return round_summary(db, game_id)


@router.get("/{game_id}/state")
async def get_game_state_by_id(game_id: str, db: Session = Depends(database.get_db)) -> dict[str, Any]:
    """Get current game state for a specific multiplayer game.

    The database is the single source of truth. (The old in-memory simulation
    cache was removed — it was the source of the split-brain where scorekeeper
    writes landed in the DB but /state served a stale sim. The SimpleScorekeeper
    computes rules client-side and persists via /scores, so the server engine is
    no longer in the read path.)
    """
    try:
        # Fetch from database
        game = db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).first()

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        from ..schemas.round_identity import read_round_identity_config

        writer_epoch = read_round_identity_config(db).epoch
        # If game is completed, just return the saved state
        if game.game_status == "completed":
            return {
                **(game.state or {}),
                "game_id": game_id,
                "game_status": "completed",
                "revision": game.revision,
                "writer_epoch": writer_epoch,
            }

        # If game is in setup, return lobby info
        if game.game_status == "setup":
            lobby_index = {p.get("id"): p.get("handicap_index") for p in (game.state or {}).get("players", [])}
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
                        "handicap_index": lobby_index.get(p.player_slot_id),
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
        saved_state["revision"] = game.revision
        saved_state["writer_epoch"] = writer_epoch
        saved_state["game_status"] = "in_progress"

        # Get players from database to ensure fresh data
        db_players = (
            db.query(models.GamePlayer)
            .filter(models.GamePlayer.game_id == game_id)
            .order_by(models.GamePlayer.tee_order)
            .all()
        )

        # Update players with database info including tee_order. Preserve the
        # blob's player fields and overlay fresh DB values. is_authenticated /
        # is_ghost follow the lobby convention (user_id is not None) — Stuart
        # Mode in the scorekeeper relies on these, so the DB path MUST set them
        # (it previously dropped them, which broke ghost games on reload).
        if db_players:
            player_map = {p.get("id"): p for p in saved_state.get("players", [])}
            enriched_players = []
            for db_player in db_players:
                existing = player_map.get(db_player.player_slot_id, {})
                authenticated = db_player.user_id is not None
                enriched_players.append(
                    {
                        **existing,
                        "id": db_player.player_slot_id,
                        "name": db_player.player_name,
                        "handicap": db_player.handicap,
                        "tee_order": db_player.tee_order,
                        "points": existing.get("points", 0),
                        "float_used": existing.get("float_used", 0),
                        "is_authenticated": authenticated,
                        "is_ghost": not authenticated,
                    }
                )
            saved_state["players"] = enriched_players

        return saved_state

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game state for {game_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving game state: {e!s}")
