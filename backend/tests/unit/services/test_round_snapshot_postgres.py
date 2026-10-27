"""Physical PostgreSQL refresh serialization and commit-fence tests (local only)."""

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from app import models
from app.services import spreadsheet_sync_service as sheet


@pytest.fixture
def engine(monkeypatch):
    raw = os.environ.get("SCORE_SAVE_TEST_DATABASE_URL")
    if not raw:
        pytest.skip("Requires disposable localhost PostgreSQL *_test database")
    url = make_url(raw)
    assert url.host in {"127.0.0.1", "localhost", "::1"} and url.database.endswith("_test") and not url.query
    schema = "snapshot_" + uuid4().hex
    admin = create_engine(url.set(drivername="postgresql+psycopg2"), poolclass=NullPool)
    with admin.begin() as tx:
        tx.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(
        url.set(drivername="postgresql+psycopg2"),
        poolclass=NullPool,
        connect_args={"options": f"-csearch_path={schema} -cstatement_timeout=10000"},
    )
    models.Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(models.AppConfig(name="round_identity", value={"mode": "canonical", "epoch": 2, "season": 2026}))
        db.commit()
    monkeypatch.setattr(sheet, "PRIMARY_SHEET_ID", "fixture")
    monkeypatch.setattr(sheet, "PRIMARY_SHEET_TAB_GID", "tab")
    monkeypatch.setattr(
        sheet,
        "_sheets_metadata_get",
        lambda *_: {
            "sheets": [
                {
                    "properties": {
                        "sheetId": "tab",
                        "title": "Details",
                        "gridProperties": {"rowCount": 2, "columnCount": 8},
                    }
                }
            ],
            "fixture_token_contract": True,
        },
    )
    monkeypatch.setattr(
        sheet,
        "_sheets_api_get",
        lambda _, range_: {
            "range": range_,
            "majorDimension": "ROWS",
            "values": [["6-Oct", "B", "Private fixture", "0", "", "", "r1", "s1"]],
        },
    )
    try:
        yield engine
    finally:
        engine.dispose()
        with admin.begin() as tx:
            tx.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


def test_concurrent_refresh_endpoints_one_uuid_and_physical_readback(engine, monkeypatch):
    from app.routers.spreadsheet_sync import trigger_legacy_rounds_sync
    from app.routers.unified_data import sync_sheets_to_db

    entered, release = Event(), Event()
    original = sheet.fetch_round_snapshot
    counts = {}

    def fetch(*args, **kwargs):
        from threading import get_ident

        tid = get_ident()
        counts[tid] = counts.get(tid, 0) + 1
        if counts[tid] == 2:
            entered.set()
            assert release.wait(10)
        return original(*args, **kwargs)

    monkeypatch.setattr(sheet, "fetch_round_snapshot", fetch)

    def call(endpoint):
        with Session(engine) as db:
            return endpoint(db)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(call, trigger_legacy_rounds_sync)
        assert entered.wait(10)
        try:
            second = executor.submit(call, sync_sheets_to_db).result(timeout=10)
            assert second["status"] == "held"
        finally:
            release.set()
        assert first.result(timeout=10)["success"]
    with Session(engine) as fresh:
        assert fresh.query(models.GameStateModel).count() == 1
        assert fresh.query(models.GameRecord).count() == 1
        assert fresh.query(models.GamePlayerResult).one().total_earnings == 0
        game_id = fresh.query(models.RoundSource).one().game_id
    assert call(sync_sheets_to_db)["success"]
    with Session(engine) as fresh:
        assert fresh.query(models.RoundSource).one().game_id == game_id
        assert fresh.query(models.RoundIdentityLease).one().epoch == 2


@pytest.mark.parametrize("mode", ["canonical", "paused", "legacy"])
def test_legacy_config_transition_during_fetch_holds_cache(engine, monkeypatch, mode):
    from types import SimpleNamespace

    from app.services import unified_data_service

    with Session(engine) as db:
        db.get(models.AppConfig, "round_identity").value = {"mode": "legacy", "epoch": 2}
        db.add(models.LegacyRound(date="2026-01-01", member="Keep", score=3, source="primary_sheet"))
        db.commit()

    def fetch(**_):
        with Session(engine) as other:
            other.get(models.AppConfig, "round_identity").value = {"mode": mode, "epoch": 3}
            other.commit()
        return [
            SimpleNamespace(
                date_sortable="2026-10-06",
                group="B",
                member="New",
                score=0,
                location="",
                duration=None,
                source="primary_sheet",
            )
        ]

    monkeypatch.setattr(
        unified_data_service, "get_unified_data_service", lambda **_: SimpleNamespace(get_all_rounds=fetch)
    )
    with Session(engine) as db:
        assert sheet.refresh_round_history(db)["status"] == "held"
    with Session(engine) as fresh:
        assert fresh.query(models.LegacyRound).one().member == "Keep"
        assert fresh.query(models.GameRecord).count() == 0


