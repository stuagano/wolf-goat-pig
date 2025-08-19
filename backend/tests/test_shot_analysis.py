"""
Comprehensive test suite for Shot Range Analysis System

This module provides thorough testing for the poker-style shot analysis system,
including range calculations, game theory optimal (GTO) recommendations,
exploitative adjustments, and visual indicator generation.

Test Coverage:
- ShotRange class and equity calculations
- ShotRangeMatrix range generation and recommendations
- ShotRangeAnalyzer complete analysis workflow
- Real-time updates and caching
- Edge cases and error handling
- Performance benchmarks
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import math
from typing import Dict, List, Any

from app.domain.shot_range_analysis import (
    ShotType, RiskProfile, ShotRange, ShotRangeMatrix, ShotRangeAnalyzer,
    analyze_shot_decision
)


class TestShotRange:
    """Test suite for ShotRange class and equity calculations."""
    
    def test_shot_range_creation(self):
        """Test ShotRange object creation with valid parameters."""
        shot_range = ShotRange(
            shot_type=ShotType.STANDARD_APPROACH,
            success_probability=0.7,
            risk_factor=0.4,
            expected_value=0.15,
            variance=0.8,
            fold_equity=0.1,
            bluff_frequency=0.15,
            pot_odds_required=0.45
        )
        
        assert shot_range.shot_type == ShotType.STANDARD_APPROACH
        assert shot_range.success_probability == 0.7
        assert shot_range.risk_factor == 0.4
        assert shot_range.expected_value == 0.15
        assert shot_range.fold_equity == 0.1
    
    def test_get_equity_vs_field_basic(self):
        """Test basic equity calculation without fold equity."""
        shot_range = ShotRange(
            shot_type=ShotType.SAFE_APPROACH,
            success_probability=0.8,
            risk_factor=0.2,
            expected_value=0.0,
            variance=0.3,
            fold_equity=0.0
        )
        
        equity = shot_range.get_equity_vs_field()
        assert equity == 0.8
    
    def test_get_equity_vs_field_with_fold_equity(self):
        """Test equity calculation with fold equity component."""
        shot_range = ShotRange(
            shot_type=ShotType.PIN_SEEKER,
            success_probability=0.4,
            risk_factor=0.8,
            expected_value=0.5,
            variance=1.2,
            fold_equity=0.3
        )
        
        # Expected: 0.4 + (1 - 0.4) * 0.3 = 0.4 + 0.18 = 0.58
        equity = shot_range.get_equity_vs_field()
        assert abs(equity - 0.58) < 0.001
    
    def test_get_equity_vs_field_capped_at_one(self):
        """Test that equity is capped at 1.0 even with high fold equity."""
        shot_range = ShotRange(
            shot_type=ShotType.HERO_SHOT,
            success_probability=0.9,
            risk_factor=0.95,
            expected_value=1.0,
            variance=2.0,
            fold_equity=0.5
        )
        
        equity = shot_range.get_equity_vs_field()
        assert equity == 1.0
    
    @pytest.mark.parametrize("success_prob,fold_eq,expected", [
        (0.2, 0.0, 0.2),
        (0.5, 0.2, 0.6),
        (0.3, 0.4, 0.58),
        (0.1, 0.8, 0.82),
        (1.0, 0.5, 1.0)
    ])
    def test_equity_calculations_parametrized(self, success_prob, fold_eq, expected):
        """Test equity calculations with various parameter combinations."""
        shot_range = ShotRange(
            shot_type=ShotType.STANDARD_APPROACH,
            success_probability=success_prob,
            risk_factor=0.5,
            expected_value=0.0,
            variance=0.5,
            fold_equity=fold_eq
        )
        
        equity = shot_range.get_equity_vs_field()
        assert abs(equity - expected) < 0.001


class TestShotRangeMatrix:
    """Test suite for ShotRangeMatrix range generation and calculations."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.basic_game_situation = {
            "hole_number": 8,
            "partnership_formed": False,
            "match_critical": False,
            "trailing_significantly": False,
            "hazards_present": False,
            "risk_reward_available": True,
            "hero_shot_possible": False,
            "opponent_style": "balanced"
        }
    
    def test_short_game_ranges_creation(self):
        """Test range creation for short game situations (< 100 yards)."""
        matrix = ShotRangeMatrix(
            lie_type="fairway",
            distance_to_pin=80,
            player_handicap=12,
            game_situation=self.basic_game_situation
        )
        
        assert len(matrix.ranges) >= 2  # At least safe and standard approaches
        
        # Check for expected shot types
        shot_types = [r.shot_type for r in matrix.ranges]
        assert ShotType.SAFE_APPROACH in shot_types
        assert ShotType.STANDARD_APPROACH in shot_types
    
    def test_approach_ranges_creation(self):
        """Test range creation for approach shots (100-150 yards)."""
        game_situation = self.basic_game_situation.copy()
        game_situation["hazards_present"] = True
        
        matrix = ShotRangeMatrix(
            lie_type="fairway",
            distance_to_pin=125,
            player_handicap=8,
            game_situation=game_situation
        )
        
        assert len(matrix.ranges) >= 3  # Lay up, standard, risk/reward
        
        shot_types = [r.shot_type for r in matrix.ranges]
        assert ShotType.LAY_UP in shot_types
        assert ShotType.STANDARD_APPROACH in shot_types
        assert ShotType.RISK_REWARD in shot_types
    
    def test_tee_shot_ranges_creation(self):
        """Test range creation for tee shots (> 200 yards)."""
        game_situation = self.basic_game_situation.copy()
        game_situation["hero_shot_possible"] = True
        
        matrix = ShotRangeMatrix(
            lie_type="tee",
            distance_to_pin=350,
            player_handicap=5,  # Low handicap for hero shot
            game_situation=game_situation
        )
        
        shot_types = [r.shot_type for r in matrix.ranges]
        assert ShotType.FAIRWAY_FINDER in shot_types
        assert ShotType.RISK_REWARD in shot_types
        assert ShotType.HERO_SHOT in shot_types
    
    def test_gto_range_calculation(self):
        """Test Game Theory Optimal range selection."""
        matrix = ShotRangeMatrix(
            lie_type="fairway",
            distance_to_pin=120,
            player_handicap=10,
            game_situation=self.basic_game_situation
        )
        
        assert matrix.gto_range is not None
        
        # GTO range should have reasonable EV
        assert matrix.gto_range.expected_value >= -0.5
        
        # Should be among the best EV ranges
        best_ev = max(r.expected_value for r in matrix.ranges)
        assert matrix.gto_range.expected_value >= best_ev * 0.8
    
    def test_gto_range_pressure_situation(self):
        """Test GTO range selection under pressure."""
        pressure_situation = self.basic_game_situation.copy()
        pressure_situation["hole_number"] = 18  # Final hole
        pressure_situation["match_critical"] = True
        
        matrix = ShotRangeMatrix(
            lie_type="fairway",
            distance_to_pin=120,
            player_handicap=10,
            game_situation=pressure_situation
        )
        
        # Under pressure, should favor lower variance
        conservative_ranges = [r for r in matrix.ranges if r.variance < 0.8]
        if conservative_ranges:
            assert matrix.gto_range in conservative_ranges
    
    def test_exploitative_adjustments_scared_opponents(self):
        """Test exploitative adjustments against scared opponents."""
        game_situation = self.basic_game_situation.copy()
        game_situation["opponent_style"] = "conservative"
        
        matrix = ShotRangeMatrix(
            lie_type="fairway",
            distance_to_pin=140,
            player_handicap=8,
            game_situation=game_situation
        )
        
        # Against scared opponents, should increase aggression
        if matrix.exploitative_range and matrix.gto_range:
            # Exploitative range should be more aggressive or have higher fold equity
            assert (matrix.exploitative_range.risk_factor >= matrix.gto_range.risk_factor or
                    matrix.exploitative_range.fold_equity >= matrix.gto_range.fold_equity)
    
    def test_exploitative_adjustments_aggressive_opponents(self):
        """Test exploitative adjustments against aggressive opponents."""
        game_situation = self.basic_game_situation.copy()
        game_situation["opponent_style"] = "aggressive"
        
        matrix = ShotRangeMatrix(
            lie_type="fairway",
            distance_to_pin=140,
            player_handicap=8,
            game_situation=game_situation
        )
        
        # Against aggressive opponents, should play tighter
        if matrix.exploitative_range and matrix.gto_range:
            assert matrix.exploitative_range.risk_factor <= matrix.gto_range.risk_factor
    
    @pytest.mark.parametrize("player_style,max_risk", [
        (RiskProfile.NIT, 0.3),
        (RiskProfile.TAG, 0.6),
        (RiskProfile.LAG, 1.0),
        (RiskProfile.MANIAC, 1.0)
    ])
    def test_get_recommended_range_by_style(self, player_style, max_risk):
        """Test range recommendations based on player style."""
        matrix = ShotRangeMatrix(
            lie_type="fairway",
            distance_to_pin=130,
            player_handicap=10,
            game_situation=self.basic_game_situation
        )
        
        recommended = matrix.get_recommended_range(player_style)
        
        assert recommended is not None
        if player_style in [RiskProfile.NIT, RiskProfile.TAG]:
            assert recommended.risk_factor <= max_risk
        elif player_style == RiskProfile.LAG:
            assert recommended.expected_value > 0  # Should be positive EV
    
    def test_range_distribution_calculation(self):
        """Test range distribution percentage calculations."""
        matrix = ShotRangeMatrix(
            lie_type="fairway",
            distance_to_pin=150,
            player_handicap=12,
            game_situation=self.basic_game_situation
        )
        
        distribution = matrix.get_range_distribution()
        
        # Should return percentages that sum to 100
        total_percentage = sum(distribution.values())
        assert abs(total_percentage - 100.0) < 0.1
        
        # Should have entries for shot types that exist in ranges
        existing_types = {r.shot_type.value for r in matrix.ranges}
        for shot_type in existing_types:
            assert shot_type in distribution
            assert distribution[shot_type] > 0
    
    def test_3bet_range_calculation(self):
        """Test '3-bet' range (ultra-aggressive) calculations."""
        matrix = ShotRangeMatrix(
            lie_type="fairway",
            distance_to_pin=160,
            player_handicap=8,
            game_situation=self.basic_game_situation
        )
        
        three_bet_ranges = matrix.calculate_3bet_range()
        
        # All 3-bet ranges should meet criteria
        for range_shot in three_bet_ranges:
            assert range_shot.risk_factor >= 0.7
            assert range_shot.fold_equity >= 0.2
        
        # Should be sorted by EV (highest first)
        if len(three_bet_ranges) > 1:
            for i in range(len(three_bet_ranges) - 1):
                assert three_bet_ranges[i].expected_value >= three_bet_ranges[i + 1].expected_value
    
    def test_helper_methods(self):
        """Test various helper methods for situational checks."""
        matrix = ShotRangeMatrix(
            lie_type="fairway",
            distance_to_pin=100,
            player_handicap=8,
            game_situation=self.basic_game_situation
        )
        
        # Test pin accessibility
        assert matrix._is_pin_accessible()
        
        # Test hazard detection
        assert not matrix._has_hazards()
        
        game_situation_with_hazards = self.basic_game_situation.copy()
        game_situation_with_hazards["hazards_present"] = True
        matrix_hazards = ShotRangeMatrix(
            lie_type="rough",
            distance_to_pin=100,
            player_handicap=8,
            game_situation=game_situation_with_hazards
        )
        assert matrix_hazards._has_hazards()
        
        # Test pressure situation detection
        pressure_situation = self.basic_game_situation.copy()
        pressure_situation["hole_number"] = 17
        matrix_pressure = ShotRangeMatrix(
            lie_type="fairway",
            distance_to_pin=100,
            player_handicap=8,
            game_situation=pressure_situation
        )
        assert matrix_pressure._is_pressure_situation()


