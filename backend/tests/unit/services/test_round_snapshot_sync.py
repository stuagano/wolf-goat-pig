"""Complete mocked Sheets snapshots; no Google/source transports are used."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import models
from app.services import spreadsheet_sync_service as sheet


@pytest.fixture
def sheets(monkeypatch):
    rows = [["6-Oct", "B", "Avery", "", "", "", "r1", "s1"]]
    metadata = {
        "sheets": [
            {
                "properties": {
                    "sheetId": "tab",
                    "title": "Details",
                    "gridProperties": {"rowCount": 6002, "columnCount": 8},
                }
            }
        ],
        "fixture_token_contract": True,
    }
    calls = []
    monkeypatch.setattr(sheet, "_sheets_metadata_get", lambda *_: metadata, raising=False)

    def get(*args):
        calls.append(args)
        return {
            "range": args[1],
            "majorDimension": "ROWS",
            "values": rows if ":H" in args[1] else [r[:6] for r in rows],
        }

    monkeypatch.setattr(sheet, "_sheets_api_get", get)
    return rows, metadata, calls


def test_blank_sheet_total_stays_unknown(sheets):
    snapshot = sheet.fetch_round_snapshot("fixture:tab:2026", season_year=2026)
    assert snapshot.complete
    assert snapshot.rounds[0].draft.players[0].quarters is None
    assert snapshot.rounds[0].draft.course_name is None
    assert snapshot.rounds[0].draft.played_on.isoformat() == "2026-10-06"


def test_complete_history_range_not_5000_and_order_independent(sheets):
    rows, _, calls = sheets
    rows[:] = [["6-Oct", "B", f"Player {i}", "0", "", "", "r1", f"s{i}"] for i in range(5001)]
    first = sheet.fetch_round_snapshot("fixture:tab:2026", season_year=2026)
    rows.reverse()
    second = sheet.fetch_round_snapshot("fixture:tab:2026", season_year=2026)
    assert len(first.rounds[0].draft.players) == 5001
    assert first.fingerprint == second.fingerprint
    assert all(call[1] == "'Details'!A2:H6002" for call in calls)


@pytest.mark.parametrize("value", ["NaN", "Infinity", "garbage", True])
def test_invalid_numeric_rows_held_not_discarded(sheets, value):
    rows, _, _ = sheets
    rows[0][3] = value
    snapshot = sheet.fetch_round_snapshot("fixture:tab:2026", season_year=2026)
    assert snapshot.rounds[0].raw_payload["parse_errors"]
    assert snapshot.rounds[0].raw_payload["rows"][0][3] == value
    assert not snapshot.rounds[0].continuity_verified


def test_unknown_year_and_explicit_zero_and_null_remain_distinct(sheets):
    rows, _, _ = sheets
    rows[0][3] = 0
    snapshot = sheet.fetch_round_snapshot("fixture:tab:unknown", season_year=None)
    assert snapshot.rounds[0].draft.played_on is None
    assert snapshot.rounds[0].draft.raw_date == "6-Oct"
    assert snapshot.rounds[0].draft.players[0].quarters == 0
    rows[0][3] = None
    snapshot = sheet.fetch_round_snapshot("fixture:tab:unknown", season_year=None)
    assert snapshot.rounds[0].raw_payload["presence"][0][3] == "null"
    rows[0] = rows[0][:3]
    snapshot = sheet.fetch_round_snapshot("fixture:tab:unknown", season_year=None)
    assert snapshot.rounds[0].raw_payload["presence"][0][3] == "missing"


def test_copied_token_and_incompatible_round_group_are_quarantined(sheets):
    rows, _, _ = sheets
    rows.append(["7-Oct", "C", "Other", "0", "", "", "r1", "s1"])
    snapshot = sheet.fetch_round_snapshot("fixture:tab:2026", season_year=2026)
    assert snapshot.rounds[0].raw_payload["parse_errors"]
    assert not snapshot.rounds[0].continuity_verified


def test_production_does_not_assume_proposed_g_h_contract(sheets):
    snapshot = sheet.fetch_round_snapshot("workbook:tab:2026", season_year=2026)
    assert not snapshot.rounds[0].continuity_verified
    assert snapshot.rounds[0].source.round_token != "r1"


@pytest.fixture
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'snapshot.db'}")
    models.Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(models.AppConfig(name="round_identity", value={"mode": "canonical", "epoch": 1, "season": 2026}))
        session.commit()
        yield session
    engine.dispose()


def test_repeated_snapshot_keeps_uuid_and_unknowns(db, sheets):
    from app.services.round_identity import sync_round_snapshot

    snapshot = sheet.fetch_round_snapshot("fixture:tab:2026", season_year=2026)
    first = sync_round_snapshot(db, snapshot)
    second = sync_round_snapshot(db, snapshot)
    assert first[0].game_id == second[0].game_id
    assert db.query(models.GameRecord).count() == 1
    assert db.query(models.GamePlayerResult).one().total_earnings is None
    assert db.query(models.GameRecord).one().course_name is None


def review(db, snapshot):
    row = db.get(models.AppConfig, "round_source_reviews")
    if row is None:
        row = models.AppConfig(name="round_source_reviews", value={})
        db.add(row)
    row.value = {snapshot.scope: {"fingerprint": snapshot.fingerprint, "reviewer_profile_id": 7}}
    db.commit()


def test_displaced_tokens_hold_before_unknown_field_fill(db, sheets):
    from app.services.round_identity import sync_round_snapshot

    rows, _, _ = sheets
    rows.append(["6-Oct", "B", "Blair", "", "", "", "r1", "s2"])
    original = sheet.fetch_round_snapshot("fixture:tab:2026", season_year=2026)
    game = sync_round_snapshot(db, original)[0].game_id
    rows[0][:6], rows[1][:6] = rows[1][:6], rows[0][:6]
    rows[0][3], rows[1][3] = 5, -5
    changed = sheet.fetch_round_snapshot("fixture:tab:2026", season_year=2026)
    held = sync_round_snapshot(db, changed)
    assert held[0].status == "held" and held[0].game_id == game
    assert all(r.total_earnings is None for r in db.query(models.GamePlayerResult))
    assert {r.player_name for r in db.query(models.GamePlayerResult)} == {"Avery", "Blair"}
    assert db.query(models.RoundIssue).filter_by(kind="continuity", status="open").count() == 1


def test_reviewed_snapshot_fills_and_missing_participant_is_review_not_removal(db, sheets):
    from app.services.round_identity import sync_round_snapshot

    rows, _, _ = sheets
    rows.append(["6-Oct", "B", "Blair", "", "", "", "r1", "s2"])
    sync_round_snapshot(db, sheet.fetch_round_snapshot("fixture:tab:2026", season_year=2026))
    rows[0][3], rows[1][3] = 2.5, -2.5
    changed = sheet.fetch_round_snapshot("fixture:tab:2026", season_year=2026)
    review(db, changed)
    assert sync_round_snapshot(db, changed)[0].status == "accepted"
    assert sorted(r.total_earnings for r in db.query(models.GamePlayerResult)) == [-2.5, 2.5]
    rows.pop()
    missing = sheet.fetch_round_snapshot("fixture:tab:2026", season_year=2026)
    review(db, missing)
    assert sync_round_snapshot(db, missing)[0].status == "held"
    assert db.query(models.RoundIssue).filter_by(kind="missing_participant", status="open").count() == 1
    assert db.query(models.GamePlayerResult).count() == 2
    assert all(not r.is_retracted for r in db.query(models.GamePlayerResult))


def test_whole_source_round_disappearance_retains_uuid_and_results(db, sheets):
    from app.services.round_identity import sync_round_snapshot

    rows, _, _ = sheets
    first = sync_round_snapshot(db, sheet.fetch_round_snapshot("fixture:tab:2026", season_year=2026))
    rows[:] = [["7-Oct", "C", "Other", "0", "", "", "r2", "s2"]]
    result = sync_round_snapshot(db, sheet.fetch_round_snapshot("fixture:tab:2026", season_year=2026))
    assert any(o.game_id == first[0].game_id and o.status == "held" for o in result)
    assert db.query(models.GameRecord).filter_by(game_id=first[0].game_id).count() == 1
    observation = db.query(models.RoundObservation).filter_by(parse_status="valid").all()
    assert any("source_round_missing" in o.raw_payload["payload"].get("parse_errors", []) for o in observation)


@pytest.mark.parametrize("failure", ["empty", "truncated", "failed", "changed"])
def test_bad_snapshot_cannot_delete_or_mutate_accepted(db, sheets, monkeypatch, failure):
    from app.services.round_identity import sync_round_snapshot

    snapshot = sheet.fetch_round_snapshot("fixture:tab:2026", season_year=2026)
    first = sync_round_snapshot(db, snapshot)[0]
    if failure == "empty":
        sheets[0].clear()
        snapshot = sheet.fetch_round_snapshot(snapshot.scope, season_year=2026)
    elif failure == "truncated":
        monkeypatch.setattr(sheet, "_sheets_api_get", lambda *_: {"range": "Details!A2:H5000", "values": []})
        snapshot = sheet.fetch_round_snapshot(snapshot.scope, season_year=2026)
    elif failure == "failed":
        monkeypatch.setattr(sheet, "_sheets_api_get", lambda *_: None)
        snapshot = sheet.fetch_round_snapshot(snapshot.scope, season_year=2026)
    else:
        sheets[0][0][3] = 42
    assert all(o.status == "held" for o in sync_round_snapshot(db, snapshot))
    assert db.query(models.GameRecord).count() == 1
    assert db.query(models.GameRecord).one().game_id == first.game_id
    assert db.query(models.GamePlayerResult).one().total_earnings is None


def test_expired_source_worker_cannot_commit(db, sheets, monkeypatch):
    from app.services import round_reconciliation, round_source_lease
    from app.services.round_identity import sync_round_snapshot

    original = round_reconciliation.observe_round

    def expired(tx, *args, **kwargs):
        outcome = original(tx, *args, **kwargs)
        tx.query(models.RoundIdentityLease).one().expires_at = "2000-01-01T00:00:00+00:00"
        tx.flush()
        return outcome

    monkeypatch.setattr(round_reconciliation, "observe_round", expired)
    snapshot = sheet.fetch_round_snapshot("fixture:tab:2026", season_year=2026)
    assert sync_round_snapshot(db, snapshot)[0].status == "held"
    assert db.query(models.GameRecord).count() == 0
    assert db.query(models.RoundObservation).count() == 0
    assert db.query(models.RoundDelivery).count() == 0
    assert round_source_lease.SourceLeaseLostError


def test_all_refresh_callers_share_one_boundary_and_redact(db, monkeypatch):
    from app.routers.spreadsheet_sync import trigger_legacy_rounds_sync
    from app.routers.unified_data import sync_sheets_to_db
    from app.services.email_scheduler import EmailScheduler

    calls = []
    health = {"success": False, "status": "held", "held": 2, "synced": 0}
    monkeypatch.setattr(sheet, "refresh_round_history", lambda session: calls.append(session) or health)
    scheduler = EmailScheduler()
    monkeypatch.setattr(scheduler, "_get_db", lambda: db)
    assert trigger_legacy_rounds_sync(db) == health
    assert sync_sheets_to_db(db) == health
    assert scheduler._sync_legacy_rounds() == health
    assert calls == [db, db, db]


def test_refresh_health_never_returns_private_source_rows(db, sheets, monkeypatch):
    monkeypatch.setattr(sheet, "PRIMARY_SHEET_ID", "fixture")
    monkeypatch.setattr(sheet, "PRIMARY_SHEET_TAB_GID", "tab")
    result = sheet.refresh_round_history(db)
    assert result["complete"]
    assert "Avery" not in str(result) and "rows" not in result


def test_production_reviewed_manifest_supplies_stable_slots_without_assuming_g_h(db, sheets):
    from app.services.round_identity import sync_round_snapshot

    scope = "workbook:tab:2026"
    snapshot = sheet.fetch_round_snapshot(scope, season_year=2026)
    item = snapshot.rounds[0]
    db.add(
        models.AppConfig(
            name="round_source_reviews",
            value={
                scope: {
                    "fingerprint": snapshot.fingerprint,
                    "reviewer_profile_id": 7,
                    "round_bindings": {
                        item.observation_key: {"round_token": "reviewed-round", "participant_ids": ["reviewed-slot"]}
                    },
                }
            },
        )
    )
    db.commit()
    first = sync_round_snapshot(db, snapshot)[0]
    assert first.game_id and first.status == "accepted"
    assert db.query(models.RoundSource).filter_by(round_token="reviewed-round").one().game_id == first.game_id
    assert db.query(models.GamePlayerResult).one().participant_id == "reviewed-slot"
    assert sync_round_snapshot(db, snapshot)[0].game_id == first.game_id
    assert db.query(models.GameRecord).count() == 1


def test_source_lease_rejects_concurrent_refresh_and_generation_increases(db):
    from app.services.round_source_lease import SourceLeaseLostError, source_lease

    with (
        source_lease(db.get_bind(), "fixture:tab:2026") as first,
        pytest.raises(SourceLeaseLostError, match="already running"),
        source_lease(db.get_bind(), "fixture:tab:2026"),
    ):
        pytest.fail("second owner admitted")
    with source_lease(db.get_bind(), "fixture:tab:2026") as second:
        assert second[2] > first[2]
