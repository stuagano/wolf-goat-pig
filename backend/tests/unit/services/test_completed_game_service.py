from app.services.completed_game_service import build_hole_history


def test_build_hole_history_maps_indices_to_player_ids_and_sums_standings():
    players = [
        {"id": "p1", "name": "John", "player_profile_id": 1},
        {"id": "p2", "name": "Mary", "player_profile_id": None},
    ]
    per_hole = [
        {"player_index": 0, "hole": 1, "quarters": 2},
        {"player_index": 1, "hole": 1, "quarters": -2},
        {"player_index": 0, "hole": 2, "quarters": -1},
        {"player_index": 1, "hole": 2, "quarters": 1},
    ]
    hole_history, standings = build_hole_history(players, per_hole)

    assert hole_history == [
        {"hole": 1, "points_delta": {"p1": 2, "p2": -2}},
        {"hole": 2, "points_delta": {"p1": -1, "p2": 1}},
    ]
    assert standings == {"p1": 1, "p2": -1}
