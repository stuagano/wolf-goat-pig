"""
Fallback Game Manager

Provides in-memory game state management when database is unavailable.
This allows the API to continue working even if database migrations fail
or the database is temporarily unavailable.
"""

import logging
import random
import string
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class FallbackGameManager:
    """
    In-memory game state manager for fallback mode.

    When the database is unavailable or has schema issues, this manager
    keeps games in memory to allow the application to continue functioning.
    """

    def __init__(self):
        self.games: Dict[str, dict] = {}
        self.games_by_join_code: Dict[str, str] = {}  # join_code -> game_id
        self.enabled = False
        logger.info("Fallback Game Manager initialized")

    def enable(self):
        """Enable fallback mode."""
        self.enabled = True
        logger.warning("⚠️ FALLBACK MODE ENABLED - Games will be stored in memory only")
        logger.warning("⚠️ All games will be lost if the server restarts!")

    def disable(self):
        """Disable fallback mode."""
        self.enabled = False
        self.games.clear()
        self.games_by_join_code.clear()
        logger.info("Fallback mode disabled, memory cleared")

    def generate_join_code(self) -> str:
        """Generate a unique 6-character join code."""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if code not in self.games_by_join_code:
                return code

    def create_game(
        self,
        game_id: str,
        join_code: Optional[str] = None,
        creator_user_id: Optional[str] = None,
        game_status: str = "setup",
        state: Optional[dict] = None
    ) -> dict:
        """Create a new game in memory."""
        if not self.enabled:
            raise RuntimeError("Fallback mode is not enabled")

        if not join_code:
            join_code = self.generate_join_code()

        now = datetime.utcnow().isoformat()

        game = {
            "id": len(self.games) + 1,  # Auto-increment ID
            "game_id": game_id,
            "join_code": join_code,
            "creator_user_id": creator_user_id,
            "game_status": game_status,
            "state": state or {},
            "created_at": now,
            "updated_at": now,
            "fallback_mode": True
        }

        self.games[game_id] = game
        self.games_by_join_code[join_code] = game_id

        logger.info(f"Created fallback game: {game_id} (join code: {join_code})")
        return game

    def get_game(self, game_id: str) -> Optional[dict]:
        """Get a game by ID."""
        return self.games.get(game_id)

    def get_game_by_join_code(self, join_code: str) -> Optional[dict]:
        """Get a game by join code."""
        game_id = self.games_by_join_code.get(join_code)
        if game_id:
            return self.games.get(game_id)
        return None

    def update_game(self, game_id: str, updates: dict) -> Optional[dict]:
        """Update a game's state."""
        game = self.games.get(game_id)
        if not game:
            return None

        # Update fields
        for key, value in updates.items():
            if key != 'id' and key != 'game_id':  # Don't allow changing these
                game[key] = value

        game['updated_at'] = datetime.utcnow().isoformat()

        logger.debug(f"Updated fallback game: {game_id}")
        return game

    def delete_game(self, game_id: str) -> bool:
        """Delete a game from memory."""
        game = self.games.get(game_id)
        if not game:
            return False

        # Remove from join code mapping
        if game.get('join_code'):
            self.games_by_join_code.pop(game['join_code'], None)

        # Remove game
        del self.games[game_id]

        logger.info(f"Deleted fallback game: {game_id}")
        return True

    def list_games(self, limit: int = 100) -> List[dict]:
        """List all games in memory."""
        games = list(self.games.values())
        return games[:limit]

    def get_stats(self) -> dict:
        """Get statistics about fallback mode."""
        return {
            "enabled": self.enabled,
            "total_games": len(self.games),
            "games": list(self.games.keys()),
            "warning": "Games are stored in memory only and will be lost on restart" if self.enabled else None
        }


# Global fallback manager instance
fallback_manager = FallbackGameManager()


def get_fallback_manager() -> FallbackGameManager:
    """Get the global fallback manager instance."""
    return fallback_manager
