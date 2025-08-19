"""
Unit tests for Monte Carlo simulation engine.
Tests simulation accuracy, convergence, and performance.
"""

import unittest
import time
import statistics
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.monte_carlo import (
    MonteCarloEngine,
    SimulationParams,
    SimulationResult,
    run_monte_carlo_simulation
)
from app.services.odds_calculator import PlayerState, HoleState, TeamConfiguration


class TestMonteCarloEngine(unittest.TestCase):
    """Test suite for Monte Carlo simulation engine"""

    def setUp(self):
        """Set up test fixtures"""
        self.engine = MonteCarloEngine()
        
        # Create test players
        self.test_players = [
            PlayerState(
                id="p1",
                name="Low Handicap",
                handicap=5.0,
                distance_to_pin=150.0,
                lie_type="fairway",
                is_captain=True
            ),
            PlayerState(
                id="p2",
                name="Mid Handicap",
                handicap=15.0,
                distance_to_pin=140.0,
                lie_type="fairway"
            ),
            PlayerState(
                id="p3",
                name="High Handicap",
                handicap=25.0,
                distance_to_pin=160.0,
                lie_type="rough"
            ),
            PlayerState(
                id="p4",
                name="Beginner",
                handicap=30.0,
                distance_to_pin=180.0,
                lie_type="fairway"
            )
        ]
        
        # Create test hole
        self.test_hole = HoleState(
            hole_number=5,
            par=4,
            difficulty_rating=3.0,
            teams=TeamConfiguration.PENDING
        )

    def test_simulation_params_validation(self):
        """Test simulation parameter validation"""
        # Valid parameters
        valid_params = SimulationParams(
            num_simulations=1000,
            confidence_level=0.95,
            max_simulation_time_ms=20.0
        )
        self.assertEqual(valid_params.num_simulations, 1000)
        self.assertEqual(valid_params.confidence_level, 0.95)
        
        # Default parameters
        default_params = SimulationParams()
        self.assertEqual(default_params.num_simulations, 10000)
        self.assertTrue(default_params.use_parallel)

    def test_single_hole_simulation(self):
        """Test simulation of a single hole"""
        result = self.engine._simulate_single_hole(self.test_players, self.test_hole)
        
        # Verify result structure
        self.assertIn("scores", result)
        self.assertIn("shot_details", result)
        self.assertIn("winner", result)
        self.assertIn("winning_score", result)
        
        # Verify scores for all players
        scores = result["scores"]
        self.assertEqual(len(scores), len(self.test_players))
        
        for player in self.test_players:
            self.assertIn(player.id, scores)
            score = scores[player.id]
            self.assertIsInstance(score, int)
            self.assertGreaterEqual(score, 1)  # Must take at least 1 shot
            self.assertLessEqual(score, 10)    # Reasonable upper bound
        
        # Verify winner determination
        winner = result["winner"]
        if winner != "tie":
            self.assertIn(winner, [p.id for p in self.test_players])
        
        winning_score = result["winning_score"]
        self.assertIsInstance(winning_score, int)
        self.assertEqual(winning_score, min(scores.values()))

    def test_player_hole_simulation(self):
        """Test simulation of individual player completing a hole"""
        player = self.test_players[0]  # Low handicap player
        
        score, shot_details = self.engine._simulate_player_hole(player, self.test_hole)
        
        # Verify score is reasonable
        self.assertIsInstance(score, int)
        self.assertGreaterEqual(score, 1)
        self.assertLessEqual(score, 10)  # Reasonable upper bound
        
        # Verify shot details
        self.assertIsInstance(shot_details, list)
        self.assertGreater(len(shot_details), 0)
        self.assertEqual(len(shot_details), score)  # One detail per shot
        
        # Verify shot detail structure
        for shot in shot_details:
            self.assertIn("shot_number", shot)
            self.assertIn("starting_distance", shot)
            self.assertIn("starting_lie", shot)
            self.assertIn("result", shot)
            
            shot_result = shot["result"]
            self.assertIn("holed_out", shot_result)
            self.assertIn("final_distance", shot_result)
            self.assertIn("quality", shot_result)

    def test_shot_simulation_realism(self):
        """Test that shot simulation produces realistic outcomes"""
        # Test with excellent player from short distance
        excellent_shot = self.engine._simulate_shot(
            handicap=0,
            distance=10,
            lie_type="green",
            hole_difficulty=2.0,
            weather_factor=1.0
        )
        
        # Should have high success rate for excellent player on short putt
        success_count = 0
        total_shots = 100
        
        for _ in range(total_shots):
            shot = self.engine._simulate_shot(0, 10, "green", 2.0, 1.0)
            if shot.get("holed_out") or shot.get("final_distance", 999) < 5:
                success_count += 1
        
        success_rate = success_count / total_shots
        self.assertGreater(success_rate, 0.6, "Excellent player should succeed often on short putts")
        
        # Test with poor player from difficult position
        poor_success_count = 0
        for _ in range(total_shots):
            shot = self.engine._simulate_shot(30, 200, "deep_rough", 5.0, 0.8)
            if shot.get("final_distance", 999) < 50:  # Made significant progress
                poor_success_count += 1
        
        poor_success_rate = poor_success_count / total_shots
        self.assertLess(poor_success_rate, success_rate, 
                       "Poor player from difficult position should succeed less often")

    def test_simulation_convergence(self):
        """Test that simulation converges to stable results"""
        params = SimulationParams(num_simulations=5000, use_parallel=False)
        
        # Run multiple simulation batches
        results = []
        for _ in range(5):
            result = self.engine.simulate_hole_outcomes(self.test_players, self.test_hole, params)
            results.append(result)
        
        # Extract win probabilities for first player
        p1_probs = [r.win_probabilities.get("p1", 0) for r in results]
        
        # Check convergence (results should be similar)
        prob_std = statistics.stdev(p1_probs) if len(p1_probs) > 1 else 0
        self.assertLess(prob_std, 0.1, f"Win probabilities should converge (std dev: {prob_std:.3f})")

    def test_simulation_performance(self):
        """Test simulation performance meets targets"""
        params = SimulationParams(
            num_simulations=1000,
            max_simulation_time_ms=25.0,
            use_parallel=True
        )
        
        start_time = time.time()
        result = self.engine.simulate_hole_outcomes(self.test_players, self.test_hole, params)
        total_time = (time.time() - start_time) * 1000
        
        # Should complete within time limit
        self.assertLess(total_time, 50, f"Simulation took {total_time:.1f}ms, should be under 50ms")
        
        # Should have run reasonable number of simulations
        self.assertGreater(result.num_simulations_run, 100, "Should run minimum number of simulations")
        
        # Should provide timing information
        self.assertIsInstance(result.simulation_time_ms, float)
        self.assertGreater(result.simulation_time_ms, 0)

    def test_team_configuration_results(self):
        """Test simulation results for different team configurations"""
        # Test solo configuration
        solo_hole = HoleState(
            hole_number=1,
            par=4,
            teams=TeamConfiguration.SOLO
        )
        
        params = SimulationParams(num_simulations=1000, use_parallel=False)
        solo_result = self.engine.simulate_hole_outcomes(self.test_players, solo_hole, params)
        
        # Should have captain vs opponents results
        self.assertIn("captain", solo_result.win_probabilities)
        self.assertIn("opponents", solo_result.win_probabilities)
        
        captain_prob = solo_result.win_probabilities["captain"]
        opponents_prob = solo_result.win_probabilities["opponents"]
        
        # Probabilities should sum approximately to 1
        total_prob = captain_prob + opponents_prob
        self.assertAlmostEqual(total_prob, 1.0, places=1, 
                             msg="Solo probabilities should sum to 1.0")
        
        # Captain (best player) should have reasonable but not overwhelming chance
        self.assertGreater(captain_prob, 0.15, "Captain should have reasonable chance")
        self.assertLess(captain_prob, 0.6, "Captain shouldn't dominate against 3 opponents")

    def test_confidence_intervals(self):
        """Test confidence interval calculations"""
        params = SimulationParams(num_simulations=2000, confidence_level=0.95)
        result = self.engine.simulate_hole_outcomes(self.test_players, self.test_hole, params)
        
        # Should have confidence intervals for each winner
        for winner_id, prob in result.win_probabilities.items():
            self.assertIn(winner_id, result.confidence_intervals)
            
            ci_lower, ci_upper = result.confidence_intervals[winner_id]
            
            # Confidence interval should contain the probability
            self.assertLessEqual(ci_lower, prob, 
                               f"CI lower bound {ci_lower:.3f} should be <= probability {prob:.3f}")
            self.assertGreaterEqual(ci_upper, prob,
                               f"CI upper bound {ci_upper:.3f} should be >= probability {prob:.3f}")
            
            # Confidence interval should be reasonable width
            ci_width = ci_upper - ci_lower
            self.assertLess(ci_width, 0.3, f"CI width {ci_width:.3f} should be reasonable")

    def test_detailed_outcomes(self):
        """Test detailed outcome analysis"""
        params = SimulationParams(num_simulations=1000)
        result = self.engine.simulate_hole_outcomes(self.test_players, self.test_hole, params)
        
        detailed = result.detailed_outcomes
        
        # Should include score distributions
        self.assertIn("score_distributions", detailed)
        score_dist = detailed["score_distributions"]
        
        for player in self.test_players:
            self.assertIn(player.id, score_dist, f"Should have score distribution for {player.name}")
            
            player_dist = score_dist[player.id]
            # Distribution should sum to approximately 1.0
            total_prob = sum(player_dist.values())
            self.assertAlmostEqual(total_prob, 1.0, places=1,
                                 msg=f"Score distribution for {player.name} should sum to 1.0")
        
        # Should include average scores
        self.assertIn("average_scores", detailed)
        avg_scores = detailed["average_scores"]
        
        for player in self.test_players:
            self.assertIn(player.id, avg_scores)
            avg_score = avg_scores[player.id]
            self.assertIsInstance(avg_score, float)
            self.assertGreater(avg_score, 1.0)  # Must be at least 1 shot
            
            # Lower handicap players should have better average scores
            if player.handicap <= 10:
                self.assertLess(avg_score, self.test_hole.par + 1.5,
                              f"Low handicap player {player.name} should score well")

    def test_parallel_vs_sequential_consistency(self):
        """Test that parallel and sequential simulations give similar results"""
        params_parallel = SimulationParams(num_simulations=1000, use_parallel=True, num_threads=2)
        params_sequential = SimulationParams(num_simulations=1000, use_parallel=False)
        
        # Set same seed for reproducibility
        self.engine.set_seed(42)
        parallel_result = self.engine.simulate_hole_outcomes(self.test_players, self.test_hole, params_parallel)
        
        self.engine.set_seed(42)
        sequential_result = self.engine.simulate_hole_outcomes(self.test_players, self.test_hole, params_sequential)
        
        # Results should be similar (allowing for some variance due to threading)
        for player_id in parallel_result.win_probabilities:
            if player_id in sequential_result.win_probabilities:
                parallel_prob = parallel_result.win_probabilities[player_id]
                sequential_prob = sequential_result.win_probabilities[player_id]
                
                prob_diff = abs(parallel_prob - sequential_prob)
                self.assertLess(prob_diff, 0.15, 
                              f"Parallel and sequential results should be similar for {player_id}")

    def test_early_stopping(self):
        """Test early stopping functionality"""
        params = SimulationParams(
            num_simulations=10000,
            early_stopping_threshold=0.02,
            use_parallel=False
        )
        
        result = self.engine.simulate_hole_outcomes(self.test_players, self.test_hole, params)
        
        # Should potentially stop early if convergence achieved
        if result.convergence_achieved:
            self.assertLess(result.num_simulations_run, params.num_simulations,
                          "Should stop early when convergence achieved")

    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Test with minimal simulations
        minimal_params = SimulationParams(num_simulations=10)
        minimal_result = self.engine.simulate_hole_outcomes(self.test_players, self.test_hole, minimal_params)
        
        self.assertIsInstance(minimal_result, SimulationResult)
        self.assertEqual(minimal_result.num_simulations_run, 10)
        
        # Test with single player
        single_player = [self.test_players[0]]
        single_result = self.engine.simulate_hole_outcomes(single_player, self.test_hole)
        
        self.assertIsInstance(single_result, SimulationResult)
        self.assertIn(single_player[0].id, single_result.win_probabilities)

    def test_handicap_realism(self):
        """Test that handicap differences produce realistic score distributions"""
        scratch_player = PlayerState(id="scratch", name="Scratch", handicap=0, distance_to_pin=150)
        high_hcp_player = PlayerState(id="high", name="High HCP", handicap=30, distance_to_pin=150)
        
        players = [scratch_player, high_hcp_player]
        
        params = SimulationParams(num_simulations=2000, use_parallel=False)
        result = self.engine.simulate_hole_outcomes(players, self.test_hole, params)
        
        # Scratch player should have higher win probability
        scratch_prob = result.win_probabilities.get("scratch", 0)
        high_hcp_prob = result.win_probabilities.get("high", 0)
        
        self.assertGreater(scratch_prob, high_hcp_prob,
                         "Scratch player should have higher win probability than high handicap player")
        
        # Check average scores
        avg_scores = result.detailed_outcomes["average_scores"]
        scratch_avg = avg_scores["scratch"]
        high_hcp_avg = avg_scores["high"]
        
        self.assertLess(scratch_avg, high_hcp_avg,
                      "Scratch player should have lower average score")
        
        # Score difference should be reasonable
        score_diff = high_hcp_avg - scratch_avg
        self.assertGreater(score_diff, 0.5, "Should see meaningful score difference")
        self.assertLess(score_diff, 3.0, "Score difference should be realistic")


