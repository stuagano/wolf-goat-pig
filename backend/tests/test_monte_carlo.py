"""
Unit tests for MonteCarloEngine

Tests Monte Carlo simulation for Wolf Goat Pig betting odds calculation.
"""

import pytest
from app.services.monte_carlo import (
    MonteCarloEngine,
    SimulationParams,
    SimulationResult
)
from app.services.odds_calculator import (
    PlayerState,
    HoleState,
    TeamConfiguration
)


class TestSimulationParams:
    """Test simulation parameter handling"""

    def test_default_params(self):
        """Test default simulation parameters"""
        params = SimulationParams()
        assert params.num_simulations == 10000
        assert params.confidence_level == 0.95
        assert params.use_parallel is True

    def test_custom_params(self):
        """Test custom simulation parameters"""
        params = SimulationParams(
            num_simulations=5000,
            confidence_level=0.90,
            use_parallel=False
        )
        assert params.num_simulations == 5000
        assert params.confidence_level == 0.90
        assert params.use_parallel is False


class TestMonteCarloEngine:
    """Test Monte Carlo simulation engine"""

    def test_engine_initialization(self):
        """Test engine initializes with default params"""
        engine = MonteCarloEngine()
        assert engine.params is not None
        assert engine.random_seed is None

    def test_set_seed(self):
        """Test setting random seed for reproducibility"""
        engine = MonteCarloEngine()
        engine.set_seed(42)
        assert engine.random_seed == 42

    def test_seed_provides_reproducibility(self):
        """Test same seed gives same results"""
        params = SimulationParams(num_simulations=100, use_parallel=False)

        # Create test scenario
        players = [
            PlayerState(id="p1", name="Player 1", handicap=10.0),
            PlayerState(id="p2", name="Player 2", handicap=15.0),
            PlayerState(id="p3", name="Player 3", handicap=20.0),
            PlayerState(id="p4", name="Player 4", handicap=12.0)
        ]
        hole = HoleState(hole_number=1, par=4, teams=TeamConfiguration.PENDING)

        # Run twice with same seed
        engine1 = MonteCarloEngine(params)
        engine1.set_seed(123)
        result1 = engine1.simulate_hole_outcomes(players, hole)

        engine2 = MonteCarloEngine(params)
        engine2.set_seed(123)
        result2 = engine2.simulate_hole_outcomes(players, hole)

        # Results should be identical
        assert result1.num_simulations_run == result2.num_simulations_run
        # Win probabilities should be very close
        for player_id in result1.win_probabilities:
            assert abs(result1.win_probabilities[player_id] -
                      result2.win_probabilities[player_id]) < 0.01


class TestShotSuccessProbability:
    """Test shot success probability calculation"""

    def test_short_distance_high_prob(self):
        """Test short distances have high success probability"""
        engine = MonteCarloEngine()
        prob = engine._calculate_shot_success_probability(
            handicap=10.0,
            distance=10.0,
            lie_type="green",
            hole_difficulty=3.0
        )
        assert prob > 0.7  # Short putt should be high probability

    def test_long_distance_lower_prob(self):
        """Test long distances have lower success probability"""
        engine = MonteCarloEngine()
        prob = engine._calculate_shot_success_probability(
            handicap=10.0,
            distance=200.0,
            lie_type="fairway",
            hole_difficulty=3.0
        )
        assert prob < 0.5  # Long shot should be lower probability

    def test_better_handicap_higher_prob(self):
        """Test lower handicap gives higher probability"""
        engine = MonteCarloEngine()

        prob_scratch = engine._calculate_shot_success_probability(
            handicap=0.0,
            distance=150.0,
            lie_type="fairway",
            hole_difficulty=3.0
        )

        prob_high_hcp = engine._calculate_shot_success_probability(
            handicap=25.0,
            distance=150.0,
            lie_type="fairway",
            hole_difficulty=3.0
        )

        assert prob_scratch > prob_high_hcp

    def test_difficult_lie_lower_prob(self):
        """Test difficult lie reduces probability"""
        engine = MonteCarloEngine()

        prob_fairway = engine._calculate_shot_success_probability(
            handicap=15.0,
            distance=100.0,
            lie_type="fairway",
            hole_difficulty=3.0
        )

        prob_rough = engine._calculate_shot_success_probability(
            handicap=15.0,
            distance=100.0,
            lie_type="deep_rough",
            hole_difficulty=3.0
        )

        assert prob_fairway > prob_rough


class TestHoleSimulation:
    """Test complete hole simulation"""

    def test_simulate_single_hole(self):
        """Test simulating a single hole completion"""
        engine = MonteCarloEngine()
        engine.set_seed(42)

        players = [
            PlayerState(id="p1", name="Player 1", handicap=10.0,
                       distance_to_pin=400.0, lie_type="fairway"),
            PlayerState(id="p2", name="Player 2", handicap=15.0,
                       distance_to_pin=400.0, lie_type="fairway")
        ]
        hole = HoleState(hole_number=1, par=4)

        result = engine._simulate_single_hole(players, hole)

        assert "scores" in result
        assert "p1" in result["scores"]
        assert "p2" in result["scores"]
        assert result["scores"]["p1"] > 0
        assert result["scores"]["p2"] > 0
        assert "winner" in result

    def test_simulate_hole_outcomes_basic(self):
        """Test basic hole outcome simulation"""
        params = SimulationParams(num_simulations=100, use_parallel=False)
        engine = MonteCarloEngine(params)

        players = [
            PlayerState(id="p1", name="Player 1", handicap=10.0),
            PlayerState(id="p2", name="Player 2", handicap=20.0)
        ]
        hole = HoleState(hole_number=1, par=4, teams=TeamConfiguration.PENDING)

        result = engine.simulate_hole_outcomes(players, hole)

        assert isinstance(result, SimulationResult)
        assert result.num_simulations_run == 100
        assert len(result.win_probabilities) > 0
        assert result.simulation_time_ms > 0


