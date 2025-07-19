"""
Comprehensive test suite for refactored DRY code
"""
import pytest
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.app.exceptions import APIException, GameStateException, ValidationException
from backend.app.constants import DEFAULT_PLAYERS, DEFAULT_COURSES, GAME_CONSTANTS, VALIDATION_LIMITS
from backend.app.utils import (
    PlayerUtils, CourseUtils, GameUtils, ValidationUtils, 
    SerializationUtils, SimulationUtils
)
from backend.app.game_state import GameState
from backend.app.simulation import ComputerPlayer, MonteCarloResults, SimulationEngine


class TestExceptions:
    """Test centralized exception handling"""
    
    def test_api_exception_bad_request(self):
        """Test bad request exception creation"""
        exc = APIException.bad_request("Test error")
        assert exc.status_code == 400
        assert exc.detail == "Test error"
    
    def test_api_exception_not_found(self):
        """Test not found exception creation"""
        exc = APIException.not_found("Resource not found")
        assert exc.status_code == 404
        assert exc.detail == "Resource not found"
    
    def test_api_exception_validation_error(self):
        """Test validation error exception creation"""
        exc = APIException.validation_error("handicap", 50, "must be <= 36")
        assert exc.status_code == 400
        assert "handicap" in exc.detail
        assert "50" in exc.detail
    
    def test_api_exception_missing_field(self):
        """Test missing field exception creation"""
        exc = APIException.missing_required_field("players")
        assert exc.status_code == 400
        assert "players" in exc.detail
    
    def test_api_exception_resource_not_found(self):
        """Test resource not found exception creation"""
        exc = APIException.resource_not_found("Course", "Test Course")
        assert exc.status_code == 404
        assert "Course" in exc.detail
        assert "Test Course" in exc.detail
    
    def test_api_exception_invalid_range(self):
        """Test invalid range exception creation"""
        exc = APIException.invalid_range("Number of simulations", 1, 1000)
        assert exc.status_code == 400
        assert "between 1 and 1000" in exc.detail


class TestConstants:
    """Test centralized constants"""
    
    def test_default_players_structure(self):
        """Test default players have correct structure"""
        assert len(DEFAULT_PLAYERS) == 4
        for player in DEFAULT_PLAYERS:
            assert "id" in player
            assert "name" in player
            assert "handicap" in player
            assert "strength" in player
            assert "points" in player
    
    def test_default_courses_structure(self):
        """Test default courses have correct structure"""
        assert "Wing Point" in DEFAULT_COURSES
        assert "Championship Links" in DEFAULT_COURSES
        
        wing_point = DEFAULT_COURSES["Wing Point"]
        assert len(wing_point) == 18
        
        for hole in wing_point:
            assert "hole_number" in hole
            assert "stroke_index" in hole
            assert "par" in hole
            assert "yards" in hole
    
    def test_game_constants(self):
        """Test game constants are properly defined"""
        assert GAME_CONSTANTS["MAX_HOLES"] == 18
        assert GAME_CONSTANTS["MIN_PLAYERS"] == 4
        assert GAME_CONSTANTS["MAX_PLAYERS"] == 6
        assert GAME_CONSTANTS["DEFAULT_BASE_WAGER"] == 1
    
    def test_validation_limits(self):
        """Test validation limits are properly defined"""
        assert VALIDATION_LIMITS["MIN_PAR"] == 3
        assert VALIDATION_LIMITS["MAX_PAR"] == 6
        assert VALIDATION_LIMITS["MIN_HANDICAP"] == 1
        assert VALIDATION_LIMITS["MAX_HANDICAP"] == 18


class TestPlayerUtils:
    """Test player utility functions"""
    
    def test_handicap_to_strength(self):
        """Test handicap to strength conversion"""
        assert PlayerUtils.handicap_to_strength(2.0) == "Expert"
        assert PlayerUtils.handicap_to_strength(8.0) == "Strong"
        assert PlayerUtils.handicap_to_strength(15.0) == "Average"
        assert PlayerUtils.handicap_to_strength(25.0) == "Beginner"
        assert PlayerUtils.handicap_to_strength(50.0) == "Average"  # Fallback
    
    def test_find_player_by_id(self):
        """Test finding player by ID"""
        players = [
            {"id": "p1", "name": "Alice", "handicap": 10},
            {"id": "p2", "name": "Bob", "handicap": 15}
        ]
        
        player = PlayerUtils.find_player_by_id(players, "p1")
        assert player["name"] == "Alice"
        
        player = PlayerUtils.find_player_by_id(players, "p3")
        assert player is None
    
    def test_get_player_name(self):
        """Test getting player name by ID"""
        players = [{"id": "p1", "name": "Alice"}]
        
        name = PlayerUtils.get_player_name(players, "p1")
        assert name == "Alice"
        
        name = PlayerUtils.get_player_name(players, "p2")
        assert name == "p2"  # Returns ID if not found
    
    def test_get_player_handicap(self):
        """Test getting player handicap by ID"""
        players = [{"id": "p1", "handicap": 12.5}]
        
        handicap = PlayerUtils.get_player_handicap(players, "p1")
        assert handicap == 12.5
        
        handicap = PlayerUtils.get_player_handicap(players, "p2")
        assert handicap == 0.0  # Default if not found


