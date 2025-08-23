"""
Integration tests for simulation endpoints and flow.
Tests the complete simulation lifecycle including setup, gameplay, and completion.
"""

import pytest
import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestSimulationIntegration:
    """Test simulation endpoints integration"""
    
    def test_simulation_setup_success(self):
        """Test successful simulation setup"""
        payload = {
            "human_player": {
                "id": "human",
                "name": "Test Player",
                "handicap": 18
            },
            "computer_players": [
                {"id": "comp1", "name": "AI Player 1", "handicap": 12},
                {"id": "comp2", "name": "AI Player 2", "handicap": 15},
                {"id": "comp3", "name": "AI Player 3", "handicap": 10}
            ],
            "course_name": "Test Course"
        }
        
        response = client.post("/simulation/setup", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert "game_state" in data
        assert len(data["players"]) == 4
        assert data["current_hole"] == 1

    def test_simulation_setup_invalid_players(self):
        """Test simulation setup with invalid player count"""
        payload = {
            "human_player": {"id": "human", "name": "Test Player", "handicap": 18},
            "computer_players": [
                {"id": "comp1", "name": "AI Player 1", "handicap": 12}
            ]  # Only 2 total players (invalid)
        }
        
        response = client.post("/simulation/setup", json=payload)
        assert response.status_code == 400
        assert "At least 4 players required" in response.json()["detail"]

    def test_play_next_shot_without_setup(self):
        """Test play next shot without simulation setup"""
        response = client.post("/simulation/play-next-shot", json={})
        assert response.status_code == 400
        assert "Simulation not initialized" in response.json()["detail"]

    def test_simulation_full_flow(self):
        """Test complete simulation flow"""
        # Setup simulation
        setup_payload = {
            "human_player": {
                "id": "human",
                "name": "Test Player", 
                "handicap": 18
            },
            "computer_players": [
                {"id": "comp1", "name": "AI Player 1", "handicap": 12},
                {"id": "comp2", "name": "AI Player 2", "handicap": 15},
                {"id": "comp3", "name": "AI Player 3", "handicap": 10}
            ]
        }
        
        setup_response = client.post("/simulation/setup", json=setup_payload)
        assert setup_response.status_code == 200
        
        # Play first shot
        shot_response = client.post("/simulation/play-next-shot", json={})
        assert shot_response.status_code == 200
        
        shot_data = shot_response.json()
        assert shot_data["success"] == True
        assert "shot_result" in shot_data
        assert "game_state" in shot_data
        
        # Verify game state progression
        game_state = shot_data["game_state"]
        assert game_state["current_hole"] == 1
        assert game_state["hole_state"]["current_shot_number"] == 2

    def test_simulation_error_handling(self):
        """Test simulation error handling"""
        # Test malformed JSON
        response = client.post(
            "/simulation/setup",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_simulation_legacy_format_compatibility(self):
        """Test that simulation still works with legacy API format"""
        payload = {
            "players": [
                {"id": "human", "name": "Test Player", "handicap": 18},
                {"id": "comp1", "name": "AI Player 1", "handicap": 12},
                {"id": "comp2", "name": "AI Player 2", "handicap": 15}, 
                {"id": "comp3", "name": "AI Player 3", "handicap": 10}
            ],
            "course_name": "Test Course"
        }
        
        response = client.post("/simulation/setup", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert len(data["players"]) == 4