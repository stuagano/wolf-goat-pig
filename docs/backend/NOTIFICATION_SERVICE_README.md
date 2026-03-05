# NotificationService Documentation

## Overview

The `NotificationService` is a singleton service that manages in-app notifications for the Wolf Goat Pig application. It provides a comprehensive interface for sending, retrieving, and managing player notifications with full database persistence.

## Features

- **Singleton Pattern** - Single instance ensures consistent state management
- **Database Integration** - Full SQLAlchemy support for persistence
- **Multiple Notification Types** - Support for game events, achievements, betting updates, and more
- **Broadcast Capability** - Send notifications to all players in a game
- **Read/Unread Status** - Track which notifications have been viewed
- **Bulk Operations** - Mark all notifications as read, delete old notifications
- **Rich Data Support** - Include additional JSON data with notifications
- **Comprehensive Error Handling** - HTTPException with appropriate status codes
- **Detailed Logging** - Track all notification operations

## Notification Types

The service supports the following notification types:

| Type | Description | Use Case |
|------|-------------|----------|
| `game_start` | Game has started | Notify players when game begins |
| `game_end` | Game has ended | Notify players when game completes |
| `turn_notification` | Player's turn to act | Notify when it's a player's turn (e.g., Wolf selection) |
| `betting_update` | Betting state changed | Notify when wager changes or betting events occur |
| `achievement_earned` | Achievement/badge earned | Notify when player earns a badge |
| `partnership_formed` | Partnership created | Notify when partnerships are formed |
| `hole_complete` | Hole completed | Notify when a hole finishes |

## Database Schema

```python
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    player_profile_id = Column(Integer, index=True)  # References PlayerProfile.id
    notification_type = Column(String, index=True)
    message = Column(String)
    data = Column(JSON, nullable=True)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(String, index=True)  # ISO timestamp
```

## API Reference

### Getting the Service Instance

```python
from app.services.notification_service import get_notification_service

notification_service = get_notification_service()
```

### Core Methods

#### send_notification()

Send a notification to a specific player.

```python
def send_notification(
    self,
    player_id: int,
    notification_type: str,
    message: str,
    db: Session,
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

**Parameters:**
- `player_id` (int): ID of the player to receive notification
- `notification_type` (str): Type of notification
- `message` (str): Notification message content
- `db` (Session): Database session
- `data` (Optional[Dict]): Additional JSON data

**Returns:** Dict with notification details

**Example:**
```python
notification = notification_service.send_notification(
    player_id=1,
    notification_type="game_start",
    message="Your game has started!",
    db=db,
    data={"game_id": "abc123", "player_count": 4}
)
```

#### get_player_notifications()

Get all notifications for a player.

```python
def get_player_notifications(
    self,
    player_id: int,
    db: Session,
    unread_only: bool = False,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]
```

**Parameters:**
- `player_id` (int): ID of the player
- `db` (Session): Database session
- `unread_only` (bool): If True, only return unread notifications
- `limit` (Optional[int]): Maximum number to return

**Returns:** List of notification dicts

**Example:**
```python
# Get all notifications
all_notifications = notification_service.get_player_notifications(
    player_id=1,
    db=db
)

# Get only unread notifications
unread = notification_service.get_player_notifications(
    player_id=1,
    db=db,
    unread_only=True
)

