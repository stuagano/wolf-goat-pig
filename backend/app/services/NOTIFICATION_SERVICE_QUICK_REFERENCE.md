# NotificationService Quick Reference

## Import

```python
from app.services.notification_service import get_notification_service

notification_service = get_notification_service()
```

## Common Operations

### Send Notification to One Player

```python
notification_service.send_notification(
    player_id=1,
    notification_type="game_start",
    message="Your game has started!",
    db=db,
    data={"game_id": "abc123"}
)
```

### Broadcast to All Players in Game

```python
notification_service.broadcast_to_game(
    game_id="abc123",
    notification_type="hole_complete",
    message="Hole 1 complete!",
    db=db,
    data={"hole_number": 1}
)
```

### Get Player Notifications

```python
# All notifications
all_notifs = notification_service.get_player_notifications(
    player_id=1,
    db=db
)

# Only unread
unread = notification_service.get_player_notifications(
    player_id=1,
    db=db,
    unread_only=True
)

# Latest 10
recent = notification_service.get_player_notifications(
    player_id=1,
    db=db,
    limit=10
)
```

### Mark as Read

```python
# Single notification
notification_service.mark_as_read(notification_id=1, db=db)

# All notifications
count = notification_service.mark_all_as_read(player_id=1, db=db)
```

### Get Unread Count

```python
count = notification_service.get_unread_count(player_id=1, db=db)
```

### Delete Notification

```python
notification_service.delete_notification(notification_id=1, db=db)
```

### Clean Up Old Notifications

```python
# Delete notifications older than 30 days
count = notification_service.delete_old_notifications(
    player_id=1,
    db=db,
    days_old=30
)
```

## Notification Types

| Type | When to Use |
|------|-------------|
| `game_start` | Game begins |
| `game_end` | Game completes |
| `turn_notification` | Player's turn (Wolf selection, etc.) |
| `betting_update` | Wager changes |
| `achievement_earned` | Badge/achievement earned |
| `partnership_formed` | Partnership created |
| `hole_complete` | Hole finishes |

## Response Format

```python
{
    "id": 1,
    "player_profile_id": 1,
    "notification_type": "game_start",
    "message": "Your game has started!",
    "data": {"game_id": "abc123"},
    "is_read": False,
    "created_at": "2025-11-03T17:00:00.000000"
}
```

## Integration Patterns

### With Game Lifecycle

```python
# Start game
lifecycle_service = get_game_lifecycle_service()
game = lifecycle_service.start_game(db, game_id)

# Notify players
notification_service.broadcast_to_game(
    game_id=game_id,
    notification_type="game_start",
    message="Game has started!",
    db=db
)
```

### With Achievement Service

```python
# Award badge
achievement_service = get_achievement_service(db)
badge = achievement_service.award_badge(player_id, "Lone Wolf")

# Notify player
if badge:
    notification_service.send_notification(
        player_id=player_id,
        notification_type="achievement_earned",
        message=f"You earned '{badge['badge_name']}'!",
        db=db,
        data=badge
    )
```

### With Betting System

```python
# Handle wager change
notification_service.broadcast_to_game(
    game_id=game_id,
    notification_type="betting_update",
    message=f"Wager doubled to ${new_wager:.2f}!",
    db=db,
    data={
        "previous_wager": old_wager,
        "current_wager": new_wager
    }
)
```

## Error Handling

```python
from fastapi import HTTPException

try:
    notification = notification_service.send_notification(
        player_id=1,
        notification_type="game_start",
        message="Test",
        db=db
    )
except HTTPException as e:
    print(f"Error {e.status_code}: {e.detail}")
```

## Database Setup

```python
# Add to your models.py (already done)
from app.models import Notification

# Create table
from app.database import engine
from app.models import Base

Base.metadata.create_all(bind=engine)
```

## Tips

1. Use `broadcast_to_game()` for game-wide events
2. Include rich context in `data` parameter
3. Check `get_unread_count()` for UI badges
4. Regularly clean up with `delete_old_notifications()`
5. Use `limit` parameter for pagination
6. Always handle `HTTPException` errors
7. Log important notification events
