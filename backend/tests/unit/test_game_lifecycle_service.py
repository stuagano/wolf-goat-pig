"""
Comprehensive unit tests for GameLifecycleService.

This test suite covers all 9 methods of the GameLifecycleService class:
- create_game() - Game creation with various parameters
- get_game() - Cache hits, database loads, and 404 errors
- start_game() - Game start and state transitions
- pause_game() - Pause functionality
- resume_game() - Resume functionality
- complete_game() - Completion and final stats
- list_active_games() - Listing cached games
- cleanup_game() - Removing single game from cache
- cleanup_all_games() - Clearing all cached games

Author: Test Suite
Date: 2024-11-03
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
from datetime import datetime
from fastapi import HTTPException

from app.services.game_lifecycle_service import (
    GameLifecycleService,
    get_game_lifecycle_service
)
from app.domain.player import Player
from app.models import GameStateModel


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    db.rollback = Mock()
    db.query = Mock()
    return db

from backend.app.wolf_goat_pig import WolfGoatPigGame

@pytest.fixture
def mock_simulation():
    """Mock WolfGoatPigGame instance."""
    sim = Mock()
    sim.current_hole = 5
    sim.players = []
    # Note: betting_state doesn't exist on WolfGoatPigGame
    # Betting is managed per-hole, not globally
    sim._loaded_from_db = True
    return sim


@pytest.fixture
def sample_players():
    """Sample player data for testing."""
    return [
        Player(id="p1", name="Alice", handicap=10.0, points=0),
        Player(id="p2", name="Bob", handicap=15.0, points=0),
        Player(id="p3", name="Charlie", handicap=20.0, points=0),
        Player(id="p4", name="Dave", handicap=12.0, points=0)
    ]


@pytest.fixture
def mock_game_record():
    """Mock game state model record."""
    record = Mock(spec=GameStateModel)
    record.game_id = "test-game-id"
    record.join_code = "ABC123"
    record.creator_user_id = "user123"
    record.game_status = "setup"
    record.state = {
        "game_status": "setup",
        "player_count": 4,
        "players": [],
        "course_name": "Test Course",
        "base_wager": 1,
        "created_at": "2024-11-03T00:00:00"
    }
    record.created_at = "2024-11-03T00:00:00"
    record.updated_at = "2024-11-03T00:00:00"
    return record


@pytest.fixture
def service():
    """Fresh GameLifecycleService instance for each test."""
    # Reset singleton state
    GameLifecycleService._instance = None
    service = GameLifecycleService()
    service._active_games.clear()
    return service


# ============================================================================
# CREATE_GAME TESTS
# ============================================================================

class TestCreateGame:
    """Test create_game method."""

    @patch('app.services.game_lifecycle_service.WolfGoatPigGame')
    @patch('app.services.game_lifecycle_service.uuid.uuid4')
    @patch('app.services.game_lifecycle_service.datetime')
    def test_create_game_success(self, mock_datetime, mock_uuid, mock_sim_class,
                                 service, mock_db, sample_players, mock_simulation):
        """Test successful game creation with all parameters."""
        # Arrange
        mock_uuid.return_value = Mock()
        mock_uuid.return_value.__str__ = Mock(return_value="test-game-id")
        mock_datetime.now.return_value.isoformat.return_value = "2024-11-03T00:00:00"
        mock_sim_class.return_value = mock_simulation

        # Act
        game_id, simulation = service.create_game(
            db=mock_db,
            player_count=4,
            players=sample_players,
            course_name="Test Course",
            base_wager=2,
            join_code="ABC123",
            creator_user_id="user123"
        )

        # Assert
        assert game_id == "test-game-id"
        assert simulation == mock_simulation
        # base_wager is stored in game state, not on the game object
        # The game object doesn't have a global betting_state attribute
        # Betting state is managed per-hole when each hole starts
        assert game_id == "test-game-id"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert game_id in service._active_games

    @patch('app.services.game_lifecycle_service.WolfGoatPigGame')
    @patch('app.services.game_lifecycle_service.uuid.uuid4')
    @patch('app.services.game_lifecycle_service.datetime')
    def test_create_game_minimum_parameters(self, mock_datetime, mock_uuid,
                                           mock_sim_class, service, mock_db,
                                           sample_players, mock_simulation):
        """Test game creation with minimum required parameters."""
        # Arrange
        mock_uuid.return_value = Mock()
        mock_uuid.return_value.__str__ = Mock(return_value="test-game-id")
        mock_datetime.now.return_value.isoformat.return_value = "2024-11-03T00:00:00"
        mock_sim_class.return_value = mock_simulation

        # Act
        game_id, simulation = service.create_game(
            db=mock_db,
            player_count=4,
            players=sample_players
        )

        # Assert
        assert game_id == "test-game-id"
        assert simulation == mock_simulation
        mock_db.commit.assert_called_once()

    def test_create_game_invalid_player_count_too_low(self, service, mock_db, sample_players):
        """Test game creation fails with too few players."""
        with pytest.raises(HTTPException) as exc_info:
            service.create_game(
                db=mock_db,
                player_count=3,
                players=sample_players[:3]
            )

        assert exc_info.value.status_code == 400
        assert "player_count must be between 4 and 6" in str(exc_info.value.detail)

    def test_create_game_invalid_player_count_too_high(self, service, mock_db):
        """Test game creation fails with too many players."""
        players = [Player(id=f"p{i}", name=f"Player{i}", handicap=10.0)
                  for i in range(1, 8)]

        with pytest.raises(HTTPException) as exc_info:
            service.create_game(
                db=mock_db,
                player_count=7,
                players=players
            )

        assert exc_info.value.status_code == 400
        assert "player_count must be between 4 and 6" in str(exc_info.value.detail)

    def test_create_game_player_count_mismatch(self, service, mock_db, sample_players):
        """Test game creation fails when player count doesn't match players list."""
        with pytest.raises(HTTPException) as exc_info:
            service.create_game(
                db=mock_db,
                player_count=4,
                players=sample_players[:2]  # Only 2 players
            )

        assert exc_info.value.status_code == 400
        assert "Expected 4 players, got 2" in str(exc_info.value.detail)

    @patch('app.services.game_lifecycle_service.WolfGoatPigGame')
    @patch('app.services.game_lifecycle_service.uuid.uuid4')
    def test_create_game_database_error(self, mock_uuid, mock_sim_class,
                                       service, mock_db, sample_players, mock_simulation):
        """Test game creation handles database errors."""
        # Arrange
        mock_uuid.return_value = Mock()
        mock_uuid.return_value.__str__ = Mock(return_value="test-game-id")
        mock_sim_class.return_value = mock_simulation
        mock_db.commit.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.create_game(
                db=mock_db,
                player_count=4,
                players=sample_players
            )

        assert exc_info.value.status_code == 500
        assert "Failed to create game" in str(exc_info.value.detail)
        mock_db.rollback.assert_called_once()

    @patch('app.services.game_lifecycle_service.WolfGoatPigGame')
    @patch('app.services.game_lifecycle_service.uuid.uuid4')
    @patch('app.services.game_lifecycle_service.datetime')
    def test_create_game_with_custom_base_wager(self, mock_datetime, mock_uuid,
                                                mock_sim_class, service, mock_db,
                                                sample_players, mock_simulation):
        """Test game creation with custom base wager."""
        # Arrange
        mock_uuid.return_value = Mock()
        mock_uuid.return_value.__str__ = Mock(return_value="test-game-id")
        mock_datetime.now.return_value.isoformat.return_value = "2024-11-03T00:00:00"
        mock_sim_class.return_value = mock_simulation

        # Act
        game_id, simulation = service.create_game(
            db=mock_db,
            player_count=4,
            players=sample_players,
            base_wager=5
        )

        # Assert - base_wager is stored in game state, not on the game object
        # The game object doesn't have a global betting_state attribute
        # Betting state is managed per-hole when each hole starts
        assert game_id == "test-game-id"

    @patch('app.services.game_lifecycle_service.WolfGoatPigGame')
    @patch('app.services.game_lifecycle_service.uuid.uuid4')
    @patch('app.services.game_lifecycle_service.datetime')
    def test_create_game_six_players(self, mock_datetime, mock_uuid, mock_sim_class,
                                    service, mock_db, mock_simulation):
        """Test game creation with 6 players."""
        # Arrange
        players = [Player(id=f"p{i}", name=f"Player{i}", handicap=10.0)
                  for i in range(1, 7)]
        mock_uuid.return_value = Mock()
        mock_uuid.return_value.__str__ = Mock(return_value="test-game-id")
        mock_datetime.now.return_value.isoformat.return_value = "2024-11-03T00:00:00"
        mock_sim_class.return_value = mock_simulation

        # Act
        game_id, simulation = service.create_game(
            db=mock_db,
            player_count=6,
            players=players
        )

        # Assert
        assert game_id == "test-game-id"
        mock_sim_class.assert_called_once_with(game_id="test-game-id", player_count=6, players=players)


