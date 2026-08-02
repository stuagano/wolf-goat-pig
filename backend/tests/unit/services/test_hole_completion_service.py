"""CTK-grade contracts for hole completion scoring math."""

import pytest
from fastapi import HTTPException

from app.schemas.games import CompleteHoleRequest, HoleTeams
from app.services.hole_completion_service import (
    apply_multipliers,
    calculate_points_delta,
    process_complete_hole,
    validate_aardvark,
    validate_big_dick,
    validate_float,
)


def _partners_request(*, hole_number=3, winner="team1", wager=2.0, big_dick=None, float_by=None):
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
        float_invoked_by=float_by,
    )


def _solo_request(*, winner="captain", wager=2.0, duncan=False, tunkarri=False):
    return CompleteHoleRequest(
        hole_number=5,
        rotation_order=["p1", "p2", "p3", "p4"],
        captain_index=0,
        phase="normal",
        teams=HoleTeams(type="solo", captain="p1", opponents=["p2", "p3", "p4"]),
        final_wager=wager,
        winner=winner,
        scores={"p1": 4, "p2": 5, "p3": 5, "p4": 5},
        duncan_invoked=duncan,
        tunkarri_invoked=tunkarri,
    )


def _five_man_partners(*, tossed=False, ping_ponged=False, requested="team1", wager=1.0):
    return CompleteHoleRequest(
        hole_number=3,
        rotation_order=["p1", "p2", "p3", "p4", "p5"],
        captain_index=0,
        phase="normal",
        teams=HoleTeams(type="partners", team1=["p1", "p2", "p5"], team2=["p3", "p4"]),
        final_wager=wager,
        winner="team1",
        scores={"p1": 4, "p2": 5, "p3": 5, "p4": 6, "p5": 4},
        aardvark_requested_team=requested,
        aardvark_tossed=tossed,
        aardvark_ping_ponged=ping_ponged,
    )


def _game_state(*, float_used_p1=0, players=None):
    if players is None:
        players = [
            {"id": "p1", "name": "A", "total_points": 0, "points": 0, "float_used": float_used_p1},
            {"id": "p2", "name": "B", "total_points": 0, "points": 0, "float_used": 0},
            {"id": "p3", "name": "C", "total_points": 0, "points": 0, "float_used": 0},
            {"id": "p4", "name": "D", "total_points": 0, "points": 0, "float_used": 0},
        ]
    return {
        "players": players,
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


# ── Float ────────────────────────────────────────────────────────────────────


def test_float_marks_usage_on_the_invoking_captain():
    request = _partners_request(float_by="p1")
    game_state = _game_state()

    hole_result, updated = process_complete_hole(request, game_state)

    assert hole_result["float_invoked_by"] == "p1"
    p1 = next(p for p in updated["players"] if p["id"] == "p1")
    assert p1["float_used"] == 1


def test_float_rejected_when_captain_already_used_it():
    request = _partners_request(float_by="p1")
    game_state = _game_state(float_used_p1=1)

    with pytest.raises(HTTPException) as exc:
        validate_float(request, game_state)
    assert exc.value.status_code == 400
    assert "already used" in str(exc.value.detail).lower()


def test_float_rejected_when_non_captain_invokes():
    request = _partners_request(float_by="p3")  # captain is p1
    with pytest.raises(HTTPException) as exc:
        validate_float(request, _game_state())
    assert "captain" in str(exc.value.detail).lower()


# ── Duncan (3-for-2 solo) ────────────────────────────────────────────────────


def test_duncan_win_pays_captain_three_halves_of_wager():
    """Captain win on Duncan: total_payout = (wager * 3) / 2, split across opponents."""
    request = _solo_request(winner="captain", wager=2.0, duncan=True)
    points = calculate_points_delta(request, _game_state())

    assert points["p1"] == pytest.approx(3.0)  # (2 * 3) / 2
    assert points["p2"] == pytest.approx(-1.0)
    assert points["p3"] == pytest.approx(-1.0)
    assert points["p4"] == pytest.approx(-1.0)
    assert abs(sum(points.values())) < 0.01


def test_duncan_loss_captain_pays_full_wager_to_each_opponent():
    request = _solo_request(winner="opponents", wager=2.0, duncan=True)
    points = calculate_points_delta(request, _game_state())

    assert points["p1"] == pytest.approx(-6.0)  # 2 * 3 opponents
    assert points["p2"] == pytest.approx(2.0)
    assert points["p3"] == pytest.approx(2.0)
    assert points["p4"] == pytest.approx(2.0)
    assert abs(sum(points.values())) < 0.01


def test_plain_solo_win_is_not_duncan_math():
    request = _solo_request(winner="captain", wager=2.0, duncan=False)
    points = calculate_points_delta(request, _game_state())

    assert points["p1"] == pytest.approx(6.0)  # 2 * 3 opponents
    assert points["p2"] == pytest.approx(-2.0)


# ── Aardvark ─────────────────────────────────────────────────────────────────


def test_aardvark_captain_cannot_form_direct_2_person_partnership():
    request = CompleteHoleRequest(
        hole_number=2,
        rotation_order=["p1", "p2", "p3", "p4", "p5"],
        captain_index=0,
        phase="normal",
        teams=HoleTeams(type="partners", team1=["p1", "p5"], team2=["p2", "p3", "p4"]),
        final_wager=1.0,
        winner="team1",
        scores={"p1": 4, "p2": 5, "p3": 5, "p4": 5, "p5": 4},
    )
    with pytest.raises(HTTPException) as exc:
        validate_aardvark(request, player_count=5)
    assert "aardvark" in str(exc.value.detail).lower()


def test_aardvark_ping_pong_requires_toss_first():
    request = _five_man_partners(tossed=False, ping_ponged=True)
    with pytest.raises(HTTPException) as exc:
        validate_aardvark(request, player_count=5)
    assert "ping-pong" in str(exc.value.detail).lower() or "tossed" in str(exc.value.detail).lower()


def test_aardvark_toss_doubles_points_delta():
    request = _five_man_partners(tossed=True, ping_ponged=False, wager=1.0)
    players = [{"id": f"p{i}", "name": str(i), "points": 0, "float_used": 0} for i in range(1, 6)]
    base = calculate_points_delta(request, _game_state(players=players))
    multiplied = apply_multipliers(dict(base), request, 3)

    for pid in base:
        assert multiplied[pid] == pytest.approx(base[pid] * 2)
    assert abs(sum(multiplied.values())) < 0.01


def test_aardvark_ping_pong_quadruples_points_delta():
    request = _five_man_partners(tossed=True, ping_ponged=True, wager=1.0)
    players = [{"id": f"p{i}", "name": str(i), "points": 0, "float_used": 0} for i in range(1, 6)]
    base = calculate_points_delta(request, _game_state(players=players))
    multiplied = apply_multipliers(dict(base), request, 3)

    for pid in base:
        assert multiplied[pid] == pytest.approx(base[pid] * 4)
    assert abs(sum(multiplied.values())) < 0.01
