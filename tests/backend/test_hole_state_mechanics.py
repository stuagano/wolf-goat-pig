"""Unit tests for the HoleState mechanics in the Wolf-Goat-Pig simulation."""

from __future__ import annotations

from typing import List

import pytest

from backend.app.wolf_goat_pig_simulation import (
    BallPosition,
    BettingState,
    HoleState,
    TeamFormation,
    WGPPlayer,
    WGPShotResult,
)


def _make_players() -> List[WGPPlayer]:
    """Create a consistent roster for hole state tests."""
    return [
        WGPPlayer(id="p1", name="Player One", handicap=0),
        WGPPlayer(id="p2", name="Player Two", handicap=10.5),
        WGPPlayer(id="p3", name="Player Three", handicap=18),
        WGPPlayer(id="p4", name="Player Four", handicap=22),
    ]


def _make_hole_state(hitting_order: List[str] | None = None) -> HoleState:
    """Build a HoleState with predictable defaults for testing."""
    order = hitting_order or ["p1", "p2", "p3", "p4"]
    teams = TeamFormation(type="partners", team1=["p1", "p3"], team2=["p2", "p4"])
    return HoleState(hole_number=1, hitting_order=order, teams=teams, betting=BettingState())


@pytest.fixture
def hole_state() -> HoleState:
    return _make_hole_state()


def test_calculate_stroke_advantages_supports_full_half_and_net_scores(hole_state: HoleState) -> None:
    players = _make_players()

    # Validate full and half stroke behaviour on a mid-difficulty hole.
    hole_state.set_hole_info(par=4, yardage=420, stroke_index=11)
    hole_state.calculate_stroke_advantages(players)

    scratch = hole_state.get_player_stroke_advantage("p1")
    assert scratch is not None and scratch.strokes_received == pytest.approx(0)

    half_stroke_player = hole_state.get_player_stroke_advantage("p2")
    assert half_stroke_player is not None and half_stroke_player.strokes_received == pytest.approx(0.5)

    full_stroke_player = hole_state.get_player_stroke_advantage("p3")
    assert full_stroke_player is not None and full_stroke_player.strokes_received == pytest.approx(1.0)

    # Net scores should account for the strokes received by each player.
    net_score = hole_state.calculate_net_score("p3", gross_score=5)
    assert net_score == pytest.approx(4.0)


def test_update_order_of_play_tracks_line_of_scrimmage(hole_state: HoleState) -> None:
    hole_state.ball_positions = {
        "p1": BallPosition(player_id="p1", distance_to_pin=150, lie_type="fairway", shot_count=1),
        "p2": BallPosition(player_id="p2", distance_to_pin=210, lie_type="rough", shot_count=1),
        "p3": BallPosition(player_id="p3", distance_to_pin=60, lie_type="green", shot_count=2),
    }

    hole_state.update_order_of_play()

    assert hole_state.current_order_of_play == ["p2", "p1", "p3"]
    assert hole_state.line_of_scrimmage == "p2"
    assert hole_state.next_player_to_hit == "p2"


def test_add_shot_marks_hole_complete_when_all_players_finish() -> None:
    hole_state = _make_hole_state(hitting_order=["p1", "p2"])

    hole_state.add_shot(
        "p1",
        WGPShotResult(
            player_id="p1",
            shot_number=1,
            lie_type="fairway",
            distance_to_pin=140,
            shot_quality="good",
        ),
    )
    assert hole_state.ball_positions["p1"].shot_count == 1
    assert not hole_state.hole_complete

    hole_state.add_shot(
        "p1",
        WGPShotResult(
            player_id="p1",
            shot_number=2,
            lie_type="green",
            distance_to_pin=0,
            shot_quality="excellent",
            made_shot=True,
        ),
    )
    assert hole_state.ball_positions["p1"].holed is True
    assert hole_state.wagering_closed is True

    hole_state.add_shot(
        "p2",
        WGPShotResult(
            player_id="p2",
            shot_number=1,
            lie_type="green",
            distance_to_pin=0,
            shot_quality="excellent",
            made_shot=True,
        ),
    )

    assert hole_state.ball_positions["p2"].holed is True
    assert hole_state.hole_complete is True


def test_get_approach_shot_betting_opportunities_identifies_pressure_moments(hole_state: HoleState) -> None:
    hole_state.ball_positions = {
        "p1": BallPosition(player_id="p1", distance_to_pin=25, lie_type="green", shot_count=2),
        "p2": BallPosition(player_id="p2", distance_to_pin=18, lie_type="green", shot_count=2),
        "p3": BallPosition(player_id="p3", distance_to_pin=80, lie_type="fairway", shot_count=2),
    }

    opportunities = hole_state.get_approach_shot_betting_opportunities()

    assert any(op["type"] == "pressure_approach" for op in opportunities)
    short_approach = [op for op in opportunities if op["type"] == "short_approach"]
    assert short_approach and short_approach[0]["player"] == "p3"


def test_process_tee_shot_updates_invitation_windows() -> None:
    hole_state = _make_hole_state()

    for player_id in ["p1", "p2", "p3", "p4"]:
        hole_state.process_tee_shot(
            player_id,
            WGPShotResult(
                player_id=player_id,
                shot_number=1,
                lie_type="tee",
                distance_to_pin=250,
                shot_quality="average",
            ),
        )

    assert hole_state.tee_shots_complete == 4
    assert hole_state.partnership_deadline_passed is True
    assert hole_state.invitation_windows["p1"] is False
    assert hole_state.invitation_windows["p2"] is False


def test_can_offer_double_respects_line_of_scrimmage(hole_state: HoleState) -> None:
    hole_state.ball_positions = {
        "p1": BallPosition(player_id="p1", distance_to_pin=200, lie_type="rough", shot_count=1),
        "p2": BallPosition(player_id="p2", distance_to_pin=90, lie_type="fairway", shot_count=1),
    }

    hole_state.update_order_of_play()

    assert hole_state.line_of_scrimmage == "p1"
    assert hole_state.can_offer_double("p1") is True
    assert hole_state.can_offer_double("p2") is False

    hole_state.wagering_closed = True
    assert hole_state.can_offer_double("p1") is False
