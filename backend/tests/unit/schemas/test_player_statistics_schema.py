"""PlayerStatisticsResponse must tolerate legacy rows with NULL JSON columns.

Stats rows written before the JSON columns were added store SQL NULL. A
Pydantic field default does not apply to an explicit None, so those rows used
to fail validation and turn GET /players/{id}/statistics into a 500 — the
account page then rendered "No game data yet" for players who had history.
"""

from app.schemas.players import PlayerStatisticsResponse


def _legacy_row(**overrides):
    """Attribute bag mimicking a PlayerStatistics ORM row with NULL JSON columns."""

    values = {
        "id": 1,
        "player_id": 20,
        "games_played": 12,
        "games_won": 5,
        "total_earnings": 42.0,
        "holes_played": 216,
        "holes_won": 60,
        "avg_earnings_per_hole": 0.19,
        "betting_success_rate": 0.5,
        "successful_bets": 10,
        "total_bets": 20,
        "partnership_success_rate": 0.5,
        "partnerships_formed": 8,
        "partnerships_won": 4,
        "solo_attempts": 2,
        "solo_wins": 1,
        "favorite_game_mode": "wolf_goat_pig",
        "preferred_player_count": 4,
        "best_hole_performance": None,
        "worst_hole_performance": None,
        "performance_trends": None,
        "head_to_head_records": None,
        "last_updated": "2026-07-27T00:00:00",
    }
    values.update(overrides)
    return type("LegacyStatsRow", (), values)()


def test_null_json_columns_become_empty_collections():
    stats = PlayerStatisticsResponse.model_validate(_legacy_row())

    assert stats.best_hole_performance == []
    assert stats.worst_hole_performance == []
    assert stats.performance_trends == []
    assert stats.head_to_head_records == {}


def test_history_is_preserved_not_zeroed():
    stats = PlayerStatisticsResponse.model_validate(_legacy_row())

    assert stats.games_played == 12
    assert stats.games_won == 5
    assert stats.total_earnings == 42.0


def test_populated_json_columns_pass_through():
    stats = PlayerStatisticsResponse.model_validate(
        _legacy_row(
            performance_trends=[{"date": "2026-07-01", "earnings": 5}],
            head_to_head_records={"Andy": {"wins": 2}},
        )
    )

    assert stats.performance_trends == [{"date": "2026-07-01", "earnings": 5}]
    assert stats.head_to_head_records == {"Andy": {"wins": 2}}
