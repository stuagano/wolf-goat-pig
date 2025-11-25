"""
Persistence Mixin for Wolf Goat Pig Game State

Provides database save/load functionality that can be mixed into any game engine class.
Extracted from GameState to enable persistence in WolfGoatPigGame.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, cast

from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import GamePlayerResult, GameRecord, GameStateModel


class PersistenceMixin:
    """
    Mixin that adds database persistence capabilities to a game engine.

    Required attributes on the class using this mixin:
    - game_id: str
    - Any game state attributes you want to persist

    Required methods to implement:
    - _serialize() -> Dict[str, Any]: Convert game state to JSON-serializable dict
    - _deserialize(data: Dict[str, Any]): Restore game state from dict
    """

    def __init_persistence__(self, game_id: Optional[str] = None) -> None:
        """
        Initialize persistence layer. Call this from your __init__.

        Args:
            game_id: Optional game ID. If None, generates new UUID.
        """
        self.game_id = game_id or str(uuid.uuid4())
        self._db_session: Session = SessionLocal()
        self._game_start_time = datetime.now(timezone.utc).isoformat()
        self._game_completed = False

        # Try to load existing game from DB
        self._load_from_db()

    def _save_to_db(self):
        """
        Save the current game state as JSON in the database.

        Uses game_id as unique identifier. Creates new record if not exists,
        otherwise updates existing record.

        Gracefully handles DB failures - game continues in memory if DB is down.
        """
        try:
            state_json = self._serialize()
            session = self._db_session

            # Find existing game by game_id
            obj = session.query(GameStateModel).filter(
                GameStateModel.game_id == self.game_id
            ).first()

            current_time = datetime.now(timezone.utc).isoformat()

            if obj:
                # Update existing - use setattr to avoid Column type errors
                setattr(obj, 'state', state_json)
                setattr(obj, 'updated_at', current_time)
            else:
                # Create new
                obj = GameStateModel(
                    game_id=self.game_id,
                    state=state_json,
                    created_at=self._game_start_time,
                    updated_at=current_time
                )
                session.add(obj)

            session.commit()

        except Exception as e:
            print(f"⚠️ Database save failed for game {self.game_id}: {e}")
            # Continue without saving - allows app to work even if DB is down
            if hasattr(self, '_db_session'):
                try:
                    self._db_session.rollback()
                except:
                    pass

    def _load_from_db(self):
        """
        Load game state from database by game_id.

        If game exists in DB, deserializes and restores all state.
        If game doesn't exist, this is a new game (no-op).

        Gracefully handles DB failures - starts fresh game if DB is down.
        """
        try:
            session = self._db_session

            # Try to load by game_id
            obj = session.query(GameStateModel).filter(
                GameStateModel.game_id == self.game_id
            ).first()

            if obj and obj.state:
                # Restore state from DB - cast to proper type
                state_data = cast(Dict[str, Any], obj.state)
                self._deserialize(state_data)

                # Preserve DB metadata - use str() to convert Column types
                self.game_id = str(obj.game_id)
                self._game_start_time = str(obj.created_at)
            else:
                # New game - keep generated game_id, start fresh
                pass

        except Exception as e:
            print(f"⚠️ Database load failed for game {self.game_id}: {e}")
            # Fall back to new game state if DB is unavailable
            pass

    def _serialize(self) -> Dict[str, Any]:
        """
        Convert game state to JSON-serializable dictionary.

        MUST BE IMPLEMENTED BY SUBCLASS.

        Returns:
            Dict containing all game state that should be persisted
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _serialize()"
        )

    def _deserialize(self, data: Dict[str, Any]) -> None:
        """
        Restore game state from dictionary.

        MUST BE IMPLEMENTED BY SUBCLASS.

        Args:
            data: Dictionary from _serialize() containing game state
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _deserialize(data)"
        )

    def complete_game(self) -> str:
        """
        Mark game as completed and save permanent results to database.

        Creates a GameRecord with final scores and game statistics.
        This is separate from the in-progress state saves.

        Returns:
            Success message or error description
        """
        if self._game_completed:
            return "Game already completed"

        try:
            session = self._db_session
            current_time = datetime.now(timezone.utc).isoformat()

            # Calculate game duration
            start_time = datetime.fromisoformat(self._game_start_time)
            end_time = datetime.now(timezone.utc)
            duration_minutes = int((end_time - start_time).total_seconds() / 60)

            # Get final scores - subclass must provide this via _get_final_scores()
            if hasattr(self, '_get_final_scores'):
                final_scores = self._get_final_scores()
            else:
                final_scores = {}

            # Get game metadata
            game_metadata = self._get_game_metadata() if hasattr(self, '_get_game_metadata') else {}

            # Create permanent GameRecord
            game_record = GameRecord(
                game_id=self.game_id,
                course_name=game_metadata.get('course_name', 'Unknown Course'),
                game_mode="wolf_goat_pig",
                player_count=game_metadata.get('player_count', 4),
                total_holes_played=game_metadata.get('total_holes_played', 0),
                game_duration_minutes=duration_minutes,
                created_at=self._game_start_time,
                completed_at=current_time,
                game_settings=game_metadata.get('settings', {}),
                final_scores=final_scores
            )

            session.add(game_record)

            # Create individual player results if subclass provides player data
            if hasattr(self, '_get_player_results'):
                for player_result in self._get_player_results():
                    session.add(GamePlayerResult(**player_result, game_record_id=game_record.id))

            session.commit()

            self._game_completed = True
            self._save_to_db()  # Save completion status

            return f"Game {self.game_id} completed successfully"

        except Exception as e:
            print(f"⚠️ Failed to complete game {self.game_id}: {e}")
            if hasattr(self, '_db_session'):
                try:
                    self._db_session.rollback()
                except:
                    pass
            return f"Failed to complete game: {str(e)}"

    def close_db_session(self):
        """Close the database session. Call this when done with the game."""
        if hasattr(self, '_db_session') and self._db_session:
            try:
                self._db_session.close()
            except:
                pass
