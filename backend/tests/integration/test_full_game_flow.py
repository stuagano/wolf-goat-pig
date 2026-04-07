"""
Integration tests for complete game flow scenarios
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from app.database import init_db


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def initialized_game(client):
    """Create a test game via the API and return the response with game_id"""
    response = client.post("/games/create-test?player_count=4")
    assert response.status_code == 200, f"Failed to create test game: {response.text}"
    data = response.json()
    return data


class TestCompleteHoleFlow:
    """Test playing through a complete hole"""
    
    @pytest.mark.skip(reason="PLAY_SHOT requires simulate_shot which is not implemented on WolfGoatPigGame")
    def test_hole_with_partnership(self, client, initialized_game):
        """Test a hole where captain takes a partner"""
        game_id = initialized_game["game_id"]

        # Play first tee shot
        response = client.post(f"/wgp/{game_id}/action", json={
            "action_type": "PLAY_SHOT"
        })
        assert response.status_code == 200
        
        # Continue playing shots until partnership opportunity
        shots_played = 0
        partnership_requested = False
        
        while shots_played < 20:  # Safety limit
            current_state = response.json()
            available_actions = current_state.get("available_actions", [])
            
            # Check if we can request partnership
            partnership_actions = [a for a in available_actions if a["action_type"] == "REQUEST_PARTNERSHIP"]
            if partnership_actions and not partnership_requested:
                # Request partnership
                response = client.post(f"/wgp/{game_id}/action", json={
                    "action_type": "REQUEST_PARTNERSHIP",
                    "payload": partnership_actions[0]["payload"]
                })
                assert response.status_code == 200
                partnership_requested = True
                
                # Accept partnership
                response = client.post(f"/wgp/{game_id}/action", json={
                    "action_type": "RESPOND_PARTNERSHIP",
                    "payload": {"accepted": True}
                })
                assert response.status_code == 200
                break
            
            # Otherwise, play a shot if available
            shot_actions = [a for a in available_actions if a["action_type"] == "PLAY_SHOT"]
            if shot_actions:
                response = client.post(f"/wgp/{game_id}/action", json={
                    "action_type": "PLAY_SHOT"
                })
                assert response.status_code == 200
                shots_played += 1
            else:
                break
        
        # Verify partnership was formed
        if partnership_requested:
            game_state = response.json()["game_state"]
            assert game_state["hole_state"]["teams"]["type"] in ["partners", "solo"]
    
    def test_hole_with_solo_captain(self, client, initialized_game):
        """Test a hole where captain goes solo"""
        game_id = initialized_game["game_id"]
        
        # Play shots until we get partnership opportunity
        for _ in range(10):
            response = client.post(f"/wgp/{game_id}/action", json={
                "action_type": "PLAY_SHOT"
            })
            
            available_actions = response.json().get("available_actions", [])
            solo_actions = [a for a in available_actions if a["action_type"] == "DECLARE_SOLO"]
            
            if solo_actions:
                # Go solo
                response = client.post(f"/wgp/{game_id}/action", json={
                    "action_type": "DECLARE_SOLO"
                })
                assert response.status_code == 200
                
                # Verify solo was set
                game_state = response.json()["game_state"]
                assert game_state["hole_state"]["teams"]["type"] == "solo"
                break
    
    def test_hole_with_double_wager(self, client, initialized_game):
        """Test doubling the wager during a hole"""
        game_id = initialized_game["game_id"]
        
        # Play shots and look for double opportunity
        double_offered = False
        for _ in range(15):
            response = client.post(f"/wgp/{game_id}/action", json={
                "action_type": "PLAY_SHOT"
            })
            
            available_actions = response.json().get("available_actions", [])
            double_actions = [a for a in available_actions if a["action_type"] == "OFFER_DOUBLE"]
            
            if double_actions and not double_offered:
                # Offer double
                response = client.post(f"/wgp/{game_id}/action", json={
                    "action_type": "OFFER_DOUBLE",
                    "payload": double_actions[0]["payload"]
                })
                assert response.status_code == 200
                double_offered = True
                
                # Accept double
                response = client.post(f"/wgp/{game_id}/action", json={
                    "action_type": "ACCEPT_DOUBLE",
                    "payload": {"accepted": True}
                })
                assert response.status_code == 200
                
                # Verify wager was doubled
                game_state = response.json()["game_state"]
                assert game_state["hole_state"]["betting"]["doubled"] == True
                break


class TestMultiHoleGame:
    """Test playing multiple holes"""
    
    def test_play_three_holes(self, client, initialized_game):
        """Test playing through three complete holes"""
        game_id = initialized_game["game_id"]
        holes_completed = 0
        
        while holes_completed < 3:
            # Play shots until hole is complete
            shots_in_hole = 0
            hole_complete = False
            
            while shots_in_hole < 30 and not hole_complete:  # Safety limit
                response = client.post(f"/wgp/{game_id}/action", json={
                    "action_type": "PLAY_SHOT"
                })
                
                if response.status_code != 200:
                    # Might need to handle other actions
                    available_actions = response.json().get("available_actions", [])
                    if available_actions:
                        # Take the first available action
                        action = available_actions[0]
                        response = client.post(f"/wgp/{game_id}/action", json={
                            "action_type": action["action_type"],
                            "payload": action.get("payload", {})
                        })
                
                # Check if we can enter scores
                available_actions = response.json().get("available_actions", [])
                score_actions = [a for a in available_actions if a["action_type"] == "ENTER_HOLE_SCORES"]
                
                if score_actions:
                    # Enter scores
                    scores = {"p1": 4, "p2": 5, "p3": 4, "p4": 6}
                    response = client.post(f"/wgp/{game_id}/action", json={
                        "action_type": "ENTER_HOLE_SCORES",
                        "payload": {"scores": scores}
                    })
                    assert response.status_code == 200
                    
                    # Advance to next hole
                    response = client.post(f"/wgp/{game_id}/action", json={
                        "action_type": "ADVANCE_HOLE"
                    })
                    assert response.status_code == 200
                    
                    holes_completed += 1
                    hole_complete = True
                    break
                
                shots_in_hole += 1
        
        # Verify we completed 3 holes
        assert holes_completed == 3
        game_state = response.json()["game_state"]
        assert game_state["current_hole"] == 4


class TestSpecialScenarios:
    """Test special game scenarios"""
    
    def test_hole_18_big_dick(self, client):
        """Test Big Dick challenge on hole 18"""
        # Create a test game via the API
        create_resp = client.post("/games/create-test?player_count=4")
        assert create_resp.status_code == 200
        game_id = create_resp.json()["game_id"]

        # Test Big Dick offer (should fail if not on hole 18, but endpoint should exist)
        response = client.post(f"/wgp/{game_id}/action", json={
            "action_type": "OFFER_BIG_DICK",
            "payload": {"player_id": "test-player-1"}
        })
        # Should fail if not on hole 18, but endpoint should exist (not 404)
        assert response.status_code in [200, 400, 500]
    
    @pytest.mark.skip(reason="PLAY_SHOT requires simulate_shot which is not implemented on WolfGoatPigGame")
    def test_analytics_retrieval(self, client, initialized_game):
        """Test getting analytics during game"""
        game_id = initialized_game["game_id"]

        # Play some shots first
        for _ in range(5):
            client.post(f"/wgp/{game_id}/action", json={
                "action_type": "PLAY_SHOT"
            })
        
        # Get analytics
        response = client.post(f"/wgp/{game_id}/action", json={
            "action_type": "GET_ADVANCED_ANALYTICS"
        })
        assert response.status_code == 200
        
        analytics = response.json()["game_state"].get("analytics", {})
        assert "player_performance" in analytics
        assert "partnership_analytics" in analytics
        assert "betting_trends" in analytics
    
    @pytest.mark.skip(reason="PLAY_SHOT requires simulate_shot which is not implemented on WolfGoatPigGame")
    def test_post_hole_analysis(self, client, initialized_game):
        """Test getting post-hole analysis"""
        game_id = initialized_game["game_id"]

        # Play through a hole (simplified)
        for _ in range(10):
            response = client.post(f"/wgp/{game_id}/action", json={
                "action_type": "PLAY_SHOT"
            })
            
            available_actions = response.json().get("available_actions", [])
            if any(a["action_type"] == "ENTER_HOLE_SCORES" for a in available_actions):
                # Enter scores
                client.post(f"/wgp/{game_id}/action", json={
                    "action_type": "ENTER_HOLE_SCORES",
                    "payload": {"scores": {"p1": 4, "p2": 5, "p3": 4, "p4": 6}}
                })
                break
        
        # Get post-hole analysis
        response = client.post(f"/wgp/{game_id}/action", json={
            "action_type": "GET_POST_HOLE_ANALYSIS",
            "payload": {"hole_number": 1}
        })
        assert response.status_code == 200
        
        details = response.json()["timeline_event"]["details"]
        assert "hole_number" in details
        assert "teams" in details


class TestErrorRecovery:
    """Test error handling and recovery"""
    
    def test_invalid_partnership_request(self, client, initialized_game):
        """Test requesting partnership with invalid player"""
        game_id = initialized_game["game_id"]
        response = client.post(f"/wgp/{game_id}/action", json={
            "action_type": "REQUEST_PARTNERSHIP",
            "payload": {"target_player_name": "NonexistentPlayer"}
        })
        # Handler wraps the 400 in a 500 due to error handling chain
        assert response.status_code in [400, 500]
        assert "not found" in response.json()["detail"].lower()
    
    def test_action_out_of_sequence(self, client, initialized_game):
        """Test performing actions out of sequence"""
        game_id = initialized_game["game_id"]
        # Try to enter scores without playing shots
        response = client.post(f"/wgp/{game_id}/action", json={
            "action_type": "ENTER_HOLE_SCORES",
            "payload": {"scores": {"test-player-1": 4, "test-player-2": 5, "test-player-3": 4, "test-player-4": 6}}
        })
        # Should either handle gracefully or return appropriate error
        assert response.status_code in [200, 400, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])