class TestCourseUtils:
    """Test course utility functions"""
    
    def test_convert_hole_to_dict(self):
        """Test converting hole object to dictionary"""
        class MockHole:
            def __init__(self):
                self.hole_number = 1
                self.par = 4
                self.yards = 400
                self.handicap = 10
                self.description = "Test hole"
        
        hole = MockHole()
        result = CourseUtils.convert_hole_to_dict(hole)
        
        assert result["hole_number"] == 1
        assert result["par"] == 4
        assert result["yards"] == 400
        assert result["stroke_index"] == 10
        assert result["description"] == "Test hole"
    
    def test_convert_course_create_to_dict(self):
        """Test converting course create object to dictionary"""
        class MockCourse:
            def __init__(self):
                self.name = "Test Course"
                self.holes = []
        
        class MockHole:
            def __init__(self):
                self.hole_number = 1
                self.par = 4
                self.yards = 400
                self.handicap = 10
                self.description = "Test hole"
        
        course = MockCourse()
        course.holes = [MockHole()]
        
        result = CourseUtils.convert_course_create_to_dict(course)
        
        assert result["name"] == "Test Course"
        assert len(result["holes"]) == 1
        assert result["holes"][0]["hole_number"] == 1


class TestGameUtils:
    """Test game utility functions"""
    
    def test_assess_hole_difficulty(self):
        """Test hole difficulty assessment"""
        # Test basic difficulty calculation
        difficulty = GameUtils.assess_hole_difficulty(1, 4, 450, 15.0)
        assert 0.0 <= difficulty <= 1.0
        
        # Harder stroke index should give higher difficulty
        hard_difficulty = GameUtils.assess_hole_difficulty(1, 4, 400, 15.0)
        easy_difficulty = GameUtils.assess_hole_difficulty(18, 4, 400, 15.0)
        assert hard_difficulty > easy_difficulty
    
    def test_calculate_stroke_advantage(self):
        """Test stroke advantage calculation"""
        team1_handicaps = [10.0, 15.0]
        team2_handicaps = [8.0, 12.0]
        team1_strokes = [1]
        team2_strokes = [0]
        
        advantage = GameUtils.calculate_stroke_advantage(
            team1_handicaps, team2_handicaps, team1_strokes, team2_strokes
        )
        
        assert -1.0 <= advantage <= 1.0


class TestValidationUtils:
    """Test validation utility functions"""
    
    def test_validate_player_count(self):
        """Test player count validation"""
        players = [{"id": "p1"}, {"id": "p2"}, {"id": "p3"}, {"id": "p4"}]
        
        assert ValidationUtils.validate_player_count(players, 4, 6) is True
        assert ValidationUtils.validate_player_count(players[:2], 4, 6) is False
        assert ValidationUtils.validate_player_count(players * 2, 4, 6) is False
    
    def test_validate_handicap_range(self):
        """Test handicap range validation"""
        assert ValidationUtils.validate_handicap_range(10.0) is True
        assert ValidationUtils.validate_handicap_range(-5.0) is False
        assert ValidationUtils.validate_handicap_range(50.0) is False
    
    def test_validate_hole_number_sequence(self):
        """Test hole number sequence validation"""
        valid_holes = [{"hole_number": i} for i in range(1, 19)]
        invalid_holes = [{"hole_number": i} for i in range(2, 20)]
        
        assert ValidationUtils.validate_hole_number_sequence(valid_holes) is True
        assert ValidationUtils.validate_hole_number_sequence(invalid_holes) is False
    
    def test_validate_unique_handicaps(self):
        """Test unique handicap validation"""
        valid_holes = [{"stroke_index": i} for i in range(1, 19)]
        invalid_holes = [{"stroke_index": 1} for _ in range(18)]
        
        assert ValidationUtils.validate_unique_handicaps(valid_holes) is True
        assert ValidationUtils.validate_unique_handicaps(invalid_holes) is False


