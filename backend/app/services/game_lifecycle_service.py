"""
Game Lifecycle Management Service

This service handles all game lifecycle operations including:
- Game creation and initialization
- Game retrieval from cache or database
- Game state transitions (start, pause, resume, complete)
- Active games management
- Game cleanup operations
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import GameStateModel
from ..wolf_goat_pig import Player, WolfGoatPigGame

logger = logging.getLogger(__name__)


class GameLifecycleService:
    """
    Service class for managing Wolf Goat Pig game lifecycle operations.

    This service centralizes all game management logic including creation,
    retrieval, state transitions, and cleanup. It maintains an in-memory
    cache of active games for performance while persisting all changes to
    the database.

    Uses singleton pattern to ensure consistent state management across
    the application.
    """

    _instance = None

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(GameLifecycleService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the service with empty active games cache."""
        if self._initialized:
            return

        self._active_games: Dict[str, WolfGoatPigGame] = {}
        self._initialized = True
        logger.info("GameLifecycleService initialized")

    def create_game(
        self,
        db: Session,
        player_count: int,
        players: List[Player],
        course_name: Optional[str] = None,
        base_wager: Optional[float] = None,
        join_code: Optional[str] = None,
        creator_user_id: Optional[str] = None
    ) -> Tuple[str, WolfGoatPigGame]:
        """
        Create a new Wolf Goat Pig game.

        This method creates a new game with a unique ID, initializes the
        simulation with the provided players, and persists the initial
        game state to the database.

        Args:
            db: Database session for persistence
            player_count: Number of players (4-6)
            players: List of Player objects representing game participants
            course_name: Optional name of the golf course
            base_wager: Optional base wager amount in quarters (default: 1)
            join_code: Optional join code for multiplayer games
            creator_user_id: Optional Auth0 user ID of game creator

        Returns:
            Tuple of (game_id: str, simulation: WolfGoatPigGame)

        Raises:
            HTTPException: If game creation fails
            ValueError: If invalid parameters are provided
        """
        try:
            # Validate inputs
            if not 4 <= player_count <= 6:
                raise ValueError("player_count must be between 4 and 6")

            if len(players) != player_count:
                raise ValueError(f"Expected {player_count} players, got {len(players)}")

            # Generate unique game ID
            game_id = str(uuid.uuid4())
            current_time = datetime.now(timezone.utc).isoformat()

            logger.info(f"Creating new game {game_id} with {player_count} players")

            # Initialize game engine
            game = WolfGoatPigGame(
                game_id=game_id,
                player_count=len(players),
                players=players
            )

            # Set optional parameters
            if base_wager is not None:
                game.betting_state.base_wager = base_wager # Changed from simulation to game
                game.betting_state.current_wager = base_wager # Changed from simulation to game

            # Prepare initial game state for database
            initial_state = {
                "game_status": "setup",
                "player_count": player_count,
                "players": [
                    {
                        "id": p.id,
                        "name": p.name,
                        "handicap": p.handicap,
                        "points": p.points
                    }
                    for p in players
                ],
                "course_name": course_name,
                "base_wager": base_wager or 1,
                "created_at": current_time
            }

            # Create database record
            game_record = GameStateModel(
                game_id=game_id,
                join_code=join_code,
                creator_user_id=creator_user_id,
                state=initial_state,
                game_status="setup",
                created_at=current_time,
                updated_at=current_time
            )

            db.add(game_record)
            db.commit()
            db.refresh(game_record)

            # Add to active games cache
            self._active_games[game_id] = game

            logger.info(f"Successfully created game {game_id}")
            return game_id, game

        except ValueError as e:
            logger.error(f"Validation error creating game: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating game: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create game: {str(e)}"
            )

    def get_game(self, db: Session, game_id: str) -> WolfGoatPigGame:
        """
        Get a game simulation instance by game ID.

        This method first checks the active games cache for performance.
        If not found in cache, it attempts to load the game from the
        database and adds it to the cache.

        Args:
            db: Database session for loading from persistence
            game_id: Unique game identifier

        Returns:
            WolfGoatPigGame instance for the game

        Raises:
            HTTPException: If game not found or loading fails
        """
        try:
            # Check cache first
            if game_id in self._active_games:
                logger.debug(f"Loading game {game_id} from cache")
                return self._active_games[game_id]

            # Load from database
            logger.info(f"Game {game_id} not in cache, loading from database")

            game_record = db.query(GameStateModel).filter(
                GameStateModel.game_id == game_id
            ).first()

            if not game_record:
                logger.warning(f"Game {game_id} not found in database")
                raise HTTPException(
                    status_code=404,
                    detail=f"Game {game_id} not found"
                )

            # Reconstruct simulation from database state
            # Initialize game engine (will load state from DB via PersistenceMixin)
            game = WolfGoatPigGame(game_id=game_id)

            # Verify the game was loaded successfully
            if not hasattr(game, '_loaded_from_db') or not game._loaded_from_db:
                logger.error(f"Failed to load game {game_id} from database")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to load game {game_id}"
                )

            # Add to cache
            self._active_games[game_id] = game
            logger.info(f"Successfully loaded game {game_id} from database")

            return game

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving game {game_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error loading game: {str(e)}"
            )

    def start_game(self, db: Session, game_id: str) -> WolfGoatPigGame:
        """
        Start a game that is in setup state.

        This transitions the game from 'setup' to 'in_progress' status,
        indicating that gameplay has begun. This is typically called after
        all players have joined and the game is ready to start.

        Args:
            db: Database session for persistence
            game_id: Unique game identifier

        Returns:
            Updated WolfGoatPigGame instance

        Raises:
            HTTPException: If game not found or already started
        """
        try:
            # Get the game
            game = self.get_game(db, game_id)

            # Get the database record
            game_record = db.query(GameStateModel).filter(
                GameStateModel.game_id == game_id
            ).first()

            if not game_record:
                raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

            # Validate state transition
            if game_record.game_status != "setup":
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot start game in '{game_record.game_status}' status"
                )

            # Update status
            game_record.game_status = "in_progress"
            game_record.state["game_status"] = "in_progress"
            game_record.updated_at = datetime.now(timezone.utc).isoformat()

            db.commit()

            logger.info(f"Started game {game_id}")
            return game

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error starting game {game_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start game: {str(e)}"
            )

    def pause_game(self, db: Session, game_id: str) -> WolfGoatPigGame:
        """
        Pause an active game.

        This transitions the game to a 'paused' state, allowing players
        to take a break without losing game progress.

        Args:
            db: Database session for persistence
            game_id: Unique game identifier

        Returns:
            Updated WolfGoatPigGame instance

        Raises:
            HTTPException: If game not found or not in progress
        """
        try:
            # Get the game
            game = self.get_game(db, game_id)

            # Get the database record
            game_record = db.query(GameStateModel).filter(
                GameStateModel.game_id == game_id
            ).first()

            if not game_record:
                raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

            # Validate state transition
            if game_record.game_status != "in_progress":
                raise HTTPException(
                    status_code=400,
                    detail="Can only pause games that are in progress"
                )

            # Update status
            game_record.game_status = "paused"
            game_record.state["game_status"] = "paused"
            game_record.updated_at = datetime.now(timezone.utc).isoformat()

            db.commit()

            logger.info(f"Paused game {game_id}")
            return game

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error pausing game {game_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to pause game: {str(e)}"
            )

    def resume_game(self, db: Session, game_id: str) -> WolfGoatPigGame:
        """
        Resume a paused game.

        This transitions a paused game back to 'in_progress' status,
        allowing gameplay to continue.

        Args:
            db: Database session for persistence
            game_id: Unique game identifier

        Returns:
            Updated WolfGoatPigGame instance

        Raises:
            HTTPException: If game not found or not paused
        """
        try:
            # Get the game
            game = self.get_game(db, game_id)

            # Get the database record
            game_record = db.query(GameStateModel).filter(
                GameStateModel.game_id == game_id
            ).first()

            if not game_record:
                raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

            # Validate state transition
            if game_record.game_status != "paused":
                raise HTTPException(
                    status_code=400,
                    detail="Can only resume games that are paused"
                )

            # Update status
            game_record.game_status = "in_progress"
            game_record.state["game_status"] = "in_progress"
            game_record.updated_at = datetime.now(timezone.utc).isoformat()

            db.commit()

            logger.info(f"Resumed game {game_id}")
            return game

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error resuming game {game_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to resume game: {str(e)}"
            )

    def complete_game(self, db: Session, game_id: str) -> Dict[str, Any]:
        """
        Mark a game as complete and return final statistics.

        This transitions the game to 'completed' status and generates
        a summary of the final game state including scores, earnings,
        and player statistics.

        Args:
            db: Database session for persistence
            game_id: Unique game identifier

        Returns:
            Dictionary containing final game statistics and results

        Raises:
            HTTPException: If game not found or already completed
        """
        try:
            # Get the game
            game = self.get_game(db, game_id)

            # Get the database record
            game_record = db.query(GameStateModel).filter(
                GameStateModel.game_id == game_id
            ).first()

            if not game_record:
                raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

            # Validate state transition
            if game_record.game_status == "completed":
                logger.info(f"Game {game_id} already completed")
                # Return existing stats instead of error

            # Gather final statistics
            final_stats = {
                "game_id": game_id,
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "final_scores": {},
                "total_holes_played": game.current_hole - 1 if hasattr(game, 'current_hole') else 0,
                "course_name": game_record.state.get("course_name"),
                "base_wager": game_record.state.get("base_wager", 1)
            }

            # Extract player results
            if hasattr(game, 'players'):
                for player in game.players:
                    final_stats["final_scores"][player.id] = {
                        "name": player.name,
                        "points": player.points,
                        "handicap": player.handicap
                    }

            # Update database record
            game_record.game_status = "completed"
            game_record.state["game_status"] = "completed"
            game_record.state["final_stats"] = final_stats
            game_record.updated_at = datetime.now(timezone.utc).isoformat()

            db.commit()

            logger.info(f"Completed game {game_id}")
            return final_stats

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error completing game {game_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to complete game: {str(e)}"
            )

    def list_active_games(self) -> List[str]:
        """
        Get a list of all active game IDs currently in cache.

        This returns only games that are currently loaded in memory,
        not all games in the database.

        Returns:
            List of game ID strings
        """
        game_ids = list(self._active_games.keys())
        logger.debug(f"Listing {len(game_ids)} active games")
        return game_ids

    def cleanup_game(self, game_id: str) -> None:
        """
        Remove a game from the active games cache.

        This removes the game from memory but does not delete it from
        the database. The game can be reloaded later if needed.
        This is useful for memory management with long-running servers.

        Args:
            game_id: Unique game identifier
        """
        if game_id in self._active_games:
            del self._active_games[game_id]
            logger.info(f"Cleaned up game {game_id} from cache")
        else:
            logger.debug(f"Game {game_id} not in cache, nothing to clean up")

    def cleanup_all_games(self) -> int:
        """
        Remove all games from the active games cache.

        This is useful for testing or when performing maintenance.
        Games remain in the database and can be reloaded as needed.

        Returns:
            Number of games cleaned up
        """
        count = len(self._active_games)
        self._active_games.clear()
        logger.info(f"Cleaned up {count} games from cache")
        return count


# Singleton accessor function
_service_instance = None


def get_game_lifecycle_service() -> GameLifecycleService:
    """
    Get the singleton GameLifecycleService instance.

    This function provides access to the shared service instance,
    creating it if it doesn't exist yet.

    Returns:
        GameLifecycleService singleton instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = GameLifecycleService()
    return _service_instance
