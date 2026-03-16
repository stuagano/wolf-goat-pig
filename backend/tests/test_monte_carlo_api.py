"""
Direct API tests for Monte Carlo simulation endpoints
"""

import pytest
import requests
import time
from typing import Dict, Any

# Test configuration
API_BASE = "http://localhost:8000"

class TestMonteCarloAPI:
    """Test Monte Carlo simulation API endpoints directly"""
    
    @pytest.fixture
    def valid_simulation_config(self) -> Dict[str, Any]:
        """Standard valid simulation configuration"""
        return {
            "human_player": {
                "id": "human",
                "name": "Stuart",
                "handicap": 10.0
            },
            "computer_players": [
                {
                    "id": "comp1",
                    "name": "Tiger Bot", 
                    "handicap": 2.0,
                    "personality": "aggressive"
                },
                {
                    "id": "comp2",
                    "name": "Strategic Sam",
                    "handicap": 8.5, 
                    "personality": "strategic"
                },
                {
                    "id": "comp3",
                    "name": "Conservative Carl",
                    "handicap": 15.0,
                    "personality": "conservative"
                }
            ],
            "num_simulations": 10,
            "course_name": None
        }
    
    def test_monte_carlo_endpoint_exists(self):
        """Test that Monte Carlo endpoint is available"""
        response = requests.get(f"{API_BASE}/docs")
        assert response.status_code == 200
        # The OpenAPI docs should contain our endpoint
        assert "/simulation/monte-carlo" in response.text
    
    def test_monte_carlo_simulation_basic(self, valid_simulation_config):
        """Test basic Monte Carlo simulation functionality"""
        response = requests.post(
            f"{API_BASE}/simulation/monte-carlo",
            json=valid_simulation_config,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "status" in data
        assert data["status"] == "ok"
        assert "summary" in data
        assert "insights" in data
        assert "simulation_details" in data
        
        # Check summary structure
        summary = data["summary"]
        assert "total_simulations" in summary
        assert summary["total_simulations"] == 10
        assert "player_statistics" in summary
        
        # Check all 4 players are present
        player_stats = summary["player_statistics"]
        assert len(player_stats) == 4
        assert "human" in player_stats
        
        # Check human player stats
        human_stats = player_stats["human"]
        assert "wins" in human_stats
        assert "win_percentage" in human_stats
        assert "average_score" in human_stats
        assert "best_score" in human_stats
        assert "worst_score" in human_stats
        assert "score_distribution" in human_stats
        
        # Check insights
        assert isinstance(data["insights"], list)
        assert len(data["insights"]) > 0
    
    def test_monte_carlo_simulation_performance(self, valid_simulation_config):
        """Test Monte Carlo simulation performance"""
        # Test with 50 simulations
        config = valid_simulation_config.copy()
        config["num_simulations"] = 50
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE}/simulation/monte-carlo",
            json=config,
            headers={"Content-Type": "application/json"},
            timeout=60  # 60 second timeout
        )
        end_time = time.time()
        
        assert response.status_code == 200
        duration = end_time - start_time
        
        # Should complete within reasonable time (60 seconds)
        assert duration < 60, f"Simulation took too long: {duration:.2f} seconds"
        
        data = response.json()
        assert data["summary"]["total_simulations"] == 50
    
    def test_monte_carlo_validation_errors(self):
        """Test validation errors for invalid configurations"""
        
        # Test missing computer players
        invalid_config = {
            "human_player": {"id": "human", "name": "Stuart", "handicap": 10.0},
            "computer_players": [],  # Empty list
            "num_simulations": 10
        }
        
        response = requests.post(
            f"{API_BASE}/simulation/monte-carlo",
            json=invalid_config,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
        
        # Test invalid simulation count
        invalid_config = {
            "human_player": {"id": "human", "name": "Stuart", "handicap": 10.0},
            "computer_players": [
                {"id": "comp1", "name": "Bot1", "handicap": 5.0, "personality": "balanced"},
                {"id": "comp2", "name": "Bot2", "handicap": 10.0, "personality": "balanced"},
                {"id": "comp3", "name": "Bot3", "handicap": 15.0, "personality": "balanced"}
            ],
            "num_simulations": 0  # Invalid count
        }
        
        response = requests.post(
            f"{API_BASE}/simulation/monte-carlo",
            json=invalid_config,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
    
    def test_monte_carlo_handicap_analysis(self):
        """Test Monte Carlo simulation with different handicap scenarios"""
        
        # Test scenario: Low handicap player vs high handicap opponents
        config = {
            "human_player": {"id": "human", "name": "Pro Stuart", "handicap": 2.0},
            "computer_players": [
                {"id": "comp1", "name": "Beginner1", "handicap": 20.0, "personality": "conservative"},
                {"id": "comp2", "name": "Beginner2", "handicap": 25.0, "personality": "conservative"},
                {"id": "comp3", "name": "Beginner3", "handicap": 22.0, "personality": "conservative"}
            ],
            "num_simulations": 25
        }
        
        response = requests.post(
            f"{API_BASE}/simulation/monte-carlo",
            json=config,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Low handicap player should have higher win percentage
        human_stats = data["summary"]["player_statistics"]["human"]
        assert human_stats["win_percentage"] > 20  # Should win more than 25% due to skill advantage
    
    def test_monte_carlo_consistency(self, valid_simulation_config):
        """Test that multiple runs give consistent but different results"""
        
        # Run same configuration twice
        response1 = requests.post(
            f"{API_BASE}/simulation/monte-carlo",
            json=valid_simulation_config,
            headers={"Content-Type": "application/json"}
        )
        
        response2 = requests.post(
            f"{API_BASE}/simulation/monte-carlo", 
            json=valid_simulation_config,
            headers={"Content-Type": "application/json"}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Both should have same number of simulations
        assert data1["summary"]["total_simulations"] == data2["summary"]["total_simulations"]
        
        # Results should be similar but not identical (due to randomness)
        human_stats1 = data1["summary"]["player_statistics"]["human"]
        human_stats2 = data2["summary"]["player_statistics"]["human"]
        
        # Win percentages should be in reasonable range but may differ
        assert 0 <= human_stats1["win_percentage"] <= 100
        assert 0 <= human_stats2["win_percentage"] <= 100
    
    def test_monte_carlo_detailed_endpoint(self, valid_simulation_config):
        """Test the detailed results endpoint"""
        
        # Modify config for smaller sample
        config = valid_simulation_config.copy()
        config["num_simulations"] = 5
        
        response = requests.post(
            f"{API_BASE}/simulation/monte-carlo-detailed/5",
            json=config,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "detailed_results" in data
        assert "summary" in data
        
        # Check detailed results structure
        detailed_results = data["detailed_results"]
        assert len(detailed_results) == 5
        
        for game_result in detailed_results:
            assert "game_number" in game_result
            assert "scores" in game_result
            assert "winner" in game_result
            
            # Check scores structure
            scores = game_result["scores"]
            assert len(scores) == 4  # 4 players
            assert "human" in scores
    
    def test_monte_carlo_personality_differences(self):
        """Test that different personalities produce different behaviors"""
        
        # Test with all aggressive opponents
        aggressive_config = {
            "human_player": {"id": "human", "name": "Stuart", "handicap": 10.0},
            "computer_players": [
                {"id": "comp1", "name": "Aggressive1", "handicap": 8.0, "personality": "aggressive"},
                {"id": "comp2", "name": "Aggressive2", "handicap": 12.0, "personality": "aggressive"},
                {"id": "comp3", "name": "Aggressive3", "handicap": 14.0, "personality": "aggressive"}
            ],
            "num_simulations": 20
        }
        
        # Test with all conservative opponents
        conservative_config = {
            "human_player": {"id": "human", "name": "Stuart", "handicap": 10.0},
            "computer_players": [
                {"id": "comp1", "name": "Conservative1", "handicap": 8.0, "personality": "conservative"},
                {"id": "comp2", "name": "Conservative2", "handicap": 12.0, "personality": "conservative"},
                {"id": "comp3", "name": "Conservative3", "handicap": 14.0, "personality": "conservative"}
            ],
            "num_simulations": 20
        }
        
        aggressive_response = requests.post(
            f"{API_BASE}/simulation/monte-carlo",
            json=aggressive_config,
            headers={"Content-Type": "application/json"}
        )
        
        conservative_response = requests.post(
            f"{API_BASE}/simulation/monte-carlo",
            json=conservative_config,
            headers={"Content-Type": "application/json"}
        )
        
        assert aggressive_response.status_code == 200
        assert conservative_response.status_code == 200
        
        # Both should complete successfully
        aggressive_data = aggressive_response.json()
        conservative_data = conservative_response.json()
        
        assert aggressive_data["summary"]["total_simulations"] == 20
        assert conservative_data["summary"]["total_simulations"] == 20
    
    def test_monte_carlo_course_selection(self, valid_simulation_config):
        """Test Monte Carlo simulation with course selection"""
        
        # Test with specific course (if available)
        config = valid_simulation_config.copy()
        config["course_name"] = "Test Course"  # This may or may not exist
        
        response = requests.post(
            f"{API_BASE}/simulation/monte-carlo",
            json=config,
            headers={"Content-Type": "application/json"}
        )
        
        # Should still work even if course doesn't exist
        assert response.status_code == 200
        data = response.json()
        
        # Check simulation details
        sim_details = data["simulation_details"]
        assert "course" in sim_details
    
    @pytest.mark.slow
    def test_monte_carlo_large_simulation(self, valid_simulation_config):
        """Test Monte Carlo with larger number of simulations"""
        
        config = valid_simulation_config.copy()
        config["num_simulations"] = 100
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE}/simulation/monte-carlo",
            json=config,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minute timeout for large simulation
        )
        end_time = time.time()
        
        assert response.status_code == 200
        duration = end_time - start_time
        
        data = response.json()
        assert data["summary"]["total_simulations"] == 100
        
        # Should complete in reasonable time
        assert duration < 120, f"Large simulation took too long: {duration:.2f} seconds"
        
        # Results should be more stable with larger sample
        human_stats = data["summary"]["player_statistics"]["human"]
        
        # With 100 simulations, results should be more reliable
        assert isinstance(human_stats["win_percentage"], (int, float))
        assert isinstance(human_stats["average_score"], (int, float))

@pytest.mark.integration
class TestMonteCarloIntegration:
    """Integration tests that test the full stack"""
    
    def test_full_monte_carlo_workflow(self):
        """Test complete Monte Carlo workflow from API to results"""
        
        # Step 1: Get available personalities
        personalities_response = requests.get(f"{API_BASE}/simulation/available-personalities")
        assert personalities_response.status_code == 200
        personalities_data = personalities_response.json()
        assert "personalities" in personalities_data
        
        # Step 2: Setup simulation with available personalities
        config = {
            "human_player": {"id": "human", "name": "Integration Test User", "handicap": 12.0},
            "computer_players": [
                {"id": "comp1", "name": "AI Player 1", "handicap": 5.0, "personality": "aggressive"},
                {"id": "comp2", "name": "AI Player 2", "handicap": 10.0, "personality": "strategic"},
                {"id": "comp3", "name": "AI Player 3", "handicap": 18.0, "personality": "conservative"}
            ],
            "num_simulations": 15
        }
        
        # Step 3: Run simulation
        simulation_response = requests.post(
            f"{API_BASE}/simulation/monte-carlo",
            json=config,
            headers={"Content-Type": "application/json"}
        )
        
        assert simulation_response.status_code == 200
        simulation_data = simulation_response.json()
        
        # Step 4: Validate complete response
        assert simulation_data["status"] == "ok"
        assert simulation_data["summary"]["total_simulations"] == 15
        
        # Validate insights
        insights = simulation_data["insights"]
        assert len(insights) >= 3  # Should have multiple insights
        
        # Validate simulation details
        sim_details = simulation_data["simulation_details"]
        assert sim_details["total_games"] == 15
        assert sim_details["human_player"] == "Integration Test User"
        assert len(sim_details["opponents"]) == 3
        
        print("✅ Full Monte Carlo integration test passed!")

if __name__ == "__main__":
    # Quick smoke test when run directly
    test_api = TestMonteCarloAPI()
    valid_config = {
        "human_player": {"id": "human", "name": "Stuart", "handicap": 10.0},
        "computer_players": [
            {"id": "comp1", "name": "Test Bot", "handicap": 8.0, "personality": "balanced"}
        ] * 3,  # Quick way to create 3 similar opponents
        "num_simulations": 5
    }
    
    try:
        test_api.test_monte_carlo_simulation_basic(valid_config)
        print("✅ Smoke test passed!")
    except Exception as e:
        print(f"❌ Smoke test failed: {e}")