# Get latest 10 notifications
recent = notification_service.get_player_notifications(
    player_id=1,
    db=db,
    limit=10
)
```

#### mark_as_read()

Mark a specific notification as read.

```python
def mark_as_read(
    self,
    notification_id: int,
    db: Session
) -> Dict[str, Any]
```

**Parameters:**
- `notification_id` (int): ID of notification to mark as read
- `db` (Session): Database session

**Returns:** Dict with updated notification details

**Example:**
```python
updated = notification_service.mark_as_read(
    notification_id=1,
    db=db
)
```

#### mark_all_as_read()

Mark all player notifications as read.

```python
def mark_all_as_read(
    self,
    player_id: int,
    db: Session
) -> int
```

**Parameters:**
- `player_id` (int): ID of the player
- `db` (Session): Database session

**Returns:** Number of notifications marked as read

**Example:**
```python
count = notification_service.mark_all_as_read(
    player_id=1,
    db=db
)
print(f"Marked {count} notifications as read")
```

#### delete_notification()

Delete a specific notification.

```python
def delete_notification(
    self,
    notification_id: int,
    db: Session
) -> Dict[str, str]
```

**Parameters:**
- `notification_id` (int): ID of notification to delete
- `db` (Session): Database session

**Returns:** Dict with confirmation message

**Example:**
```python
result = notification_service.delete_notification(
    notification_id=1,
    db=db
)
```

#### get_unread_count()

Get count of unread notifications.

```python
def get_unread_count(
    self,
    player_id: int,
    db: Session
) -> int
```

**Parameters:**
- `player_id` (int): ID of the player
- `db` (Session): Database session

**Returns:** Number of unread notifications

**Example:**
```python
count = notification_service.get_unread_count(
    player_id=1,
    db=db
)
print(f"You have {count} unread notifications")
```

#### broadcast_to_game()

Send notification to all players in a game.

```python
def broadcast_to_game(
    self,
    game_id: str,
    notification_type: str,
    message: str,
    db: Session,
    data: Optional[Dict[str, Any]] = None
) -> int
```

**Parameters:**
- `game_id` (str): ID of the game
- `notification_type` (str): Type of notification
- `message` (str): Notification message content
- `db` (Session): Database session
- `data` (Optional[Dict]): Additional JSON data

**Returns:** Number of notifications sent

**Example:**
```python
count = notification_service.broadcast_to_game(
    game_id="abc123",
    notification_type="hole_complete",
    message="Hole 1 complete! Moving to hole 2.",
    db=db,
    data={"hole_number": 1, "next_hole": 2}
)
print(f"Notified {count} players")
```

### Utility Methods

#### delete_old_notifications()

Delete notifications older than specified days.

```python
def delete_old_notifications(
    self,
    player_id: int,
    db: Session,
    days_old: int = 30
) -> int
```

**Parameters:**
- `player_id` (int): ID of the player
- `db` (Session): Database session
- `days_old` (int): Delete notifications older than this many days

**Returns:** Number of notifications deleted

**Example:**
```python
# Delete notifications older than 30 days
count = notification_service.delete_old_notifications(
    player_id=1,
    db=db,
    days_old=30
)
```

#### get_notification_by_id()

Get a specific notification by ID.

```python
def get_notification_by_id(
    self,
    notification_id: int,
    db: Session
) -> Optional[Dict[str, Any]]
```

**Parameters:**
- `notification_id` (int): ID of notification
- `db` (Session): Database session

**Returns:** Dict with notification details or None

**Example:**
```python
notification = notification_service.get_notification_by_id(
    notification_id=1,
    db=db
)
```

## Integration Examples

### Game Lifecycle Integration

```python
from app.services.notification_service import get_notification_service
from app.services.game_lifecycle_service import get_game_lifecycle_service

def start_game_with_notifications(game_id: str, db: Session):
    # Start the game
    lifecycle_service = get_game_lifecycle_service()
    game = lifecycle_service.start_game(db, game_id)

    # Notify all players
    notification_service = get_notification_service()
    notification_service.broadcast_to_game(
        game_id=game_id,
        notification_type="game_start",
        message="Game has started! Good luck!",
        db=db,
        data={"player_count": len(game.players)}
    )
```

### Achievement Integration

```python
from app.services.notification_service import get_notification_service
from app.services.achievement_service import get_achievement_service

def award_badge_with_notification(player_id: int, badge_name: str, db: Session):
    # Award the badge
    achievement_service = get_achievement_service(db)
    badge_info = achievement_service.award_badge(
        player_profile_id=player_id,
        badge_name=badge_name
    )

    if badge_info:
        # Send notification
        notification_service = get_notification_service()
        notification_service.send_notification(
            player_id=player_id,
            notification_type="achievement_earned",
            message=f"Congratulations! You earned the '{badge_name}' badge!",
            db=db,
            data=badge_info
        )
```

### Betting System Integration

```python
from app.services.notification_service import get_notification_service

def handle_wager_double(game_id: str, new_wager: float, db: Session):
    notification_service = get_notification_service()

    # Notify all players about wager change
    notification_service.broadcast_to_game(
        game_id=game_id,
        notification_type="betting_update",
        message=f"The wager has doubled to ${new_wager:.2f}!",
        db=db,
        data={
            "previous_wager": new_wager / 2,
            "current_wager": new_wager,
            "reason": "wager_doubled"
        }
    )
