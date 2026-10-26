"""Saved-card identity is stricter than legacy score-total deduplication."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.services.unified_data_service import UnifiedDataService, UnifiedRound


def game(source, key, *, day="2026-10-25", course="Test Golf Club", group="A", scores=None, known=True):
    scores = scores or [("Avery", 147), ("Blair", 82), ("Casey", -8), ("Devon", -16), ("Emery", -66), ("Frankie", -139)]
    return [
        UnifiedRound(
            "25-Oct",
            day,
            group,
            name,
            score,
            course,
            source=source,
            game_key=(source, key),
            game_id=key if source == "database" else None,
            played_date_known=known,
            hole_scores=[{"hole": 1, "quarters": score}] if source == "database" else None,
        )
        for name, score in scores
    ]


def test_six_player_sheet_round_keeps_uuid_and_holes_without_double_counting():
    rows = UnifiedDataService._drop_sheet_duplicates(game("primary_sheet", "sheet") + game("database", "card"))
    assert len(rows) == 6
    assert {r.source for r in rows} == {"primary_sheet"}
    assert {r.game_id for r in rows} == {"card"}
    assert all(r.hole_scores == [{"hole": 1, "quarters": r.score}] for r in rows)


@pytest.mark.parametrize("extra", [game("database", "other"), game("primary_sheet", "other", group="B")])
def test_multiple_candidates_never_pick_a_card(extra):
    rows = UnifiedDataService._drop_sheet_duplicates(game("primary_sheet", "sheet") + game("database", "card") + extra)
    assert all(r.game_id is None and r.hole_scores is None for r in rows if r.source == "primary_sheet")


def test_identical_totals_with_different_player_pairings_do_not_link():
    rows = UnifiedDataService._drop_sheet_duplicates(
        game("primary_sheet", "sheet", scores=[("Avery", 10), ("Blair", -10)])
        + game("database", "card", scores=[("Avery", -10), ("Blair", 10)])
    )
    assert len(rows) == 2  # sheet totals still authoritative for the same roster/day
    assert all(r.game_id is None and r.hole_scores is None for r in rows)


def test_repeat_roster_on_different_known_played_dates_is_not_dropped():
    rows = UnifiedDataService._drop_sheet_duplicates(
        game("primary_sheet", "sheet") + game("database", "card", day="2026-10-26")
    )
    assert len(rows) == 12
    assert {r.game_id for r in rows if r.source == "database"} == {"card"}
    assert all(r.game_id is None for r in rows if r.source == "primary_sheet")


@pytest.mark.parametrize("course", ["Other Golf Club", "Test", ""])
def test_course_mismatch_is_never_guessed(course):
    rows = UnifiedDataService._drop_sheet_duplicates(
        game("primary_sheet", "sheet") + game("database", "card", course=course)
    )
    assert all(r.game_id is None and r.hole_scores is None for r in rows if r.source == "primary_sheet")


def test_legacy_approximate_dedup_does_not_transfer_card_or_holes():
    rows = UnifiedDataService._drop_sheet_duplicates(
        game("primary_sheet", "sheet") + game("database", "card", day="2026-10-26", known=False)
    )
    assert len(rows) == 6
    assert all(r.game_id is None and r.hole_scores is None for r in rows)


def test_two_distinct_same_day_games_stay_distinct_without_sheet():
    rows = UnifiedDataService._drop_sheet_duplicates(game("database", "one") + game("database", "two"))
    assert len(rows) == 12
    assert {r.game_id for r in rows} == {"one", "two"}


def test_sheet_only_and_member_only_do_not_invent_ids():
    rows = UnifiedDataService._drop_sheet_duplicates(game("primary_sheet", "sheet") + game("member", "posted"))
    assert all(r.game_id is None for r in rows)


def test_duplicate_normalized_names_are_not_authoritative_identity():
    scores = [("Avery", 10), (" avery ", -10)]
    rows = UnifiedDataService._drop_sheet_duplicates(
        game("primary_sheet", "sheet", scores=scores) + game("database", "card", scores=scores)
    )
    assert all(r.game_id is None for r in rows if r.source == "primary_sheet")


def test_conversion_requires_reachable_game_and_preserves_played_date():
    record = SimpleNamespace(
        id=7,
        game_id="saved-uuid",
        completed_at="2026-10-26T13:00:00",
        created_at="2026-10-26T12:00:00",
        game_settings={"played_at": "2026-10-25T12:00:00"},
        course_name="Test Golf Club",
        game_duration_minutes=None,
    )
    result = SimpleNamespace(player_name="Avery", total_earnings=147, hole_scores=[])
    state = SimpleNamespace(game_id="saved-uuid", state={}, created_at=record.created_at)
    with patch("app.services.unified_data_service.SpreadsheetSyncService"):
        service = UnifiedDataService()
    row = service._db_result_to_unified(result, record, state)
    assert row.game_id == "saved-uuid"
    assert row.date_sortable == "2026-10-25"
    assert row.played_date_known
    assert service._db_result_to_unified(result, record).game_id is None
