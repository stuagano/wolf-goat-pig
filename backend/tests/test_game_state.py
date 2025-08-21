"""
Comprehensive tests for game_state.py - Core game state management

Tests cover:
- Game state initialization and reset
- Action dispatching and validation
- Player management integration
- Betting state integration
- Score recording and point calculation
- Hole progression and state transitions
- Database persistence (serialization/deserialization)
- Course management integration
- Error handling and edge cases
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.app.game_state import GameState, DEFAULT_PLAYERS
from backend.app.domain.player import Player
from backend.app.state.betting_state import BettingState
from backend.app.state.player_manager import PlayerManager
from backend.app.state.course_manager import CourseManager
from backend.app.state.shot_state import ShotState
from backend.app.models import GameStateModel


class TestGameStateInitialization:
    """Test game state initialization and setup"""
    
    def test_game_state_init_with_defaults(self):
        """Test default initialization"""
        with patch('backend.app.game_state.SessionLocal') as mock_session:
            mock_session.return_value.query.return_value.get.return_value = None
            
            game_state = GameState()
            
            assert game_state.current_hole == 1
            assert isinstance(game_state.player_manager, PlayerManager)
            assert isinstance(game_state.betting_state, BettingState)
            assert isinstance(game_state.course_manager, CourseManager)
            assert isinstance(game_state.shot_state, ShotState)
            assert game_state.game_status_message == "Time to toss the tees!"
            assert not game_state.carry_over
            assert len(game_state.hole_history) == 0

    def test_game_state_init_with_db_load(self):
        """Test initialization with existing database state"""
        with patch('backend.app.game_state.SessionLocal') as mock_session:
            mock_db_state = {
                "current_hole": 5,
                "game_status_message": "Test message",
                "carry_over": True,
                "hole_history": [{"hole": 1}]
            }
            mock_obj = Mock()
            mock_obj.state = mock_db_state
            mock_session.return_value.query.return_value.get.return_value = mock_obj
            
            game_state = GameState()
            
            assert game_state.current_hole == 5
            assert game_state.game_status_message == "Test message"
            assert game_state.carry_over == True
            assert len(game_state.hole_history) == 1

    def test_game_state_init_with_db_error(self):
        """Test initialization handles database errors gracefully"""
        with patch('backend.app.game_state.SessionLocal') as mock_session:
            mock_session.return_value.query.side_effect = Exception("DB Error")
            
            game_state = GameState()
            
            # Should fall back to default state
            assert game_state.current_hole == 1
            assert game_state.game_status_message == "Time to toss the tees!"

    def test_reset_functionality(self):
        """Test game state reset"""
        with patch('backend.app.game_state.SessionLocal'):
            game_state = GameState()
            
            # Modify state
            game_state.current_hole = 10
            game_state.carry_over = True
            game_state.hole_history = [{"hole": 1}]
            
            # Reset
            game_state.reset()
            
            assert game_state.current_hole == 1
            assert not game_state.carry_over
            assert len(game_state.hole_history) == 0
            assert game_state.game_status_message == "Time to toss the tees!"


class TestActionDispatcher:
    """Test action dispatching system"""
    
    @pytest.fixture
    def game_state(self):
        with patch('backend.app.game_state.SessionLocal'):
            return GameState()
    
    def test_betting_action_dispatch(self, game_state):
        """Test betting actions are dispatched to betting state"""
        with patch.object(game_state.betting_state, 'dispatch_action', return_value="Partner request sent."):
            result = game_state.dispatch_action("request_partner", {"captain_id": "p1", "partner_id": "p2"})
            
            assert "request sent" in result.lower()
            game_state.betting_state.dispatch_action.assert_called_once()

    def test_invoke_float_action(self, game_state):
        """Test float invocation"""
        # Mock player with float available
        test_player = Mock()
        test_player.id = "p1"
        test_player.use_float.return_value = True
        game_state.player_manager.players = [test_player]
        
        result = game_state.dispatch_action("invoke_float", {"captain_id": "p1"})
        
        assert result == "Float invoked."
        assert game_state.betting_state.base_wager == 2  # Should be doubled
        test_player.use_float.assert_called_once()

    def test_invoke_float_already_used(self, game_state):
        """Test float invocation when already used"""
        test_player = Mock()
        test_player.id = "p1"
        test_player.use_float.return_value = False
        game_state.player_manager.players = [test_player]
        
        with pytest.raises(ValueError, match="Float already used"):
            game_state.dispatch_action("invoke_float", {"captain_id": "p1"})

    def test_invoke_float_invalid_captain(self, game_state):
        """Test float invocation with invalid captain"""
        with pytest.raises(ValueError, match="Captain not found"):
            game_state.dispatch_action("invoke_float", {"captain_id": "invalid"})

    def test_toggle_option_action(self, game_state):
        """Test option toggle"""
        result = game_state.dispatch_action("toggle_option", {"captain_id": "p1"})
        
        assert result == "Option toggled."
        assert game_state.betting_state.base_wager == 2  # Should be doubled

    def test_record_net_score_action(self, game_state):
        """Test score recording"""
        result = game_state.dispatch_action("record_net_score", {"player_id": "p1", "score": 4})
        
        assert result == "Score recorded."
        assert game_state.hole_scores["p1"] == 4

    def test_record_net_score_invalid_player(self, game_state):
        """Test score recording with invalid player"""
        with pytest.raises(ValueError, match="Invalid player ID"):
            game_state.dispatch_action("record_net_score", {"player_id": "invalid", "score": 4})

    def test_calculate_hole_points_action(self, game_state):
        """Test hole points calculation"""
        with patch.object(game_state.betting_state, 'calculate_hole_points', return_value="Points calculated"):
            result = game_state.dispatch_action("calculate_hole_points", {})
            
            assert result == "Points calculated"
            game_state.betting_state.calculate_hole_points.assert_called_once()

    def test_next_hole_action(self, game_state):
        """Test hole progression"""
        result = game_state.dispatch_action("next_hole", {})
        
        assert result == "Advanced to next hole."
        assert game_state.current_hole == 2

    def test_unknown_action(self, game_state):
        """Test unknown action handling"""
        with pytest.raises(ValueError, match="Unknown action: invalid_action"):
            game_state.dispatch_action("invalid_action", {})


class TestScoreManagement:
    """Test score recording and management"""
    
    @pytest.fixture
    def game_state(self):
        with patch('backend.app.game_state.SessionLocal'):
            return GameState()
    
    def test_record_net_score_valid(self, game_state):
        """Test valid score recording"""
        result = game_state.record_net_score("p1", 4)
        
        assert result == "Score recorded."
        assert game_state.hole_scores["p1"] == 4

    def test_record_net_score_updates_player(self, game_state):
        """Test score recording updates player object"""
        # Mock the player to verify score recording
        test_player = Mock()
        test_player.id = "p1"
        test_player.record_hole_score = Mock()
        game_state.player_manager.players = [test_player]
        
        game_state.record_net_score("p1", 4)
        
        test_player.record_hole_score.assert_called_once_with(1, 4)

    def test_calculate_hole_points_with_history(self, game_state):
        """Test hole points calculation creates history"""
        # Set up some scores
        game_state.hole_scores = {"p1": 4, "p2": 5, "p3": 3, "p4": 6}
        
        # Mock betting state calculation
        with patch.object(game_state.betting_state, 'calculate_hole_points', return_value="Test result"):
            result = game_state.calculate_hole_points()
            
            assert result == "Test result"
            assert len(game_state.hole_history) == 1
            
            history_entry = game_state.hole_history[0]
            assert history_entry["hole"] == 1
            assert history_entry["net_scores"] == {"p1": 4, "p2": 5, "p3": 3, "p4": 6}


class TestHoleProgression:
    """Test hole progression and state transitions"""
    
    @pytest.fixture
    def game_state(self):
        with patch('backend.app.game_state.SessionLocal'):
            return GameState()
    
    def test_next_hole_progression(self, game_state):
        """Test advancing to next hole"""
        initial_hole = game_state.current_hole
        
        with patch.object(game_state.player_manager, 'rotate_captain'):
            with patch.object(game_state.betting_state, 'reset_hole'):
                result = game_state.next_hole()
        
        assert result == "Advanced to next hole."
        assert game_state.current_hole == initial_hole + 1
        game_state.player_manager.rotate_captain.assert_called_once()
        game_state.betting_state.reset_hole.assert_called_once()

    def test_next_hole_resets_scores(self, game_state):
        """Test next hole resets hole scores"""
        game_state.hole_scores = {"p1": 4, "p2": 5, "p3": 3, "p4": 6}
        
        game_state.next_hole()
        
        for player_id in game_state.hole_scores:
            assert game_state.hole_scores[player_id] is None

    def test_next_hole_resets_float_usage(self, game_state):
        """Test next hole resets float usage for all players"""
        # Mock players with float reset method
        for player in game_state.player_manager.players:
            player.reset_float = Mock()
        
        game_state.next_hole()
        
        for player in game_state.player_manager.players:
            player.reset_float.assert_called_once()

    def test_next_hole_resets_shot_state(self, game_state):
        """Test next hole resets shot state"""
        with patch.object(game_state.shot_state, 'reset_for_hole') as mock_reset:
            game_state.next_hole()
            mock_reset.assert_called_once()


class TestPlayerSetup:
    """Test player setup and management"""
    
    @pytest.fixture
    def game_state(self):
        with patch('backend.app.game_state.SessionLocal'):
            return GameState()
    
    def test_setup_players_valid(self, game_state):
        """Test valid player setup"""
        players = [
            {"id": "p1", "name": "Alice", "handicap": 10.0, "strength": "Strong"},
            {"id": "p2", "name": "Bob", "handicap": 15.0, "strength": "Medium"},
            {"id": "p3", "name": "Charlie", "handicap": 8.0, "strength": "Strong"},
            {"id": "p4", "name": "Dave", "handicap": 20.0, "strength": "Weak"}
        ]
        
        with patch.object(game_state.player_manager, 'setup_players'):
            game_state.setup_players(players)
        
        assert game_state.current_hole == 1
        assert game_state.game_status_message == "Players set. Time to toss the tees!"
        game_state.player_manager.setup_players.assert_called_once()

    def test_setup_players_with_course(self, game_state):
        """Test player setup with course selection"""
        players = [
            {"id": "p1", "name": "Alice", "handicap": 10.0, "strength": "Strong"},
            {"id": "p2", "name": "Bob", "handicap": 15.0, "strength": "Medium"},
            {"id": "p3", "name": "Charlie", "handicap": 8.0, "strength": "Strong"},
            {"id": "p4", "name": "Dave", "handicap": 20.0, "strength": "Weak"}
        ]
        
        with patch.object(game_state.course_manager, 'load_course') as mock_load:
            game_state.setup_players(players, "Test Course")
            mock_load.assert_called_once_with("Test Course")

    def test_setup_players_wrong_count(self, game_state):
        """Test player setup with wrong player count"""
        players = [
            {"id": "p1", "name": "Alice", "handicap": 10.0, "strength": "Strong"},
            {"id": "p2", "name": "Bob", "handicap": 15.0, "strength": "Medium"}
        ]
        
        with pytest.raises(ValueError, match="Exactly 4 players required"):
            game_state.setup_players(players)

    def test_setup_players_missing_fields(self, game_state):
        """Test player setup with missing required fields"""
        players = [
            {"id": "p1", "name": "Alice", "handicap": 10.0},  # Missing strength
            {"id": "p2", "name": "Bob", "handicap": 15.0, "strength": "Medium"},
            {"id": "p3", "name": "Charlie", "handicap": 8.0, "strength": "Strong"},
            {"id": "p4", "name": "Dave", "handicap": 20.0, "strength": "Weak"}
        ]
        
        with pytest.raises(ValueError, match="Each player must have id, name, handicap, and strength"):
            game_state.setup_players(players)


class TestStrokeCalculation:
    """Test handicap stroke calculations"""
    
    @pytest.fixture
    def game_state(self):
        with patch('backend.app.game_state.SessionLocal'):
            gs = GameState()
            # Mock course with known stroke indexes
            gs.course_manager.hole_stroke_indexes = list(range(1, 19))  # 1, 2, 3, ..., 18
            return gs
    
    def test_get_player_strokes_basic(self, game_state):
        """Test basic stroke calculation"""
        # Player with handicap 9 should get strokes on holes with indexes 1-9
        player = Player(id="test", name="Test", handicap=9.0)
        game_state.player_manager.players = [player]
        
        strokes = game_state.get_player_strokes()
        
        assert "test" in strokes
        player_strokes = strokes["test"]
        
        # Should get strokes on holes 1-9 (stroke indexes 1-9)
        for hole in range(1, 10):
            assert player_strokes[hole] == 1
        for hole in range(10, 19):
            assert player_strokes[hole] == 0

    def test_get_player_strokes_half_stroke(self, game_state):
        """Test stroke calculation with half stroke"""
        player = Player(id="test", name="Test", handicap=9.5)
        game_state.player_manager.players = [player]
        
        strokes = game_state.get_player_strokes()
        player_strokes = strokes["test"]
        
        # Should get full strokes on holes 1-9, half stroke on hole 10
        for hole in range(1, 10):
            assert player_strokes[hole] == 1
        assert player_strokes[10] == 0.5
        for hole in range(11, 19):
            assert player_strokes[hole] == 0

    def test_get_player_strokes_high_handicap(self, game_state):
        """Test stroke calculation for high handicap (>18)"""
        player = Player(id="test", name="Test", handicap=20.0)
        game_state.player_manager.players = [player]
        
        strokes = game_state.get_player_strokes()
        player_strokes = strokes["test"]
        
        # Should get 1 stroke on all holes, plus second stroke on hardest 2 holes
        for hole in range(1, 19):
            if hole <= 2:  # Hardest holes (stroke index 1 and 2)
                assert player_strokes[hole] == 2
            else:
                assert player_strokes[hole] == 1


class TestCourseManagement:
    """Test course management integration"""
    
    @pytest.fixture
    def game_state(self):
        with patch('backend.app.game_state.SessionLocal'):
            return GameState()
    
    def test_add_course_valid(self, game_state):
        """Test adding a valid course"""
        course_data = {
            "name": "Test Course",
            "holes": [
                {"hole_number": i, "par": 4, "yards": 400, "stroke_index": i}
                for i in range(1, 19)
            ]
        }
        
        with patch.object(game_state.course_manager, 'add_course') as mock_add:
            with patch.object(game_state.course_manager, 'get_courses', return_value={}):
                result = game_state.add_course(course_data)
        
        assert result == True
        mock_add.assert_called_once()

    def test_add_course_duplicate_name(self, game_state):
        """Test adding course with duplicate name"""
        course_data = {"name": "Existing Course", "holes": []}
        
        with patch.object(game_state.course_manager, 'get_courses', return_value={"Existing Course": {}}):
            with pytest.raises(ValueError, match="Course 'Existing Course' already exists"):
                game_state.add_course(course_data)

    def test_add_course_wrong_hole_count(self, game_state):
        """Test adding course with wrong number of holes"""
        course_data = {
            "name": "Test Course",
            "holes": [{"hole_number": 1, "par": 4, "yards": 400, "stroke_index": 1}]
        }
        
        with pytest.raises(ValueError, match="Course must have exactly 18 holes"):
            game_state.add_course(course_data)

    def test_add_course_invalid_stroke_indexes(self, game_state):
        """Test adding course with invalid stroke indexes"""
        course_data = {
            "name": "Test Course",
            "holes": [
                {"hole_number": i, "par": 4, "yards": 400, "stroke_index": 1}  # All stroke index 1
                for i in range(1, 19)
            ]
        }
        
        with patch.object(game_state.course_manager, 'get_courses', return_value={}):
            with pytest.raises(ValueError, match="Stroke indexes must be unique"):
                game_state.add_course(course_data)


class TestDatabasePersistence:
    """Test database serialization and persistence"""
    
    @pytest.fixture
    def game_state(self):
        with patch('backend.app.game_state.SessionLocal'):
            return GameState()
    
    def test_serialize_basic_state(self, game_state):
        """Test basic state serialization"""
        serialized = game_state._serialize()
        
        assert "current_hole" in serialized
        assert "game_status_message" in serialized
        assert "betting_state" in serialized
        assert "player_manager" in serialized
        assert "hole_scores" in serialized

    def test_serialize_deserialize_roundtrip(self, game_state):
        """Test serialize/deserialize maintains state"""
        # Modify state
        game_state.current_hole = 5
        game_state.game_status_message = "Test message"
        game_state.carry_over = True
        
        # Serialize and deserialize
        serialized = game_state._serialize()
        new_state = GameState()
        new_state._deserialize(serialized)
        
        assert new_state.current_hole == 5
        assert new_state.game_status_message == "Test message"
        assert new_state.carry_over == True

    def test_save_to_db_success(self, game_state):
        """Test successful database save"""
        mock_session = Mock()
        mock_obj = Mock()
        mock_session.query.return_value.get.return_value = mock_obj
        game_state._db_session = mock_session
        
        game_state._save_to_db()
        
        mock_session.commit.assert_called_once()

    def test_save_to_db_new_record(self, game_state):
        """Test database save creates new record when none exists"""
        mock_session = Mock()
        mock_session.query.return_value.get.return_value = None
        game_state._db_session = mock_session
        
        game_state._save_to_db()
        
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_save_to_db_error_handling(self, game_state):
        """Test database save handles errors gracefully"""
        mock_session = Mock()
        mock_session.commit.side_effect = Exception("DB Error")
        game_state._db_session = mock_session
        
        # Should not raise exception
        game_state._save_to_db()

    def test_load_from_db_success(self, game_state):
        """Test successful database load"""
        mock_session = Mock()
        mock_obj = Mock()
        mock_obj.state = {"current_hole": 10, "game_status_message": "Loaded"}
        mock_session.query.return_value.get.return_value = mock_obj
        game_state._db_session = mock_session
        
        game_state._load_from_db()
        
        assert game_state.current_hole == 10
        assert game_state.game_status_message == "Loaded"

    def test_load_from_db_no_data(self, game_state):
        """Test database load when no data exists"""
        mock_session = Mock()
        mock_session.query.return_value.get.return_value = None
        game_state._db_session = mock_session
        
        with patch.object(game_state, 'reset') as mock_reset:
            game_state._load_from_db()
            mock_reset.assert_called_once()

    def test_load_from_db_error_handling(self, game_state):
        """Test database load handles errors gracefully"""
        mock_session = Mock()
        mock_session.query.side_effect = Exception("DB Error")
        game_state._db_session = mock_session
        
        with patch.object(game_state, 'reset') as mock_reset:
            game_state._load_from_db()
            mock_reset.assert_called_once()


class TestUtilityMethods:
    """Test utility and helper methods"""
    
    @pytest.fixture
    def game_state(self):
        with patch('backend.app.game_state.SessionLocal'):
            return GameState()
    
    def test_player_name_lookup(self, game_state):
        """Test player name lookup"""
        # Mock a player
        test_player = Mock()
        test_player.id = "p1"
        test_player.name = "Alice"
        game_state.player_manager.players = [test_player]
        
        name = game_state._player_name("p1")
        assert name == "Alice"
        
        # Test unknown player returns ID
        name = game_state._player_name("unknown")
        assert name == "unknown"

    def test_get_hole_history(self, game_state):
        """Test hole history retrieval"""
        test_history = [{"hole": 1}, {"hole": 2}]
        game_state.hole_history = test_history
        
        history = game_state.get_hole_history()
        assert history == test_history

    def test_get_betting_tips(self, game_state):
        """Test betting tips retrieval"""
        with patch.object(game_state.betting_state, 'get_betting_tips', return_value="Test tips"):
            tips = game_state.get_betting_tips()
            assert tips == "Test tips"

    def test_get_current_hole_info(self, game_state):
        """Test current hole info retrieval"""
        with patch.object(game_state.course_manager, 'get_current_hole_info', return_value={"par": 4}):
            info = game_state.get_current_hole_info()
            assert info == {"par": 4}

    def test_get_hole_difficulty_factor(self, game_state):
        """Test hole difficulty factor calculation"""
        with patch.object(game_state.course_manager, 'get_hole_difficulty_factor', return_value=1.2):
            factor = game_state.get_hole_difficulty_factor(5)
            assert factor == 1.2

    def test_get_human_player_id(self, game_state):
        """Test human player ID retrieval"""
        with patch.object(Player, 'get_human_player_id', return_value="human1"):
            player_id = game_state.get_human_player_id()
            assert player_id == "human1"

    def test_get_state(self, game_state):
        """Test getting current state dictionary"""
        with patch.object(game_state, '_serialize', return_value={"test": "data"}):
            state = game_state.get_state()
            assert state == {"test": "data"}


class TestBackwardCompatibility:
    """Test backward compatibility features"""
    
    @pytest.fixture
    def game_state(self):
        with patch('backend.app.game_state.SessionLocal'):
            return GameState()
    
    def test_deserialize_old_format(self, game_state):
        """Test deserializing old format data"""
        old_data = {
            "players": [
                {"id": "p1", "name": "Alice", "handicap": 10.0},
                {"id": "p2", "name": "Bob", "handicap": 15.0}
            ],
            "hitting_order": ["p1", "p2"],
            "captain_id": "p1",
            "teams": {},
            "base_wager": 2,
            "game_phase": "Regular"
        }
        
        game_state._deserialize(old_data)
        
        assert game_state.player_manager.captain_id == "p1"
        assert game_state.betting_state.base_wager == 2

    def test_deserialize_old_shot_sequence_format(self, game_state):
        """Test deserializing old shot sequence format"""
        old_data = {
            "shot_sequence": {
                "phase": "approach_shots",
                "current_player_index": 2,
                "pending_decisions": ["decision1"],
                "completed_shots": [
                    {"player_id": "p1", "shot_result": {"result": "good"}}
                ]
            }
        }
        
        game_state._deserialize(old_data)
        
        assert game_state.shot_state.phase == "approach_shots"
        assert game_state.shot_state.current_player_index == 2


if __name__ == "__main__":
    pytest.main([__file__])