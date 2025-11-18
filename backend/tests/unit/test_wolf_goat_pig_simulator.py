"""
Tests for WolfGoatPigSimulator

Verifies that the simulator class:
1. Inherits all game functionality from WolfGoatPigGame
2. Provides simulation-specific methods
3. Can run Monte Carlo simulations
4. Can generate simulated shots
"""

import pytest
from backend.app.wolf_goat_pig_simulator import WolfGoatPigSimulator
from backend.app.wolf_goat_pig import Player


class TestWolfGoatPigSimulator:
    """Test suite for WolfGoatPigSimulator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.players = [
            Player(id="p1", name="Player 1", handicap=10.0),
            Player(id="p2", name="Player 2", handicap=15.0),
            Player(id="p3", name="Player 3", handicap=20.0),
            Player(id="p4", name="Player 4", handicap=5.0)
        ]
        self.simulator = WolfGoatPigSimulator(
            player_count=4,
            players=self.players
        )
    
    def test_simulator_inherits_from_game(self):
        """Test that simulator is an instance of WolfGoatPigGame."""
        from backend.app.wolf_goat_pig import WolfGoatPigGame
        assert isinstance(self.simulator, WolfGoatPigGame)
    
    def test_simulator_has_game_functionality(self):
        """Test that simulator has all game engine methods."""
        # Check for core game methods
        assert hasattr(self.simulator, 'enter_hole_scores')
        assert hasattr(self.simulator, 'get_game_state')
        assert hasattr(self.simulator, 'players')
        assert len(self.simulator.players) == 4
    
    def test_simulator_has_simulation_methods(self):
        """Test that simulator has simulation-specific methods."""
        assert hasattr(self.simulator, 'run_monte_carlo_simulation')
        assert hasattr(self.simulator, 'simulate_shot')
        assert hasattr(self.simulator, '_simulate_player_shot')
    
    def test_simulate_shot_returns_result(self):
        """Test that simulate_shot returns a valid shot result."""
        result = self.simulator.simulate_shot(
            player_id="p1",
            lie_type="fairway",
            distance_to_pin=150.0
        )
        
        assert result is not None
        assert result.player_id == "p1"
        assert result.shot_quality in ["excellent", "good", "average", "poor", "terrible"]
        assert result.distance_to_pin >= 0
        assert isinstance(result.made_shot, bool)
    
    def test_simulate_shot_quality_varies_by_handicap(self):
        """Test that shot quality is influenced by handicap."""
        # Run multiple shots for low and high handicap players
        low_handicap_qualities = []
        high_handicap_qualities = []
        
        quality_scores = {
            "excellent": 5,
            "good": 4,
            "average": 3,
            "poor": 2,
            "terrible": 1
        }
        
        for _ in range(50):
            low_shot = self.simulator.simulate_shot(
                player_id="p4",  # handicap 5.0
                lie_type="fairway",
                distance_to_pin=150.0
            )
            high_shot = self.simulator.simulate_shot(
                player_id="p3",  # handicap 20.0
                lie_type="fairway",
                distance_to_pin=150.0
            )
            
            low_handicap_qualities.append(quality_scores[low_shot.shot_quality])
            high_handicap_qualities.append(quality_scores[high_shot.shot_quality])
        
        # Low handicap should have better average quality
        avg_low = sum(low_handicap_qualities) / len(low_handicap_qualities)
        avg_high = sum(high_handicap_qualities) / len(high_handicap_qualities)
        
        assert avg_low > avg_high, "Low handicap player should have better shot quality"
    
    def test_monte_carlo_simulation_runs(self):
        """Test that Monte Carlo simulation executes without errors."""
        results = self.simulator.run_monte_carlo_simulation(iterations=10)
        
        assert results is not None
        assert "iterations" in results
        assert results["iterations"] == 10
        assert "win_probabilities" in results
        assert "expected_values" in results
        assert "outcomes" in results
        assert len(results["outcomes"]) == 10
    
    def test_monte_carlo_preserves_game_state(self):
        """Test that Monte Carlo simulation doesn't alter game state."""
        # Set some game state
        self.simulator.players[0].points = 10
        self.simulator.current_hole = 5
        
        # Run simulation
        self.simulator.run_monte_carlo_simulation(iterations=5)
        
        # Verify state is preserved
        assert self.simulator.players[0].points == 10
        assert self.simulator.current_hole == 5
    
    def test_short_game_simulation(self):
        """Test simulation of short game shots."""
        # Test very short putt
        result = self.simulator.simulate_shot(
            player_id="p1",
            lie_type="green",
            distance_to_pin=2.0
        )
        
        # Should either hole out or be very close
        assert result.distance_to_pin <= 3.0 or result.made_shot
    
    def test_tee_shot_simulation(self):
        """Test simulation of tee shots."""
        result = self.simulator.simulate_shot(
            player_id="p1",
            lie_type="tee",
            distance_to_pin=400.0
        )
        
        # Tee shot should advance significantly
        assert result.distance_to_pin < 400.0
        assert result.distance_to_pin >= 0
    
    def test_lie_type_determination(self):
        """Test that lie types are determined appropriately."""
        # Excellent shots should usually result in good lies
        excellent_lies = []
        for _ in range(20):
            lie = self.simulator._determine_lie_type("excellent", 200.0)
            excellent_lies.append(lie)
        
        # Most should be fairway or green
        good_lies = [l for l in excellent_lies if l in ["fairway", "green"]]
        assert len(good_lies) > len(excellent_lies) * 0.7
        
        # Terrible shots should usually result in bad lies
        terrible_lies = []
        for _ in range(20):
            lie = self.simulator._determine_lie_type("terrible", 200.0)
            terrible_lies.append(lie)
        
        # Most should be rough or sand
        bad_lies = [l for l in terrible_lies if l in ["rough", "sand"]]
        assert len(bad_lies) > len(terrible_lies) * 0.7


class TestSimulatorIntegration:
    """Integration tests for simulator with game engine."""
    
    def test_can_use_as_game_engine(self):
        """Test that simulator can be used exactly like game engine."""
        players = [
            Player(id=f"p{i}", name=f"Player {i}", handicap=10.0)
            for i in range(1, 5)
        ]
        
        sim = WolfGoatPigSimulator(player_count=4, players=players)
        
        # Should be able to use all game methods
        state = sim.get_game_state()
        
        assert state is not None
        assert "current_hole" in state
    
    def test_simulation_and_game_tracking_together(self):
        """Test using both simulation and game tracking features."""
        players = [
            Player(id=f"p{i}", name=f"Player {i}", handicap=10.0)
            for i in range(1, 5)
        ]
        
        sim = WolfGoatPigSimulator(player_count=4, players=players)
        
        # Use simulation
        shot = sim.simulate_shot(player_id="p1", distance_to_pin=150.0)
        
        # Both should work
        assert sim.current_hole == 1
        assert shot is not None
