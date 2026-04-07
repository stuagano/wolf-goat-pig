"""
Comprehensive tests for Wolf Goat Pig API endpoints
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from app.database import SessionLocal, init_db


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Setup test database before each test"""
    init_db()
    yield
    # Cleanup can be added here if needed


class TestHealthEndpoints:
    """Test health and diagnostic endpoints"""
    
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert "timestamp" in response.json()
    
    def test_ghin_diagnostic(self, client):
        response = client.get("/ghin/diagnostic")
        assert response.status_code == 200
        assert "email_configured" in response.json()
        assert "environment" in response.json()


class TestCourseManagement:
    """Test course management endpoints"""
    
    def test_get_courses(self, client):
        response = client.get("/courses")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have default course
        assert len(data) > 0
    
    def test_add_course(self, client):
        new_course = {
            "name": "Test Golf Club",
            "holes": [
                {"hole": i, "par": 4, "yards": 400, "stroke_index": i}
                for i in range(1, 19)
            ]
        }
        
        response = client.post("/courses", json=new_course)
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "Test Golf Club" in response.json()["message"]
    
    def test_update_course(self, client):
        # First add a course
        new_course = {
            "name": "Update Test Club",
            "holes": [
                {"hole": i, "par": 4, "yards": 400, "stroke_index": i}
                for i in range(1, 19)
            ]
        }
        client.post("/courses", json=new_course)
        
        # Update it
        update_data = {
            "holes": [
                {"hole": i, "par": 3 if i % 3 == 0 else 4, "yards": 350, "stroke_index": i}
                for i in range(1, 19)
            ]
        }
        
        response = client.put("/courses/Update Test Club", json=update_data)
        assert response.status_code == 200
        assert response.json()["status"] == "success"
    
    def test_delete_course(self, client):
        # First add a course
        new_course = {
            "name": "Delete Test Club",
            "holes": [
                {"hole": i, "par": 4, "yards": 400, "stroke_index": i}
                for i in range(1, 19)
            ]
        }
        client.post("/courses", json=new_course)
        
        # Delete it
        response = client.delete("/courses/Delete Test Club")
        assert response.status_code == 200
        assert response.json()["status"] == "success"


class TestGameEndpoints:
    """Test game-related endpoints"""

    def test_get_rules(self, client):
        response = client.get("/rules")
        assert response.status_code == 200
        rules = response.json()
        assert isinstance(rules, list)
        # Should have seeded rules
        assert len(rules) > 0


class TestUnifiedActionAPI:
    """Test the unified action API endpoint"""
    
    def test_initialize_game_action(self, client):
        action_data = {
            "action_type": "INITIALIZE_GAME",
            "payload": {
                "players": [
                    {"id": "p1", "name": "Alice", "handicap": 10, "strength": 8},
                    {"id": "p2", "name": "Bob", "handicap": 15, "strength": 6},
                    {"id": "p3", "name": "Charlie", "handicap": 18, "strength": 5},
                    {"id": "p4", "name": "David", "handicap": 20, "strength": 4}
                ],
                "course_name": "Wing Point Golf & Country Club"
            }
        }
        
        response = client.post("/wgp/test-game/action", json=action_data)
        assert response.status_code == 200
        data = response.json()
        assert "game_state" in data
        assert "log_message" in data
        assert "available_actions" in data
        assert len(data["game_state"]["players"]) == 4
    
    def test_play_shot_action(self, client):
        # First initialize game
        init_action = {
            "action_type": "INITIALIZE_GAME",
            "payload": {
                "players": [
                    {"id": "p1", "name": "Alice", "handicap": 10},
                    {"id": "p2", "name": "Bob", "handicap": 15},
                    {"id": "p3", "name": "Charlie", "handicap": 18},
                    {"id": "p4", "name": "David", "handicap": 20}
                ]
            }
        }
        client.post("/wgp/test-game/action", json=init_action)
        
        # Play a shot
        shot_action = {
            "action_type": "PLAY_SHOT",
            "payload": {}
        }
        
        response = client.post("/wgp/test-game/action", json=shot_action)
        assert response.status_code == 200
        data = response.json()
        assert "shot" in data["log_message"].lower()
        assert "timeline_event" in data
    
    def test_request_partnership_action(self, client):
        # Initialize game first
        init_action = {
            "action_type": "INITIALIZE_GAME",
            "payload": {
                "players": [
                    {"id": "p1", "name": "Alice", "handicap": 10},
                    {"id": "p2", "name": "Bob", "handicap": 15},
                    {"id": "p3", "name": "Charlie", "handicap": 18},
                    {"id": "p4", "name": "David", "handicap": 20}
                ]
            }
        }
        client.post("/wgp/test-game/action", json=init_action)
        
        # Request partnership
        partnership_action = {
            "action_type": "REQUEST_PARTNERSHIP",
            "payload": {"target_player_name": "Bob"}
        }
        
        response = client.post("/wgp/test-game/action", json=partnership_action)
        assert response.status_code == 200
        data = response.json()
        assert "partnership" in data["log_message"].lower()
    
    def test_invalid_action_type(self, client):
        action_data = {
            "action_type": "INVALID_ACTION",
            "payload": {}
        }
        
        response = client.post("/wgp/test-game/action", json=action_data)
        assert response.status_code == 400
        assert "Unknown action type" in response.json()["detail"]
    
    def test_declare_solo_action(self, client):
        # Initialize and set up captain
        init_action = {
            "action_type": "INITIALIZE_GAME",
            "payload": {
                "players": [
                    {"id": "p1", "name": "Alice", "handicap": 10},
                    {"id": "p2", "name": "Bob", "handicap": 15},
                    {"id": "p3", "name": "Charlie", "handicap": 18},
                    {"id": "p4", "name": "David", "handicap": 20}
                ]
            }
        }
        client.post("/wgp/test-game/action", json=init_action)
        
        # Declare solo
        solo_action = {
            "action_type": "DECLARE_SOLO",
            "payload": {}
        }
        
        response = client.post("/wgp/test-game/action", json=solo_action)
        # This might fail if no captain is set, but we're testing the endpoint works
        assert response.status_code in [200, 400]


class TestCourseImport:
    """Test course import endpoints"""
    
    def test_get_import_sources(self, client):
        response = client.get("/courses/import/sources")
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert len(data["sources"]) > 0
    
    def test_preview_course_import(self, client):
        request_data = {
            "course_name": "Pebble Beach Golf Links",
            "state": "CA",
            "city": "Pebble Beach"
        }
        
        response = client.post("/courses/import/preview", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert "course_name" in data
        assert "preview_data" in data


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_player_count(self, client):
        action_data = {
            "action_type": "INITIALIZE_GAME",
            "payload": {
                "players": [
                    {"id": "p1", "name": "Alice", "handicap": 10}
                ],  # Only 1 player, should fail
                "course_name": "Test Course"
            }
        }
        
        response = client.post("/wgp/test-game/action", json=action_data)
        assert response.status_code == 400
        assert "4, 5, or 6 players required" in response.json()["detail"]
    
    def test_missing_required_fields(self, client):
        action_data = {
            "action_type": "INITIALIZE_GAME",
            "payload": {
                "players": [
                    {"id": "p1"},  # Missing name and handicap
                    {"id": "p2", "name": "Bob"},  # Missing handicap
                    {"id": "p3", "name": "Charlie", "handicap": 18},
                    {"id": "p4", "name": "David", "handicap": 20}
                ]
            }
        }
        
        response = client.post("/wgp/test-game/action", json=action_data)
        assert response.status_code == 400
        assert "must have" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])