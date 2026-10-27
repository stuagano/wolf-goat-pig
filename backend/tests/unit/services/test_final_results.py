"""Real-session checks for the shared final-result projection boundary."""

from copy import deepcopy

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app import models
from app.schemas.round_identity import RoundDraft
from app.services.completed_game_service import build_hole_history, persist_completed_game


@pytest.fixture
def identity_db():
    engine = create_engine("sqlite://")
    models.Base.metadata.create_all(engine)
    with Session(engine, autoflush=False) as db:
        yield db
    engine.dispose()


def game(db):
    row = models.GameStateModel(game_id="synthetic-round", state={}, game_status="setup")
    db.add(row)
    db.flush()
    return row


def draft(**updates):
    values = {
        "raw_date": "unknown",
        "players": [
            {"participant_id": "guest-a", "name": "Avery", "quarters": 0},
            {"participant_id": "guest-b", "name": "Avery", "quarters": None},
        ],
        "roster_complete": True,
    }
    values.update(updates)
    return RoundDraft(**values)


def persist(db, row, value):
    from app.services.completed_game_service import persist_final_results

    return persist_final_results(db, row, value)


def test_totals_only_rollback_has_no_projection(identity_db):
    row = game(identity_db)
    persist(identity_db, row, draft())
    identity_db.rollback()
    assert identity_db.query(models.GameStateModel).count() == 0
    assert identity_db.query(models.GameRecord).count() == 0
    assert identity_db.query(models.GamePlayerResult).count() == 0


def test_unknown_metrics_zero_and_distinct_guest_slots(identity_db):
    row = game(identity_db)
    revision = persist(identity_db, row, draft())
    identity_db.commit()
    record = identity_db.query(models.GameRecord).one()
    results = identity_db.query(models.GamePlayerResult).order_by(models.GamePlayerResult.participant_id).all()
    assert revision == record.accepted_revision == row.revision == 1
    assert record.course_name is None
    assert record.total_holes_played is None
    assert record.played_on is None
    assert record.raw_date == "unknown"
    assert record.score_eligible is False
    assert record.final_scores == {"guest-a": 0, "guest-b": None}
    assert [r.total_earnings for r in results] == [0, None]
    for result in results:
        assert result.final_position is None
        assert result.holes_won is None
        assert result.total_bets is None
        assert result.performance_metrics is None
        assert result.hole_scores is None
    assert row.game_status == "completed"
    assert "current_hole" not in row.state
    assert not row.state.get("hole_history")
    assert all("handicap" not in p for p in row.state["players"])


def test_stable_ids_missing_values_and_revision_idempotency(identity_db):
    row = game(identity_db)
    value = draft()
    persist(identity_db, row, value)
    identity_db.commit()
    original = {r.participant_id: r.id for r in identity_db.query(models.GamePlayerResult)}
    assert persist(identity_db, row, value) == 1
    value.players[0].name = "Renamed guest"
    value.players[0].quarters = 1.25
    assert persist(identity_db, row, value) == 2
    identity_db.commit()
    value.players[0].quarters = None
    persist(identity_db, row, value)
    assert {r.participant_id: r.id for r in identity_db.query(models.GamePlayerResult)} == original
    assert identity_db.query(models.GamePlayerResult).filter_by(participant_id="guest-a").one().total_earnings == 1.25
    record = identity_db.query(models.GameRecord).one()
    assert record.game_settings["field_provenance"]


def detail(count=18):
    return [
        {
            "hole": h,
            "points_delta": {"guest-a": 1, "guest-b": -1},
            "gross_scores": {"guest-a": 4},
            "teams": [["guest-a"], ["guest-b"]],
            "notes": "preserve",
            "custom_evidence": {"observed": True},
        }
        for h in range(1, count + 1)
    ]


def test_partial_and_disagreeing_complete_detail_preserve_explicit_totals(identity_db):
    row = game(identity_db)
    value = draft()
    value.players[1].quarters = 0
    persist(identity_db, row, value)
    for count, coverage in [(1, "partial"), (18, "per_hole_complete")]:
        value.detail_coverage = coverage
        value.hole_history = detail(count)
        persist(identity_db, row, value)
        record = identity_db.query(models.GameRecord).one()
        assert record.final_scores == {"guest-a": 0, "guest-b": 0}
    assert record.game_settings["detail_discrepancies"] == {
        "guest-a": {"accepted": 0, "computed": 18},
        "guest-b": {"accepted": 0, "computed": -18},
    }
    assert row.state["hole_history"][0]["custom_evidence"] == {"observed": True}


def test_targeted_detail_update_preserves_all_unsupplied_evidence(identity_db):
    row = game(identity_db)
    value = draft(detail_coverage="per_hole_complete", hole_history=detail())
    value.players[0].quarters = None
    persist(identity_db, row, value)
    value.hole_history = [{"hole": 1, "points_delta": {"guest-a": 2, "guest-b": -2}}]
    value.detail_coverage = "partial"
    persist(identity_db, row, value)
    saved = row.state["hole_history"]
    assert len(saved) == 18
    assert saved[0]["gross_scores"] == {"guest-a": 4}
    assert saved[0]["notes"] == "preserve"
    assert saved[0]["teams"]
    assert saved[0]["custom_evidence"] == {"observed": True}


