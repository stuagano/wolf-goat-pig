"""Post-hole analysis service for Wolf Goat Pig game engine."""

from typing import Any, Callable

from ..domain.game_types import GamePhase, HoleState


def get_post_hole_analysis(
    hole_states: dict[int, HoleState],
    game_phase: GamePhase,
    players: list[Any],
    get_player_name_fn: Callable[[str | None], str],
    hole_number: int,
    calculate_hole_points_fn: Callable[[HoleState], dict[str, Any]],
) -> dict[str, Any]:
    if hole_number not in hole_states:
        raise ValueError(f"Hole {hole_number} not found")

    hole_state = hole_states[hole_number]

    return {
        "hole_number": hole_number,
        "game_phase": game_phase.value,
        "final_teams": _analyze_final_teams(hole_state, get_player_name_fn),
        "betting_summary": _analyze_betting_summary(hole_state),
        "scoring_analysis": _analyze_scoring(hole_state, get_player_name_fn),
        "strategic_insights": _generate_strategic_insights(hole_state),
        "point_distribution": _analyze_point_distribution(
            hole_state, get_player_name_fn, calculate_hole_points_fn
        ),
        "key_decisions": _analyze_key_decisions(hole_state, get_player_name_fn),
        "performance_ratings": _generate_performance_ratings(hole_state, get_player_name_fn),
        "what_if_scenarios": _generate_what_if_scenarios(hole_state),
    }


def _analyze_final_teams(
    hole_state: HoleState, get_player_name_fn: Callable[[str | None], str]
) -> dict[str, Any]:
    teams = hole_state.teams

    team_analysis: dict[str, Any] = {
        "formation_type": teams.type,
        "captain": get_player_name_fn(teams.captain),
        "captain_id": teams.captain,
    }

    if teams.type == "partners":
        team_analysis_update: dict[str, Any] = {
            "team1": [get_player_name_fn(pid) for pid in teams.team1],
            "team2": [get_player_name_fn(pid) for pid in teams.team2],
            "partnership_formed": True,
            "partnership_details": {
                "captain_partner": (
                    get_player_name_fn(teams.team1[1]) if len(teams.team1) > 1 else None
                ),
                "opposition": [get_player_name_fn(pid) for pid in teams.team2],
            },
        }
        team_analysis.update(team_analysis_update)
    elif teams.type == "solo":
        team_analysis_update_solo: dict[str, Any] = {
            "solo_player": get_player_name_fn(teams.solo_player),
            "opponents": [get_player_name_fn(pid) for pid in teams.opponents],
            "solo_risk_level": ("HIGH" if hole_state.betting.current_wager > 2 else "MEDIUM"),
        }
        team_analysis.update(team_analysis_update_solo)

    return team_analysis


def _analyze_betting_summary(hole_state: HoleState) -> dict[str, Any]:
    betting = hole_state.betting

    special_rules_list: list[str] = []
    betting_summary: dict[str, Any] = {
        "starting_wager": betting.base_wager,
        "final_wager": betting.current_wager,
        "wager_multiplier": betting.current_wager / betting.base_wager,
        "special_rules_invoked": special_rules_list,
    }

    if betting.duncan_invoked:
        special_rules_list.append("The Duncan (3-for-2 odds)")
    if betting.tunkarri_invoked:
        special_rules_list.append("The Tunkarri (Aardvark solo)")
    if betting.big_dick_invoked:
        special_rules_list.append("The Big Dick (18th hole)")
    if betting.option_invoked:
        special_rules_list.append("The Option (losing captain)")
    if betting.float_invoked:
        special_rules_list.append("The Float (captain's choice)")
    if betting.joes_special_value:
        special_rules_list.append(f"Joe's Special ({betting.joes_special_value} quarters)")
    if betting.carry_over:
        special_rules_list.append("Carry-over from previous hole")
    if betting.ping_pong_count > 0:
        special_rules_list.append(f"Ping Pong Aardvark ({betting.ping_pong_count}x)")

    return betting_summary


def _analyze_scoring(
    hole_state: HoleState, get_player_name_fn: Callable[[str | None], str]
) -> dict[str, Any]:
    if not hole_state.scores:
        return {"scores_entered": False}

    scores = hole_state.scores

    net_scores: dict[str, int] = {}
    for player_id, gross_score in scores.items():
        if gross_score is None:
            continue
        stroke_advantage = hole_state.stroke_advantages.get(player_id, 0)
        if isinstance(stroke_advantage, (int, float)):
            net_scores[player_id] = gross_score - int(stroke_advantage)
        else:
            net_scores[player_id] = gross_score

    valid_scores = {pid: score for pid, score in scores.items() if score is not None}
    if not valid_scores:
        return {"scores_entered": False}

    best_gross = min(valid_scores.values())
    best_net = min(net_scores.values()) if net_scores else best_gross
    best_gross_players = [pid for pid, score in valid_scores.items() if score == best_gross]
    best_net_players = [pid for pid, score in net_scores.items() if score == best_net]

    return {
        "scores_entered": True,
        "gross_scores": {pid: valid_scores[pid] for pid in valid_scores},
        "net_scores": net_scores,
        "best_gross_score": best_gross,
        "best_net_score": best_net,
        "best_gross_players": [get_player_name_fn(pid) for pid in best_gross_players],
        "best_net_players": [get_player_name_fn(pid) for pid in best_net_players],
        "score_spread": max(valid_scores.values()) - min(valid_scores.values()),
    }


