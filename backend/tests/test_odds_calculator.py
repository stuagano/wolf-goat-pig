"""
Comprehensive unit tests for the odds calculation engine.
Tests mathematical accuracy, performance, and edge cases.
"""

import unittest
import time
import numpy as np
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.odds_calculator import (
    OddsCalculator, 
    PlayerState, 
    HoleState, 
    TeamConfiguration,
    ShotDifficulty,
    BettingScenario,
    create_player_state_from_game_data,
    create_hole_state_from_game_data
)


class TestOddsCalculator(unittest.TestCase):
    """Test suite for the OddsCalculator class"""

    def setUp(self):
        """Set up test fixtures"""
        self.calculator = OddsCalculator()
        
        # Create test players with different skill levels
        self.test_players = [
            PlayerState(
                id="p1",
                name="Scratch Player",
                handicap=0.0,
                distance_to_pin=150.0,
                lie_type="fairway",
                is_captain=True
            ),
            PlayerState(
                id="p2", 
                name="Low Handicap",
                handicap=5.0,
                distance_to_pin=140.0,
                lie_type="fairway"
            ),
            PlayerState(
                id="p3",
                name="Mid Handicap", 
                handicap=15.0,
                distance_to_pin=160.0,
                lie_type="rough"
            ),
            PlayerState(
                id="p4",
                name="High Handicap",
                handicap=25.0,
                distance_to_pin=180.0,
                lie_type="fairway"
            )
        ]
        
        # Create test hole
        self.test_hole = HoleState(
            hole_number=10,
            par=4,
            difficulty_rating=3.5,
            teams=TeamConfiguration.PENDING
        )

    def test_shot_success_probability_calculation(self):
        """Test shot success probability calculations for accuracy"""
        # Test distance-based probabilities
        short_putt_prob = self.calculator._calculate_shot_success_probability(
            handicap=10, distance=5, lie_type="green", hole_difficulty=3.0
        )
        self.assertGreater(short_putt_prob, 0.8, "Short putts should have high success probability")
        
        long_shot_prob = self.calculator._calculate_shot_success_probability(
            handicap=10, distance=250, lie_type="fairway", hole_difficulty=3.0
        )
        self.assertLess(long_shot_prob, 0.5, "Long shots should have lower success probability")
        
        # Test handicap adjustments
        scratch_prob = self.calculator._calculate_shot_success_probability(
            handicap=0, distance=150, lie_type="fairway", hole_difficulty=3.0
        )
        high_hcp_prob = self.calculator._calculate_shot_success_probability(
            handicap=30, distance=150, lie_type="fairway", hole_difficulty=3.0
        )
        self.assertGreater(scratch_prob, high_hcp_prob, "Lower handicap should have higher success probability")
        
        # Test lie adjustments
        fairway_prob = self.calculator._calculate_shot_success_probability(
            handicap=10, distance=150, lie_type="fairway", hole_difficulty=3.0
        )
        rough_prob = self.calculator._calculate_shot_success_probability(
            handicap=10, distance=150, lie_type="rough", hole_difficulty=3.0
        )
        self.assertGreater(fairway_prob, rough_prob, "Fairway lie should have higher success probability than rough")

    def test_hole_completion_probability_distribution(self):
        """Test hole completion probability distributions"""
        for player in self.test_players:
            probs = self.calculator._calculate_hole_completion_probability(player, self.test_hole)
            
            # Verify probability distribution properties
            total_prob = sum(probs.values())
            self.assertAlmostEqual(total_prob, 1.0, places=2, 
                                 msg=f"Probabilities should sum to 1.0 for player {player.name}")
            
            # Verify all probabilities are valid
            for score, prob in probs.items():
                self.assertGreaterEqual(prob, 0.0, f"Probability for score {score} should be non-negative")
                self.assertLessEqual(prob, 1.0, f"Probability for score {score} should not exceed 1.0")
            
            # Lower handicap players should have better expected scores
            expected_score = sum(float(score) * prob for score, prob in probs.items())
            if player.handicap <= 5:
                self.assertLessEqual(expected_score, self.test_hole.par + 1, 
                                   f"Low handicap player should score near par")

    def test_team_win_probability_calculations(self):
        """Test team win probability calculations"""
        # Test pending teams
        pending_hole = HoleState(hole_number=1, par=4, teams=TeamConfiguration.PENDING)
        pending_probs = self.calculator._calculate_team_win_probability(self.test_players, pending_hole)
        self.assertEqual(pending_probs.get("pending"), 1.0, "Pending teams should return 100% pending probability")
        
        # Test solo configuration
        solo_hole = HoleState(hole_number=1, par=4, teams=TeamConfiguration.SOLO)
        solo_probs = self.calculator._calculate_team_win_probability(self.test_players, solo_hole)
        
        self.assertIn("captain", solo_probs, "Solo configuration should include captain probability")
        self.assertIn("opponents", solo_probs, "Solo configuration should include opponents probability")
        
        captain_prob = solo_probs["captain"]
        opponents_prob = solo_probs["opponents"]
        self.assertAlmostEqual(captain_prob + opponents_prob, 1.0, places=2,
                             msg="Captain and opponents probabilities should sum to 1.0")
        
        # Captain (scratch player) should have reasonable chance but not overwhelming
        self.assertGreater(captain_prob, 0.1, "Captain should have reasonable win probability")
        self.assertLess(captain_prob, 0.6, "Captain shouldn't have overwhelming advantage against 3 players")

    def test_expected_value_calculations(self):
        """Test expected value calculations for betting scenarios"""
        # Test offer double scenario
        ev_offer = self.calculator._calculate_expected_value(
            scenario="offer_double",
            win_prob=0.6,
            current_wager=2,
            players=self.test_players
        )
        # Should be positive for favorable odds
        self.assertGreater(ev_offer, 0, "Offering double with 60% win probability should have positive EV")
        
        # Test accept double scenario
        ev_accept = self.calculator._calculate_expected_value(
            scenario="accept_double", 
            win_prob=0.4,
            current_wager=2,
            players=self.test_players
        )
        # Should be negative for unfavorable odds
        self.assertLess(ev_accept, 0, "Accepting double with 40% win probability should have negative EV")
        
        # Test go solo scenario
        ev_solo = self.calculator._calculate_expected_value(
            scenario="go_solo",
            win_prob=0.3,
            current_wager=1,
            players=self.test_players
        )
        # Solo has 3:1 payout but double stakes, so needs good probability
        self.assertIsInstance(ev_solo, float, "Solo EV should be a valid number")

    def test_risk_assessment(self):
        """Test risk level assessment logic"""
        # Low risk scenario
        low_risk = self.calculator._assess_risk_level(win_prob=0.7, expected_value=1.5)
        self.assertEqual(low_risk, "low", "High win probability with positive EV should be low risk")
        
        # Medium risk scenario
        medium_risk = self.calculator._assess_risk_level(win_prob=0.5, expected_value=0.2)
        self.assertEqual(medium_risk, "medium", "Moderate win probability should be medium risk")
        
        # High risk scenario
        high_risk = self.calculator._assess_risk_level(win_prob=0.3, expected_value=-0.8)
        self.assertEqual(high_risk, "high", "Low win probability with negative EV should be high risk")

    def test_educational_insights_generation(self):
        """Test educational insights generation"""
        # Create diverse player set for insights
        diverse_players = [
            PlayerState(id="p1", name="Scratch", handicap=0, distance_to_pin=50),
            PlayerState(id="p2", name="Bogey", handicap=18, distance_to_pin=200)
        ]
        
        insights = self.calculator._generate_educational_insights(
            diverse_players, self.test_hole, []
        )
        
        self.assertIsInstance(insights, list, "Insights should be a list")
        self.assertGreater(len(insights), 0, "Should generate some insights")
        
        # Check for handicap spread insight
        handicap_insight = any("handicap spread" in insight.lower() for insight in insights)
        self.assertTrue(handicap_insight, "Should mention handicap spread for diverse players")

    def test_performance_timing(self):
        """Test that calculations meet performance requirements"""
        start_time = time.time()
        
        result = self.calculator.calculate_real_time_odds(
            self.test_players,
            self.test_hole
        )
        
        end_time = time.time()
        calculation_time_ms = (end_time - start_time) * 1000
        
        # Check performance target
        self.assertLess(calculation_time_ms, 100, 
                       f"Calculation took {calculation_time_ms:.1f}ms, should be under 100ms")
        
        # Check that result is valid
        self.assertIsNotNone(result, "Should return a valid result")
        self.assertIsInstance(result.calculation_time_ms, float, "Should include calculation time")
        self.assertGreater(result.confidence_level, 0, "Should have positive confidence level")

    def test_caching_functionality(self):
        """Test that caching improves performance"""
        # First calculation
        start_time = time.time()
        result1 = self.calculator._calculate_shot_success_probability(
            handicap=10, distance=150, lie_type="fairway", hole_difficulty=3.0
        )
        first_calc_time = time.time() - start_time
        
        # Second calculation (should hit cache)
        start_time = time.time()
        result2 = self.calculator._calculate_shot_success_probability(
            handicap=10, distance=150, lie_type="fairway", hole_difficulty=3.0
        )
        second_calc_time = time.time() - start_time
        
        # Results should be identical
        self.assertEqual(result1, result2, "Cached results should be identical")
        
        # Second calculation should be faster (cache hit)
        self.assertLessEqual(second_calc_time, first_calc_time, 
                           "Cached calculation should not be slower")

    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Empty player list
        empty_result = self.calculator.calculate_real_time_odds([], self.test_hole)
        self.assertIsNotNone(empty_result, "Should handle empty player list gracefully")
        
        # Extreme handicaps
        extreme_player = PlayerState(
            id="extreme", name="Extreme", handicap=50, distance_to_pin=500
        )
        extreme_prob = self.calculator._calculate_shot_success_probability(
            handicap=50, distance=500, lie_type="water", hole_difficulty=5.0
        )
        self.assertGreaterEqual(extreme_prob, 0.05, "Should maintain minimum probability")
        self.assertLessEqual(extreme_prob, 0.95, "Should maintain maximum probability")
        
        # Zero distance (on green)
        zero_distance_prob = self.calculator._calculate_shot_success_probability(
            handicap=20, distance=0, lie_type="green", hole_difficulty=3.0
        )
        self.assertGreater(zero_distance_prob, 0.8, "Zero distance should have very high success probability")

    def test_mathematical_consistency(self):
        """Test mathematical consistency and conservation laws"""
        # Test that probabilities are monotonic with respect to skill
        handicaps = [0, 5, 10, 15, 20, 25, 30]
        probabilities = []
        
        for hcp in handicaps:
            prob = self.calculator._calculate_shot_success_probability(
                handicap=hcp, distance=150, lie_type="fairway", hole_difficulty=3.0
            )
            probabilities.append(prob)
        
        # Probabilities should generally decrease with increasing handicap
        for i in range(len(probabilities) - 1):
            # Allow for small deviations due to discrete handicap adjustments
            self.assertGreaterEqual(probabilities[i] + 0.05, probabilities[i + 1],
                                  f"Probability should not increase significantly with higher handicap: "
                                  f"{handicaps[i]} hcp: {probabilities[i]:.3f}, "
                                  f"{handicaps[i+1]} hcp: {probabilities[i+1]:.3f}")

    def test_betting_scenario_generation(self):
        """Test betting scenario generation"""
        team_probs = {"captain": 0.4, "opponents": 0.6}
        
        scenarios = self.calculator._generate_betting_scenarios(
            self.test_players, self.test_hole, team_probs
        )
        
        self.assertIsInstance(scenarios, list, "Should return list of scenarios")
        
        for scenario in scenarios:
            self.assertIsInstance(scenario, BettingScenario, "Each scenario should be a BettingScenario")
            self.assertIsInstance(scenario.win_probability, float, "Win probability should be float")
            self.assertGreaterEqual(scenario.win_probability, 0, "Win probability should be non-negative")
            self.assertLessEqual(scenario.win_probability, 1, "Win probability should not exceed 1")
            self.assertIsInstance(scenario.expected_value, float, "Expected value should be float")
            self.assertIn(scenario.risk_level, ["low", "medium", "high"], "Risk level should be valid")

    def test_confidence_calculations(self):
        """Test confidence level calculations"""
        # Test with good data quality
        high_conf = self.calculator._calculate_overall_confidence(
            {"p1": {"win_probability": 0.3}, "p2": {"win_probability": 0.7}},
            {"team1": 0.5, "team2": 0.5},
            self.test_hole
        )
        
        self.assertGreater(high_conf, 0.5, "Should have reasonable confidence with good data")
        self.assertLessEqual(high_conf, 1.0, "Confidence should not exceed 1.0")
        
        # Test with limited data
        low_conf = self.calculator._calculate_overall_confidence(
            {"p1": {"win_probability": 0.5}},  # Only one player
            {},  # No team data
            HoleState(hole_number=1, par=4, teams=TeamConfiguration.PENDING)
        )
        
        self.assertLess(low_conf, high_conf, "Should have lower confidence with limited data")


