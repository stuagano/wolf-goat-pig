
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from backend.app.wolf_goat_pig import WolfGoatPigGame, Player
from backend.app.models import GameRecord, GamePlayerResult

class TestGameCompletionPersistence:
    """Test game completion and persistence to database"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        with patch('backend.app.mixins.persistence_mixin.SessionLocal') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session
            yield mock_session

    def test_game_completion_persistence(self, mock_db_session):
        """Test that finishing a game persists GameRecord and GamePlayerResult to DB"""
        
        # 1. Initialize Simulation
        players = [
            Player(id="p1", name="Player 1", handicap=10),
            Player(id="p2", name="Player 2", handicap=15),
            Player(id="p3", name="Player 3", handicap=12),
            Player(id="p4", name="Player 4", handicap=8),
        ]
        
        # Mock _load_from_db to avoid trying to load from real DB
        with patch.object(WolfGoatPigGame, '_load_from_db'):
            sim = WolfGoatPigGame(player_count=4, players=players)

        # 2. Simulate game state at end of hole 18
        sim.current_hole = 18
        # Mock hole states for 18 holes
        sim.hole_states = {i: MagicMock() for i in range(1, 19)}
        
        # Give players some points
        sim.players[0].points = 5
        sim.players[1].points = -2
        sim.players[2].points = 10
        sim.players[3].points = 3
        
        # 3. Advance to next hole (which should trigger finish)
        result = sim.advance_to_next_hole()
        
        # 4. Verify result indicates completion
        assert result["status"] == "game_finished"
        assert "final_scores" in result
        assert "winners" in result
        
        # 5. Verify DB interactions
        # Check that add was called for GameRecord
        # We expect at least one add call for GameRecord, and one for each player (4)
        # Plus potentially intermediate saves, but we care about the final record
        
        # Filter calls to add that involve GameRecord
        game_record_calls = [
            call for call in mock_db_session.add.call_args_list 
            if isinstance(call[0][0], GameRecord)
        ]
        
        assert len(game_record_calls) == 1, "Should have saved exactly one GameRecord"
        
        saved_record = game_record_calls[0][0][0]
        assert saved_record.game_mode == "wolf_goat_pig"
        assert saved_record.player_count == 4
        assert saved_record.total_holes_played == 18
        assert saved_record.final_scores == {
            "p1": 5, "p2": -2, "p3": 10, "p4": 3
        }
        
        # Filter calls for GamePlayerResult
        player_result_calls = [
            call for call in mock_db_session.add.call_args_list 
            if isinstance(call[0][0], GamePlayerResult)
        ]
        
        assert len(player_result_calls) == 4, "Should have saved 4 GamePlayerResults"
        
        # Verify commit was called
        assert mock_db_session.commit.called
