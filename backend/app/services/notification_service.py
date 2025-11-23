"""
Notification Service - In-App Notification Management

This service handles all notification operations for the Wolf Goat Pig application including:
- Sending notifications to individual players
- Broadcasting notifications to all players in a game
- Retrieving player notifications
- Managing notification read/unread status
- Deleting notifications
- Tracking unread notification counts

Notification types supported:
- game_start: Game has started
- game_end: Game has ended
- turn_notification: Player's turn to act
- betting_update: Betting state has changed
- achievement_earned: Player earned an achievement/badge
- partnership_formed: Partnership was formed
- hole_complete: Hole has been completed
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import Notification

logger = logging.getLogger(__name__)


# ====================================================================================
# NOTIFICATION SERVICE
# ====================================================================================

class NotificationService:
    """
    Service class for managing Wolf Goat Pig in-app notifications.

    This service centralizes all notification logic including creation,
    retrieval, status management, and deletion. It provides methods for
    both individual and broadcast notifications.

    Uses singleton pattern to ensure consistent notification management
    across the application.
    """

    _instance = None
    _initialized: bool

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(NotificationService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the service."""
        if self._initialized:
            return

        self._initialized = True
        logger.info("NotificationService initialized")

    # ====================================================================================
    # CORE NOTIFICATION METHODS
    # ====================================================================================

    def send_notification(
        self,
        player_id: int,
        notification_type: str,
        message: str,
        db: Session,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a notification to a specific player.

        Creates a new notification record in the database for the specified
        player. The notification will appear in the player's notification
        list and can be marked as read or deleted later.

        Args:
            player_id: ID of the player to receive the notification
            notification_type: Type of notification (game_start, game_end, etc.)
            message: Notification message content
            db: Database session for persistence
            data: Optional additional data as JSON dict

        Returns:
            Dict containing the created notification information

        Raises:
            HTTPException: If notification creation fails
        """
        try:
            # Validate notification type
            valid_types = [
                "game_start",
                "game_end",
                "turn_notification",
                "betting_update",
                "achievement_earned",
                "partnership_formed",
                "hole_complete"
            ]

            if notification_type not in valid_types:
                logger.warning(
                    f"Unknown notification type '{notification_type}', "
                    f"proceeding anyway"
                )

            # Create notification record
            notification = Notification(
                player_profile_id=player_id,
                notification_type=notification_type,
                message=message,
                data=data or {},
                is_read=False,
                created_at=datetime.utcnow().isoformat()
            )

            db.add(notification)
            db.commit()
            db.refresh(notification)

            logger.info(
                f"Sent {notification_type} notification to player {player_id}: "
                f"'{message}'"
            )

            return {
                "id": notification.id,
                "player_profile_id": notification.player_profile_id,
                "notification_type": notification.notification_type,
                "message": notification.message,
                "data": notification.data,
                "is_read": notification.is_read,
                "created_at": notification.created_at
            }

        except Exception as e:
            db.rollback()
            logger.error(
                f"Error sending notification to player {player_id}: {e}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send notification: {str(e)}"
            )

    def get_player_notifications(
        self,
        player_id: int,
        db: Session,
        unread_only: bool = False,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all notifications for a specific player.

        Retrieves notifications from the database, optionally filtering
        to only unread notifications. Results are ordered by creation
        time with newest first.

        Args:
            player_id: ID of the player
            db: Database session for querying
            unread_only: If True, only return unread notifications
            limit: Optional maximum number of notifications to return

        Returns:
            List of dicts containing notification information

        Raises:
            HTTPException: If retrieval fails
        """
        try:
            # Build query
            query = db.query(Notification).filter(
                Notification.player_profile_id == player_id
            )

            # Apply filters
            if unread_only:
                query = query.filter(Notification.is_read == False)

            # Order by newest first
            query = query.order_by(Notification.created_at.desc())

            # Apply limit if specified
            if limit:
                query = query.limit(limit)

            notifications = query.all()

            result = []
            for notification in notifications:
                result.append({
                    "id": notification.id,
                    "player_profile_id": notification.player_profile_id,
                    "notification_type": notification.notification_type,
                    "message": notification.message,
                    "data": notification.data,
                    "is_read": notification.is_read,
                    "created_at": notification.created_at
                })

            logger.debug(
                f"Retrieved {len(result)} notifications for player {player_id} "
                f"(unread_only={unread_only})"
            )

            return result

        except Exception as e:
            logger.error(
                f"Error retrieving notifications for player {player_id}: {e}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve notifications: {str(e)}"
            )

    def mark_as_read(
        self,
        notification_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Mark a specific notification as read.

        Updates the is_read status of a notification to True. This is
        typically called when a player views a notification.

        Args:
            notification_id: ID of the notification to mark as read
            db: Database session for persistence

        Returns:
            Dict containing updated notification information

        Raises:
            HTTPException: If notification not found or update fails
        """
        try:
            # Get notification
            notification = db.query(Notification).filter(
                Notification.id == notification_id
            ).first()

            if not notification:
                logger.warning(f"Notification {notification_id} not found")
                raise HTTPException(
                    status_code=404,
                    detail=f"Notification {notification_id} not found"
                )

            # Update read status
            notification.is_read = True
            db.commit()
            db.refresh(notification)

            logger.debug(f"Marked notification {notification_id} as read")

            return {
                "id": notification.id,
                "player_profile_id": notification.player_profile_id,
                "notification_type": notification.notification_type,
                "message": notification.message,
                "data": notification.data,
                "is_read": notification.is_read,
                "created_at": notification.created_at
            }

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking notification {notification_id} as read: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to mark notification as read: {str(e)}"
            )

    def mark_all_as_read(
        self,
        player_id: int,
        db: Session
    ) -> int:
        """
        Mark all notifications for a player as read.

        Bulk updates all unread notifications for the specified player
        to read status. This is useful when a player wants to clear
        all notifications at once.

        Args:
            player_id: ID of the player
            db: Database session for persistence

        Returns:
            Number of notifications marked as read

        Raises:
            HTTPException: If update fails
        """
        try:
            # Get all unread notifications for player
            unread_notifications = db.query(Notification).filter(
                Notification.player_profile_id == player_id,
                Notification.is_read == False
            ).all()

            count = len(unread_notifications)

            # Mark all as read
            for notification in unread_notifications:
                notification.is_read = True

            db.commit()

            logger.info(
                f"Marked {count} notifications as read for player {player_id}"
            )

            return count

        except Exception as e:
            db.rollback()
            logger.error(
                f"Error marking all notifications as read for player {player_id}: {e}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to mark all notifications as read: {str(e)}"
            )

    def delete_notification(
        self,
        notification_id: int,
        db: Session
    ) -> Dict[str, str]:
        """
        Delete a specific notification.

        Permanently removes a notification from the database. This action
        cannot be undone.

        Args:
            notification_id: ID of the notification to delete
            db: Database session for persistence

        Returns:
            Dict confirming deletion

        Raises:
            HTTPException: If notification not found or deletion fails
        """
        try:
            # Get notification
            notification = db.query(Notification).filter(
                Notification.id == notification_id
            ).first()

            if not notification:
                logger.warning(f"Notification {notification_id} not found")
                raise HTTPException(
                    status_code=404,
                    detail=f"Notification {notification_id} not found"
                )

            # Delete notification
            player_id = notification.player_profile_id
            db.delete(notification)
            db.commit()

            logger.info(
                f"Deleted notification {notification_id} for player {player_id}"
            )

            return {
                "message": f"Notification {notification_id} deleted successfully"
            }

        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting notification {notification_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete notification: {str(e)}"
            )

    def get_unread_count(
        self,
        player_id: int,
        db: Session
    ) -> int:
        """
        Get the count of unread notifications for a player.

        Returns the number of notifications that have not been marked
        as read. This is useful for displaying notification badges in
        the UI.

        Args:
            player_id: ID of the player
            db: Database session for querying

        Returns:
            Number of unread notifications

        Raises:
            HTTPException: If query fails
        """
        try:
            count = db.query(Notification).filter(
                Notification.player_profile_id == player_id,
                Notification.is_read == False
            ).count()

            logger.debug(f"Player {player_id} has {count} unread notifications")

            return int(count)

        except Exception as e:
            logger.error(
                f"Error getting unread count for player {player_id}: {e}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get unread notification count: {str(e)}"
            )

    def broadcast_to_game(
        self,
        game_id: str,
        notification_type: str,
        message: str,
        db: Session,
        data: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Broadcast a notification to all players in a game.

        Sends the same notification to all players associated with the
        specified game. This is useful for game-wide events like game
        start, game end, or hole completion.

        Args:
            game_id: ID of the game
            notification_type: Type of notification
            message: Notification message content
            db: Database session for persistence
            data: Optional additional data as JSON dict

        Returns:
            Number of notifications sent

        Raises:
            HTTPException: If game not found or broadcast fails
        """
        try:
            # Import here to avoid circular dependency
            from ..models import GamePlayer

            # Get all players in the game
            game_players = db.query(GamePlayer).filter(
                GamePlayer.game_id == game_id
            ).all()

            if not game_players:
                logger.warning(f"No players found for game {game_id}")
                return 0

            notification_count = 0

            # Send notification to each player
            for game_player in game_players:
                if game_player.player_profile_id:
                    try:
                        self.send_notification(
                            player_id=game_player.player_profile_id,
                            notification_type=notification_type,
                            message=message,
                            db=db,
                            data=data
                        )
                        notification_count += 1
                    except Exception as e:
                        logger.error(
                            f"Error sending notification to player "
                            f"{game_player.player_profile_id}: {e}"
                        )
                        # Continue with other players even if one fails
                        continue

            logger.info(
                f"Broadcast {notification_type} notification to {notification_count} "
                f"players in game {game_id}"
            )

            return notification_count

        except Exception as e:
            logger.error(f"Error broadcasting to game {game_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to broadcast notification: {str(e)}"
            )

    # ====================================================================================
    # UTILITY METHODS
    # ====================================================================================

    def delete_old_notifications(
        self,
        player_id: int,
        db: Session,
        days_old: int = 30
    ) -> int:
        """
        Delete notifications older than a specified number of days.

        This is useful for cleaning up old notifications and preventing
        the notifications table from growing indefinitely. Typically
        called as part of a maintenance routine.

        Args:
            player_id: ID of the player
            db: Database session for persistence
            days_old: Delete notifications older than this many days

        Returns:
            Number of notifications deleted

        Raises:
            HTTPException: If deletion fails
        """
        try:
            from datetime import timedelta

            # Calculate cutoff date
            cutoff_date = (datetime.utcnow() - timedelta(days=days_old)).isoformat()

            # Get old notifications
            old_notifications = db.query(Notification).filter(
                Notification.player_profile_id == player_id,
                Notification.created_at < cutoff_date
            ).all()

            count = len(old_notifications)

            # Delete old notifications
            for notification in old_notifications:
                db.delete(notification)

            db.commit()

            logger.info(
                f"Deleted {count} notifications older than {days_old} days "
                f"for player {player_id}"
            )

            return count

        except Exception as e:
            db.rollback()
            logger.error(
                f"Error deleting old notifications for player {player_id}: {e}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete old notifications: {str(e)}"
            )

    def get_notification_by_id(
        self,
        notification_id: int,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific notification by ID.

        Retrieves a single notification record. This is useful for
        getting details of a specific notification.

        Args:
            notification_id: ID of the notification
            db: Database session for querying

        Returns:
            Dict containing notification information, or None if not found

        Raises:
            HTTPException: If query fails
        """
        try:
            notification = db.query(Notification).filter(
                Notification.id == notification_id
            ).first()

            if not notification:
                return None

            return {
                "id": notification.id,
                "player_profile_id": notification.player_profile_id,
                "notification_type": notification.notification_type,
                "message": notification.message,
                "data": notification.data,
                "is_read": notification.is_read,
                "created_at": notification.created_at
            }

        except Exception as e:
            logger.error(f"Error getting notification {notification_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get notification: {str(e)}"
            )


# ====================================================================================
# SINGLETON ACCESSOR
# ====================================================================================

_service_instance = None


def get_notification_service() -> NotificationService:
    """
    Get the singleton NotificationService instance.

    This function provides access to the shared service instance,
    creating it if it doesn't exist yet.

    Returns:
        NotificationService singleton instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = NotificationService()
    return _service_instance
