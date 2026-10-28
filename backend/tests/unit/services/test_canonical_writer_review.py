"""Deterministic cutover interleavings at real legacy caller transaction boundaries."""

from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import models
from app.schemas import GamePlayerResultCreate
from app.services.player_service import PlayerService
from tests.unit.services.test_canonical_round_statistics import canonical_history, save


def set_mode(db, mode):
    row = db.get(models.AppConfig, "round_identity")
    row.value = {"mode": mode, "season": 2026}
    db.commit()


def test_result_writer_locks_before_branch_selection(canonical_history, monkeypatch):
    import app.services.round_writes as writes

    db = canonical_history
    save(db, "complete", [8, -8])
    record = db.query(models.GameRecord).one()
    set_mode(db, "legacy")
    original = writes.acquire_reconciliation_lock
    calls = []

    def cutover_before_lock(session):
        if not calls:
            with Session(db.bind) as cutover:
                set_mode(cutover, "canonical")
        calls.append(True)
        original(session)

    monkeypatch.setattr(writes, "acquire_reconciliation_lock", cutover_before_lock)
    with pytest.raises(ValueError, match="canonical final-result writer"):
        PlayerService(db).record_game_result(
            GamePlayerResultCreate(
                game_record_id=record.id,
                player_profile_id=1,
                player_name="Avery",
                total_earnings=999,
                final_position=1,
                holes_played=18,
                holes_won=10,
            )
        )
    assert calls
    db.rollback()
    assert db.query(models.GamePlayerResult).count() == 2
    assert db.query(models.PlayerStatistics).count() == 0


@pytest.mark.parametrize("boundary", ["profile_commit", "success_commit", "failure_rollback"])
def test_csv_revalidates_after_each_transaction_end(canonical_history, monkeypatch, boundary):
    from app.database import get_db
    from app.main import app
    from app.routers import sheet_integration as route

    db = canonical_history
    db.add(models.PlayerProfile(id=2, name="Blair", created_at="2026-01-01"))
    db.add_all([models.PlayerStatistics(player_id=i, games_played=3, total_earnings=17) for i in (1, 2)])
    db.commit()
    set_mode(db, "legacy")
    if db.bind.dialect.name == "postgresql":
        from sqlalchemy import text

        db.execute(text("SELECT setval(pg_get_serial_sequence('player_profiles', 'id'), 2)"))
        db.commit()
    first = "New Player" if boundary == "profile_commit" else "Avery"
    response = Mock(text=f"Member,Quarters\n{first},999\nBlair,777")
    response.raise_for_status = Mock()
    transport = AsyncMock()
    transport.get.return_value = response
    transport.__aenter__.return_value = transport
    monkeypatch.setattr(route.httpx, "AsyncClient", lambda **kwargs: transport)
    monkeypatch.setattr(route.sheet_sync_cache, "get", lambda key: None)
    real_commit, real_rollback = db.commit, db.rollback
    transitions = []

    def switch():
        if not transitions:
            with Session(db.bind) as cutover:
                set_mode(cutover, "canonical")
            transitions.append(boundary)

    def commit():
        real_commit()
        if boundary != "failure_rollback":
            switch()

    def rollback():
        real_rollback()
        if boundary == "failure_rollback":
            switch()

    monkeypatch.setattr(db, "commit", commit)
    monkeypatch.setattr(db, "rollback", rollback)
    if boundary == "failure_rollback":

        def fail_first_commit():
            raise RuntimeError("controlled per-player failure")

        monkeypatch.setattr(db, "commit", fail_first_commit)

    def override():
        yield db

    app.dependency_overrides[get_db] = override
    try:
        with TestClient(app) as client:
            result = client.post(
                "/sheet-integration/sync-wgp-sheet",
                json={"csv_url": "https://synthetic.invalid/input.csv"},
                headers={"X-Scheduled-Job": "true"},
            )
        assert result.status_code == 409, result.text
        assert transitions == [boundary]
        db.expire_all()
        assert db.query(models.PlayerStatistics).filter_by(player_id=2).one().total_earnings == 17
        if boundary == "profile_commit":
            new = db.query(models.PlayerProfile).filter_by(name=first).one()
            assert db.query(models.PlayerStatistics).filter_by(player_id=new.id).one().total_earnings == 0
        elif boundary == "failure_rollback":
            assert db.query(models.PlayerStatistics).filter_by(player_id=1).one().total_earnings == 17
        else:
            assert db.query(models.PlayerStatistics).filter_by(player_id=1).one().total_earnings == 999
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_live_ghin_and_player_fallback_publish_shared_coverage(canonical_history, monkeypatch):
    import app.services.canonical_round_reads as reads
    from app.database import get_db
    from app.main import app
    from app.services.ghin_service import GHINService

    db = canonical_history
    save(db, "complete", [8, -8])
    save(db, "partial", [2, None])

    def override():
        yield db

    app.dependency_overrides[get_db] = override
    try:
        with TestClient(app) as client:
            response = client.get("/leaderboard/ghin-enhanced")
        assert response.status_code == 200
        payload = response.json()
        entry = payload["leaderboard"][0] if isinstance(payload, dict) else payload[0]
        for result in (
            entry,
            PlayerService(db).get_leaderboard()[0].model_dump(),
            PlayerService(db).get_player_statistics(1).model_dump(),
        ):
            assert result["known_participation_count"] == 2
            assert result["scored_round_count"] == result["games_played"] == 1
            assert result["incomplete_round_count"] == 1
        original = reads.profile_statistics_pairs
        calls = []

        def fail_ghin_once(*a, **kw):
            if not calls:
                calls.append(True)
                raise RuntimeError("controlled GHIN path failure")
            return original(*a, **kw)

        monkeypatch.setattr(reads, "profile_statistics_pairs", fail_ghin_once)
        fallback = GHINService(db).get_leaderboard_with_ghin_data()[0]
        assert fallback["known_participation_count"] == 2
        assert fallback["scored_round_count"] == fallback["incomplete_round_count"] == 1
    finally:
        app.dependency_overrides.pop(get_db, None)
