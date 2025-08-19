"""
Comprehensive API Integration Test Suite

This module provides thorough testing for all API endpoints and integrations,
including request/response validation, error handling, authentication,
rate limiting, and end-to-end API workflows.

Test Coverage:
- All REST API endpoints
- WebSocket connections
- Authentication and authorization
- Request/response validation
- Error handling and status codes
- Rate limiting and throttling
- CORS handling
- File upload/download
- Database integration
- External service integration
- Performance and load testing
"""

import pytest
import json
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import websockets
import threading
import concurrent.futures

# Import the FastAPI app and dependencies
from app.main import app
from app.database import get_db
from app.models import Base, PlayerProfile, GameRecord, CourseData
from app.schemas import (
    PlayerProfileCreate, GameSetupRequest, OddsCalculationRequest,
    MonteCarloRequest, ShotAnalysisRequest
)


class TestAPIIntegration:
    """Comprehensive API integration test suite."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        # Create test database
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(self.engine)
        
        self.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Override database dependency
        def override_get_db():
            try:
                db = self.TestingSessionLocal()
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Create test client
        self.client = TestClient(app)
        
        # Test data
        self.test_course_data = {
            "id": "test_course_123",
            "name": "Test Golf Course",
            "holes": [
                {
                    "number": 1,
                    "par": 4,
                    "yardage": 380,
                    "difficulty": 3.2,
                    "hazards": ["water", "bunker"]
                },
                {
                    "number": 2,
                    "par": 3,
                    "yardage": 165,
                    "difficulty": 2.8,
                    "hazards": ["bunker"]
                }
            ]
        }
        
        self.test_player_data = {
            "name": "Test Player",
            "handicap": 12.5,
            "avatar_url": "https://example.com/avatar.jpg"
        }
    
    def teardown_method(self):
        """Clean up after each test."""
        app.dependency_overrides.clear()


class TestHealthAndStatus:
    """Test health check and status endpoints."""
    
    def setup_method(self):
        self.client = TestClient(app)
    
    def test_health_check_endpoint(self):
        """Test the health check endpoint."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert data["status"] == "healthy"
    
    def test_status_endpoint_with_details(self):
        """Test detailed status endpoint."""
        response = self.client.get("/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert "services" in data
        assert "uptime" in data
        assert "memory_usage" in data
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint for monitoring."""
        response = self.client.get("/metrics")
        
        assert response.status_code == 200
        # Metrics might be in different format (prometheus, json, etc.)
        assert response.headers.get("content-type") is not None


class TestPlayerProfileAPI(TestAPIIntegration):
    """Test player profile API endpoints."""
    
    def test_create_player_profile_success(self):
        """Test successful player profile creation."""
        response = self.client.post("/api/players", json=self.test_player_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == self.test_player_data["name"]
        assert data["handicap"] == self.test_player_data["handicap"]
        assert "id" in data
        assert "created_date" in data
    
    def test_create_player_profile_validation_error(self):
        """Test player creation with invalid data."""
        invalid_data = {
            "name": "",  # Empty name
            "handicap": -5  # Invalid handicap
        }
        
        response = self.client.post("/api/players", json=invalid_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert any("name" in str(error) for error in data["detail"])
    
    def test_get_player_profile_success(self):
        """Test retrieving existing player profile."""
        # First create a player
        create_response = self.client.post("/api/players", json=self.test_player_data)
        player_id = create_response.json()["id"]
        
        # Then retrieve it
        response = self.client.get(f"/api/players/{player_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == player_id
        assert data["name"] == self.test_player_data["name"]
    
    def test_get_player_profile_not_found(self):
        """Test retrieving non-existent player."""
        response = self.client.get("/api/players/99999")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_update_player_profile_success(self):
        """Test updating player profile."""
        # Create player
        create_response = self.client.post("/api/players", json=self.test_player_data)
        player_id = create_response.json()["id"]
        
        # Update player
        update_data = {"name": "Updated Name", "handicap": 8.5}
        response = self.client.put(f"/api/players/{player_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["handicap"] == 8.5
    
    def test_delete_player_profile_success(self):
        """Test deleting player profile."""
        # Create player
        create_response = self.client.post("/api/players", json=self.test_player_data)
        player_id = create_response.json()["id"]
        
        # Delete player
        response = self.client.delete(f"/api/players/{player_id}")
        
        assert response.status_code == 204
        
        # Verify deletion
        get_response = self.client.get(f"/api/players/{player_id}")
        assert get_response.status_code == 404
    
    def test_list_all_players(self):
        """Test listing all players."""
        # Create multiple players
        players_data = [
            {"name": "Player 1", "handicap": 10},
            {"name": "Player 2", "handicap": 15},
            {"name": "Player 3", "handicap": 20}
        ]
        
        for player_data in players_data:
            self.client.post("/api/players", json=player_data)
        
        # Get all players
        response = self.client.get("/api/players")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("name" in player for player in data)
    
    def test_player_statistics_endpoint(self):
        """Test player statistics retrieval."""
        # Create player
        create_response = self.client.post("/api/players", json=self.test_player_data)
        player_id = create_response.json()["id"]
        
        # Get statistics
        response = self.client.get(f"/api/players/{player_id}/statistics")
        
        assert response.status_code == 200
        data = response.json()
        assert "games_played" in data
        assert "total_earnings" in data
        assert "win_rate" in data


class TestGameAPI(TestAPIIntegration):
    """Test game-related API endpoints."""
    
    def test_create_game_session(self):
        """Test creating a new game session."""
        game_data = {
            "course_id": "test_course_123",
            "players": [
                {"name": "Player 1", "handicap": 12},
                {"name": "Player 2", "handicap": 15}
            ],
            "game_type": "wolf_goat_pig",
            "stakes": 2.0
        }
        
        response = self.client.post("/api/games", json=game_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "game_id" in data
        assert "status" in data
        assert data["status"] == "created"
    
    def test_get_game_status(self):
        """Test retrieving game status."""
        # Create game first
        game_data = {
            "course_id": "test_course",
            "players": [{"name": "Test Player", "handicap": 12}],
            "game_type": "wolf_goat_pig"
        }
        create_response = self.client.post("/api/games", json=game_data)
        game_id = create_response.json()["game_id"]
        
        # Get game status
        response = self.client.get(f"/api/games/{game_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["game_id"] == game_id
        assert "status" in data
        assert "players" in data
    
    def test_update_game_state(self):
        """Test updating game state."""
        # Create game
        game_data = {"course_id": "test", "players": [{"name": "Player", "handicap": 12}]}
        create_response = self.client.post("/api/games", json=game_data)
        game_id = create_response.json()["game_id"]
        
        # Update game state
        update_data = {
            "hole": 1,
            "scores": [{"player_id": "player_1", "strokes": 4}],
            "teams": "solo"
        }
        
        response = self.client.post(f"/api/games/{game_id}/update", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "updated" in data
    
    def test_complete_game(self):
        """Test completing a game."""
        # Create and update game to completion
        game_data = {"course_id": "test", "players": [{"name": "Player", "handicap": 12}]}
        create_response = self.client.post("/api/games", json=game_data)
        game_id = create_response.json()["game_id"]
        
        # Complete game
        completion_data = {
            "final_scores": [{"player_id": "player_1", "total_score": 85, "earnings": 10.5}]
        }
        
        response = self.client.post(f"/api/games/{game_id}/complete", json=completion_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"


class TestOddsCalculationAPI(TestAPIIntegration):
    """Test odds calculation API endpoints."""
    
    def test_calculate_real_time_odds(self):
        """Test real-time odds calculation."""
        odds_request = {
            "players": [
                {
                    "id": "p1",
                    "name": "Player 1",
                    "handicap": 10,
                    "distance_to_pin": 150,
                    "lie_type": "fairway"
                },
                {
                    "id": "p2", 
                    "name": "Player 2",
                    "handicap": 15,
                    "distance_to_pin": 180,
                    "lie_type": "rough"
                }
            ],
            "hole": {
                "number": 5,
                "par": 4,
                "difficulty": 3.5
            }
        }
        
        response = self.client.post("/api/odds/calculate", json=odds_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "overall_odds" in data
        assert "betting_scenarios" in data
        assert "confidence" in data
        assert "calculation_time_ms" in data
    
    def test_odds_calculation_validation_error(self):
        """Test odds calculation with invalid input."""
        invalid_request = {
            "players": [],  # Empty players list
            "hole": {"number": 0, "par": -1}  # Invalid hole data
        }
        
        response = self.client.post("/api/odds/calculate", json=invalid_request)
        
        assert response.status_code == 422
    
    def test_odds_calculation_performance(self):
        """Test that odds calculation completes within reasonable time."""
        odds_request = {
            "players": [
                {"id": f"p{i}", "name": f"Player {i}", "handicap": 10 + i, 
                 "distance_to_pin": 150 + i*10, "lie_type": "fairway"}
                for i in range(6)  # Maximum players
            ],
            "hole": {"number": 1, "par": 4, "difficulty": 3.0}
        }
        
        start_time = time.time()
        response = self.client.post("/api/odds/calculate", json=odds_request)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Should complete in under 2 seconds
        
        data = response.json()
        assert data["calculation_time_ms"] < 1000  # Server-side timing


class TestMonteCarloAPI(TestAPIIntegration):
    """Test Monte Carlo simulation API endpoints."""
    
    def test_monte_carlo_simulation(self):
        """Test Monte Carlo simulation endpoint."""
        simulation_request = {
            "players": [
                {"name": "Player 1", "handicap": 12, "position": {"distance": 150, "lie": "fairway"}},
                {"name": "Player 2", "handicap": 18, "position": {"distance": 170, "lie": "rough"}}
            ],
            "hole": {"par": 4, "difficulty": 3.2},
            "iterations": 1000,
            "scenarios": ["current", "double_stakes", "go_solo"]
        }
        
        response = self.client.post("/api/simulation/monte-carlo", json=simulation_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "scenarios" in data
        assert "statistics" in data
        assert len(data["scenarios"]) == 3
    
    def test_monte_carlo_performance(self):
        """Test Monte Carlo simulation performance."""
        high_iteration_request = {
            "players": [{"name": "Player", "handicap": 15}],
            "hole": {"par": 4, "difficulty": 3.0},
            "iterations": 10000  # High iteration count
        }
        
        start_time = time.time()
        response = self.client.post("/api/simulation/monte-carlo", json=high_iteration_request)
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 10.0  # Should complete within 10 seconds
    
    def test_monte_carlo_parameter_validation(self):
        """Test parameter validation for Monte Carlo simulation."""
        invalid_requests = [
            {"iterations": 0},  # Invalid iteration count
            {"players": []},    # No players
            {"iterations": 1000000}  # Too many iterations
        ]
        
        for invalid_request in invalid_requests:
            response = self.client.post("/api/simulation/monte-carlo", json=invalid_request)
            assert response.status_code == 422


class TestShotAnalysisAPI(TestAPIIntegration):
    """Test shot analysis API endpoints."""
    
    def test_shot_analysis_calculation(self):
        """Test shot analysis endpoint."""
        analysis_request = {
            "current_lie": "fairway",
            "distance": 150,
            "player_handicap": 12,
            "hole_number": 8,
            "game_situation": {
                "team_situation": "partnership",
                "score_differential": 2,
                "opponents": ["aggressive", "conservative"]
            }
        }
        
        response = self.client.post("/api/analysis/shot", json=analysis_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "recommended_shot" in data
        assert "all_ranges" in data
        assert "strategic_advice" in data
        assert "player_style" in data
    
    def test_shot_analysis_edge_cases(self):
        """Test shot analysis with edge case inputs."""
        edge_cases = [
            {"distance": 0, "player_handicap": 0},  # Minimum values
            {"distance": 500, "player_handicap": 36},  # Maximum values
            {"current_lie": "water", "distance": 250}  # Unusual lie
        ]
        
        for case in edge_cases:
            analysis_request = {
                "current_lie": case.get("current_lie", "fairway"),
                "distance": case["distance"],
                "player_handicap": case["player_handicap"],
                "hole_number": 1
            }
            
            response = self.client.post("/api/analysis/shot", json=analysis_request)
            assert response.status_code == 200
    
    def test_shot_visualization_data(self):
        """Test shot visualization data endpoint."""
        viz_request = {
            "shot_analysis": {
                "recommended_shot": {"type": "standard_approach", "success_rate": "65%"},
                "all_ranges": [{"type": "safe_approach", "ev": "+0.1"}]
            }
        }
        
        response = self.client.post("/api/analysis/shot/visualization", json=viz_request)
        
        assert response.status_code == 200
        data = response.json()
        assert "chart_data" in data
        assert "visual_indicators" in data


class TestCourseAPI(TestAPIIntegration):
    """Test course management API endpoints."""
    
    def test_get_available_courses(self):
        """Test retrieving available courses."""
        response = self.client.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_course_details(self):
        """Test retrieving specific course details."""
        # Assume we have a test course
        response = self.client.get("/api/courses/test_course_id")
        
        # Should return course data or 404
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "name" in data
            assert "holes" in data
    
    def test_course_import_validation(self):
        """Test course data import validation."""
        invalid_course_data = {
            "name": "",  # Empty name
            "holes": []  # No holes
        }
        
        response = self.client.post("/api/courses/import", json=invalid_course_data)
        
        assert response.status_code == 422


class TestAuthenticationAPI:
    """Test authentication and authorization."""
    
    def setup_method(self):
        self.client = TestClient(app)
    
    @pytest.mark.skipif(True, reason="Auth not implemented yet")
    def test_login_endpoint(self):
        """Test user login."""
        login_data = {
            "username": "testuser",
            "password": "testpass"
        }
        
        response = self.client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
    
    @pytest.mark.skipif(True, reason="Auth not implemented yet")  
    def test_protected_endpoint_without_auth(self):
        """Test accessing protected endpoint without authentication."""
        response = self.client.get("/api/protected-resource")
        
        assert response.status_code == 401
    
    @pytest.mark.skipif(True, reason="Auth not implemented yet")
    def test_protected_endpoint_with_auth(self):
        """Test accessing protected endpoint with authentication."""
        # Login first
        login_data = {"username": "testuser", "password": "testpass"}
        login_response = self.client.post("/api/auth/login", json=login_data)
        token = login_response.json()["access_token"]
        
        # Access protected resource
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.get("/api/protected-resource", headers=headers)
        
        assert response.status_code == 200


class TestWebSocketAPI:
    """Test WebSocket connections and real-time features."""
    
    def setup_method(self):
        self.client = TestClient(app)
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(True, reason="WebSocket not fully implemented")
    async def test_websocket_connection(self):
        """Test WebSocket connection establishment."""
        with self.client.websocket_connect("/ws/game/123") as websocket:
            # Send test message
            await websocket.send_json({"type": "ping"})
            
            # Receive response
            response = await websocket.receive_json()
            assert response["type"] == "pong"
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(True, reason="WebSocket not fully implemented")
    async def test_real_time_game_updates(self):
        """Test real-time game state updates via WebSocket."""
        with self.client.websocket_connect("/ws/game/123") as websocket:
            # Send game update
            update = {
                "type": "game_update",
                "hole": 5,
                "player_scores": [{"id": "p1", "strokes": 4}]
            }
            await websocket.send_json(update)
            
            # Should receive confirmation
            response = await websocket.receive_json()
            assert response["type"] == "update_confirmed"


class TestErrorHandling(TestAPIIntegration):
    """Test API error handling and edge cases."""
    
    def test_invalid_json_request(self):
        """Test handling of invalid JSON in request."""
        response = self.client.post(
            "/api/players",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        incomplete_data = {"name": "Test"}  # Missing required handicap
        
        response = self.client.post("/api/players", json=incomplete_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_database_connection_error(self):
        """Test handling of database connection errors."""
        with patch('app.database.get_db') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            response = self.client.get("/api/players")
            
            assert response.status_code == 500
    
    def test_external_service_timeout(self):
        """Test handling of external service timeouts."""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = asyncio.TimeoutError()
            
            # Endpoint that calls external service
            response = self.client.post("/api/odds/calculate", json={
                "players": [{"name": "Test", "handicap": 12}],
                "hole": {"par": 4}
            })
            
            # Should handle timeout gracefully
            assert response.status_code in [500, 503, 408]
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        # Make many rapid requests
        responses = []
        for i in range(100):
            response = self.client.get("/health")
            responses.append(response.status_code)
        
        # Should eventually hit rate limit (if implemented)
        # For now, just ensure server doesn't crash
        assert all(status in [200, 429] for status in responses)
    
    def test_large_payload_handling(self):
        """Test handling of large request payloads."""
        large_payload = {
            "players": [
                {"name": f"Player {i}", "handicap": 12, "data": "x" * 1000}
                for i in range(100)
            ]
        }
        
        response = self.client.post("/api/odds/calculate", json=large_payload)
        
        # Should either process or reject gracefully
        assert response.status_code in [200, 413, 422]


class TestCORSAndSecurity(TestAPIIntegration):
    """Test CORS and security headers."""
    
    def test_cors_headers(self):
        """Test that CORS headers are set correctly."""
        response = self.client.options("/api/players")
        
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
    
    def test_security_headers(self):
        """Test security headers in responses."""
        response = self.client.get("/health")
        
        # Common security headers
        security_headers = [
            "x-frame-options",
            "x-content-type-options", 
            "x-xss-protection"
        ]
        
        # At least some security headers should be present
        present_headers = sum(1 for header in security_headers 
                            if header in response.headers)
        assert present_headers > 0
    
    def test_content_type_validation(self):
        """Test content type validation."""
        # Send non-JSON content to JSON endpoint
        response = self.client.post(
            "/api/players",
            data="not json",
            headers={"Content-Type": "text/plain"}
        )
        
        assert response.status_code in [400, 415, 422]


class TestAPIPerformance:
    """Test API performance characteristics."""
    
    def setup_method(self):
        self.client = TestClient(app)
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        def make_request():
            return self.client.get("/health")
        
        # Make 20 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        assert all(response.status_code == 200 for response in responses)
    
    def test_response_time_consistency(self):
        """Test that response times are consistent."""
        times = []
        
        for _ in range(10):
            start_time = time.time()
            response = self.client.get("/health")
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
        
        # Calculate response time statistics
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Response times should be reasonable and consistent
        assert avg_time < 0.1  # Average under 100ms
        assert max_time < 0.5  # No response over 500ms
    
    def test_memory_usage_stability(self):
        """Test that repeated requests don't cause memory leaks."""
        import gc
        import sys
        
        # Force garbage collection
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Make many requests
        for _ in range(100):
            response = self.client.get("/health")
            assert response.status_code == 200
        
        # Force garbage collection again
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Object count shouldn't grow significantly
        growth_ratio = final_objects / initial_objects
        assert growth_ratio < 1.5  # Less than 50% growth


class TestAPIDocumentation:
    """Test API documentation and schema endpoints."""
    
    def setup_method(self):
        self.client = TestClient(app)
    
    def test_openapi_schema_accessible(self):
        """Test that OpenAPI schema is accessible."""
        response = self.client.get("/openapi.json")
        
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
        assert "components" in schema
    
    def test_swagger_ui_accessible(self):
        """Test that Swagger UI is accessible."""
        response = self.client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_redoc_accessible(self):
        """Test that ReDoc documentation is accessible."""
        response = self.client.get("/redoc")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_api_endpoints_documented(self):
        """Test that all API endpoints are documented in schema."""
        response = self.client.get("/openapi.json")
        schema = response.json()
        
        # Check that main endpoints are documented
        paths = schema["paths"]
        expected_paths = [
            "/health",
            "/api/players",
            "/api/games",
            "/api/odds/calculate"
        ]
        
        documented_paths = set(paths.keys())
        for expected_path in expected_paths:
            # Check if path or similar pattern exists
            assert any(expected_path in path for path in documented_paths)


class TestDataValidation:
    """Test comprehensive data validation across API endpoints."""
    
    def setup_method(self):
        self.client = TestClient(app)
    
    def test_input_sanitization(self):
        """Test that inputs are properly sanitized."""
        malicious_inputs = [
            {"name": "<script>alert('xss')</script>", "handicap": 12},
            {"name": "'; DROP TABLE players; --", "handicap": 15},
            {"name": "test\x00null", "handicap": 20}
        ]
        
        for malicious_input in malicious_inputs:
            response = self.client.post("/api/players", json=malicious_input)
            
            # Should either sanitize or reject
            if response.status_code == 201:
                data = response.json()
                # Name should be sanitized
                assert "<script>" not in data["name"]
                assert "DROP TABLE" not in data["name"]
                assert "\x00" not in data["name"]
            else:
                # Or should be rejected with validation error
                assert response.status_code == 422
    
    def test_numeric_range_validation(self):
        """Test validation of numeric ranges."""
        test_cases = [
            {"handicap": -10, "expected_status": 422},  # Negative handicap
            {"handicap": 100, "expected_status": 422},  # Too high handicap
            {"handicap": 0, "expected_status": 201},    # Valid minimum
            {"handicap": 36, "expected_status": 201}    # Valid maximum
        ]
        
        for case in test_cases:
            player_data = {"name": "Test Player", "handicap": case["handicap"]}
            response = self.client.post("/api/players", json=player_data)
            
            assert response.status_code == case["expected_status"]
    
    def test_string_length_validation(self):
        """Test validation of string lengths."""
        test_cases = [
            {"name": "", "expected_status": 422},  # Empty name
            {"name": "x" * 256, "expected_status": 422},  # Too long name
            {"name": "Valid Name", "expected_status": 201}  # Valid name
        ]
        
        for case in test_cases:
            player_data = {"name": case["name"], "handicap": 12}
            response = self.client.post("/api/players", json=player_data)
            
            assert response.status_code == case["expected_status"]


if __name__ == "__main__":
    # Run specific test classes or all tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--disable-warnings",
        # Add coverage reporting
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])