def test_legacy_config_lock_covers_mutation_and_failure_rolls_back(engine, monkeypatch):
    from types import SimpleNamespace

    from sqlalchemy import event
    from sqlalchemy.exc import OperationalError

    from app.services import unified_data_service

    with Session(engine) as db:
        db.get(models.AppConfig, "round_identity").value = {"mode": "legacy", "epoch": 2}
        db.add(models.LegacyRound(date="2026-01-01", member="Keep", score=3, source="primary_sheet"))
        db.commit()
    row = SimpleNamespace(
        date_sortable="2026-10-06", group="B", member="New", score=0, location="", duration=None, source="primary_sheet"
    )
    monkeypatch.setattr(
        unified_data_service, "get_unified_data_service", lambda **_: SimpleNamespace(get_all_rounds=lambda **_: [row])
    )
    locked = []

    def cutover():
        with Session(engine) as other:
            other.execute(text("SET LOCAL lock_timeout = '100ms'"))
            with pytest.raises(OperationalError):
                other.execute(
                    models.AppConfig.__table__.update()
                    .where(models.AppConfig.name == "round_identity")
                    .values(value={"mode": "canonical", "epoch": 3})
                )
            other.rollback()
        locked.append(True)

    def fail_insert(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith("INSERT INTO legacy_rounds"):
            with ThreadPoolExecutor(max_workers=1) as executor:
                executor.submit(cutover).result(timeout=5)
            raise RuntimeError("injected cache insert failure after deletion")

    event.listen(engine, "before_cursor_execute", fail_insert)
    try:
        with Session(engine) as db:
            assert sheet.refresh_round_history(db)["status"] == "held"
    finally:
        event.remove(engine, "before_cursor_execute", fail_insert)
    assert locked == [True]
    with Session(engine) as fresh:
        assert fresh.query(models.LegacyRound).one().member == "Keep"
        assert fresh.get(models.AppConfig, "round_identity").value == {"mode": "legacy", "epoch": 2}
        assert fresh.query(models.GameRecord).count() == 0


def test_publication_marker_tracks_accepted_revision_and_rolls_back_with_results(engine, monkeypatch):
    from app.services import round_source_lease
    from app.services.round_identity import sync_round_snapshot

    # First accepted round has unknown earnings; a reviewed zero can fill it.
    rows = [["6-Oct", "B", "Private fixture", "", "", "", "r1", "s1"]]
    monkeypatch.setattr(
        sheet, "_sheets_api_get", lambda _, range_: {"range": range_, "majorDimension": "ROWS", "values": rows}
    )
    first = sheet.fetch_round_snapshot("fixture:tab:2026", season_year=2026)
    with Session(engine) as db:
        assert sync_round_snapshot(db, first)[0].status == "accepted"
    with Session(engine) as db:
        source = db.query(models.RoundSource).one()
        marker = source.binding_evidence["sheet_publication"]
        assert marker["snapshot_fingerprint"] == first.fingerprint
        assert marker["accepted_revision"] == db.query(models.GameStateModel).one().revision
    rows[0][3] = 0
    second = sheet.fetch_round_snapshot(first.scope, season_year=2026)
    with Session(engine) as db:
        db.add(
            models.AppConfig(
                name="round_source_reviews",
                value={first.scope: {"fingerprint": second.fingerprint, "reviewer_profile_id": 7}},
            )
        )
        db.commit()
    original = round_source_lease.fence
    calls = []

    def fail_final_fence(db, lease):
        calls.append(True)
        if len(calls) == 2:
            db.flush()
            assert (
                db.query(models.RoundSource).one().binding_evidence["sheet_publication"]["snapshot_fingerprint"]
                == second.fingerprint
            )
            raise round_source_lease.SourceLeaseLostError("injected precommit lease loss")
        return original(db, lease)

    monkeypatch.setattr(round_source_lease, "fence", fail_final_fence)
    with Session(engine) as db:
        assert sync_round_snapshot(db, second)[0].status == "held"
    with Session(engine) as db:
        assert db.query(models.RoundSource).one().binding_evidence["sheet_publication"] == marker
        assert db.query(models.GamePlayerResult).one().total_earnings is None
        assert db.query(models.RoundObservation).count() == 1
    monkeypatch.setattr(round_source_lease, "fence", original)
    with Session(engine) as db:
        assert sync_round_snapshot(db, second)[0].status == "accepted"
    with Session(engine) as db:
        assert db.query(models.GamePlayerResult).one().total_earnings == 0
        assert (
            db.query(models.RoundSource).one().binding_evidence["sheet_publication"]["snapshot_fingerprint"]
            == second.fingerprint
        )


def test_writer_epoch_change_during_read_aborts_before_mutation(engine, monkeypatch):
    from app.services.round_identity import sync_round_snapshot

    snapshot = sheet.fetch_round_snapshot("fixture:tab:2026", season_year=2026)
    original = sheet.fetch_round_snapshot

    def changed(*args, **kwargs):
        with Session(engine) as other:
            config = other.get(models.AppConfig, "round_identity")
            config.value = {**config.value, "epoch": 3}
            other.commit()
        return original(*args, **kwargs)

    monkeypatch.setattr(sheet, "fetch_round_snapshot", changed)
    with Session(engine) as db:
        assert sync_round_snapshot(db, snapshot)[0].status == "held"
    with Session(engine) as fresh:
        assert fresh.query(models.GameRecord).count() == 0
        assert fresh.query(models.RoundObservation).count() == 0
        assert fresh.query(models.RoundDelivery).count() == 0
