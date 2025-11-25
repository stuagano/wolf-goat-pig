"""
Unit tests for NotificationService

Tests the core functionality of the NotificationService including:
- Sending notifications
- Retrieving notifications
- Marking notifications as read
- Deleting notifications
- Broadcasting to games
- Unread counts
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.services.notification_service import get_notification_service, Notification
from app.models import Base, PlayerProfile, GamePlayer
from app.database import get_db


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_notifications.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_player(db):
    """Create a test player profile."""
    player = PlayerProfile(
        name="Test Player",
        email="test@example.com",
        handicap=18.0,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


@pytest.fixture
def test_game_players(db, test_player):
    """Create test game players."""
    game_id = "test-game-123"

    # Create additional players
    players = []
    for i in range(3):
        player = PlayerProfile(
            name=f"Player {i+2}",
            email=f"player{i+2}@example.com",
            handicap=18.0,
            created_at=datetime.now(timezone.utc).isoformat()
        )
        db.add(player)
        players.append(player)

    db.commit()

    # Add test_player to list
    players.insert(0, test_player)

    # Create game player records
    for i, player in enumerate(players):
        game_player = GamePlayer(
            game_id=game_id,
            player_slot_id=f"p{i+1}",
            player_profile_id=player.id,
            player_name=player.name,
            handicap=player.handicap,
            join_status="joined",
            created_at=datetime.now(timezone.utc).isoformat()
        )
        db.add(game_player)

    db.commit()

    return game_id, players


class TestNotificationService:
    """Test suite for NotificationService."""

    def test_send_notification(self, db, test_player):
        """Test sending a notification to a player."""
        service = get_notification_service()

        notification = service.send_notification(
            player_id=test_player.id,
            notification_type="game_start",
            message="Test notification",
            db=db,
            data={"test_key": "test_value"}
        )

        assert notification["player_profile_id"] == test_player.id
        assert notification["notification_type"] == "game_start"
        assert notification["message"] == "Test notification"
        assert notification["data"]["test_key"] == "test_value"
        assert notification["is_read"] is False
        assert "created_at" in notification

    def test_get_player_notifications(self, db, test_player):
        """Test retrieving player notifications."""
        service = get_notification_service()

        # Send multiple notifications
        for i in range(3):
            service.send_notification(
                player_id=test_player.id,
                notification_type="game_start",
                message=f"Notification {i+1}",
                db=db
            )

        # Get all notifications
        notifications = service.get_player_notifications(
            player_id=test_player.id,
            db=db
        )

        assert len(notifications) == 3
        # Should be ordered newest first
        assert "Notification 3" in notifications[0]["message"]

    def test_get_unread_only(self, db, test_player):
        """Test filtering for unread notifications only."""
        service = get_notification_service()

        # Send notifications
        notif1 = service.send_notification(
            player_id=test_player.id,
            notification_type="game_start",
            message="Unread notification",
            db=db
        )

        notif2 = service.send_notification(
            player_id=test_player.id,
            notification_type="game_end",
            message="Another notification",
            db=db
        )

        # Mark one as read
        service.mark_as_read(notif1["id"], db)

        # Get only unread
        unread = service.get_player_notifications(
            player_id=test_player.id,
            db=db,
            unread_only=True
        )

        assert len(unread) == 1
        assert unread[0]["id"] == notif2["id"]

    def test_mark_as_read(self, db, test_player):
        """Test marking a notification as read."""
        service = get_notification_service()

        # Send notification
        notification = service.send_notification(
            player_id=test_player.id,
            notification_type="game_start",
            message="Test notification",
            db=db
        )

        assert notification["is_read"] is False

        # Mark as read
        updated = service.mark_as_read(notification["id"], db)

        assert updated["is_read"] is True
        assert updated["id"] == notification["id"]

    def test_mark_all_as_read(self, db, test_player):
        """Test marking all notifications as read."""
        service = get_notification_service()

        # Send multiple notifications
        for i in range(5):
            service.send_notification(
                player_id=test_player.id,
                notification_type="game_start",
                message=f"Notification {i+1}",
                db=db
            )

        # Mark all as read
        count = service.mark_all_as_read(test_player.id, db)

        assert count == 5

        # Verify all are read
        unread_count = service.get_unread_count(test_player.id, db)
        assert unread_count == 0

    def test_delete_notification(self, db, test_player):
        """Test deleting a notification."""
        service = get_notification_service()

        # Send notification
        notification = service.send_notification(
            player_id=test_player.id,
            notification_type="game_start",
            message="Test notification",
            db=db
        )

        # Delete it
        result = service.delete_notification(notification["id"], db)

        assert "deleted successfully" in result["message"]

        # Verify it's gone
        notifications = service.get_player_notifications(
            player_id=test_player.id,
            db=db
        )
        assert len(notifications) == 0

    def test_get_unread_count(self, db, test_player):
        """Test getting unread notification count."""
        service = get_notification_service()

        # Initially should be 0
        count = service.get_unread_count(test_player.id, db)
        assert count == 0

        # Send notifications
        notif1 = service.send_notification(
            player_id=test_player.id,
            notification_type="game_start",
            message="Notification 1",
            db=db
        )

        service.send_notification(
            player_id=test_player.id,
            notification_type="game_end",
            message="Notification 2",
            db=db
        )

        # Should be 2
        count = service.get_unread_count(test_player.id, db)
        assert count == 2

        # Mark one as read
        service.mark_as_read(notif1["id"], db)

        # Should be 1
        count = service.get_unread_count(test_player.id, db)
        assert count == 1

    def test_broadcast_to_game(self, db, test_game_players):
        """Test broadcasting notification to all game players."""
        service = get_notification_service()
        game_id, players = test_game_players

        # Broadcast to game
        count = service.broadcast_to_game(
            game_id=game_id,
            notification_type="hole_complete",
            message="Hole 1 is complete!",
            db=db,
            data={"hole_number": 1}
        )

        assert count == len(players)

        # Verify each player received notification
        for player in players:
            notifications = service.get_player_notifications(
                player_id=player.id,
                db=db
            )
            assert len(notifications) == 1
            assert "Hole 1 is complete!" in notifications[0]["message"]
            assert notifications[0]["data"]["hole_number"] == 1

    def test_notification_limit(self, db, test_player):
        """Test limiting number of notifications returned."""
        service = get_notification_service()

        # Send 10 notifications
        for i in range(10):
            service.send_notification(
                player_id=test_player.id,
                notification_type="game_start",
                message=f"Notification {i+1}",
                db=db
            )

        # Get only 5
        notifications = service.get_player_notifications(
            player_id=test_player.id,
            db=db,
            limit=5
        )

        assert len(notifications) == 5

    def test_notification_not_found(self, db):
        """Test error handling when notification doesn't exist."""
        service = get_notification_service()

        with pytest.raises(HTTPException) as exc_info:
            service.mark_as_read(99999, db)

        assert exc_info.value.status_code == 404

    def test_delete_old_notifications(self, db, test_player):
        """Test deleting old notifications."""
        service = get_notification_service()

        # Send notifications
        for i in range(5):
            service.send_notification(
                player_id=test_player.id,
                notification_type="game_start",
                message=f"Notification {i+1}",
                db=db
            )

        # Manually set some as old (modify created_at)
        from datetime import timedelta
        old_date = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()

        notifications = db.query(Notification).filter(
            Notification.player_profile_id == test_player.id
        ).limit(3).all()

        for notif in notifications:
            notif.created_at = old_date

        db.commit()

        # Delete notifications older than 30 days
        count = service.delete_old_notifications(
            player_id=test_player.id,
            db=db,
            days_old=30
        )

        assert count == 3

        # Verify remaining notifications
        remaining = service.get_player_notifications(
            player_id=test_player.id,
            db=db
        )
        assert len(remaining) == 2

    def test_notification_types(self, db, test_player):
        """Test all supported notification types."""
        service = get_notification_service()

        notification_types = [
            "game_start",
            "game_end",
            "turn_notification",
            "betting_update",
            "achievement_earned",
            "partnership_formed",
            "hole_complete"
        ]

        for notif_type in notification_types:
            notification = service.send_notification(
                player_id=test_player.id,
                notification_type=notif_type,
                message=f"Test {notif_type}",
                db=db
            )
            assert notification["notification_type"] == notif_type

    def test_singleton_pattern(self):
        """Test that service uses singleton pattern."""
        service1 = get_notification_service()
        service2 = get_notification_service()

        assert service1 is service2

    def test_notification_with_null_data(self, db, test_player):
        """Test sending notification without data parameter."""
        service = get_notification_service()

        notification = service.send_notification(
            player_id=test_player.id,
            notification_type="game_start",
            message="Test notification",
            db=db
        )

        assert notification["data"] == {}

    def test_get_notification_by_id(self, db, test_player):
        """Test getting a specific notification by ID."""
        service = get_notification_service()

        # Send notification
        sent_notification = service.send_notification(
            player_id=test_player.id,
            notification_type="game_start",
            message="Test notification",
            db=db
        )

        # Get by ID
        retrieved = service.get_notification_by_id(
            notification_id=sent_notification["id"],
            db=db
        )

        assert retrieved is not None
        assert retrieved["id"] == sent_notification["id"]
        assert retrieved["message"] == "Test notification"

    def test_get_notification_by_id_not_found(self, db):
        """Test getting notification that doesn't exist returns None."""
        service = get_notification_service()

        retrieved = service.get_notification_by_id(
            notification_id=99999,
            db=db
        )

        assert retrieved is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
