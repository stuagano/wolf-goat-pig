"""Test Vinnie's Variation for 4-player games"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_vinnies_variation_doubles_holes_13_to_16():
    """Test Vinnie's Variation doubles base wager on holes 13-16"""
    # Create test game
    game_response = client.post("/games/create-test?player_count=4")
    assert game_response.status_code == 200
    game_id = game_response.json()["game_id"]

    # Hole 13: Should have Vinnie's Variation (2x base)
    wager_13 = client.get(f"/games/{game_id}/next-hole-wager?current_hole=13")
    assert wager_13.status_code == 200
    data = wager_13.json()
    assert data["base_wager"] == 2  # 1Q × 2 (assuming base_wager=1)
    assert data["vinnies_variation"] is True

    # Hole 14
    wager_14 = client.get(f"/games/{game_id}/next-hole-wager?current_hole=14")
    assert wager_14.status_code == 200
    assert wager_14.json()["base_wager"] == 2
    assert wager_14.json()["vinnies_variation"] is True

    # Hole 15
    wager_15 = client.get(f"/games/{game_id}/next-hole-wager?current_hole=15")
    assert wager_15.status_code == 200
    assert wager_15.json()["base_wager"] == 2
    assert wager_15.json()["vinnies_variation"] is True

    # Hole 16
    wager_16 = client.get(f"/games/{game_id}/next-hole-wager?current_hole=16")
    assert wager_16.status_code == 200
    assert wager_16.json()["base_wager"] == 2
    assert wager_16.json()["vinnies_variation"] is True

    # Hole 17: Hoepfinger starts, no more Vinnie's Variation
    wager_17 = client.get(f"/games/{game_id}/next-hole-wager?current_hole=17")
    assert wager_17.status_code == 200
    assert wager_17.json()["base_wager"] == 1  # Back to normal
    assert wager_17.json().get("vinnies_variation", False) is False


def test_vinnies_variation_only_for_4_players():
    """Test Vinnie's Variation only applies to 4-player games"""
    # 5-player game
    game_response = client.post("/games/create-test?player_count=5")
    assert game_response.status_code == 200
    game_id = game_response.json()["game_id"]

    # Hole 13 in 5-player should NOT have Vinnie's Variation
    wager_13 = client.get(f"/games/{game_id}/next-hole-wager?current_hole=13")
    assert wager_13.status_code == 200
    assert wager_13.json()["base_wager"] == 1
    assert wager_13.json().get("vinnies_variation", False) is False


def test_vinnies_variation_not_on_hole_12():
    """Test Vinnie's Variation does not apply on hole 12"""
    # Create test game
    game_response = client.post("/games/create-test?player_count=4")
    assert game_response.status_code == 200
    game_id = game_response.json()["game_id"]

    # Hole 12: Should NOT have Vinnie's Variation
    wager_12 = client.get(f"/games/{game_id}/next-hole-wager?current_hole=12")
    assert wager_12.status_code == 200
    assert wager_12.json()["base_wager"] == 1
    assert wager_12.json().get("vinnies_variation", False) is False