class TestTeamConfigurations:
    """Test different team configurations"""

    def test_solo_configuration(self):
        """Test captain vs opponents solo play"""
        params = SimulationParams(num_simulations=100, use_parallel=False)
        engine = MonteCarloEngine(params)
        engine.set_seed(42)

        players = [
            PlayerState(id="captain", name="Captain", handicap=10.0, is_captain=True),
            PlayerState(id="p2", name="Player 2", handicap=15.0),
            PlayerState(id="p3", name="Player 3", handicap=20.0),
            PlayerState(id="p4", name="Player 4", handicap=18.0)
        ]
        hole = HoleState(hole_number=1, par=4, teams=TeamConfiguration.SOLO)

        result = engine.simulate_hole_outcomes(players, hole)

        # Should have captain and opponents probabilities
        assert "captain" in result.win_probabilities or "opponents" in result.win_probabilities

    def test_partners_configuration(self):
        """Test team vs team partners play"""
        params = SimulationParams(num_simulations=100, use_parallel=False)
        engine = MonteCarloEngine(params)
        engine.set_seed(42)

        players = [
            PlayerState(id="p1", name="Player 1", handicap=10.0, team_id="team1"),
            PlayerState(id="p2", name="Player 2", handicap=15.0, team_id="team1"),
            PlayerState(id="p3", name="Player 3", handicap=20.0, team_id="team2"),
            PlayerState(id="p4", name="Player 4", handicap=18.0, team_id="team2")
        ]
        hole = HoleState(hole_number=1, par=4, teams=TeamConfiguration.PARTNERS)

        result = engine.simulate_hole_outcomes(players, hole)

        # Should have team1 and team2 probabilities
        assert "team1" in result.win_probabilities or "team2" in result.win_probabilities


class TestParallelSimulation:
    """Test parallel simulation execution"""

    def test_parallel_vs_sequential_same_result(self):
        """Test parallel gives similar results to sequential"""
        players = [
            PlayerState(id="p1", name="Player 1", handicap=10.0),
            PlayerState(id="p2", name="Player 2", handicap=15.0)
        ]
        hole = HoleState(hole_number=1, par=4, teams=TeamConfiguration.PENDING)

        # Sequential
        params_seq = SimulationParams(num_simulations=1000, use_parallel=False)
        engine_seq = MonteCarloEngine(params_seq)
        engine_seq.set_seed(42)
        result_seq = engine_seq.simulate_hole_outcomes(players, hole)

        # Parallel
        params_par = SimulationParams(num_simulations=1000, use_parallel=True, num_threads=2)
        engine_par = MonteCarloEngine(params_par)
        engine_par.set_seed(42)
        result_par = engine_par.simulate_hole_outcomes(players, hole)

        # Results should be similar (within 10% due to parallel execution differences)
        for player_id in result_seq.win_probabilities:
            if player_id in result_par.win_probabilities:
                diff = abs(result_seq.win_probabilities[player_id] -
                          result_par.win_probabilities[player_id])
                assert diff < 0.15  # Allow 15% difference


class TestConfidenceIntervals:
    """Test confidence interval calculation"""

    def test_confidence_intervals_present(self):
        """Test confidence intervals are calculated"""
        params = SimulationParams(num_simulations=100, use_parallel=False)
        engine = MonteCarloEngine(params)

        players = [
            PlayerState(id="p1", name="Player 1", handicap=10.0),
            PlayerState(id="p2", name="Player 2", handicap=15.0)
        ]
        hole = HoleState(hole_number=1, par=4, teams=TeamConfiguration.PENDING)

        result = engine.simulate_hole_outcomes(players, hole)

        assert len(result.confidence_intervals) > 0
        # Check CI format
        for player_id, (lower, upper) in result.confidence_intervals.items():
            assert 0 <= lower <= upper <= 1


class TestDetailedOutcomes:
    """Test detailed outcome reporting"""

    def test_detailed_outcomes_structure(self):
        """Test detailed outcomes contain expected data"""
        params = SimulationParams(num_simulations=100, use_parallel=False)
        engine = MonteCarloEngine(params)

        players = [
            PlayerState(id="p1", name="Player 1", handicap=10.0),
            PlayerState(id="p2", name="Player 2", handicap=15.0)
        ]
        hole = HoleState(hole_number=1, par=4, teams=TeamConfiguration.PENDING)

        result = engine.simulate_hole_outcomes(players, hole)

        assert "score_distributions" in result.detailed_outcomes
        assert "average_scores" in result.detailed_outcomes
        assert "tie_rate" in result.detailed_outcomes


class TestFactoryFunction:
    """Test the factory function for easy integration"""

    def test_run_monte_carlo_simulation_factory(self):
        """Test factory function works correctly"""
        from app.services.monte_carlo import run_monte_carlo_simulation

        players = [
            PlayerState(id="p1", name="Player 1", handicap=10.0),
            PlayerState(id="p2", name="Player 2", handicap=15.0)
        ]
        hole = HoleState(hole_number=1, par=4, teams=TeamConfiguration.PENDING)

        result = run_monte_carlo_simulation(players, hole, num_simulations=100)

        assert isinstance(result, SimulationResult)
        assert result.num_simulations_run <= 100
        assert result.simulation_time_ms < 100  # Should be fast