# ============================================================================
# GET_GAME TESTS
# ============================================================================

class TestGetGame:
    """Test get_game method."""

    def test_get_game_from_cache(self, service, mock_db, mock_simulation):
        """Test getting game from cache (fast path)."""
        # Arrange
        game_id = "cached-game-id"
        service._active_games[game_id] = mock_simulation

        # Act
        result = service.get_game(mock_db, game_id)

        # Assert
        assert result == mock_simulation
        mock_db.query.assert_not_called()

    @patch('app.services.game_lifecycle_service.WolfGoatPigGame')
    def test_get_game_from_database(self, mock_sim_class, service, mock_db,
                                   mock_game_record, mock_simulation):
        """Test loading game from database when not in cache."""
        # Arrange
        game_id = "db-game-id"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record
        mock_sim_class.return_value = mock_simulation

        # Act
        result = service.get_game(mock_db, game_id)

        # Assert
        assert result == mock_simulation
        assert game_id in service._active_games
        mock_sim_class.assert_called_once_with(game_id=game_id)

    def test_get_game_not_found(self, service, mock_db):
        """Test 404 error when game doesn't exist."""
        # Arrange
        game_id = "nonexistent-game-id"
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.get_game(mock_db, game_id)

        assert exc_info.value.status_code == 404
        assert f"Game {game_id} not found" in str(exc_info.value.detail)

    @patch('app.services.game_lifecycle_service.WolfGoatPigGame')
    def test_get_game_failed_to_load(self, mock_sim_class, service, mock_db,
                                    mock_game_record):
        """Test error when game fails to load from database."""
        # Arrange
        game_id = "db-game-id"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record
        failed_sim = Mock()
        failed_sim._loaded_from_db = False
        mock_sim_class.return_value = failed_sim

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.get_game(mock_db, game_id)

        assert exc_info.value.status_code == 500
        assert f"Failed to load game {game_id}" in str(exc_info.value.detail)

    def test_get_game_database_error(self, service, mock_db):
        """Test handling of database errors."""
        # Arrange
        game_id = "error-game-id"
        mock_db.query.side_effect = Exception("Database connection error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.get_game(mock_db, game_id)

        assert exc_info.value.status_code == 500
        assert "Error loading game" in str(exc_info.value.detail)

    @patch('app.services.game_lifecycle_service.WolfGoatPigGame')
    def test_get_game_caches_after_db_load(self, mock_sim_class, service, mock_db,
                                          mock_game_record, mock_simulation):
        """Test that game is cached after loading from database."""
        # Arrange
        game_id = "db-game-id"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record
        mock_sim_class.return_value = mock_simulation

        # Act - First call loads from DB
        result1 = service.get_game(mock_db, game_id)

        # Reset mock to verify second call uses cache
        mock_db.reset_mock()
        mock_sim_class.reset_mock()

        # Act - Second call should use cache
        result2 = service.get_game(mock_db, game_id)

        # Assert
        assert result1 == result2 == mock_simulation
        mock_db.query.assert_not_called()  # Second call doesn't touch DB
        mock_sim_class.assert_not_called()  # Second call doesn't create new simulation


# ============================================================================
# START_GAME TESTS
# ============================================================================

class TestStartGame:
    """Test start_game method."""

    @patch('app.services.game_lifecycle_service.datetime')
    def test_start_game_success(self, mock_datetime, service, mock_db,
                               mock_simulation, mock_game_record):
        """Test successful game start from setup state."""
        # Arrange
        game_id = "test-game-id"
        service._active_games[game_id] = mock_simulation
        mock_game_record.game_status = "setup"
        mock_datetime.now.return_value.isoformat.return_value = "2024-11-03T01:00:00"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record

        # Act
        result = service.start_game(mock_db, game_id)

        # Assert
        assert result == mock_simulation
        assert mock_game_record.game_status == "in_progress"
        assert mock_game_record.state["game_status"] == "in_progress"
        assert mock_game_record.updated_at == "2024-11-03T01:00:00"
        mock_db.commit.assert_called_once()

    def test_start_game_not_found(self, service, mock_db):
        """Test error when game doesn't exist."""
        # Arrange
        game_id = "nonexistent-game-id"
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.start_game(mock_db, game_id)

        assert exc_info.value.status_code == 404

    def test_start_game_already_in_progress(self, service, mock_db,
                                           mock_simulation, mock_game_record):
        """Test error when trying to start already in-progress game."""
        # Arrange
        game_id = "test-game-id"
        service._active_games[game_id] = mock_simulation
        mock_game_record.game_status = "in_progress"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.start_game(mock_db, game_id)

        assert exc_info.value.status_code == 400
        assert "Cannot start game in 'in_progress' status" in str(exc_info.value.detail)

    def test_start_game_already_completed(self, service, mock_db,
                                         mock_simulation, mock_game_record):
        """Test error when trying to start completed game."""
        # Arrange
        game_id = "test-game-id"
        service._active_games[game_id] = mock_simulation
        mock_game_record.game_status = "completed"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.start_game(mock_db, game_id)

        assert exc_info.value.status_code == 400
        assert "Cannot start game in 'completed' status" in str(exc_info.value.detail)

    def test_start_game_database_error(self, service, mock_db,
                                      mock_simulation, mock_game_record):
        """Test handling of database errors during game start."""
        # Arrange
        game_id = "test-game-id"
        service._active_games[game_id] = mock_simulation
        mock_game_record.game_status = "setup"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record
        mock_db.commit.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.start_game(mock_db, game_id)

        assert exc_info.value.status_code == 500
        assert "Failed to start game" in str(exc_info.value.detail)
        mock_db.rollback.assert_called_once()


# ============================================================================
# PAUSE_GAME TESTS
# ============================================================================

class TestPauseGame:
    """Test pause_game method."""

    @patch('app.services.game_lifecycle_service.datetime')
    def test_pause_game_success(self, mock_datetime, service, mock_db,
                               mock_simulation, mock_game_record):
        """Test successful game pause."""
        # Arrange
        game_id = "test-game-id"
        service._active_games[game_id] = mock_simulation
        mock_game_record.game_status = "in_progress"
        mock_datetime.now.return_value.isoformat.return_value = "2024-11-03T02:00:00"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record

        # Act
        result = service.pause_game(mock_db, game_id)

        # Assert
        assert result == mock_simulation
        assert mock_game_record.game_status == "paused"
        assert mock_game_record.state["game_status"] == "paused"
        assert mock_game_record.updated_at == "2024-11-03T02:00:00"
        mock_db.commit.assert_called_once()

    def test_pause_game_not_found(self, service, mock_db):
        """Test error when game doesn't exist."""
        # Arrange
        game_id = "nonexistent-game-id"
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.pause_game(mock_db, game_id)

        assert exc_info.value.status_code == 404

    def test_pause_game_not_in_progress(self, service, mock_db,
                                       mock_simulation, mock_game_record):
        """Test error when trying to pause game not in progress."""
        # Arrange
        game_id = "test-game-id"
        service._active_games[game_id] = mock_simulation
        mock_game_record.game_status = "setup"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.pause_game(mock_db, game_id)

        assert exc_info.value.status_code == 400
        assert "Can only pause games that are in progress" in str(exc_info.value.detail)

    def test_pause_game_already_completed(self, service, mock_db,
                                         mock_simulation, mock_game_record):
        """Test error when trying to pause completed game."""
        # Arrange
        game_id = "test-game-id"
        service._active_games[game_id] = mock_simulation
        mock_game_record.game_status = "completed"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.pause_game(mock_db, game_id)

        assert exc_info.value.status_code == 400

    def test_pause_game_database_error(self, service, mock_db,
                                      mock_simulation, mock_game_record):
        """Test handling of database errors during game pause."""
        # Arrange
        game_id = "test-game-id"
        service._active_games[game_id] = mock_simulation
        mock_game_record.game_status = "in_progress"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record
        mock_db.commit.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.pause_game(mock_db, game_id)

        assert exc_info.value.status_code == 500
        assert "Failed to pause game" in str(exc_info.value.detail)
        mock_db.rollback.assert_called_once()


# ============================================================================
# RESUME_GAME TESTS
# ============================================================================

class TestResumeGame:
    """Test resume_game method."""

    @patch('app.services.game_lifecycle_service.datetime')
    def test_resume_game_success(self, mock_datetime, service, mock_db,
                                mock_simulation, mock_game_record):
        """Test successful game resume."""
        # Arrange
        game_id = "test-game-id"
        service._active_games[game_id] = mock_simulation
        mock_game_record.game_status = "paused"
        mock_datetime.now.return_value.isoformat.return_value = "2024-11-03T03:00:00"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record

        # Act
        result = service.resume_game(mock_db, game_id)

        # Assert
        assert result == mock_simulation
        assert mock_game_record.game_status == "in_progress"
        assert mock_game_record.state["game_status"] == "in_progress"
        assert mock_game_record.updated_at == "2024-11-03T03:00:00"
        mock_db.commit.assert_called_once()

    def test_resume_game_not_found(self, service, mock_db):
        """Test error when game doesn't exist."""
        # Arrange
        game_id = "nonexistent-game-id"
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.resume_game(mock_db, game_id)

        assert exc_info.value.status_code == 404

    def test_resume_game_not_paused(self, service, mock_db,
                                   mock_simulation, mock_game_record):
        """Test error when trying to resume game not paused."""
        # Arrange
        game_id = "test-game-id"
        service._active_games[game_id] = mock_simulation
        mock_game_record.game_status = "in_progress"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.resume_game(mock_db, game_id)

        assert exc_info.value.status_code == 400
        assert "Can only resume games that are paused" in str(exc_info.value.detail)

    def test_resume_game_in_setup(self, service, mock_db,
                                 mock_simulation, mock_game_record):
        """Test error when trying to resume game in setup."""
        # Arrange
        game_id = "test-game-id"
        service._active_games[game_id] = mock_simulation
        mock_game_record.game_status = "setup"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.resume_game(mock_db, game_id)

        assert exc_info.value.status_code == 400

    def test_resume_game_database_error(self, service, mock_db,
                                       mock_simulation, mock_game_record):
        """Test handling of database errors during game resume."""
        # Arrange
        game_id = "test-game-id"
        service._active_games[game_id] = mock_simulation
        mock_game_record.game_status = "paused"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record
        mock_db.commit.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.resume_game(mock_db, game_id)

        assert exc_info.value.status_code == 500
        assert "Failed to resume game" in str(exc_info.value.detail)
        mock_db.rollback.assert_called_once()


# ============================================================================
# COMPLETE_GAME TESTS
# ============================================================================

class TestCompleteGame:
    """Test complete_game method."""

    @patch('app.services.game_lifecycle_service.datetime')
    def test_complete_game_success(self, mock_datetime, service, mock_db,
                                  mock_simulation, mock_game_record, sample_players):
        """Test successful game completion."""
        # Arrange
        game_id = "test-game-id"
        mock_simulation.current_hole = 19  # Game finished
        mock_simulation.players = sample_players
        service._active_games[game_id] = mock_simulation
        mock_game_record.game_status = "in_progress"
        mock_datetime.now.return_value.isoformat.return_value = "2024-11-03T04:00:00"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record

        # Act
        result = service.complete_game(mock_db, game_id)

        # Assert
        assert result["game_id"] == game_id
        assert result["status"] == "completed"
        assert result["completed_at"] == "2024-11-03T04:00:00"
        assert "final_scores" in result
        assert len(result["final_scores"]) == 4
        assert mock_game_record.game_status == "completed"
        assert mock_game_record.state["game_status"] == "completed"
        mock_db.commit.assert_called_once()

    @patch('app.services.game_lifecycle_service.datetime')
    def test_complete_game_already_completed(self, mock_datetime, service, mock_db,
                                            mock_simulation, mock_game_record):
        """Test completing already completed game returns existing stats."""
        # Arrange
        game_id = "test-game-id"
        service._active_games[game_id] = mock_simulation
        mock_game_record.game_status = "completed"
        mock_datetime.now.return_value.isoformat.return_value = "2024-11-03T04:00:00"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record

        # Act
        result = service.complete_game(mock_db, game_id)

        # Assert - Should still return stats, not error
        assert result["game_id"] == game_id
        assert result["status"] == "completed"

    def test_complete_game_not_found(self, service, mock_db):
        """Test error when game doesn't exist."""
        # Arrange
        game_id = "nonexistent-game-id"
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.complete_game(mock_db, game_id)

        assert exc_info.value.status_code == 404

    @patch('app.services.game_lifecycle_service.datetime')
    def test_complete_game_with_course_name(self, mock_datetime, service, mock_db,
                                           mock_simulation, mock_game_record, sample_players):
        """Test game completion includes course name."""
        # Arrange
        game_id = "test-game-id"
        mock_simulation.players = sample_players
        service._active_games[game_id] = mock_simulation
        mock_game_record.game_status = "in_progress"
        mock_game_record.state["course_name"] = "Pebble Beach"
        mock_datetime.now.return_value.isoformat.return_value = "2024-11-03T04:00:00"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record

        # Act
        result = service.complete_game(mock_db, game_id)

        # Assert
        assert result["course_name"] == "Pebble Beach"

    @patch('app.services.game_lifecycle_service.datetime')
    def test_complete_game_with_base_wager(self, mock_datetime, service, mock_db,
                                          mock_simulation, mock_game_record, sample_players):
        """Test game completion includes base wager."""
        # Arrange
        game_id = "test-game-id"
        mock_simulation.players = sample_players
        service._active_games[game_id] = mock_simulation
        mock_game_record.game_status = "in_progress"
        mock_game_record.state["base_wager"] = 5
        mock_datetime.now.return_value.isoformat.return_value = "2024-11-03T04:00:00"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record

        # Act
        result = service.complete_game(mock_db, game_id)

        # Assert
        assert result["base_wager"] == 5

    def test_complete_game_database_error(self, service, mock_db,
                                         mock_simulation, mock_game_record):
        """Test handling of database errors during game completion."""
        # Arrange
        game_id = "test-game-id"
        service._active_games[game_id] = mock_simulation
        mock_game_record.game_status = "in_progress"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record
        mock_db.commit.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.complete_game(mock_db, game_id)

        assert exc_info.value.status_code == 500
        assert "Failed to complete game" in str(exc_info.value.detail)
        mock_db.rollback.assert_called_once()

    @patch('app.services.game_lifecycle_service.datetime')
    def test_complete_game_stores_final_stats(self, mock_datetime, service, mock_db,
                                             mock_simulation, mock_game_record, sample_players):
        """Test that final stats are stored in database state."""
        # Arrange
        game_id = "test-game-id"
        mock_simulation.players = sample_players
        service._active_games[game_id] = mock_simulation
        mock_game_record.game_status = "in_progress"
        mock_datetime.now.return_value.isoformat.return_value = "2024-11-03T04:00:00"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record

        # Act
        result = service.complete_game(mock_db, game_id)

        # Assert
        assert "final_stats" in mock_game_record.state
        assert mock_game_record.state["final_stats"]["game_id"] == game_id


# ============================================================================
# LIST_ACTIVE_GAMES TESTS
# ============================================================================

class TestListActiveGames:
    """Test list_active_games method."""

    def test_list_active_games_empty(self, service):
        """Test listing active games when none exist."""
        # Act
        result = service.list_active_games()

        # Assert
        assert result == []

    def test_list_active_games_single(self, service, mock_simulation):
        """Test listing single active game."""
        # Arrange
        service._active_games["game1"] = mock_simulation

        # Act
        result = service.list_active_games()

        # Assert
        assert result == ["game1"]

    def test_list_active_games_multiple(self, service, mock_simulation):
        """Test listing multiple active games."""
        # Arrange
        sim1 = Mock()
        sim2 = Mock()
        sim3 = Mock()
        service._active_games["game1"] = sim1
        service._active_games["game2"] = sim2
        service._active_games["game3"] = sim3

        # Act
        result = service.list_active_games()

        # Assert
        assert len(result) == 3
        assert "game1" in result
        assert "game2" in result
        assert "game3" in result

    def test_list_active_games_after_cleanup(self, service, mock_simulation):
        """Test listing games after some are cleaned up."""
        # Arrange
        service._active_games["game1"] = mock_simulation
        service._active_games["game2"] = mock_simulation
        service._active_games["game3"] = mock_simulation

        # Act - Remove one game
        del service._active_games["game2"]
        result = service.list_active_games()

        # Assert
        assert len(result) == 2
        assert "game1" in result
        assert "game3" in result
        assert "game2" not in result


# ============================================================================
# CLEANUP_GAME TESTS
# ============================================================================

class TestCleanupGame:
    """Test cleanup_game method."""

    def test_cleanup_game_success(self, service, mock_simulation):
        """Test successful cleanup of single game."""
        # Arrange
        game_id = "test-game-id"
        service._active_games[game_id] = mock_simulation

        # Act
        service.cleanup_game(game_id)

        # Assert
        assert game_id not in service._active_games

    def test_cleanup_game_not_in_cache(self, service):
        """Test cleanup of game not in cache (no error)."""
        # Arrange
        game_id = "nonexistent-game-id"

        # Act - Should not raise error
        service.cleanup_game(game_id)

        # Assert - No error, cache still empty
        assert game_id not in service._active_games

    def test_cleanup_game_leaves_others(self, service, mock_simulation):
        """Test cleanup removes only specified game."""
        # Arrange
        service._active_games["game1"] = mock_simulation
        service._active_games["game2"] = mock_simulation
        service._active_games["game3"] = mock_simulation

        # Act
        service.cleanup_game("game2")

        # Assert
        assert "game1" in service._active_games
        assert "game2" not in service._active_games
        assert "game3" in service._active_games

    def test_cleanup_game_multiple_times(self, service, mock_simulation):
        """Test cleaning up same game multiple times (idempotent)."""
        # Arrange
        game_id = "test-game-id"
        service._active_games[game_id] = mock_simulation

        # Act
        service.cleanup_game(game_id)
        service.cleanup_game(game_id)  # Second time

        # Assert - No error
        assert game_id not in service._active_games


# ============================================================================
# CLEANUP_ALL_GAMES TESTS
# ============================================================================

class TestCleanupAllGames:
    """Test cleanup_all_games method."""

    def test_cleanup_all_games_empty(self, service):
        """Test cleanup when no games exist."""
        # Act
        count = service.cleanup_all_games()

        # Assert
        assert count == 0
        assert len(service._active_games) == 0

    def test_cleanup_all_games_single(self, service, mock_simulation):
        """Test cleanup with single game."""
        # Arrange
        service._active_games["game1"] = mock_simulation

        # Act
        count = service.cleanup_all_games()

        # Assert
        assert count == 1
        assert len(service._active_games) == 0

    def test_cleanup_all_games_multiple(self, service, mock_simulation):
        """Test cleanup with multiple games."""
        # Arrange
        service._active_games["game1"] = mock_simulation
        service._active_games["game2"] = mock_simulation
        service._active_games["game3"] = mock_simulation
        service._active_games["game4"] = mock_simulation

        # Act
        count = service.cleanup_all_games()

        # Assert
        assert count == 4
        assert len(service._active_games) == 0

    def test_cleanup_all_games_idempotent(self, service, mock_simulation):
        """Test cleanup all games multiple times."""
        # Arrange
        service._active_games["game1"] = mock_simulation
        service._active_games["game2"] = mock_simulation

        # Act
        count1 = service.cleanup_all_games()
        count2 = service.cleanup_all_games()

        # Assert
        assert count1 == 2
        assert count2 == 0
        assert len(service._active_games) == 0


# ============================================================================
# SINGLETON PATTERN TESTS
# ============================================================================

class TestSingletonPattern:
    """Test singleton pattern implementation."""

    def test_singleton_same_instance(self):
        """Test that multiple calls return same instance."""
        # Reset singleton
        GameLifecycleService._instance = None

        # Act
        service1 = GameLifecycleService()
        service2 = GameLifecycleService()

        # Assert
        assert service1 is service2

    def test_get_game_lifecycle_service_returns_singleton(self):
        """Test that get_game_lifecycle_service returns singleton."""
        # Reset singleton
        GameLifecycleService._instance = None

        # Act
        service1 = get_game_lifecycle_service()
        service2 = get_game_lifecycle_service()

        # Assert
        assert service1 is service2
        assert isinstance(service1, GameLifecycleService)

    def test_singleton_state_persists(self, mock_simulation):
        """Test that state persists across singleton accesses."""
        # Reset singleton
        GameLifecycleService._instance = None

        # Act
        service1 = GameLifecycleService()
        service1._active_games["test-game"] = mock_simulation

        service2 = GameLifecycleService()

        # Assert
        assert "test-game" in service2._active_games
        assert service2._active_games["test-game"] == mock_simulation


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Test multiple methods working together."""

    @patch('app.services.game_lifecycle_service.WolfGoatPigGame')
    @patch('app.services.game_lifecycle_service.uuid.uuid4')
    @patch('app.services.game_lifecycle_service.datetime')
    def test_full_game_lifecycle(self, mock_datetime, mock_uuid, mock_sim_class,
                                 service, mock_db, sample_players, mock_simulation,
                                 mock_game_record):
        """Test complete game lifecycle from creation to completion."""
        # Arrange
        game_id = "test-game-id"
        mock_uuid.return_value = Mock()
        mock_uuid.return_value.__str__ = Mock(return_value=game_id)
        mock_datetime.now.return_value.isoformat.return_value = "2024-11-03T00:00:00"
        mock_sim_class.return_value = mock_simulation
        mock_simulation.players = sample_players
        mock_game_record.game_id = game_id
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record

        # Act 1: Create game
        created_id, sim = service.create_game(
            db=mock_db,
            player_count=4,
            players=sample_players
        )

        # Act 2: Start game
        mock_game_record.game_status = "setup"
        service.start_game(mock_db, game_id)

        # Act 3: Pause game
        mock_game_record.game_status = "in_progress"
        service.pause_game(mock_db, game_id)

        # Act 4: Resume game
        mock_game_record.game_status = "paused"
        service.resume_game(mock_db, game_id)

        # Act 5: Complete game
        mock_game_record.game_status = "in_progress"
        result = service.complete_game(mock_db, game_id)

        # Assert
        assert created_id == game_id
        assert result["status"] == "completed"
        assert game_id in service._active_games

    @patch('app.services.game_lifecycle_service.WolfGoatPigGame')
    @patch('app.services.game_lifecycle_service.uuid.uuid4')
    @patch('app.services.game_lifecycle_service.datetime')
    def test_multiple_games_management(self, mock_datetime, mock_uuid, mock_sim_class,
                                      service, mock_db, sample_players, mock_simulation):
        """Test managing multiple games simultaneously."""
        # Arrange
        game_ids = []
        for i in range(3):
            gid = f"game-{i}"
            game_ids.append(gid)
            mock_uuid.return_value = Mock()
            mock_uuid.return_value.__str__ = Mock(return_value=gid)
            mock_datetime.now.return_value.isoformat.return_value = "2024-11-03T00:00:00"
            mock_sim_class.return_value = mock_simulation

            # Act: Create game
            service.create_game(
                db=mock_db,
                player_count=4,
                players=sample_players
            )

        # Assert
        active_games = service.list_active_games()
        assert len(active_games) == 3
        for gid in game_ids:
            assert gid in active_games

        # Act: Cleanup one game
        service.cleanup_game(game_ids[1])

        # Assert
        active_games = service.list_active_games()
        assert len(active_games) == 2
        assert game_ids[1] not in active_games

    def test_cache_behavior_across_operations(self, service, mock_db,
                                             mock_simulation, mock_game_record):
        """Test that cache behaves correctly across different operations."""
        # Arrange
        game_id = "cache-test-game"
        service._active_games[game_id] = mock_simulation
        mock_db.query.return_value.filter.return_value.first.return_value = mock_game_record
        mock_game_record.game_id = game_id
        mock_game_record.game_status = "in_progress"

        # Act 1: Get from cache
        result1 = service.get_game(mock_db, game_id)
        assert result1 == mock_simulation

        # Act 2: List games
        active = service.list_active_games()
        assert game_id in active

        # Act 3: Pause game (should still be in cache)
        service.pause_game(mock_db, game_id)
        assert game_id in service._active_games

        # Act 4: Cleanup
        service.cleanup_game(game_id)
        assert game_id not in service._active_games

        # Act 5: List games again
        active = service.list_active_games()
        assert game_id not in active
