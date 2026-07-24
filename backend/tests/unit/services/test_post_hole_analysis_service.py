"""CTK-grade contracts for post-hole analysis narrative shape."""

import pytest

from app.domain.game_types import BettingState, GamePhase, HoleState, TeamFormation
from app.services.post_hole_analysis_service import get_post_hole_analysis


def _names(pid):
    return {"p1": "Alice", "p2": "Bob", "p3": "Cara", "p4": "Dan"}.get(pid or "", "Unknown")


def _points(_hole_state):
    return {"p1": 2, "p2": 2, "p3": -2, "p4": -2}


def test_partners_analysis_returns_expected_shape():
    hole = HoleState(
        hole_number=5,
        hitting_order=["p1", "p2", "p3", "p4"],
        teams=TeamFormation(
            type="partners",
            captain="p1",
            team1=["p1", "p2"],
            team2=["p3", "p4"],
        ),
        betting=BettingState(base_wager=1, current_wager=2),
        scores={"p1": 4, "p2": 5, "p3": 5, "p4": 6},
    )
    analysis = get_post_hole_analysis(
        {5: hole},
        GamePhase.REGULAR,
        [],
        _names,
        5,
        _points,
    )
    assert analysis["hole_number"] == 5
    assert set(analysis) >= {
        "final_teams",
        "betting_summary",
        "scoring_analysis",
        "strategic_insights",
        "point_distribution",
        "key_decisions",
        "performance_ratings",
        "what_if_scenarios",
    }
    assert analysis["final_teams"]["formation_type"] == "partners"
    assert analysis["final_teams"]["partnership_formed"] is True
    assert analysis["betting_summary"]["wager_multiplier"] == 2
    assert analysis["scoring_analysis"]["scores_entered"] is True


def test_duncan_solo_marks_special_rule_and_high_risk():
    hole = HoleState(
        hole_number=8,
        hitting_order=["p1", "p2", "p3", "p4"],
        teams=TeamFormation(
            type="solo",
            captain="p1",
            solo_player="p1",
            opponents=["p2", "p3", "p4"],
        ),
        betting=BettingState(base_wager=1, current_wager=4, duncan_invoked=True),
        scores={"p1": 3, "p2": 5, "p3": 5, "p4": 5},
    )
    analysis = get_post_hole_analysis(
        {8: hole},
        GamePhase.REGULAR,
        [],
        _names,
        8,
        _points,
    )
    assert "The Duncan (3-for-2 odds)" in analysis["betting_summary"]["special_rules_invoked"]
    assert analysis["final_teams"]["solo_risk_level"] == "HIGH"


def test_unknown_hole_raises_value_error():
    with pytest.raises(ValueError, match="Hole 9 not found"):
        get_post_hole_analysis({}, GamePhase.REGULAR, [], _names, 9, _points)