class TestDataConversion(unittest.TestCase):
    """Test data conversion utilities"""

    def test_player_state_conversion(self):
        """Test conversion from game data to PlayerState"""
        game_player_data = {
            "id": "test_player",
            "name": "Test Player",
            "handicap": 12.5,
            "distance_to_pin": 175.0,
            "lie_type": "rough",
            "is_captain": True,
            "team_id": "team1"
        }
        
        player_state = create_player_state_from_game_data(game_player_data)
        
        self.assertEqual(player_state.id, "test_player")
        self.assertEqual(player_state.name, "Test Player")
        self.assertEqual(player_state.handicap, 12.5)
        self.assertEqual(player_state.distance_to_pin, 175.0)
        self.assertEqual(player_state.lie_type, "rough")
        self.assertTrue(player_state.is_captain)
        self.assertEqual(player_state.team_id, "team1")

    def test_hole_state_conversion(self):
        """Test conversion from game data to HoleState"""
        game_hole_data = {
            "hole_number": 15,
            "par": 5,
            "difficulty_rating": 4.2,
            "teams": "solo",
            "current_wager": 4,
            "is_doubled": True
        }
        
        hole_state = create_hole_state_from_game_data(game_hole_data)
        
        self.assertEqual(hole_state.hole_number, 15)
        self.assertEqual(hole_state.par, 5)
        self.assertEqual(hole_state.difficulty_rating, 4.2)
        self.assertEqual(hole_state.teams, TeamConfiguration.SOLO)
        self.assertEqual(hole_state.current_wager, 4)
        self.assertTrue(hole_state.is_doubled)

    def test_missing_data_handling(self):
        """Test handling of missing or incomplete data"""
        minimal_player_data = {
            "id": "minimal",
            "name": "Minimal Player"
        }
        
        player_state = create_player_state_from_game_data(minimal_player_data)
        
        # Should provide reasonable defaults
        self.assertEqual(player_state.handicap, 18.0)  # Default handicap
        self.assertEqual(player_state.distance_to_pin, 0.0)  # Default distance
        self.assertEqual(player_state.lie_type, "fairway")  # Default lie
        self.assertFalse(player_state.is_captain)  # Default captain status


