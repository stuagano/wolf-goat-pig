"""Game lifecycle routes — start, delete, complete (plus post-game badge checks)."""

import logging
import traceback
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.attributes import flag_modified

from .. import database, models
from ..badge_engine import BadgeEngine
from ..services.completed_game_service import validate_round_scores
from ..services.game_lifecycle_service import get_game_lifecycle_service
from ..services.notification_service import get_notification_service
from ..state.course_manager import CourseManager
from ..utils.admin_auth import require_admin
from ..utils.round_card import require_round_member_or_admin
from ..utils.time import utc_now
from ..wolf_goat_pig import Player, WolfGoatPigGame

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])


def _check_saved_game_achievements(sessions, game_id: str, record_id: int) -> None:
    """Best-effort side effect after saving; never reuse the score transaction."""
    try:
        with sessions() as badge_db:
            _check_game_achievements(badge_db, game_id, record_id)
    except Exception:
        logger.warning("Post-save badge processing failed for game %s", game_id)


def _check_game_achievements(db: Session, game_id: str, record_id: int) -> None:
    """Run post-game badge checks for all linked players. Never raises — failures are logged only."""
    try:
        game_players = (
            db.query(models.GamePlayer)
            .filter(
                models.GamePlayer.game_id == game_id,
                models.GamePlayer.player_profile_id.isnot(None),
            )
            .all()
        )
        if not game_players:
            return
        engine = BadgeEngine(db)
        for gp in game_players:
            try:
                earned = engine.check_post_game_achievements(record_id, int(gp.player_profile_id))
                if earned:
                    logger.info(
                        "🏅 Awarded %d badge(s) to player %d after game %s",
                        len(earned),
                        gp.player_profile_id,
                        game_id,
                    )
            except Exception as e:
                logger.error("Badge check failed for player %d: %s", gp.player_profile_id, e)
    except Exception as e:
        logger.error("_check_game_achievements failed for game %s: %s", game_id, e)


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

        # Build the initial game state from the simulation, then persist it. The
        # sim is a one-shot state generator — not cached (the /action engine that
        # used the cache was retired; the DB is the source of truth for /state).
        initial_state = simulation.get_game_state()
        # The simulation omits profile identity and handicap index from its players.
        lobby_players = {p.get("id"): p for p in (game.state or {}).get("players", [])}
        for sp in initial_state.get("players", []):
            lobby_player = lobby_players.get(sp.get("id"), {})
            sp["handicap_index"] = lobby_player.get("handicap_index")
            sp["player_profile_id"] = lobby_player.get("player_profile_id")

        # Update database game state
        game.game_status = "in_progress"  # type: ignore
        game.updated_at = utc_now().isoformat()  # type: ignore
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


@router.delete("/{game_id}", dependencies=[Depends(require_admin)])
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
        from app.services.canonical_round_reads import canonical_mode
        from app.services.round_cutover import guard_writer

        guard_writer(db)
        if canonical_mode(db):
            raise HTTPException(409, "Permanent round UUIDs cannot be deleted; use reviewed retraction")
        # Check if game exists under the transaction fence, retained until commit.
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


@router.post("/{game_id}/complete", dependencies=[Depends(require_round_member_or_admin)])
async def mark_game_complete(
    game_id: str, expected_epoch: int | None = Query(None), db: Session = Depends(database.get_db)
):
    """
    Mark a game as completed and persist results to GameRecord / GamePlayerResult.

    Extracts hole-by-hole data from the game state JSON and writes it to the
    permanent results tables so it's queryable by the Commissioner data explorer.
    """
    try:
        from ..services.round_cutover import guard_client_epoch

        guard_client_epoch(db, expected_epoch if isinstance(expected_epoch, int) else None)
        game = (
            db.query(models.GameStateModel).filter(models.GameStateModel.game_id == game_id).populate_existing().first()
        )

        if not game:
            raise HTTPException(status_code=404, detail="Game not found")

        validate_round_scores((game.state or {}).get("players", []), (game.state or {}).get("hole_history", []))

        if game.game_status == "completed":
            # Check if results were already persisted
            existing_record = db.query(models.GameRecord).filter(models.GameRecord.game_id == game_id).first()
            if existing_record:
                return {
                    "success": True,
                    "message": "Game is already marked as completed",
                    "game_id": game_id,
                    "game_status": "completed",
                    "revision": game.revision,
                    "status": "unchanged",
                    "issue_ids": [],
                }
            # Fall through to persist results for previously completed games
            logger.info("Game %s was completed but has no GameRecord — backfilling", game_id)

        if game.game_status == "setup":
            raise HTTPException(status_code=400, detail="Cannot complete a game that hasn't started yet")

        state = game.state or {}
        players = state.get("players", [])
        hole_history = state.get("hole_history", [])
        hole_quarters = state.get("hole_quarters", {})

        # Derive standings from hole_history if not present
        standings = state.get("standings", {})
        if not standings and hole_history:
            for entry in hole_history:
                for pid, q in entry.get("points_delta", {}).items():
                    standings[pid] = standings.get(pid, 0) + q

        # Update game status
        game.game_status = "completed"
        state["game_status"] = "completed"
        game.state = state
        # state is the same dict object as game.state — reassigning doesn't mark
        # the JSON column dirty. Without this the blob's game_status/standings
        # wouldn't persist (only the scalar game.game_status column would).
        flag_modified(game, "state")

        from ..services.completed_game_service import persist_completed_game

        results_created = persist_completed_game(db, game)
        record_id = db.query(models.GameRecord).filter(models.GameRecord.game_id == game_id).first().id

        logger.info(
            "Game %s completed: %d players, %d holes, %d results created",
            game_id,
            len(players),
            len(hole_quarters),
            results_created,
        )

        # Snapshot IDs/factory before commit; source ORM session is never read
        # afterwards. BadgeEngine owns separate best-effort transactions.
        badge_sessions = sessionmaker(bind=db.get_bind())
        saved_game_id = str(game.game_id)
        saved_revision = game.revision
        db.commit()
        _check_saved_game_achievements(badge_sessions, saved_game_id, record_id)

        return {
            "success": True,
            "message": "Game marked as completed",
            "game_id": game_id,
            "game_status": "completed",
            "results_created": results_created,
            "revision": saved_revision,
            "status": "accepted",
            "issue_ids": [],
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error completing game {game_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error completing game: {e!s}")
