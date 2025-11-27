"""
Simple API tests that work with the current implementation
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import after path setup
from app.main import app


class TestBasicEndpoints:
    """Test basic API endpoints"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
    
    def test_get_rules(self):
        """Test getting game rules"""
        with TestClient(app) as client:
            response = client.get("/rules")
            assert response.status_code == 200
            rules = response.json()
            assert isinstance(rules, list)
    
    def test_get_courses(self):
        """Test getting available courses"""
        with TestClient(app) as client:
            response = client.get("/courses")
            assert response.status_code == 200
            courses = response.json()
            assert isinstance(courses, list)
            # Should have at least the default course
            assert len(courses) > 0
    
    def test_ghin_diagnostic(self):
        """Test GHIN diagnostic endpoint"""
        with TestClient(app) as client:
            response = client.get("/ghin/diagnostic")
            assert response.status_code == 200
            data = response.json()
            assert "email_configured" in data
            assert "password_configured" in data
            assert "environment" in data


class TestActionAPI:
    """Test the unified action API"""
    
    def test_initialize_game(self):
        """Test initializing a game"""
        with TestClient(app) as client:
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
    
    def test_invalid_player_count(self):
        """Test that invalid player count is rejected"""
        with TestClient(app) as client:
            action_data = {
                "action_type": "INITIALIZE_GAME",
                "payload": {
                    "players": [
                        {"id": "p1", "name": "Alice", "handicap": 10, "strength": 8}
                    ],
                    "course_name": "Wing Point Golf & Country Club"
                }
            }
            
            response = client.post("/wgp/test-game/action", json=action_data)
            assert response.status_code == 400
            assert "4, 5, or 6 players required" in response.json()["detail"]
    
    def test_play_shot_after_init(self):
        """Test playing a shot after game initialization"""
        with TestClient(app) as client:
            # First initialize the game
            init_data = {
                "action_type": "INITIALIZE_GAME",
                "payload": {
                    "players": [
                        {"id": "p1", "name": "Alice", "handicap": 10, "strength": 8},
                        {"id": "p2", "name": "Bob", "handicap": 15, "strength": 6},
                        {"id": "p3", "name": "Charlie", "handicap": 18, "strength": 5},
                        {"id": "p4", "name": "David", "handicap": 20, "strength": 4}
                    ]
                }
            }
            
            init_response = client.post("/wgp/test-game/action", json=init_data)
            assert init_response.status_code == 200
            
            # Then play a shot
            shot_data = {
                "action_type": "PLAY_SHOT",
                "payload": {}
            }
            
            shot_response = client.post("/wgp/test-game/action", json=shot_data)
            assert shot_response.status_code == 200
            data = shot_response.json()
            assert "game_state" in data
            assert "timeline_event" in data


class TestCourseEndpoints:
    """Test course management endpoints"""
    
    def test_add_new_course(self):
        """Test adding a new course"""
        with TestClient(app) as client:
            course_data = {
                "name": "Test Golf Course",
                "holes": [
                    {"hole": i, "par": 4, "yards": 400, "stroke_index": i}
                    for i in range(1, 19)
                ]
            }
            
            response = client.post("/courses", json=course_data)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "Test Golf Course" in data["message"]
    
    def test_get_import_sources(self):
        """Test getting course import sources"""
        with TestClient(app) as client:
            response = client.get("/courses/import/sources")
            assert response.status_code == 200
            data = response.json()
            assert "sources" in data
            assert len(data["sources"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])