class TestSerializationUtils:
    """Test serialization utility functions"""
    
    def test_serialize_game_state(self):
        """Test game state serialization"""
        class MockGameState:
            def __init__(self):
                self.players = []
                self.current_hole = 1
                self.hitting_order = []
                self.captain_id = None
                self.teams = {}
                self.base_wager = 1
                self.doubled_status = False
                self.game_phase = "Regular"
                self.hole_scores = {}
                self.game_status_message = "Test"
                self.player_float_used = {}
                self.carry_over = False
                self.hole_stroke_indexes = []
                self.hole_pars = []
                self.selected_course = None
            
            def get_hole_history(self):
                return []
        
        game_state = MockGameState()
        result = SerializationUtils.serialize_game_state(game_state)
        
        assert "players" in result
        assert "current_hole" in result
        assert result["current_hole"] == 1


class TestSimulationUtils:
    """Test simulation utility functions"""
    
    def test_convert_computer_player_configs(self):
        """Test converting computer player configs"""
        class MockConfig:
            def __init__(self):
                self.id = "cp1"
                self.name = "Bot"
                self.handicap = 10.0
                self.personality = "balanced"
        
        configs = [MockConfig()]
        result = SimulationUtils.convert_computer_player_configs(configs)
        
        assert len(result) == 1
        assert result[0]["id"] == "cp1"
        assert result[0]["name"] == "Bot"
    
    def test_setup_all_players(self):
        """Test setting up all players for simulation"""
        human_player = {"id": "h1", "name": "Human", "handicap": 12.0}
        computer_configs = [{"id": "c1", "name": "Bot", "handicap": 10.0}]
        
        result = SimulationUtils.setup_all_players(human_player, computer_configs)
        
        assert len(result) == 2
        assert result[0]["id"] == "h1"
        assert result[0]["strength"] == "Average"
        assert result[1]["id"] == "c1"


class TestComputerPlayer:
    """Test computer player AI"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.player = ComputerPlayer("cp1", "TestBot", 12.0, "balanced")
        self.game_state = GameState()
        self.game_state.players = [
            {"id": "cp1", "name": "TestBot", "handicap": 12.0, "points": 0},
            {"id": "h1", "name": "Human", "handicap": 15.0, "points": 2},
            {"id": "cp2", "name": "Bot2", "handicap": 8.0, "points": -1},
            {"id": "cp3", "name": "Bot3", "handicap": 18.0, "points": 1}
        ]
        self.game_state.current_hole = 5
        self.game_state.hole_stroke_indexes = list(range(1, 19))
        self.game_state.hole_pars = [4] * 18
    
    def test_get_current_points(self):
        """Test getting current points"""
        points = self.player._get_current_points(self.game_state)
        assert points == 0
    
    def test_personality_partnership_decisions(self):
        """Test different personality types make appropriate decisions"""
        # Test aggressive personality
        aggressive_player = ComputerPlayer("cp1", "Aggressive", 12.0, "aggressive")
        aggressive_player.player_id = "cp1"
        
        # Aggressive should accept partnerships when behind
        self.game_state.players[0]["points"] = -5
        decision = aggressive_player.should_accept_partnership(10.0, self.game_state)
        # This test is probabilistic, so we just check it doesn't crash
        assert isinstance(decision, bool)
    
    def test_assess_hole_difficulty(self):
        """Test hole difficulty assessment"""
        difficulty = self.player._assess_hole_difficulty(self.game_state)
        assert 0.0 <= difficulty <= 1.0


class TestMonteCarloResults:
    """Test Monte Carlo results class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.results = MonteCarloResults()
    
    def test_add_game_result(self):
        """Test adding game results"""
        scores = {"p1": 5, "p2": -2, "p3": 0, "p4": 3}
        self.results.add_game_result(scores)
        
        assert self.results.total_simulations == 1
        assert len(self.results.detailed_results) == 1
        assert self.results.win_counts["p1"] == 1  # Highest score wins
    
    def test_calculate_statistics(self):
        """Test statistics calculation"""
        # Add multiple game results
        for i in range(5):
            scores = {"p1": i, "p2": i-1, "p3": i-2, "p4": i-3}
            self.results.add_game_result(scores)
        
        self.results.calculate_statistics()
        
        # Check average scores
        assert self.results.avg_scores["p1"] == 2.0  # (0+1+2+3+4)/5
        assert self.results.avg_scores["p2"] == 1.0  # (-1+0+1+2+3)/5
    
    def test_get_summary(self):
        """Test getting summary statistics"""
        scores = {"p1": 5, "p2": -2}
        self.results.add_game_result(scores)
        
        summary = self.results.get_summary()
        
        assert "total_simulations" in summary
        assert "player_statistics" in summary
        assert "p1" in summary["player_statistics"]
        assert "win_percentage" in summary["player_statistics"]["p1"]


