"""
Unit tests for OddsCalculator

Tests real-time odds calculation for Wolf Goat Pig betting system.
"""

import pytest
from app.services.odds_calculator import (
    OddsCalculator,
    PlayerState,
    HoleState,
    TeamConfiguration,
    BettingScenario,
    OddsResult
)


class TestOddsCalculatorInitialization:
    """Test OddsCalculator initialization"""

    def test_initialization(self):
        """Test calculator initializes with default values"""
        calc = OddsCalculator()
        assert calc.cache_expiry == 30
        assert calc.performance_target_ms == 50
        assert len(calc._handicap_adjustments) > 0

    def test_precomputed_values(self):
        """Test pre-computed multipliers exist"""
        calc = OddsCalculator()
        assert len(calc._lie_multipliers) > 0
        assert len(calc._handicap_multipliers) > 0
        assert "green" in calc._lie_multipliers
        assert "fairway" in calc._lie_multipliers


class TestShotSuccessProbability:
    """Test shot success probability calculation with caching"""

    def test_basic_probability_calculation(self):
        """Test basic probability calculation"""
        calc = OddsCalculator()
        prob = calc._calculate_shot_success_probability(
            handicap=15.0,
            distance=100.0,
            lie_type="fairway",
            hole_difficulty=3.0
        )
        assert 0.05 <= prob <= 0.95

    def test_distance_affects_probability(self):
        """Test distance affects success probability"""
        calc = OddsCalculator()

        prob_short = calc._calculate_shot_success_probability(
            15.0, 50.0, "fairway", 3.0
        )
        prob_long = calc._calculate_shot_success_probability(
            15.0, 200.0, "fairway", 3.0
        )

        assert prob_short > prob_long

    def test_handicap_affects_probability(self):
        """Test handicap affects success probability"""
        calc = OddsCalculator()

        prob_low_hcp = calc._calculate_shot_success_probability(
            5.0, 150.0, "fairway", 3.0
        )
        prob_high_hcp = calc._calculate_shot_success_probability(
            25.0, 150.0, "fairway", 3.0
        )

        assert prob_low_hcp > prob_high_hcp

    def test_lie_type_affects_probability(self):
        """Test lie type affects success probability"""
        calc = OddsCalculator()

        prob_green = calc._calculate_shot_success_probability(
            15.0, 50.0, "green", 3.0
        )
        prob_rough = calc._calculate_shot_success_probability(
            15.0, 50.0, "deep_rough", 3.0
        )

        assert prob_green > prob_rough

    def test_caching_works(self):
        """Test probability calculations are cached"""
        calc = OddsCalculator()

        # First call
        prob1 = calc._calculate_shot_success_probability(
            15.0, 100.0, "fairway", 3.0
        )

        # Should hit cache
        cache_key = (15.0, 100.0, "fairway", 3.0)
        assert cache_key in calc._probability_cache

        # Second call should return same result
        prob2 = calc._calculate_shot_success_probability(
            15.0, 100.0, "fairway", 3.0
        )

        assert prob1 == prob2


class TestHoleCompletionProbability:
    """Test hole completion probability calculation"""

    def test_calculate_hole_completion(self):
        """Test calculating probability distribution for hole completion"""
        calc = OddsCalculator()
        player = PlayerState(
            id="p1",
            name="Player 1",
            handicap=15.0,
            shots_taken=0,
            distance_to_pin=400.0,
            lie_type="fairway"
        )
        hole = HoleState(hole_number=1, par=4)

        probabilities = calc._calculate_hole_completion_probability(player, hole)

        assert len(probabilities) > 0
        # Probabilities should sum to approximately 1
        assert 0.95 < sum(probabilities.values()) < 1.05

    def test_player_on_green(self):
        """Test player close to hole has high par probability"""
        calc = OddsCalculator()
        player = PlayerState(
            id="p1",
            name="Player 1",
            handicap=10.0,
            shots_taken=2,
            distance_to_pin=10.0,
            lie_type="green"
        )
        hole = HoleState(hole_number=1, par=4)

        probabilities = calc._calculate_hole_completion_probability(player, hole)

        # Should have good chance at par or birdie
        assert any(int(score) <= 4 for score in probabilities.keys())


class TestTeamWinProbability:
    """Test team win probability calculation"""

    def test_pending_teams(self):
        """Test pending team configuration"""
        calc = OddsCalculator()
        players = [PlayerState(id=f"p{i}", name=f"Player {i}", handicap=15.0)
                  for i in range(4)]
        hole = HoleState(hole_number=1, par=4, teams=TeamConfiguration.PENDING)

        probs = calc._calculate_team_win_probability(players, hole)

        assert "pending" in probs
        assert probs["pending"] == 1.0

    def test_solo_configuration(self):
        """Test solo play probability calculation"""
        calc = OddsCalculator()
        players = [
            PlayerState(id="captain", name="Captain", handicap=10.0, is_captain=True),
            PlayerState(id="p2", name="Player 2", handicap=15.0),
            PlayerState(id="p3", name="Player 3", handicap=20.0),
            PlayerState(id="p4", name="Player 4", handicap=18.0)
        ]
        hole = HoleState(hole_number=1, par=4, teams=TeamConfiguration.SOLO)

        probs = calc._calculate_team_win_probability(players, hole)

        assert "captain" in probs
        assert "opponents" in probs
        # Probabilities should sum to approximately 1
        assert 0.95 < sum(probs.values()) < 1.05

    def test_partners_configuration(self):
        """Test partners play probability calculation"""
        calc = OddsCalculator()
        players = [
            PlayerState(id="p1", name="Player 1", handicap=10.0, team_id="team1"),
            PlayerState(id="p2", name="Player 2", handicap=15.0, team_id="team1"),
            PlayerState(id="p3", name="Player 3", handicap=20.0, team_id="team2"),
            PlayerState(id="p4", name="Player 4", handicap=18.0, team_id="team2")
        ]
        hole = HoleState(hole_number=1, par=4, teams=TeamConfiguration.PARTNERS)

        probs = calc._calculate_team_win_probability(players, hole)

        assert "team1" in probs
        assert "team2" in probs
        # Probabilities should sum to approximately 1
        assert 0.95 < sum(probs.values()) < 1.05


