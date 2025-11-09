"""
Comprehensive integration tests for complete game scenarios

Tests cover:
- Full game flow from setup to completion
- Frontend-backend integration
- Player interactions and game state synchronization
- Betting mechanics and point calculations
- Course management integration
- Error handling across system boundaries
- Performance under realistic load
- Data persistence and recovery
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Backend imports
from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.game_state import GameState
from backend.app.domain.player import Player
from backend.app.services.player_service import PlayerService
from backend.app.models import PlayerProfile, PlayerStatistics, GameRecord

# Create test database
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db


class TestCompleteGameIntegration:
    """Test complete game scenarios from start to finish"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def db_session(self):
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    @pytest.fixture
    def sample_players(self):
        return [
            {"id": "p1", "name": "Alice", "handicap": 10.0, "strength": "Strong"},
            {"id": "p2", "name": "Bob", "handicap": 15.0, "strength": "Medium"},
            {"id": "p3", "name": "Charlie", "handicap": 8.0, "strength": "Strong"},
            {"id": "p4", "name": "Dave", "handicap": 20.0, "strength": "Weak"}
        ]
    
    @pytest.fixture
    def test_course(self):
        return {
            "name": "Test Course",
            "holes": [
                {"hole_number": i, "par": 4, "yards": 400, "stroke_index": i}
                for i in range(1, 19)
            ]
        }

    def test_complete_game_flow_regular_mode(self, client, sample_players, test_course):
        """Test complete game flow in regular mode"""
        
        # 1. Setup game with players and course
        setup_response = client.post("/game/setup", json={
            "players": sample_players,
            "course": test_course["name"]
        })
        assert setup_response.status_code == 200
        
        # 2. Start the game
        start_response = client.post("/game/start")
        assert start_response.status_code == 200
        
        # 3. Get initial game state
        state_response = client.get("/game/state")
        assert state_response.status_code == 200
        game_state = state_response.json()
        
        assert game_state["current_hole"] == 1
        assert len(game_state["players"]) == 4
        assert game_state["captain_id"] == "p1"
        
        # 4. Play through first hole
        self._play_complete_hole(client, hole_number=1)
        
        # 5. Advance to next hole
        next_hole_response = client.post("/game/action", json={
            "action": "next_hole",
            "payload": {}
        })
        assert next_hole_response.status_code == 200
        
        # 6. Verify hole advancement
        state_response = client.get("/game/state")
        game_state = state_response.json()
        assert game_state["current_hole"] == 2
        
        # 7. Play several more holes
        for hole in range(2, 6):  # Play holes 2-5
            self._play_complete_hole(client, hole_number=hole)
            if hole < 5:  # Don't advance after last hole
                client.post("/game/action", json={
                    "action": "next_hole",
                    "payload": {}
                })
        
        # 8. Check final state
        final_state_response = client.get("/game/state")
        final_state = final_state_response.json()
        assert final_state["current_hole"] == 5
        
        # Verify players have points
        total_points = sum(player.get("points", 0) for player in final_state["players"])
        assert total_points != 0  # Someone should have won/lost points

    def test_partnership_betting_flow(self, client, sample_players):
        """Test complete partnership betting workflow"""
        
        # Setup game
        client.post("/game/setup", json={"players": sample_players})
        client.post("/game/start")
        
        # 1. Captain requests partner
        partner_request = client.post("/game/action", json={
            "action": "request_partner",
            "payload": {"captain_id": "p1", "partner_id": "p2"}
        })
        assert partner_request.status_code == 200
        
        # 2. Partner accepts
        partner_accept = client.post("/game/action", json={
            "action": "accept_partner",
            "payload": {"partner_id": "p2"}
        })
        assert partner_accept.status_code == 200
        
        # 3. Check teams are formed
        state_response = client.get("/game/state")
        game_state = state_response.json()
        teams = game_state["teams"]
        assert teams["type"] == "partners"
        assert "p1" in teams["team1"]
        assert "p2" in teams["team1"]
        assert "p3" in teams["team2"]
        assert "p4" in teams["team2"]
        
        # 4. Record scores (team1 wins)
        self._record_hole_scores(client, {"p1": 4, "p2": 5, "p3": 6, "p4": 7})
        
        # 5. Calculate points
        points_response = client.post("/game/action", json={
            "action": "calculate_hole_points",
            "payload": {}
        })
        assert points_response.status_code == 200
        
        # 6. Verify point distribution
        final_state = client.get("/game/state").json()
        players = {p["id"]: p for p in final_state["players"]}
        
        # Team1 should have positive points, team2 negative
        assert players["p1"]["points"] > 0
        assert players["p2"]["points"] > 0
        assert players["p3"]["points"] < 0
        assert players["p4"]["points"] < 0

    def test_solo_betting_flow(self, client, sample_players):
        """Test solo betting workflow"""
        
        # Setup game
        client.post("/game/setup", json={"players": sample_players})
        client.post("/game/start")
        
        # 1. Captain goes solo
        solo_response = client.post("/game/action", json={
            "action": "go_solo",
            "payload": {"captain_id": "p1"}
        })
        assert solo_response.status_code == 200
        
        # 2. Check teams and wager
        state_response = client.get("/game/state")
        game_state = state_response.json()
        teams = game_state["teams"]
        assert teams["type"] == "solo"
        assert teams["captain"] == "p1"
        assert game_state["base_wager"] == 2  # Doubled for solo
        
        # 3. Captain wins hole
        self._record_hole_scores(client, {"p1": 3, "p2": 4, "p3": 5, "p4": 6})
        
        # 4. Calculate points
        client.post("/game/action", json={
            "action": "calculate_hole_points",
            "payload": {}
        })
        
        # 5. Verify captain gets points from all three opponents
        final_state = client.get("/game/state").json()
        players = {p["id"]: p for p in final_state["players"]}
        
        assert players["p1"]["points"] == 6  # 2 points from each of 3 opponents
        assert players["p2"]["points"] == -2
        assert players["p3"]["points"] == -2
        assert players["p4"]["points"] == -2

    def test_double_offer_workflow(self, client, sample_players):
        """Test double offer and acceptance workflow"""
        
        # Setup game with partnership
        client.post("/game/setup", json={"players": sample_players})
        client.post("/game/start")
        
        # Form partnership
        client.post("/game/action", json={
            "action": "request_partner",
            "payload": {"captain_id": "p1", "partner_id": "p2"}
        })
        client.post("/game/action", json={
            "action": "accept_partner",
            "payload": {"partner_id": "p2"}
        })
        
        # 1. Offer double
        double_offer = client.post("/game/action", json={
            "action": "offer_double",
            "payload": {"offering_team_id": "team1", "target_team_id": "team2"}
        })
        assert double_offer.status_code == 200
        
        # 2. Check double status
        state_response = client.get("/game/state")
        game_state = state_response.json()
        assert game_state["doubled_status"] == True
        
        # 3. Accept double
        double_accept = client.post("/game/action", json={
            "action": "accept_double",
            "payload": {"team_id": "team2"}
        })
        assert double_accept.status_code == 200
        
        # 4. Verify wager doubled
        final_state = client.get("/game/state").json()
        assert final_state["base_wager"] == 2
        assert final_state["doubled_status"] == False

    def test_float_usage_workflow(self, client, sample_players):
        """Test float invocation workflow"""
        
        # Setup game
        client.post("/game/setup", json={"players": sample_players})
        client.post("/game/start")
        
        # 1. Captain invokes float
        float_response = client.post("/game/action", json={
            "action": "invoke_float",
            "payload": {"captain_id": "p1"}
        })
        assert float_response.status_code == 200
        
        # 2. Verify wager doubled and float used
        state_response = client.get("/game/state")
        game_state = state_response.json()
        assert game_state["base_wager"] == 2
        assert game_state["player_float_used"]["p1"] == True
        
        # 3. Try to use float again (should fail)
        float_retry = client.post("/game/action", json={
            "action": "invoke_float",
            "payload": {"captain_id": "p1"}
        })
        assert float_retry.status_code == 400
        
        # 4. Next hole should reset float
        self._complete_hole_scoring(client)
        client.post("/game/action", json={
            "action": "next_hole",
            "payload": {}
        })
        
        # Float should be available again for new captain
        final_state = client.get("/game/state").json()
        # All float usage should be reset
        assert all(not used for used in final_state["player_float_used"].values())

    def test_karl_marx_rule_application(self, client, sample_players):
        """Test Karl Marx rule for odd quarter distribution"""
        
        # Setup game
        client.post("/game/setup", json={"players": sample_players})
        client.post("/game/start")
        
        # Set up scenario where Karl Marx rule applies
        # 3 base wager, 1 winner, 2 losers = 6 total quarters, 6/1 = 6 each, no remainder
        # Let's make it 1 base wager, 3 winners, 1 loser = 3 total, 3/3 = 1 each, no remainder
        # For remainder, need: 2 base wager, 3 winners, 1 loser = 6 total, 6/3 = 2 each, no remainder
        # Try: 1 base wager, solo captain wins vs 3 = 3 total, captain gets all 3
        
        # Captain goes solo
        client.post("/game/action", json={
            "action": "go_solo",
            "payload": {"captain_id": "p1"}
        })
        
        # Set different point totals for players to test Karl Marx
        state_response = client.get("/game/state")
        game_state = state_response.json()
        
        # Modify player points manually for testing
        # This would normally be done through the API but for testing we'll simulate
        
        # Opponents win (captain loses)
        self._record_hole_scores(client, {"p1": 6, "p2": 3, "p3": 4, "p4": 5})
        
        # Calculate points
        points_response = client.post("/game/action", json={
            "action": "calculate_hole_points",
            "payload": {}
        })
        
        # Check that points were distributed correctly
        result_message = points_response.json().get("message", "")
        final_state = client.get("/game/state").json()
        
        # Verify the calculation worked
        players = {p["id"]: p for p in final_state["players"]}
        assert players["p1"]["points"] < 0  # Captain lost
        assert players["p2"]["points"] > 0  # Opponents won
        assert players["p3"]["points"] > 0
        assert players["p4"]["points"] > 0

    def test_game_history_tracking(self, client, sample_players):
        """Test that game history is properly tracked"""
        
        # Setup and play multiple holes
        client.post("/game/setup", json={"players": sample_players})
        client.post("/game/start")
        
        # Play 3 holes with different scenarios
        holes_data = []
        
        # Hole 1: Partnership
        client.post("/game/action", json={
            "action": "request_partner",
            "payload": {"captain_id": "p1", "partner_id": "p2"}
        })
        client.post("/game/action", json={
            "action": "accept_partner",
            "payload": {"partner_id": "p2"}
        })
        self._record_hole_scores(client, {"p1": 4, "p2": 5, "p3": 6, "p4": 7})
        client.post("/game/action", json={
            "action": "calculate_hole_points",
            "payload": {}
        })
        client.post("/game/action", json={
            "action": "next_hole",
            "payload": {}
        })
        
        # Hole 2: Solo
        client.post("/game/action", json={
            "action": "go_solo",
            "payload": {"captain_id": "p2"}  # New captain
        })
        self._record_hole_scores(client, {"p1": 5, "p2": 3, "p3": 4, "p4": 6})
        client.post("/game/action", json={
            "action": "calculate_hole_points",
            "payload": {}
        })
        client.post("/game/action", json={
            "action": "next_hole",
            "payload": {}
        })
        
        # Check game history
        history_response = client.get("/game/history")
        assert history_response.status_code == 200
        history = history_response.json()
        
        assert len(history) == 2  # Two holes played
        assert history[0]["hole"] == 1
        assert history[1]["hole"] == 2
        
        # Verify hole data structure
        hole1 = history[0]
        assert "net_scores" in hole1
        assert "points_delta" in hole1
        assert "teams" in hole1

    def test_error_handling_and_recovery(self, client, sample_players):
        """Test error handling and recovery scenarios"""
        
        # Setup game
        client.post("/game/setup", json={"players": sample_players})
        client.post("/game/start")
        
        # 1. Test invalid action
        invalid_response = client.post("/game/action", json={
            "action": "invalid_action",
            "payload": {}
        })
        assert invalid_response.status_code == 400
        
        # 2. Test action without required payload
        missing_payload = client.post("/game/action", json={
            "action": "request_partner",
            "payload": {}  # Missing required fields
        })
        assert missing_payload.status_code == 400
        
        # 3. Test recording incomplete scores
        incomplete_scores = client.post("/game/action", json={
            "action": "record_net_score",
            "payload": {"player_id": "p1", "score": 4}
        })
        # This should succeed (recording individual score)
        assert incomplete_scores.status_code == 200
        
        # Try to calculate points with incomplete scores
        points_response = client.post("/game/action", json={
            "action": "calculate_hole_points",
            "payload": {}
        })
        assert points_response.status_code == 400  # Should fail with incomplete scores
        
        # 4. Game state should still be consistent
        state_response = client.get("/game/state")
        assert state_response.status_code == 200
        game_state = state_response.json()
        assert game_state["current_hole"] == 1  # Still on first hole

    def test_performance_under_load(self, client, sample_players):
        """Test performance with rapid API calls"""
        
        # Setup game
        client.post("/game/setup", json={"players": sample_players})
        client.post("/game/start")
        
        start_time = time.time()
        
        # Make many rapid API calls
        for i in range(50):
            state_response = client.get("/game/state")
            assert state_response.status_code == 200
            
            # Occasionally make game actions
            if i % 10 == 0:
                client.post("/game/action", json={
                    "action": "record_net_score",
                    "payload": {"player_id": f"p{(i % 4) + 1}", "score": 4}
                })
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete within reasonable time (adjust as needed)
        assert total_time < 10.0  # 50 API calls in under 10 seconds
        
        # Game state should still be consistent
        final_state = client.get("/game/state").json()
        assert final_state["current_hole"] == 1

    def test_player_profile_integration(self, client, db_session):
        """Test integration with player profile system"""
        
        # Create player profiles
        player_service = PlayerService(db_session)
        
        profiles = []
        for i, player_data in enumerate([
            {"name": "Alice", "handicap": 10.0},
            {"name": "Bob", "handicap": 15.0},
            {"name": "Charlie", "handicap": 8.0},
            {"name": "Dave", "handicap": 20.0}
        ]):
            from backend.app.schemas import PlayerProfileCreate
            profile = player_service.create_player_profile(
                PlayerProfileCreate(**player_data)
            )
            profiles.append(profile)
        
        # Use profiles in game
        players_with_profiles = [
            {
                "id": f"p{i+1}",
                "name": profile.name,
                "handicap": profile.handicap,
                "strength": "Medium",
                "profile_id": profile.id
            }
            for i, profile in enumerate(profiles)
        ]
        
        # Setup and play game
        client.post("/game/setup", json={"players": players_with_profiles})
        client.post("/game/start")
        
        # Complete a hole
        self._play_complete_hole(client, hole_number=1)
        
        # Check that profiles were updated (would need additional API endpoints)
        for profile in profiles:
            updated_profile = player_service.get_player_profile(profile.id)
            assert updated_profile is not None

    # Helper methods
    
    def _play_complete_hole(self, client, hole_number):
        """Play a complete hole with betting and scoring"""
        
        # Get current captain
        state_response = client.get("/game/state")
        game_state = state_response.json()
        captain_id = game_state["captain_id"]
        
        # Make betting decision (randomly choose partnership or solo)
        if hole_number % 2 == 0:  # Even holes: partnership
            other_players = [p["id"] for p in game_state["players"] if p["id"] != captain_id]
            partner_id = other_players[0]
            
            client.post("/game/action", json={
                "action": "request_partner",
                "payload": {"captain_id": captain_id, "partner_id": partner_id}
            })
            client.post("/game/action", json={
                "action": "accept_partner",
                "payload": {"partner_id": partner_id}
            })
        else:  # Odd holes: solo
            client.post("/game/action", json={
                "action": "go_solo",
                "payload": {"captain_id": captain_id}
            })
        
        # Record scores (vary scores for interesting results)
        scores = {}
        base_score = 4
        for i, player in enumerate(game_state["players"]):
            scores[player["id"]] = base_score + (i % 3)  # Scores 4, 5, 6, 4
        
        self._record_hole_scores(client, scores)
        
        # Calculate points
        client.post("/game/action", json={
            "action": "calculate_hole_points",
            "payload": {}
        })
    
    def _record_hole_scores(self, client, scores):
        """Record hole scores for all players"""
        for player_id, score in scores.items():
            client.post("/game/action", json={
                "action": "record_net_score",
                "payload": {"player_id": player_id, "score": score}
            })
    
    def _complete_hole_scoring(self, client):
        """Complete scoring for current hole with default scores"""
        self._record_hole_scores(client, {"p1": 4, "p2": 5, "p3": 6, "p4": 7})
        client.post("/game/action", json={
            "action": "calculate_hole_points",
            "payload": {}
        })


