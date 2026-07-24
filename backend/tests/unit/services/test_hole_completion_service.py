"""CTK-grade contracts for hole completion scoring math."""

import pytest
from fastapi import HTTPException

from app.schemas.games import CompleteHoleRequest, HoleTeams
from app.services.hole_completion_service import (
    apply_multipliers,
    calculate_points_delta,
    process_complete_hole,
    validate_big_dick,
)


def _partners_request(*, hole_number=3, winner="team1", wager=2.0, big_dick=None):
    return CompleteHoleRequest(
        hole_number=hole_number,
        rotation_order=["p1", "p2", "p3", "p4"],
        captain_index=0,
        phase="normal",
        teams=HoleTeams(type="partners", team1=["p1", "p2"], team2=["p3", "p4"]),
        final_wager=wager,
        winner=winner,
        scores={"p1": 4, "p2": 5, "p3": 5, "p4": 6},
        big_dick_invoked_by=big_dick,
    )


def _game_state():
    return {
        "players": [
            {"id": "p1", "name": "A", "total_points": 0, "points": 0},
            {"id": "p2", "name": "B", "total_points": 0, "points": 0},
            {"id": "p3", "name": "C", "total_points": 0, "points": 0},
            {"id": "p4", "name": "D", "total_points": 0, "points": 0},
        ],
        "hole_history": [],
        "current_hole": 3,
    }


def test_process_complete_hole_partners_win_is_zero_sum_and_advances():
    request = _partners_request()
    game_state = _game_state()

    hole_result, updated = process_complete_hole(request, game_state)

    points_delta = hole_result["points_delta"]
    assert abs(sum(points_delta.values())) < 0.01
    assert points_delta["p1"] == 2
    assert points_delta["p2"] == 2
    assert points_delta["p3"] == -2
    assert points_delta["p4"] == -2
    assert len(updated["hole_history"]) == 1
    assert updated["current_hole"] == 4


def test_validate_big_dick_rejects_non_18():
    request = _partners_request(hole_number=17, big_dick="p1")
    with pytest.raises(HTTPException) as exc:
        validate_big_dick(request)
    assert exc.value.status_code == 400
    assert "hole 18" in str(exc.value.detail)


def test_apply_multipliers_doubles_points_on_holes_17_and_18():
    request = _partners_request(hole_number=17)
    game_state = _game_state()
    points = calculate_points_delta(request, game_state)
    doubled = apply_multipliers(dict(points), request, 17)
    assert doubled["p1"] == points["p1"] * 2
    assert doubled["p3"] == points["p3"] * 2
    assert abs(sum(doubled.values())) < 0.01