class TestPerformanceBenchmarks(unittest.TestCase):
    """Performance benchmark tests"""

    def setUp(self):
        self.calculator = OddsCalculator()
        
    def test_large_group_performance(self):
        """Test performance with maximum player count"""
        # Create 6 players (maximum supported)
        large_group = []
        for i in range(6):
            large_group.append(PlayerState(
                id=f"p{i+1}",
                name=f"Player {i+1}",
                handicap=float(i * 5),
                distance_to_pin=150.0 + i * 10,
                lie_type="fairway"
            ))
        
        hole = HoleState(hole_number=1, par=4)
        
        start_time = time.time()
        result = self.calculator.calculate_real_time_odds(large_group, hole)
        calc_time = (time.time() - start_time) * 1000
        
        self.assertLess(calc_time, 150, f"Large group calculation took {calc_time:.1f}ms, should be under 150ms")
        self.assertIsNotNone(result)

    def test_complex_scenario_performance(self):
        """Test performance with complex scenarios"""
        # Complex scenario: solo play with different lies
        players = [
            PlayerState(id="captain", name="Captain", handicap=8, distance_to_pin=120, 
                       lie_type="bunker", is_captain=True),
            PlayerState(id="p2", name="Player 2", handicap=12, distance_to_pin=95, lie_type="green"),
            PlayerState(id="p3", name="Player 3", handicap=16, distance_to_pin=160, lie_type="rough"),
            PlayerState(id="p4", name="Player 4", handicap=20, distance_to_pin=200, lie_type="trees")
        ]
        
        hole = HoleState(
            hole_number=18, 
            par=5, 
            difficulty_rating=4.5,
            teams=TeamConfiguration.SOLO,
            current_wager=4,
            is_doubled=True
        )
        
        start_time = time.time()
        result = self.calculator.calculate_real_time_odds(players, hole)
        calc_time = (time.time() - start_time) * 1000
        
        self.assertLess(calc_time, 100, f"Complex scenario took {calc_time:.1f}ms, should be under 100ms")
        self.assertGreater(len(result.betting_scenarios), 0, "Should generate betting scenarios")
    
    def test_repeated_calculations_performance(self):
        """Test performance improvement with repeated calculations (caching)"""
        players = self.test_players
        hole = HoleState(hole_number=5, par=4, difficulty_rating=3.0)
        
        # Time first calculation
        times = []
        for i in range(10):
            start_time = time.time()
            result = self.calculator.calculate_real_time_odds(players, hole)
            calc_time = (time.time() - start_time) * 1000
            times.append(calc_time)
        
        # Later calculations should generally be faster due to caching
        avg_first_half = sum(times[:5]) / 5
        avg_second_half = sum(times[5:]) / 5
        
        # Allow some variance, but second half should trend faster
        self.assertLessEqual(avg_second_half, avg_first_half * 1.2, 
                           f"Second half avg ({avg_second_half:.1f}ms) should not be much slower than first half ({avg_first_half:.1f}ms)")
    
    def test_memory_usage_stability(self):
        """Test that repeated calculations don't cause memory leaks"""
        import gc
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run many calculations
        for i in range(100):
            players = [
                PlayerState(id=f"p{j}", name=f"Player {j}", handicap=float(j*2), 
                           distance_to_pin=100 + i*2) for j in range(4)
            ]
            hole = HoleState(hole_number=i % 18 + 1, par=4)
            result = self.calculator.calculate_real_time_odds(players, hole)
        
        gc.collect()  # Force garbage collection
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (under 50MB)
        self.assertLess(memory_growth, 50, 
                       f"Memory grew by {memory_growth:.1f}MB, should be under 50MB")
    
    def test_concurrent_calculation_safety(self):
        """Test thread safety of calculations"""
        import threading
        import queue
        
        results_queue = queue.Queue()
        errors_queue = queue.Queue()
        
        def calculate_worker(worker_id):
            try:
                players = [
                    PlayerState(id=f"w{worker_id}_p{i}", name=f"Worker {worker_id} Player {i}", 
                               handicap=float(worker_id + i), distance_to_pin=150 + worker_id*10)
                    for i in range(3)
                ]
                hole = HoleState(hole_number=worker_id % 18 + 1, par=4)
                
                result = self.calculator.calculate_real_time_odds(players, hole)
                results_queue.put((worker_id, result))
            except Exception as e:
                errors_queue.put((worker_id, e))
        
        # Start multiple threads
        threads = []
        for i in range(8):
            thread = threading.Thread(target=calculate_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check for errors
        while not errors_queue.empty():
            worker_id, error = errors_queue.get()
            self.fail(f"Worker {worker_id} failed with error: {error}")
        
        # Check results
        results = {}
        while not results_queue.empty():
            worker_id, result = results_queue.get()
            results[worker_id] = result
        
        self.assertEqual(len(results), 8, "All workers should complete successfully")
        for worker_id, result in results.items():
            self.assertIsNotNone(result, f"Worker {worker_id} should return valid result")


class TestAdvancedEdgeCases(unittest.TestCase):
    """Advanced edge case and error handling tests"""
    
    def setUp(self):
        self.calculator = OddsCalculator()
    
    def test_extreme_handicap_values(self):
        """Test handling of extreme handicap values"""
        test_cases = [
            (-5.0, "Negative handicap"),
            (0.0, "Scratch player"),
            (54.0, "Maximum handicap"),
            (100.0, "Beyond maximum handicap")
        ]
        
        for handicap, description in test_cases:
            with self.subTest(handicap=handicap, description=description):
                prob = self.calculator._calculate_shot_success_probability(
                    handicap=handicap, distance=150, lie_type="fairway", hole_difficulty=3.0
                )
                self.assertIsInstance(prob, float, f"Should return float for {description}")
                self.assertGreaterEqual(prob, 0.0, f"Probability should be non-negative for {description}")
                self.assertLessEqual(prob, 1.0, f"Probability should not exceed 1.0 for {description}")
    
    def test_extreme_distances(self):
        """Test handling of extreme distances"""
        test_cases = [
            (0.0, "On the pin"),
            (1.0, "Tap-in distance"),
            (500.0, "Very long shot"),
            (1000.0, "Unrealistic distance")
        ]
        
        for distance, description in test_cases:
            with self.subTest(distance=distance, description=description):
                prob = self.calculator._calculate_shot_success_probability(
                    handicap=15, distance=distance, lie_type="fairway", hole_difficulty=3.0
                )
                self.assertIsInstance(prob, float, f"Should return float for {description}")
                self.assertGreaterEqual(prob, 0.0, f"Probability should be non-negative for {description}")
                self.assertLessEqual(prob, 1.0, f"Probability should not exceed 1.0 for {description}")
    
    def test_unusual_lie_types(self):
        """Test handling of unusual lie types"""
        unusual_lies = ["water", "trees", "cart_path", "bunker_lip", "deep_rough", "waste_area"]
        
        for lie_type in unusual_lies:
            with self.subTest(lie_type=lie_type):
                prob = self.calculator._calculate_shot_success_probability(
                    handicap=12, distance=150, lie_type=lie_type, hole_difficulty=3.0
                )
                self.assertIsInstance(prob, float, f"Should handle {lie_type} lie")
                self.assertGreater(prob, 0.0, f"Should maintain minimum probability for {lie_type}")
                self.assertLess(prob, 1.0, f"Should not be certain success for {lie_type}")
    
    def test_invalid_team_configurations(self):
        """Test handling of invalid team configurations"""
        players = [
            PlayerState(id="p1", name="Player 1", handicap=10, is_captain=True),
            PlayerState(id="p2", name="Player 2", handicap=15)
        ]
        
        # Test with invalid team string
        hole = HoleState(hole_number=1, par=4, teams="invalid_team_config")
        result = self.calculator.calculate_real_time_odds(players, hole)
        self.assertIsNotNone(result, "Should handle invalid team configuration gracefully")
    
    def test_missing_captain_in_solo_play(self):
        """Test handling of solo play without designated captain"""
        players = [
            PlayerState(id="p1", name="Player 1", handicap=10, is_captain=False),
            PlayerState(id="p2", name="Player 2", handicap=15, is_captain=False)
        ]
        
        hole = HoleState(hole_number=1, par=4, teams=TeamConfiguration.SOLO)
        result = self.calculator.calculate_real_time_odds(players, hole)
        self.assertIsNotNone(result, "Should handle missing captain gracefully")
    
    def test_multiple_captains(self):
        """Test handling of multiple designated captains"""
        players = [
            PlayerState(id="p1", name="Player 1", handicap=10, is_captain=True),
            PlayerState(id="p2", name="Player 2", handicap=15, is_captain=True)
        ]
        
        hole = HoleState(hole_number=1, par=4, teams=TeamConfiguration.SOLO)
        result = self.calculator.calculate_real_time_odds(players, hole)
        self.assertIsNotNone(result, "Should handle multiple captains gracefully")
    
    def test_zero_or_negative_par(self):
        """Test handling of invalid par values"""
        players = [PlayerState(id="p1", name="Player 1", handicap=10)]
        
        # Test zero par
        hole_zero_par = HoleState(hole_number=1, par=0)
        result = self.calculator.calculate_real_time_odds(players, hole_zero_par)
        self.assertIsNotNone(result, "Should handle zero par gracefully")
        
        # Test negative par
        hole_neg_par = HoleState(hole_number=1, par=-1)
        result = self.calculator.calculate_real_time_odds(players, hole_neg_par)
        self.assertIsNotNone(result, "Should handle negative par gracefully")
    
    def test_extreme_difficulty_ratings(self):
        """Test handling of extreme difficulty ratings"""
        players = [PlayerState(id="p1", name="Player 1", handicap=10)]
        
        test_difficulties = [0.0, -1.0, 6.0, 100.0]
        
        for difficulty in test_difficulties:
            with self.subTest(difficulty=difficulty):
                hole = HoleState(hole_number=1, par=4, difficulty_rating=difficulty)
                result = self.calculator.calculate_real_time_odds(players, hole)
                self.assertIsNotNone(result, f"Should handle difficulty {difficulty} gracefully")
    
    def test_fractional_wagers(self):
        """Test handling of fractional wager amounts"""
        players = [PlayerState(id="p1", name="Player 1", handicap=10)]
        
        # Test fractional wager
        hole = HoleState(hole_number=1, par=4, current_wager=2.5)
        result = self.calculator.calculate_real_time_odds(players, hole)
        self.assertIsNotNone(result, "Should handle fractional wagers")
        
        # Test zero wager
        hole_zero = HoleState(hole_number=1, par=4, current_wager=0)
        result = self.calculator.calculate_real_time_odds(players, hole_zero)
        self.assertIsNotNone(result, "Should handle zero wager")


class TestCachingMechanisms(unittest.TestCase):
    """Test caching mechanisms and cache invalidation"""
    
    def setUp(self):
        self.calculator = OddsCalculator()
    
    def test_shot_probability_caching(self):
        """Test that shot probability calculations are properly cached"""
        # First calculation
        prob1 = self.calculator._calculate_shot_success_probability(
            handicap=12, distance=150, lie_type="fairway", hole_difficulty=3.0
        )
        
        # Second identical calculation (should hit cache)
        prob2 = self.calculator._calculate_shot_success_probability(
            handicap=12, distance=150, lie_type="fairway", hole_difficulty=3.0
        )
        
        self.assertEqual(prob1, prob2, "Cached results should be identical")
    
    def test_cache_key_sensitivity(self):
        """Test that cache is sensitive to parameter changes"""
        base_prob = self.calculator._calculate_shot_success_probability(
            handicap=12, distance=150, lie_type="fairway", hole_difficulty=3.0
        )
        
        # Change handicap
        handicap_prob = self.calculator._calculate_shot_success_probability(
            handicap=13, distance=150, lie_type="fairway", hole_difficulty=3.0
        )
        self.assertNotEqual(base_prob, handicap_prob, "Different handicap should give different result")
        
        # Change distance
        distance_prob = self.calculator._calculate_shot_success_probability(
            handicap=12, distance=160, lie_type="fairway", hole_difficulty=3.0
        )
        self.assertNotEqual(base_prob, distance_prob, "Different distance should give different result")
        
        # Change lie type
        lie_prob = self.calculator._calculate_shot_success_probability(
            handicap=12, distance=150, lie_type="rough", hole_difficulty=3.0
        )
        self.assertNotEqual(base_prob, lie_prob, "Different lie should give different result")
    
    def test_cache_performance_improvement(self):
        """Test that caching provides measurable performance improvement"""
        import time
        
        # Parameters for calculation
        params = (12, 150, "fairway", 3.0)
        
        # First calculation (cache miss)
        start_time = time.time()
        prob1 = self.calculator._calculate_shot_success_probability(*params)
        first_time = time.time() - start_time
        
        # Multiple cached calculations
        cached_times = []
        for _ in range(10):
            start_time = time.time()
            prob = self.calculator._calculate_shot_success_probability(*params)
            cached_times.append(time.time() - start_time)
            self.assertEqual(prob, prob1, "Cached results should be consistent")
        
        avg_cached_time = sum(cached_times) / len(cached_times)
        
        # Cached calculations should be significantly faster
        # (allowing for some variance in timing)
        self.assertLessEqual(avg_cached_time, first_time * 0.8,
                           f"Cached calculations ({avg_cached_time:.6f}s) should be faster than first ({first_time:.6f}s)")


class TestAccuracyValidation(unittest.TestCase):
    """Test mathematical accuracy and validation against known results"""
    
    def setUp(self):
        self.calculator = OddsCalculator()
    
    def test_probability_bounds_enforcement(self):
        """Test that all probability calculations stay within valid bounds"""
        import random
        
        # Test many random combinations
        for _ in range(100):
            handicap = random.uniform(-5, 50)
            distance = random.uniform(0, 500)
            lie_type = random.choice(["fairway", "rough", "bunker", "green", "trees", "water"])
            difficulty = random.uniform(1, 5)
            
            prob = self.calculator._calculate_shot_success_probability(
                handicap, distance, lie_type, difficulty
            )
            
            self.assertGreaterEqual(prob, 0.0, f"Probability {prob} should be >= 0 for "
                                             f"hcp={handicap:.1f}, dist={distance:.1f}, lie={lie_type}")
            self.assertLessEqual(prob, 1.0, f"Probability {prob} should be <= 1 for "
                                           f"hcp={handicap:.1f}, dist={distance:.1f}, lie={lie_type}")
    
    def test_handicap_progression_consistency(self):
        """Test that handicap progression follows expected patterns"""
        handicaps = range(0, 31, 2)  # 0, 2, 4, ..., 30
        probabilities = []
        
        for hcp in handicaps:
            prob = self.calculator._calculate_shot_success_probability(
                handicap=float(hcp), distance=150, lie_type="fairway", hole_difficulty=3.0
            )
            probabilities.append(prob)
        
        # Check for generally decreasing trend
        decreasing_pairs = 0
        total_pairs = len(probabilities) - 1
        
        for i in range(total_pairs):
            if probabilities[i] >= probabilities[i + 1]:
                decreasing_pairs += 1
        
        # At least 80% of pairs should follow the decreasing trend
        self.assertGreaterEqual(decreasing_pairs / total_pairs, 0.8,
                              "Probability should generally decrease with higher handicap")
    
    def test_distance_progression_consistency(self):
        """Test that distance progression follows expected patterns"""
        distances = [10, 25, 50, 75, 100, 150, 200, 250, 300]
        probabilities = []
        
        for dist in distances:
            prob = self.calculator._calculate_shot_success_probability(
                handicap=12.0, distance=float(dist), lie_type="fairway", hole_difficulty=3.0
            )
            probabilities.append(prob)
        
        # Check for generally decreasing trend with distance
        decreasing_pairs = 0
        total_pairs = len(probabilities) - 1
        
        for i in range(total_pairs):
            if probabilities[i] >= probabilities[i + 1]:
                decreasing_pairs += 1
        
        # At least 70% of pairs should follow the decreasing trend
        self.assertGreaterEqual(decreasing_pairs / total_pairs, 0.7,
                              "Probability should generally decrease with longer distance")
    
    def test_expected_value_calculation_accuracy(self):
        """Test expected value calculations for mathematical accuracy"""
        # Known scenario: 60% win rate, double or nothing bet
        ev = self.calculator._calculate_expected_value(
            scenario="offer_double",
            win_prob=0.6,
            current_wager=2,
            players=[]
        )
        
        # Expected calculation: 0.6 * 4 - 0.4 * 2 = 2.4 - 0.8 = 1.6
        expected_ev = 0.6 * 4 - 0.4 * 2
        self.assertAlmostEqual(ev, expected_ev, places=2,
                             msg=f"Expected value calculation: got {ev}, expected {expected_ev}")
    
    def test_probability_distribution_normalization(self):
        """Test that probability distributions properly normalize to 1.0"""
        player = PlayerState(id="test", name="Test", handicap=12, distance_to_pin=150)
        hole = HoleState(hole_number=10, par=4, difficulty_rating=3.0)
        
        prob_dist = self.calculator._calculate_hole_completion_probability(player, hole)
        
        total_prob = sum(prob_dist.values())
        self.assertAlmostEqual(total_prob, 1.0, places=2,
                             msg=f"Probability distribution should sum to 1.0, got {total_prob}")
        
        # Check individual probabilities
        for score, prob in prob_dist.items():
            self.assertGreaterEqual(prob, 0.0, f"Probability for score {score} should be non-negative")
            self.assertLessEqual(prob, 1.0, f"Probability for score {score} should not exceed 1.0")


if __name__ == '__main__':
    # Create test suite
    test_loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestOddsCalculator))
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestDataConversion))
    test_suite.addTest(test_loader.loadTestsFromTestCase(TestPerformanceBenchmarks))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"ODDS CALCULATOR TEST SUMMARY")
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