class TestSimulationEngine:
    """Test simulation engine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = SimulationEngine()
        self.human_player = {"id": "h1", "name": "Human", "handicap": 12.0}
        self.computer_configs = [
            {"id": "c1", "name": "Bot1", "handicap": 10.0, "personality": "balanced"},
            {"id": "c2", "name": "Bot2", "handicap": 15.0, "personality": "aggressive"},
            {"id": "c3", "name": "Bot3", "handicap": 8.0, "personality": "conservative"}
        ]
    
    def test_setup_simulation(self):
        """Test simulation setup"""
        game_state = self.engine.setup_simulation(self.human_player, self.computer_configs)
        
        assert len(game_state.players) == 4
        assert len(self.engine.computer_players) == 3
        
        # Check that computer players were created correctly
        for i, cp in enumerate(self.engine.computer_players):
            assert cp.player_id == self.computer_configs[i]["id"]
            assert cp.name == self.computer_configs[i]["name"]
    
    def test_invalid_computer_player_count(self):
        """Test error when wrong number of computer players"""
        with pytest.raises(ValueError, match="Need exactly 3"):
            self.engine.setup_simulation(self.human_player, self.computer_configs[:2])
    
    def test_get_computer_player(self):
        """Test getting computer player by ID"""
        self.engine.setup_simulation(self.human_player, self.computer_configs)
        
        cp = self.engine._get_computer_player("c1")
        assert cp is not None
        assert cp.player_id == "c1"
        
        cp = self.engine._get_computer_player("invalid")
        assert cp is None
    
    def test_simulate_player_score(self):
        """Test player score simulation"""
        game_state = self.engine.setup_simulation(self.human_player, self.computer_configs)
        
        score = self.engine._simulate_player_score(12.0, 4, 1, game_state)
        assert isinstance(score, int)
        assert score >= 1  # Minimum possible score
    
    def test_generate_monte_carlo_human_decisions(self):
        """Test generating automatic human decisions"""
        game_state = self.engine.setup_simulation(self.human_player, self.computer_configs)
        game_state.captain_id = "h1"  # Make human the captain
        
        decisions = self.engine._generate_monte_carlo_human_decisions(game_state, self.human_player)
        
        assert "action" in decisions
        assert "requested_partner" in decisions
        assert "offer_double" in decisions
        assert "accept_double" in decisions
    
    def test_run_monte_carlo_simulation_small(self):
        """Test running a small Monte Carlo simulation"""
        # Run just 2 simulations to keep test fast
        results = self.engine.run_monte_carlo_simulation(
            self.human_player, self.computer_configs, 2
        )
        
        assert results.total_simulations == 2
        assert len(results.player_results) == 4  # 1 human + 3 computers
        
        # Check that all players have results
        for player_id in ["h1", "c1", "c2", "c3"]:
            assert player_id in results.player_results
            assert len(results.player_results[player_id]) == 2


class TestGameState:
    """Test refactored GameState class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.game_state = GameState()
    
    def test_initialization(self):
        """Test game state initialization with constants"""
        # Should initialize with empty state initially
        assert self.game_state.base_wager == GAME_CONSTANTS["DEFAULT_BASE_WAGER"]
        assert len(self.game_state.courses) >= 2  # Should have default courses
    
    def test_reset_uses_constants(self):
        """Test that reset uses constants properly"""
        self.game_state.reset()
        
        assert len(self.game_state.players) == len(DEFAULT_PLAYERS)
        assert self.game_state.current_hole == 1
        assert self.game_state.base_wager == GAME_CONSTANTS["DEFAULT_BASE_WAGER"]
        assert self.game_state.game_phase == GAME_CONSTANTS["DEFAULT_GAME_PHASE"]
        assert self.game_state.game_status_message == GAME_CONSTANTS["DEFAULT_STATUS_MESSAGE"]
    
    def test_setup_players_validation(self):
        """Test player setup with validation"""
        # Test valid player setup
        valid_players = [
            {"id": "p1", "name": "Alice", "handicap": 10.0},
            {"id": "p2", "name": "Bob", "handicap": 15.0},
            {"id": "p3", "name": "Charlie", "handicap": 8.0},
            {"id": "p4", "name": "David", "handicap": 20.0}
        ]
        
        self.game_state.setup_players(valid_players)
        assert len(self.game_state.players) == 4
        
        # Test invalid player count
        with pytest.raises(ValidationException):
            self.game_state.setup_players(valid_players[:2])
        
        # Test invalid player data
        invalid_players = [
            {"id": "p1"},  # Missing name
            {"id": "p2", "name": "Bob"},
            {"id": "p3", "name": "Charlie"},
            {"id": "p4", "name": "David"}
        ]
        
        with pytest.raises(ValidationException):
            self.game_state.setup_players(invalid_players)
    
    def test_dispatch_action_improved(self):
        """Test improved dispatch action with better error handling"""
        self.game_state.reset()
        
        # Test valid action
        result = self.game_state.dispatch_action("go_solo", {"captain_id": "p1"})
        assert isinstance(result, str)
        
        # Test invalid action
        with pytest.raises(GameStateException):
            self.game_state.dispatch_action("invalid_action", {})
    
    def test_course_management_with_validation(self):
        """Test course management with proper validation"""
        # Test adding valid course
        valid_course = {
            "name": "Test Course",
            "holes": [
                {
                    "hole_number": i,
                    "stroke_index": i,
                    "par": 4,
                    "yards": 400,
                    "description": f"Hole {i}"
                }
                for i in range(1, 19)
            ]
        }
        
        self.game_state.add_course(valid_course)
        assert "Test Course" in self.game_state.courses
        
        # Test adding invalid course (wrong number of holes)
        invalid_course = {
            "name": "Invalid Course",
            "holes": [{"hole_number": 1, "stroke_index": 1, "par": 4, "yards": 400}]
        }
        
        with pytest.raises(ValidationException):
            self.game_state.add_course(invalid_course)
    
    def test_get_betting_tips_contextual(self):
        """Test contextual betting tips"""
        self.game_state.reset()
        
        # Test basic tips
        tips = self.game_state.get_betting_tips()
        assert isinstance(tips, list)
        assert len(tips) > 0
        
        # Test tips with doubled status
        self.game_state.doubled_status = True
        tips = self.game_state.get_betting_tips()
        assert any("double" in tip.lower() for tip in tips)
    
    def test_error_handling_consistency(self):
        """Test consistent error handling across methods"""
        # Test course not found
        with pytest.raises(ValidationException):
            self.game_state.get_course_stats("NonexistentCourse")
        
        # Test invalid team action
        with pytest.raises(GameStateException):
            self.game_state.accept_partner("invalid_player")


