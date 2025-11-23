"""
Example Usage of NotificationService

This file demonstrates how to use the NotificationService in your application.
"""

from sqlalchemy.orm import Session

from app.services.notification_service import get_notification_service


# Example 1: Send a notification to a player
def example_send_notification(db: Session) -> None:
    """Send a single notification to a player."""
    notification_service = get_notification_service()

    notification = notification_service.send_notification(
        player_id=1,
        notification_type="game_start",
        message="Your game has started! Good luck!",
        db=db,
        data={"game_id": "abc123", "player_count": 4}
    )

    print(f"Notification sent: {notification}")


# Example 2: Get all notifications for a player
def example_get_notifications(db: Session) -> None:
    """Get all notifications for a player."""
    notification_service = get_notification_service()

    # Get all notifications
    all_notifications = notification_service.get_player_notifications(
        player_id=1,
        db=db
    )

    print(f"Total notifications: {len(all_notifications)}")

    # Get only unread notifications
    unread_notifications = notification_service.get_player_notifications(
        player_id=1,
        db=db,
        unread_only=True
    )

    print(f"Unread notifications: {len(unread_notifications)}")


# Example 3: Mark notification as read
def example_mark_as_read(db: Session) -> None:
    """Mark a notification as read."""
    notification_service = get_notification_service()

    updated_notification = notification_service.mark_as_read(
        notification_id=1,
        db=db
    )

    print(f"Notification marked as read: {updated_notification['is_read']}")


# Example 4: Mark all notifications as read
def example_mark_all_as_read(db: Session) -> None:
    """Mark all player notifications as read."""
    notification_service = get_notification_service()

    count = notification_service.mark_all_as_read(
        player_id=1,
        db=db
    )

    print(f"Marked {count} notifications as read")


# Example 5: Get unread count
def example_get_unread_count(db: Session) -> None:
    """Get count of unread notifications."""
    notification_service = get_notification_service()

    unread_count = notification_service.get_unread_count(
        player_id=1,
        db=db
    )

    print(f"Player has {unread_count} unread notifications")


# Example 6: Broadcast to all players in a game
def example_broadcast_to_game(db: Session) -> None:
    """Broadcast a notification to all players in a game."""
    notification_service = get_notification_service()

    count = notification_service.broadcast_to_game(
        game_id="abc123",
        notification_type="hole_complete",
        message="Hole 1 is complete! Moving to hole 2.",
        db=db,
        data={"hole_number": 1, "next_hole": 2}
    )

    print(f"Notification sent to {count} players")


# Example 7: Delete a notification
def example_delete_notification(db: Session) -> None:
    """Delete a specific notification."""
    notification_service = get_notification_service()

    result = notification_service.delete_notification(
        notification_id=1,
        db=db
    )

    print(f"Result: {result['message']}")


# Example 8: Delete old notifications
def example_delete_old_notifications(db: Session) -> None:
    """Delete notifications older than 30 days."""
    notification_service = get_notification_service()

    count = notification_service.delete_old_notifications(
        player_id=1,
        db=db,
        days_old=30
    )

    print(f"Deleted {count} old notifications")


# Example 9: Send achievement notification with rich data
def example_achievement_notification(db: Session) -> None:
    """Send an achievement earned notification with additional data."""
    notification_service = get_notification_service()

    notification = notification_service.send_notification(
        player_id=1,
        notification_type="achievement_earned",
        message="Congratulations! You earned the 'Lone Wolf' badge!",
        db=db,
        data={
            "badge_id": 1,
            "badge_name": "Lone Wolf",
            "rarity": "legendary",
            "points_earned": 100,
            "serial_number": 42
        }
    )

    print(f"Achievement notification sent: {notification}")


# Example 10: Send partnership notification
def example_partnership_notification(db: Session) -> None:
    """Send a partnership formed notification."""
    notification_service = get_notification_service()

    # Send to both partners
    for player_id in [1, 2]:
        notification_service.send_notification(
            player_id=player_id,
            notification_type="partnership_formed",
            message="You've formed a partnership!",
            db=db,
            data={
                "partner_id": 2 if player_id == 1 else 1,
                "partner_name": "John Doe" if player_id == 1 else "Jane Smith",
                "hole_number": 3,
                "current_wager": 2.0
            }
        )

    print("Partnership notifications sent to both players")


# Example 11: Integration with game lifecycle
def example_game_lifecycle_integration(db: Session, game_id: str) -> None:
    """Example of how to integrate with game lifecycle events."""
    notification_service = get_notification_service()

    # When game starts
    notification_service.broadcast_to_game(
        game_id=game_id,
        notification_type="game_start",
        message="Game has started! First hole tee time.",
        db=db,
        data={"total_holes": 18, "base_wager": 1.0}
    )

    # When game ends
    notification_service.broadcast_to_game(
        game_id=game_id,
        notification_type="game_end",
        message="Game complete! Check your final scores.",
        db=db,
        data={"winner": "John Doe", "total_earnings": 15.75}
    )


# Example 12: Integration with betting system
def example_betting_integration(db: Session, game_id: str) -> None:
    """Example of how to integrate with betting events."""
    notification_service = get_notification_service()

    # When wager doubles
    notification_service.broadcast_to_game(
        game_id=game_id,
        notification_type="betting_update",
        message="The wager has doubled! Current wager: $2.00",
        db=db,
        data={
            "previous_wager": 1.0,
            "current_wager": 2.0,
            "hole_number": 5
        }
    )

    # When player is wolf
    notification_service.send_notification(
        player_id=1,
        notification_type="turn_notification",
        message="You are the Wolf! Choose your partners wisely.",
        db=db,
        data={
            "role": "wolf",
            "hole_number": 5,
            "available_partners": [2, 3, 4]
        }
    )
