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