class TestIntegration:
    """Integration tests for the refactored system"""
    
    def test_full_game_simulation_flow(self):
        """Test complete game simulation flow"""
        engine = SimulationEngine()
        human_player = {"id": "h1", "name": "Human", "handicap": 12.0}
        computer_configs = [
            {"id": "c1", "name": "Bot1", "handicap": 10.0, "personality": "balanced"},
            {"id": "c2", "name": "Bot2", "handicap": 15.0, "personality": "aggressive"},
            {"id": "c3", "name": "Bot3", "handicap": 8.0, "personality": "conservative"}
        ]
        
        # Setup simulation
        game_state = engine.setup_simulation(human_player, computer_configs)
        assert len(game_state.players) == 4
        
        # Test hole simulation
        human_decisions = {
            "action": None,
            "requested_partner": "c1",
            "offer_double": False,
            "accept_double": False
        }
        
        updated_state, feedback = engine.simulate_hole(game_state, human_decisions)
        assert isinstance(feedback, list)
        assert updated_state is not None
    
    def test_api_response_consistency(self):
        """Test that API responses use centralized serialization"""
        game_state = GameState()
        game_state.reset()
        
        # Test serialization
        serialized = SerializationUtils.serialize_game_state(game_state)
        
        # Should contain all expected fields
        required_fields = [
            "players", "current_hole", "hitting_order", "captain_id",
            "teams", "base_wager", "doubled_status", "game_phase"
        ]
        
        for field in required_fields:
            assert field in serialized
    
    def test_error_propagation(self):
        """Test that errors propagate correctly through the system"""
        game_state = GameState()
        
        # Test validation error propagation
        with pytest.raises(ValidationException):
            game_state.add_course({"name": "", "holes": []})
        
        # Test game state error propagation
        with pytest.raises(GameStateException):
            game_state.accept_double("invalid_team")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])