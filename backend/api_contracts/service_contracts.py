"""
Service Layer Contracts

Protocol definitions for all service classes. These define the expected
interface that each service must implement.
"""

from typing import Protocol, Dict, Any, List, Optional
from sqlalchemy.orm import Session


class GameLifecycleServiceProtocol(Protocol):
    """Contract for GameLifecycleService.

    Defines the interface for game lifecycle management including
    creation, retrieval, state transitions, and cleanup.
    """

    def create_game(
        self,
        db: Session,
        player_count: int,
        players: List[Dict[str, Any]],
        course_name: str,
        rules: Optional[List[str]] = None,
        join_code: Optional[str] = None
    ) -> tuple[str, Any]:
        """Create a new game instance.

        Args:
            db: Database session
            player_count: Number of players (4 or 6)
            players: List of player configurations
            course_name: Name of the course to play
            rules: Optional list of special rules
            join_code: Optional multiplayer join code

        Returns:
            Tuple of (game_id, game_instance)
        """
        ...

    def get_game(self, db: Session, game_id: str) -> Any:
        """Get game from cache or database.

        Args:
            db: Database session
            game_id: Unique game identifier

        Returns:
            Game simulation instance

        Raises:
            HTTPException: If game not found
        """
        ...

    def start_game(self, db: Session, game_id: str) -> Dict[str, Any]:
        """Start a game (transition from setup to in_progress).

        Args:
            db: Database session
            game_id: Unique game identifier

        Returns:
            Updated game state
        """
        ...

    def pause_game(self, db: Session, game_id: str) -> Dict[str, Any]:
        """Pause an active game."""
        ...

    def resume_game(self, db: Session, game_id: str) -> Dict[str, Any]:
        """Resume a paused game."""
        ...

    def complete_game(self, db: Session, game_id: str) -> Dict[str, Any]:
        """Mark game as complete and return final statistics."""
        ...

    def list_active_games(self) -> List[str]:
        """List all active game IDs in cache."""
        ...

    def cleanup_game(self, game_id: str) -> None:
        """Remove game from cache."""
        ...

    def cleanup_all_games(self) -> int:
        """Clear all games from cache."""
        ...


class NotificationServiceProtocol(Protocol):
    """Contract for NotificationService.

    Defines the interface for sending, retrieving, and managing
    player notifications.
    """

    def send_notification(
        self,
        player_id: int,
        notification_type: str,
        message: str,
        db: Session,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send notification to a player.

        Args:
            player_id: Player profile ID
            notification_type: Type of notification (game_start, game_end, etc.)
            message: Notification message
            db: Database session
            data: Optional additional data

        Returns:
            Created notification dict
        """
        ...

    def get_player_notifications(
        self,
        player_id: int,
        db: Session,
        unread_only: bool = False,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all notifications for a player."""
        ...

    def mark_as_read(self, notification_id: int, db: Session) -> Dict[str, Any]:
        """Mark notification as read."""
        ...

    def mark_all_as_read(self, player_id: int, db: Session) -> int:
        """Mark all player notifications as read."""
        ...

    def delete_notification(self, notification_id: int, db: Session) -> Dict[str, str]:
        """Delete a notification."""
        ...

    def get_unread_count(self, player_id: int, db: Session) -> int:
        """Get count of unread notifications."""
        ...

    def broadcast_to_game(
        self,
        game_id: str,
        notification_type: str,
        message: str,
        db: Session,
        data: Optional[Dict[str, Any]] = None
    ) -> int:
        """Broadcast notification to all players in a game."""
        ...


class LeaderboardServiceProtocol(Protocol):
    """Contract for LeaderboardService.

    Defines the interface for generating and caching leaderboards.
    """

    def get_leaderboard(
        self,
        leaderboard_type: str,
        db: Session,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get leaderboard by type.

        Args:
            leaderboard_type: Type of leaderboard (total_earnings, win_rate, etc.)
            db: Database session
            limit: Maximum number of entries
            offset: Number of entries to skip

        Returns:
            List of leaderboard entries
        """
        ...

    def get_available_leaderboard_types(self) -> List[str]:
        """Get list of available leaderboard types."""
        ...

    def clear_cache(self) -> None:
        """Clear leaderboard cache."""
        ...


class AchievementServiceProtocol(Protocol):
    """Contract for AchievementService.

    Defines the interface for managing badges and achievements.
    """

    def award_badge(
        self,
        player_profile_id: int,
        badge_name: str,
        game_record_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Award a badge to a player.

        Args:
            player_profile_id: Player ID
            badge_name: Name of badge to award
            game_record_id: Game where badge was earned
            db: Database session

        Returns:
            Awarded badge information
        """
        ...

    def get_player_badges(
        self,
        player_profile_id: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Get all badges earned by a player."""
        ...

    def get_available_badges(self, db: Session) -> List[Dict[str, Any]]:
        """Get all available badges."""
        ...

    def check_badge_eligibility(
        self,
        player_profile_id: int,
        badge_name: str,
        db: Session
    ) -> bool:
        """Check if player is eligible for a badge."""
        ...

    def calculate_badge_progress(
        self,
        player_profile_id: int,
        badge_name: str,
        db: Session
    ) -> Dict[str, Any]:
        """Calculate progress toward earning a badge."""
        ...
