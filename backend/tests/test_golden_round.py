"""
Test Golden Round - Validates scoring system against known golden round

This test loads the golden round and verifies that the scoring system
produces the same results as the expected values.
"""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def load_golden_round() -> dict:
    """Load the golden round JSON file."""
    script_dir = Path(__file__).parent
    golden_round_path = script_dir / 'fixtures' / 'golden_round.json'
    with open(golden_round_path, 'r') as f:
        return json.load(f)


def test_golden_round_quarters_balance():
    """Test that golden round quarters balance to zero on each hole."""
    round_data = load_golden_round()
    
    for hole in round_data['holes']:
        quarters = hole.get('quarters', {})
        total = sum(quarters.values())
        assert abs(total) < 0.01, (
            f"Hole {hole['hole_number']}: Quarters sum to {total}, expected 0. "
            f"Quarters: {quarters}"
        )


def test_golden_round_final_totals_sum_to_zero():
    """Test that final totals in golden round sum to zero."""
    round_data = load_golden_round()
    expected_final = round_data.get('expected_final_totals', {})
    
    total_sum = sum(expected_final.values())
    assert abs(total_sum) < 0.01, (
        f"Final totals sum to {total_sum}, expected 0. "
        f"Totals: {expected_final}"
    )


def test_golden_round_running_totals():
    """Test that running totals are calculated correctly."""
    round_data = load_golden_round()
    holes = round_data.get('holes', [])
    player_ids = [p['id'] for p in round_data.get('game_metadata', {}).get('players', [])]
    
    running_totals = {pid: 0 for pid in player_ids}
    
    for hole in holes:
        quarters = hole.get('quarters', {})
        expected_totals = hole.get('running_totals', {})
        
        # Calculate running totals from quarters
        for pid in player_ids:
            running_totals[pid] += quarters.get(pid, 0)
        
        # Compare with expected
        for pid in player_ids:
            expected = expected_totals.get(pid, 0)
            actual = running_totals[pid]
            assert expected == actual, (
                f"Hole {hole['hole_number']}: Running total mismatch for {pid}. "
                f"Expected {expected}, got {actual}. "
                f"Quarters: {quarters}"
            )


def test_golden_round_can_be_loaded():
    """Test that golden round file can be loaded and has required structure."""
    round_data = load_golden_round()
    
    assert 'game_metadata' in round_data
    assert 'holes' in round_data
    assert 'expected_final_totals' in round_data
    
    metadata = round_data['game_metadata']
    assert 'players' in metadata
    assert len(metadata['players']) == 4
    
    holes = round_data['holes']
    assert len(holes) == 18
    
    # Verify all holes are numbered 1-18
    hole_numbers = [h.get('hole_number') for h in holes]
    assert set(hole_numbers) == set(range(1, 19))


@pytest.mark.integration
def test_golden_round_through_scoring_system():
    """
    Integration test: Run golden round through actual scoring system.
    
    This test creates a game and submits each hole from the golden round,
    verifying that the scoring system produces the expected results.
    """
    round_data = load_golden_round()
    metadata = round_data['game_metadata']
    holes = round_data['holes']
    
    # Create a test game
    game_response = client.post("/games/create-test?player_count=4")
    assert game_response.status_code == 200
    game_id = game_response.json()["game_id"]
    players = game_response.json()["players"]
    
    # Map golden round player IDs to actual game player IDs
    # We'll use the order from the game response
    player_map = {}
    for i, golden_player in enumerate(metadata['players']):
        player_map[golden_player['id']] = players[i]['id']
    
    # Track running totals
    running_totals = {pid: 0 for pid in player_map.values()}
    
    # Submit each hole
    for hole_data in holes:
        hole_num = hole_data['hole_number']
        
        # Map teams
        teams_data = hole_data['teams']
        if teams_data['type'] == 'partners':
            team1 = [player_map[pid] for pid in teams_data['team1']]
            team2 = [player_map[pid] for pid in teams_data['team2']]
            teams = {"type": "partners", "team1": team1, "team2": team2}
        else:  # solo
            captain = player_map[teams_data['captain']]
            opponents = [player_map[pid] for pid in teams_data['opponents']]
            teams = {"type": "solo", "captain": captain, "opponents": opponents}
        
        # Map scores
        scores = {player_map[pid]: score for pid, score in hole_data['scores'].items()}
        
        # Determine winner
        if hole_data.get('halved'):
            winner = "push"
        elif teams_data['type'] == 'solo':
            winner = "captain" if hole_data['winner'] == 'captain' else "opponents"
        else:
            winner = "team1" if hole_data['winner'] == 'team1' else "team2"
        
        # Build request payload
        request_payload = {
            "hole_number": hole_num,
            "rotation_order": [player_map[pid] for pid in hole_data['rotation_order']],
            "captain_index": 0,  # First in rotation is captain
            "teams": teams,
            "final_wager": hole_data['wager'],
            "winner": winner,
            "scores": scores,
            "hole_par": hole_data['par'],
            "duncan_invoked": hole_data.get('duncan_invoked', False),
        }

        # Add phase if specified (for Hoepfinger)
        if 'phase' in hole_data:
            request_payload['phase'] = hole_data['phase']

        # Add Joe's Special wager if specified (for Hoepfinger)
        if hole_data.get('joes_special', {}).get('invoked'):
            request_payload['joes_special_wager'] = hole_data['joes_special']['chosen_value']

        # Submit hole
        response = client.post(f"/games/{game_id}/holes/complete", json=request_payload)
        
        assert response.status_code == 200, (
            f"Hole {hole_num} failed: {response.text}"
        )
        
        # Verify quarters match expected
        result = response.json()["hole_result"]
        points_delta = result["points_delta"]
        
        # Map expected quarters to actual player IDs
        expected_quarters = hole_data['quarters']
        for golden_pid, expected_q in expected_quarters.items():
            actual_pid = player_map[golden_pid]
            actual_q = points_delta.get(actual_pid, 0)
            assert expected_q == actual_q, (
                f"Hole {hole_num}, Player {golden_pid}: "
                f"Expected {expected_q} quarters, got {actual_q}"
            )
        
        # Update running totals
        for pid in running_totals:
            running_totals[pid] += points_delta.get(pid, 0)
    
    # Verify final totals
    expected_final = round_data['expected_final_totals']
    for golden_pid, expected_total in expected_final.items():
        actual_pid = player_map[golden_pid]
        actual_total = running_totals[actual_pid]
        assert expected_total == actual_total, (
            f"Final total mismatch for {golden_pid}: "
            f"Expected {expected_total}, got {actual_total}"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