class TestFactoryFunction(unittest.TestCase):
    """Test the factory function for easy integration"""

    def setUp(self):
        self.test_players = [
            PlayerState(id="p1", name="Player 1", handicap=10, distance_to_pin=150),
            PlayerState(id="p2", name="Player 2", handicap=15, distance_to_pin=160)
        ]
        self.test_hole = HoleState(hole_number=1, par=4)

    def test_factory_function_basic(self):
        """Test basic factory function usage"""
        result = run_monte_carlo_simulation(
            self.test_players,
            self.test_hole,
            num_simulations=500,
            max_time_ms=20.0
        )
        
        self.assertIsInstance(result, SimulationResult)
        self.assertGreater(result.num_simulations_run, 0)
        self.assertIn("p1", result.win_probabilities)
        self.assertIn("p2", result.win_probabilities)

    def test_factory_function_performance(self):
        """Test factory function meets performance targets"""
        start_time = time.time()
        
        result = run_monte_carlo_simulation(
            self.test_players,
            self.test_hole,
            num_simulations=1000,
            max_time_ms=25.0
        )
        
        total_time = (time.time() - start_time) * 1000
        
        self.assertLess(total_time, 50, f"Factory function took {total_time:.1f}ms, should be under 50ms")
        self.assertIsInstance(result, SimulationResult)


if __name__ == '__main__':
    # Create test suite
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestMonteCarloEngine))
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestFactoryFunction))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"MONTE CARLO SIMULATION TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)