@pytest.mark.parametrize(
    "coverage,history",
    [
        ("per_hole_complete", detail(17)),
        ("partial", detail(1) + detail(1)),
        ("totals_only", detail(1)),
        ("partial", [{"hole": 1, "points_delta": {"unknown": 0}}]),
    ],
)
def test_invalid_detail_is_rejected_before_projection(identity_db, coverage, history):
    row = game(identity_db)
    with pytest.raises(HTTPException):
        persist(identity_db, row, draft(detail_coverage=coverage, hole_history=history))
    assert identity_db.query(models.GameRecord).count() == 0


def test_detailed_entry_point_is_strict_and_never_commits(identity_db):
    row = game(identity_db)
    row.state = {"players": [{"id": "guest-a", "name": "A"}, {"id": "guest-b", "name": "B"}], "hole_history": detail()}
    commits = []
    event.listen(identity_db, "after_commit", lambda session: commits.append(True))
    assert persist_completed_game(identity_db, row) == 2
    assert commits == []
    ids = [r.id for r in identity_db.query(models.GamePlayerResult)]
    assert persist_completed_game(identity_db, row) == 0
    assert [r.id for r in identity_db.query(models.GamePlayerResult)] == ids
    identity_db.rollback()
    assert identity_db.query(models.GameRecord).count() == 0


def test_narrow_roster_correction_retains_other_slots_and_detail(identity_db):
    row = game(identity_db)
    value = draft(detail_coverage="per_hole_complete", hole_history=detail())
    value.players[0].quarters = 18
    value.players[1].quarters = -18
    persist(identity_db, row, value)
    identity_db.commit()
    before = {
        r.participant_id: (r.id, r.total_earnings, deepcopy(r.hole_scores))
        for r in identity_db.query(models.GamePlayerResult)
    }
    narrow = RoundDraft(
        players=[{"participant_id": "guest-a", "name": "Corrected A", "quarters": 21}], roster_complete=False
    )
    persist(identity_db, row, narrow)
    identity_db.commit()
    after = {r.participant_id: r for r in identity_db.query(models.GamePlayerResult)}
    assert after["guest-a"].id == before["guest-a"][0]
    assert after["guest-a"].total_earnings == 21
    assert (after["guest-b"].id, after["guest-b"].total_earnings, after["guest-b"].hole_scores) == before["guest-b"]
    assert {p["id"] for p in row.state["players"]} == {"guest-a", "guest-b"}
    assert row.state["hole_history"] == detail()


def test_roster_extension_does_not_invent_historic_cells(identity_db):
    row = game(identity_db)
    persist(identity_db, row, draft(detail_coverage="per_hole_complete", hole_history=detail()))
    old_ids = {r.participant_id: r.id for r in identity_db.query(models.GamePlayerResult)}
    persist(identity_db, row, RoundDraft(players=[{"participant_id": "guest-c", "name": "C", "quarters": 3}]))
    identity_db.commit()
    record = identity_db.query(models.GameRecord).one()
    assert record.detail_coverage == "partial"
    assert record.roster_complete is False
    assert record.score_eligible is False
    assert record.player_count == 3
    assert row.state["hole_history"] == detail()
    for h in row.state["hole_history"]:
        assert "guest-c" not in h["points_delta"]
    added = identity_db.query(models.GamePlayerResult).filter_by(participant_id="guest-c").one()
    assert not added.hole_scores
    assert added.holes_won is None
    assert added.performance_metrics is None
    assert {
        r.participant_id: r.id for r in identity_db.query(models.GamePlayerResult) if r.participant_id in old_ids
    } == old_ids


def test_existing_hole_quarters_tracks_merged_history(identity_db):
    row = game(identity_db)
    value = draft(detail_coverage="per_hole_complete", hole_history=detail())
    persist(identity_db, row, value)
    row.state = {**row.state, "hole_quarters": {"1": {"guest-a": 999}}}
    value.hole_history = [{"hole": 1, "points_delta": {"guest-a": 2, "guest-b": -2}}]
    value.detail_coverage = "partial"
    persist(identity_db, row, value)
    identity_db.commit()
    assert row.state["hole_quarters"] == {str(h["hole"]): h["points_delta"] for h in row.state["hole_history"]}
    assert row.state["hole_quarters"]["1"] == {"guest-a": 2, "guest-b": -2}


def test_build_history_rejects_duplicate_cells_and_unknown_indices():
    entries = [{"hole": 1, "player_index": 0, "quarters": 0}]
    for bad in [entries + deepcopy(entries), [{"hole": 1, "player_index": 9, "quarters": 0}]]:
        with pytest.raises(HTTPException):
            build_hole_history([{"id": "p1"}], bad)