```

### Partnership Formation

```python
from app.services.notification_service import get_notification_service

def notify_partnership_formed(player1_id: int, player2_id: int, hole_number: int, db: Session):
    notification_service = get_notification_service()

    # Notify first partner
    notification_service.send_notification(
        player_id=player1_id,
        notification_type="partnership_formed",
        message="You've formed a partnership!",
        db=db,
        data={
            "partner_id": player2_id,
            "hole_number": hole_number
        }
    )

    # Notify second partner
    notification_service.send_notification(
        player_id=player2_id,
        notification_type="partnership_formed",
        message="You've formed a partnership!",
        db=db,
        data={
            "partner_id": player1_id,
            "hole_number": hole_number
        }
    )
```

## Error Handling

All methods raise `HTTPException` with appropriate status codes:

- **400 Bad Request** - Invalid parameters
- **404 Not Found** - Notification or resource not found
- **500 Internal Server Error** - Database or processing errors

Example error handling:

```python
from fastapi import HTTPException

try:
    notification = notification_service.send_notification(
        player_id=1,
        notification_type="game_start",
        message="Game started!",
        db=db
    )
except HTTPException as e:
    print(f"Error: {e.status_code} - {e.detail}")
```

## Logging

The service uses Python's logging module with the logger name `__name__`. Log levels:

- **INFO** - Service initialization, successful operations, broadcasts
- **DEBUG** - Detailed operation info, query results
- **WARNING** - Unknown notification types, missing resources
- **ERROR** - Database errors, failed operations

## Best Practices

1. **Always use the singleton** - Get the service via `get_notification_service()`
2. **Include rich data** - Use the `data` parameter to include context
3. **Use appropriate types** - Choose the correct notification type
4. **Handle errors** - Wrap calls in try/except blocks
5. **Clean up old notifications** - Periodically run `delete_old_notifications()`
6. **Batch read operations** - Use `mark_all_as_read()` for bulk operations
7. **Check unread counts** - Use `get_unread_count()` for UI badges
8. **Test broadcasts** - Ensure game players are properly associated

## Database Migration

To add the notifications table to your database:

```python
# The Notification model is defined in both:
# - app/services/notification_service.py (for the service)
# - app/models.py (for application-wide access)

# Run Alembic migration or create table manually:
from app.database import engine
from app.models import Base

Base.metadata.create_all(bind=engine)
```

## Performance Considerations

1. **Indexes** - The table is indexed on `player_profile_id`, `notification_type`, `is_read`, and `created_at`
2. **Query optimization** - Use `unread_only` and `limit` parameters to reduce query size
3. **Cleanup** - Regularly delete old notifications to prevent table bloat
4. **Broadcasting** - Broadcast operations iterate through players; consider async for large games

## Testing

Example test cases:

```python
def test_send_notification(db):
    service = get_notification_service()
    notification = service.send_notification(
        player_id=1,
        notification_type="game_start",
        message="Test message",
        db=db
    )
    assert notification["is_read"] == False
    assert notification["player_profile_id"] == 1

def test_mark_as_read(db):
    service = get_notification_service()
    # Send notification
    notification = service.send_notification(
        player_id=1,
        notification_type="game_start",
        message="Test",
        db=db
    )
    # Mark as read
    updated = service.mark_as_read(notification["id"], db)
    assert updated["is_read"] == True

def test_broadcast(db):
    service = get_notification_service()
    count = service.broadcast_to_game(
        game_id="test-game",
        notification_type="game_start",
        message="Test broadcast",
        db=db
    )
    assert count > 0
```

## Future Enhancements

Potential improvements for future versions:

1. **Real-time notifications** - WebSocket integration for instant delivery
2. **Push notifications** - Mobile push notification support
3. **Email digests** - Periodic email summaries of notifications
4. **Notification preferences** - Per-player notification type preferences
5. **Notification templates** - Reusable templates for common notifications
6. **Analytics** - Track notification engagement and read rates
7. **Priority levels** - High/medium/low priority notifications
8. **Expiration** - Auto-expire notifications after certain time
9. **Notification channels** - In-app, email, SMS, push
10. **Batch operations** - Optimize database operations for large broadcasts