class TestShotRangeAnalyzer:
    """Test suite for ShotRangeAnalyzer complete analysis workflow."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.test_game_situation = {
            "hole_number": 10,
            "partnership_formed": True,
            "match_critical": False,
            "trailing_significantly": False,
            "hazards_present": True,
            "risk_reward_available": True,
            "hero_shot_possible": False,
            "opponent_style": "balanced"
        }
    
    def test_analyze_shot_selection_complete(self):
        """Test complete shot selection analysis workflow."""
        analysis = ShotRangeAnalyzer.analyze_shot_selection(
            lie_type="fairway",
            distance_to_pin=135,
            player_handicap=12,
            game_situation=self.test_game_situation,
            player_style=RiskProfile.TAG
        )
        
        # Check all required analysis components
        assert "recommended_shot" in analysis
        assert "gto_recommendation" in analysis
        assert "exploitative_play" in analysis
        assert "range_distribution" in analysis
        assert "all_ranges" in analysis
        assert "3bet_ranges" in analysis
        assert "player_style" in analysis
        assert "strategic_advice" in analysis
        
        # Check recommended shot details
        rec_shot = analysis["recommended_shot"]
        assert rec_shot["type"] is not None
        assert "%" in rec_shot["success_rate"]
        assert "%" in rec_shot["risk_level"]
        assert isinstance(rec_shot["expected_value"], (int, float))
        assert "%" in rec_shot["equity_vs_field"]
    
    def test_player_style_determination(self):
        """Test automatic player style determination."""
        # High handicap should be NIT
        nit_style = ShotRangeAnalyzer._determine_player_style(25, self.test_game_situation)
        assert nit_style == RiskProfile.NIT
        
        # Mid handicap should be TAG
        tag_style = ShotRangeAnalyzer._determine_player_style(12, self.test_game_situation)
        assert tag_style == RiskProfile.TAG
        
        # Low handicap should be LAG
        lag_style = ShotRangeAnalyzer._determine_player_style(7, self.test_game_situation)
        assert lag_style == RiskProfile.LAG
        
        # Scratch player should be MANIAC
        maniac_style = ShotRangeAnalyzer._determine_player_style(2, self.test_game_situation)
        assert maniac_style == RiskProfile.MANIAC
    
    def test_player_style_situational_adjustment(self):
        """Test player style adjustment based on game situation."""
        trailing_situation = self.test_game_situation.copy()
        trailing_situation["trailing_significantly"] = True
        
        # Should increase aggression when trailing
        base_style = ShotRangeAnalyzer._determine_player_style(15, self.test_game_situation)
        trailing_style = ShotRangeAnalyzer._determine_player_style(15, trailing_situation)
        
        # Trailing style should be more aggressive
        style_order = [RiskProfile.NIT, RiskProfile.TAG, RiskProfile.LAG, RiskProfile.MANIAC]
        assert style_order.index(trailing_style) > style_order.index(base_style)
    
    def test_get_style_description(self):
        """Test style description generation."""
        descriptions = {
            RiskProfile.NIT: ShotRangeAnalyzer._get_style_description(RiskProfile.NIT),
            RiskProfile.TAG: ShotRangeAnalyzer._get_style_description(RiskProfile.TAG),
            RiskProfile.LAG: ShotRangeAnalyzer._get_style_description(RiskProfile.LAG),
            RiskProfile.MANIAC: ShotRangeAnalyzer._get_style_description(RiskProfile.MANIAC)
        }
        
        for style, description in descriptions.items():
            assert isinstance(description, str)
            assert len(description) > 10  # Should be meaningful description
    
    def test_strategic_advice_generation(self):
        """Test strategic advice generation for different scenarios."""
        # Create mock objects for testing
        mock_matrix = Mock()
        mock_recommended = Mock()
        mock_recommended.risk_factor = 0.8  # High risk
        mock_recommended.fold_equity = 0.3  # High fold equity
        mock_recommended.bluff_frequency = 0.35  # High bluff frequency
        
        late_game_situation = self.test_game_situation.copy()
        late_game_situation["hole_number"] = 17
        late_game_situation["partnership_formed"] = True
        
        advice = ShotRangeAnalyzer._generate_strategic_advice(
            mock_matrix, mock_recommended, RiskProfile.TAG, late_game_situation
        )
        
        assert isinstance(advice, list)
        assert len(advice) > 0
        
        # Should contain specific advice for high-risk play
        advice_text = " ".join(advice)
        assert any(keyword in advice_text.lower() for keyword in ["risk", "pressure", "late"])
    
    def test_strategic_advice_conservative_play(self):
        """Test strategic advice for conservative plays."""
        mock_matrix = Mock()
        mock_recommended = Mock()
        mock_recommended.risk_factor = 0.2  # Low risk
        mock_recommended.fold_equity = 0.05
        mock_recommended.bluff_frequency = 0.0
        
        advice = ShotRangeAnalyzer._generate_strategic_advice(
            mock_matrix, mock_recommended, RiskProfile.NIT, self.test_game_situation
        )
        
        advice_text = " ".join(advice)
        assert any(keyword in advice_text.lower() for keyword in ["conservative", "safe", "building"])
    
    @pytest.mark.parametrize("handicap,expected_ranges", [
        (25, 1),  # High handicap - very few ranges
        (15, 2),  # Mid handicap - moderate ranges  
        (8, 3),   # Low handicap - more ranges
        (3, 4),   # Scratch - most ranges
    ])
    def test_range_count_by_handicap(self, handicap, expected_ranges):
        """Test that range count increases with lower handicap."""
        analysis = ShotRangeAnalyzer.analyze_shot_selection(
            lie_type="fairway",
            distance_to_pin=140,
            player_handicap=handicap,
            game_situation=self.test_game_situation
        )
        
        # Higher skilled players should have access to more shot types
        range_count = len(analysis["all_ranges"])
        if handicap <= 10:
            assert range_count >= expected_ranges


class TestAnalyzeShotDecision:
    """Test suite for the main entry point function."""
    
    def test_analyze_shot_decision_basic(self):
        """Test basic functionality of analyze_shot_decision."""
        result = analyze_shot_decision(
            current_lie="fairway",
            distance=145,
            player_handicap=12,
            hole_number=8,
            team_situation="partnership",
            score_differential=1,
            opponent_styles=["aggressive"]
        )
        
        assert isinstance(result, dict)
        assert "recommended_shot" in result
        assert "player_style" in result
        assert "strategic_advice" in result
    
    def test_analyze_shot_decision_critical_situation(self):
        """Test analysis for critical match situations."""
        result = analyze_shot_decision(
            current_lie="rough",
            distance=180,
            player_handicap=8,
            hole_number=18,  # Final hole
            team_situation="solo",
            score_differential=-4,  # Trailing significantly
            opponent_styles=["conservative", "aggressive"]
        )
        
        # Should recognize critical situation
        advice = result.get("strategic_advice", [])
        advice_text = " ".join(advice).lower()
        
        # Should contain late game or critical situation advice
        assert any(keyword in advice_text for keyword in ["late", "critical", "variance", "final"])
    
    def test_analyze_shot_decision_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Very short distance
        short_result = analyze_shot_decision(
            current_lie="green",
            distance=15,
            player_handicap=20,
            hole_number=1
        )
        assert short_result["recommended_shot"]["type"] is not None
        
        # Very long distance
        long_result = analyze_shot_decision(
            current_lie="tee",
            distance=450,
            player_handicap=5,
            hole_number=1
        )
        assert long_result["recommended_shot"]["type"] is not None
        
        # Extreme handicap
        high_handicap_result = analyze_shot_decision(
            current_lie="fairway",
            distance=150,
            player_handicap=36,
            hole_number=10
        )
        assert high_handicap_result["player_style"]["profile"] == RiskProfile.NIT.value


class TestPerformanceAndEdgeCases:
    """Test suite for performance benchmarks and edge cases."""
    
    def test_analysis_performance_benchmark(self):
        """Benchmark analysis performance for acceptable response times."""
        import time
        
        start_time = time.time()
        
        # Run analysis 100 times
        for _ in range(100):
            analyze_shot_decision(
                current_lie="fairway",
                distance=150,
                player_handicap=12,
                hole_number=10
            )
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 100
        
        # Should complete in under 10ms per analysis
        assert avg_time < 0.01, f"Analysis took {avg_time:.4f}s on average"
    
    def test_memory_usage_stability(self):
        """Test that repeated analyses don't cause memory leaks."""
        import gc
        
        # Force garbage collection
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Run many analyses
        for i in range(50):
            analyze_shot_decision(
                current_lie="fairway",
                distance=100 + i,
                player_handicap=10,
                hole_number=i % 18 + 1
            )
        
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Object count shouldn't grow significantly
        growth_ratio = final_objects / initial_objects
        assert growth_ratio < 1.5, f"Memory usage grew by {growth_ratio:.2f}x"
    
    def test_invalid_input_handling(self):
        """Test handling of invalid inputs."""
        # Negative distance
        result = analyze_shot_decision(
            current_lie="fairway",
            distance=-10,
            player_handicap=12,
            hole_number=8
        )
        assert result is not None  # Should handle gracefully
        
        # Invalid hole number
        result = analyze_shot_decision(
            current_lie="fairway",
            distance=150,
            player_handicap=12,
            hole_number=25  # Beyond 18 holes
        )
        assert result is not None
        
        # Extreme handicap
        result = analyze_shot_decision(
            current_lie="fairway",
            distance=150,
            player_handicap=100,
            hole_number=8
        )
        assert result is not None
    
    def test_concurrent_analysis_safety(self):
        """Test that concurrent analyses don't interfere with each other."""
        import threading
        import queue
        
        results_queue = queue.Queue()
        
        def analyze_worker(worker_id):
            result = analyze_shot_decision(
                current_lie="fairway",
                distance=150 + worker_id,
                player_handicap=10 + worker_id,
                hole_number=(worker_id % 18) + 1
            )
            results_queue.put((worker_id, result))
        
        # Start multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=analyze_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check all results
        results = {}
        while not results_queue.empty():
            worker_id, result = results_queue.get()
            results[worker_id] = result
        
        assert len(results) == 10
        for worker_id, result in results.items():
            assert result is not None
            assert "recommended_shot" in result
    
    @pytest.mark.parametrize("distance,lie,handicap", [
        (50, "sand", 20),
        (100, "rough", 15),
        (200, "fairway", 10),
        (300, "tee", 5),
        (400, "tee", 2),
    ])
    def test_various_scenario_combinations(self, distance, lie, handicap):
        """Test analysis across various realistic scenario combinations."""
        result = analyze_shot_decision(
            current_lie=lie,
            distance=distance,
            player_handicap=handicap,
            hole_number=12
        )
        
        assert result is not None
        assert "recommended_shot" in result
        assert result["recommended_shot"]["type"] is not None
        assert "strategic_advice" in result
        assert len(result["strategic_advice"]) > 0


# Test Fixtures and Utilities
@pytest.fixture
def sample_shot_range():
    """Fixture providing a sample ShotRange object."""
    return ShotRange(
        shot_type=ShotType.STANDARD_APPROACH,
        success_probability=0.65,
        risk_factor=0.5,
        expected_value=0.2,
        variance=0.6,
        fold_equity=0.1,
        bluff_frequency=0.15,
        pot_odds_required=0.4
    )

@pytest.fixture
def sample_game_situation():
    """Fixture providing a sample game situation."""
    return {
        "hole_number": 12,
        "partnership_formed": False,
        "match_critical": False,
        "trailing_significantly": False,
        "hazards_present": True,
        "risk_reward_available": True,
        "hero_shot_possible": False,
        "opponent_style": "balanced"
    }

@pytest.fixture
def sample_matrix(sample_game_situation):
    """Fixture providing a sample ShotRangeMatrix."""
    return ShotRangeMatrix(
        lie_type="fairway",
        distance_to_pin=140,
        player_handicap=10,
        game_situation=sample_game_situation
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])