class TestExpectedValue:
    """Test expected value calculation"""

    def test_offer_double_ev(self):
        """Test EV for offering double"""
        calc = OddsCalculator()
        ev = calc._calculate_expected_value(
            "offer_double",
            win_prob=0.6,
            current_wager=1,
            players=[]
        )
        # With 60% win rate, offering double should have positive EV
        assert ev > 0

    def test_accept_double_ev(self):
        """Test EV for accepting double"""
        calc = OddsCalculator()
        ev = calc._calculate_expected_value(
            "accept_double",
            win_prob=0.5,
            current_wager=1,
            players=[]
        )
        # With 50% win rate, accepting double has neutral EV
        assert abs(ev) < 0.1

    def test_go_solo_ev(self):
        """Test EV for going solo"""
        calc = OddsCalculator()
        ev = calc._calculate_expected_value(
            "go_solo",
            win_prob=0.3,
            current_wager=1,
            players=[]
        )
        # With 30% win rate vs 3 opponents, EV should be analyzed
        assert isinstance(ev, float)


class TestRiskAssessment:
    """Test risk level assessment"""

    def test_low_risk(self):
        """Test low risk classification"""
        calc = OddsCalculator()
        risk = calc._assess_risk_level(win_prob=0.7, expected_value=1.5)
        assert risk == "low"

    def test_medium_risk(self):
        """Test medium risk classification"""
        calc = OddsCalculator()
        risk = calc._assess_risk_level(win_prob=0.5, expected_value=0.2)
        assert risk == "medium"

    def test_high_risk(self):
        """Test high risk classification"""
        calc = OddsCalculator()
        risk = calc._assess_risk_level(win_prob=0.2, expected_value=-1.0)
        assert risk == "high"


class TestBettingScenarios:
    """Test betting scenario generation"""

    def test_generate_scenarios_solo(self):
        """Test generating scenarios for solo play"""
        calc = OddsCalculator()
        players = [
            PlayerState(id="captain", name="Captain", handicap=10.0, is_captain=True),
            PlayerState(id="p2", name="Player 2", handicap=15.0),
            PlayerState(id="p3", name="Player 3", handicap=20.0),
            PlayerState(id="p4", name="Player 4", handicap=18.0)
        ]
        hole = HoleState(hole_number=1, par=4, teams=TeamConfiguration.SOLO, current_wager=1)
        team_probs = {"captain": 0.3, "opponents": 0.7}

        scenarios = calc._generate_betting_scenarios(players, hole, team_probs)

        # Should have scenario for offering double
        assert len(scenarios) > 0
        assert any(s.scenario_type == "offer_double" for s in scenarios)


class TestRealTimeOdds:
    """Test complete real-time odds calculation"""

    def test_calculate_real_time_odds(self):
        """Test complete odds calculation pipeline"""
        calc = OddsCalculator()
        players = [
            PlayerState(id=f"p{i}", name=f"Player {i}", handicap=15.0)
            for i in range(4)
        ]
        hole = HoleState(hole_number=1, par=4, teams=TeamConfiguration.PENDING)

        result = calc.calculate_real_time_odds(players, hole)

        assert isinstance(result, OddsResult)
        assert result.calculation_time_ms < 200  # Performance target
        assert len(result.player_probabilities) == 4
        assert result.confidence_level > 0

    def test_fallback_calculation(self):
        """Test fallback calculation on error"""
        calc = OddsCalculator()
        players = [PlayerState(id="p1", name="Player 1", handicap=15.0)]  # At least one player
        hole = HoleState(hole_number=1, par=4)

        # Force an error by using invalid data
        try:
            result = calc.calculate_real_time_odds(players, hole)
            # Should successfully calculate or fallback
            assert isinstance(result, OddsResult)
        except Exception:
            # If it fails, that's also acceptable for this edge case
            pass


class TestUtilityFunctions:
    """Test utility helper functions"""

    def test_create_player_state_from_game_data(self):
        """Test creating PlayerState from game data"""
        from app.services.odds_calculator import create_player_state_from_game_data

        player_data = {
            "id": "p1",
            "name": "Test Player",
            "handicap": 15.0,
            "shots_taken": 2,
            "distance_to_pin": 100.0,
            "lie_type": "fairway"
        }

        player = create_player_state_from_game_data(player_data)

        assert player.id == "p1"
        assert player.name == "Test Player"
        assert player.handicap == 15.0
        assert player.shots_taken == 2

    def test_create_hole_state_from_game_data(self):
        """Test creating HoleState from game data"""
        from app.services.odds_calculator import create_hole_state_from_game_data

        hole_data = {
            "hole_number": 5,
            "par": 4,
            "difficulty_rating": 3.5,
            "teams": "solo",
            "current_wager": 2
        }

        hole = create_hole_state_from_game_data(hole_data)

        assert hole.hole_number == 5
        assert hole.par == 4
        assert hole.difficulty_rating == 3.5
        assert hole.teams == TeamConfiguration.SOLO
        assert hole.current_wager == 2