def _analyze_point_distribution(
    hole_state: HoleState,
    get_player_name_fn: Callable[[str | None], str],
    calculate_hole_points_fn: Callable[[HoleState], dict[str, Any]],
) -> dict[str, Any]:
    if not hasattr(hole_state, "points_result") or not hole_state.scores:
        return {"points_calculated": False}

    points_result = calculate_hole_points_fn(hole_state)

    winners = points_result.get("winners", [])
    points_changes = points_result.get("points_changes", {})

    return {
        "points_calculated": True,
        "winners": [get_player_name_fn(pid) for pid in winners],
        "points_changes": {
            get_player_name_fn(pid): change for pid, change in points_changes.items()
        },
        "total_quarters_in_play": sum(abs(change) for change in points_changes.values()) // 2,
        "biggest_winner": (
            max(points_changes.items(), key=lambda x: x[1])[0] if points_changes else None
        ),
        "biggest_loser": (
            min(points_changes.items(), key=lambda x: x[1])[0] if points_changes else None
        ),
        "halved": points_result.get("halved", False),
    }


def _generate_strategic_insights(hole_state: HoleState) -> list[str]:
    insights = []

    if hole_state.teams.type == "partners":
        insights.append("Partnership strategy: Sharing risk and reward with a teammate")
        if hole_state.betting.current_wager > hole_state.betting.base_wager:
            insights.append("Aggressive betting: Partnerships encouraged confidence in doubling")
    elif hole_state.teams.type == "solo":
        insights.append("Solo strategy: High risk, high reward - going it alone")
        if hole_state.betting.duncan_invoked:
            insights.append("Duncan rule applied: 3-for-2 odds increased potential reward")

    wager_ratio = hole_state.betting.current_wager / hole_state.betting.base_wager
    if wager_ratio >= 4:
        insights.append("Heavy betting action: Multiple doubles created high-stakes hole")
    elif wager_ratio >= 2:
        insights.append("Moderate betting: One double increased the pressure")

    if hole_state.betting.big_dick_invoked:
        insights.append("Big Dick challenge: Ultimate high-stakes gamble on final hole")
    if hole_state.betting.ping_pong_count > 0:
        insights.append("Ping Pong Aardvark: Complex team dynamics with multiple tosses")

    return insights


def _analyze_key_decisions(
    hole_state: HoleState, get_player_name_fn: Callable[[str | None], str]
) -> list[dict[str, Any]]:
    decisions = []

    if hole_state.teams.type == "partners":
        decisions.append(
            {
                "decision": "Partnership Formation",
                "player": get_player_name_fn(hole_state.teams.captain),
                "action": f"Requested {get_player_name_fn(hole_state.teams.team1[1]) if len(hole_state.teams.team1) > 1 else 'unknown'} as partner",
                "outcome": "Partnership accepted",
                "impact": "Shared risk/reward strategy",
            }
        )
    elif hole_state.teams.type == "solo":
        decisions.append(
            {
                "decision": "Solo Declaration",
                "player": get_player_name_fn(hole_state.teams.solo_player),
                "action": "Went solo against the field",
                "outcome": "Playing alone",
                "impact": f"Doubled base wager to {hole_state.betting.current_wager}",
            }
        )

    if hole_state.betting.current_wager > hole_state.betting.base_wager:
        decisions.append(
            {
                "decision": "Double Offer",
                "action": "Offered to double the wager",
                "outcome": "Double accepted",
                "impact": f"Wager increased to {hole_state.betting.current_wager}",
            }
        )

    return decisions


def _generate_performance_ratings(
    hole_state: HoleState, get_player_name_fn: Callable[[str | None], str]
) -> dict[str, Any]:
    if not hole_state.scores:
        return {"ratings_available": False}

    ratings = {}
    scores = hole_state.scores

    for player_id, score in scores.items():
        if score is None:
            continue
        player_name = get_player_name_fn(player_id)

        valid_scores = [s for s in scores.values() if s is not None]
        if not valid_scores:
            continue
        field_average = sum(valid_scores) / len(valid_scores)
        relative_performance = field_average - score

        if relative_performance >= 2:
            rating = "EXCELLENT"
        elif relative_performance >= 1:
            rating = "GOOD"
        elif relative_performance >= -1:
            rating = "AVERAGE"
        else:
            rating = "POOR"

        ratings[player_name] = {
            "rating": rating,
            "score": score,
            "relative_to_field": relative_performance,
        }

    return ratings


def _generate_what_if_scenarios(hole_state: HoleState) -> list[str]:
    scenarios = []

    if hole_state.teams.type == "partners":
        scenarios.append(
            "What if captain had gone solo instead? Higher risk but potentially higher reward"
        )
        scenarios.append(
            "What if different partnership was formed? Team dynamics could have changed"
        )

    if hole_state.teams.type == "solo":
        scenarios.append(
            "What if solo player had requested a partner? Shared risk might have been safer"
        )

    if hole_state.betting.current_wager == hole_state.betting.base_wager:
        scenarios.append(
            "What if someone had offered a double? Could have increased the stakes"
        )

    if hole_state.betting.current_wager > hole_state.betting.base_wager:
        scenarios.append(
            "What if the double was declined? Hole would have ended with smaller stakes"
        )

    return scenarios