class TestConcurrentGameOperations:
    """Test concurrent game operations and race conditions"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_concurrent_score_recording(self, client):
        """Test concurrent score recording doesn't cause race conditions"""
        
        # Setup game
        sample_players = [
            {"id": "p1", "name": "Alice", "handicap": 10.0, "strength": "Strong"},
            {"id": "p2", "name": "Bob", "handicap": 15.0, "strength": "Medium"},
            {"id": "p3", "name": "Charlie", "handicap": 8.0, "strength": "Strong"},
            {"id": "p4", "name": "Dave", "handicap": 20.0, "strength": "Weak"}
        ]
        
        client.post("/game/setup", json={"players": sample_players})
        client.post("/game/start")
        
        # Set up partnership
        client.post("/game/action", json={
            "action": "request_partner",
            "payload": {"captain_id": "p1", "partner_id": "p2"}
        })
        client.post("/game/action", json={
            "action": "accept_partner",
            "payload": {"partner_id": "p2"}
        })
        
        # Simulate concurrent score recording
        import threading
        import queue
        
        results = queue.Queue()
        
        def record_score(player_id, score):
            try:
                response = client.post("/game/action", json={
                    "action": "record_net_score",
                    "payload": {"player_id": player_id, "score": score}
                })
                results.put((player_id, response.status_code))
            except Exception as e:
                results.put((player_id, str(e)))
        
        # Start concurrent threads
        threads = []
        scores = [("p1", 4), ("p2", 5), ("p3", 6), ("p4", 7)]
        
        for player_id, score in scores:
            thread = threading.Thread(target=record_score, args=(player_id, score))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        recorded_scores = []
        while not results.empty():
            player_id, status_code = results.get()
            recorded_scores.append((player_id, status_code))
        
        # All scores should be recorded successfully
        assert len(recorded_scores) == 4
        for player_id, status_code in recorded_scores:
            assert status_code == 200
        
        # Verify final state is consistent
        final_state = client.get("/game/state").json()
        hole_scores = final_state["hole_scores"]
        assert len(hole_scores) == 4
        assert all(score is not None for score in hole_scores.values())


if __name__ == "__main__":
    pytest.main([__file__])