"""Physical PostgreSQL correction races, audit rollback and fresh readback."""

from types import SimpleNamespace

import pytest
from sqlalchemy import select, text

from app import models
from app.routers import admin
from app.services.auth_service import get_current_user
from tests.unit.participant_audit_guard_support import MUTATIONS, assert_audit_guard
from tests.unit.round_identity_postgres_support import identity_pg, race

GAME = "a93b258a-3c0e-4531-b0ff-cab5a22d5073"
PATH = "/admin/participant-results/20"


def setup_api(pg):
    pg.app.include_router(admin.router)
    pg.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=8)
    with pg.sessions() as db:
        db.get(models.AppConfig, "round_identity").value = {"mode": "legacy", "epoch": 4}
        db.add_all(
            [
                models.PlayerProfile(id=20, name="Stuart Gano", is_active=1),
                models.PlayerProfile(id=21, name="Kevin Gent", is_active=1),
                models.PlayerProfile(id=22, name="Other", is_active=1),
                models.GameRecord(id=10, game_id=GAME, final_scores={"untouched": -257}),
                models.GamePlayerResult(
                    id=20, game_record_id=10, player_name="Stuart Gano", player_profile_id=21, total_earnings=-257
                ),
            ]
        )
        db.commit()


def request(pg, key="correction-race", replacement=20):
    preview = pg.client.get(PATH, params={"replacement_profile_id": replacement})
    assert preview.status_code == 200, preview.text
    view = preview.json()
    return {
        "replacement_profile_id": replacement,
        "expected_old_profile_id": 21,
        "expected_epoch": 4,
        "expected_snapshot": view["snapshot"],
        "reason": "Synthetic verified correction",
        "confirmed": True,
        "request_key": key,
    }


def test_same_request_concurrent_retry_is_one_audit(identity_pg):
    pg = identity_pg
    setup_api(pg)
    body = request(pg)
    before = pg.snapshot()
    responses = race(*[lambda: pg.client.post(PATH + "/correct", json=body) for _ in range(2)])
    assert [r.status_code for r in responses] == [200, 200], [r.text for r in responses]
    assert responses[0].json()["audit_id"] == responses[1].json()["audit_id"]
    with pg.sessions() as db:
        after = pg.snapshot()
        assert after["game_player_results"] == [{**before["game_player_results"][0], "player_profile_id": 20}]
        assert {k: v for k, v in after.items() if k != "game_player_results"} == {
            k: v for k, v in before.items() if k != "game_player_results"
        }
        audit = db.execute(select(models.ParticipantCorrectionAudit.__table__)).mappings().one()
        assert (audit["actor_profile_id"], audit["old_profile_id"], audit["new_profile_id"]) == (8, 21, 20)
        assert audit["before"]["total_earnings"] == audit["after"]["total_earnings"] == -257


def test_competing_previews_one_wins_other_is_stale(identity_pg):
    pg = identity_pg
    setup_api(pg)
    a, b = request(pg, "first", 20), request(pg, "second", 22)
    responses = race(
        lambda: pg.client.post(PATH + "/correct", json=a), lambda: pg.client.post(PATH + "/correct", json=b)
    )
    assert sorted(r.status_code for r in responses) == [200, 409], [r.text for r in responses]
    with pg.sessions() as db:
        assert db.query(models.ParticipantCorrectionAudit).count() == 1
        assert db.get(models.GamePlayerResult, 20).player_profile_id in (20, 22)
        assert db.get(models.GameRecord, 10).game_id == GAME


@pytest.mark.parametrize("operation", MUTATIONS + ["TRUNCATE TABLE participant_correction_audits CASCADE"])
def test_fresh_postgres_audit_rejects_physical_mutation(identity_pg, operation):
    pg = identity_pg
    setup_api(pg)
    response = pg.client.post(PATH + "/correct", json=request(pg))
    assert response.status_code == 200, response.text
    assert_audit_guard(pg.sessions, operation)


def test_production_audit_ddl_is_idempotent_and_usable(identity_pg):
    from pathlib import Path

    from app.migrations_runner import _statements

    pg = identity_pg
    with pg.engine.begin() as conn:
        conn.execute(text("DROP TABLE participant_correction_audits"))
        ddl = Path("migrations/zz_20261029_participant_correction_audit_postgres.sql").read_text()
        for _ in range(2):
            for statement in _statements(ddl):
                conn.execute(text(statement))
    setup_api(pg)
    response = pg.client.post(PATH + "/correct", json=request(pg))
    assert response.status_code == 200, response.text
    with pg.sessions() as db:
        audit = db.query(models.ParticipantCorrectionAudit).one()
        assert audit.game_id == GAME
        assert audit.after["player_profile_id"] == 20
    # Upgrade an already-populated audit table; original migration may be recorded.
    guards = Path("migrations/zz_20261029_participant_correction_guards_postgres.sql").read_text()
    for _ in range(2):
        with pg.engine.begin() as conn:
            for statement in _statements(guards):
                conn.execute(text(statement))
        for operation in MUTATIONS + ["TRUNCATE TABLE participant_correction_audits CASCADE"]:
            assert_audit_guard(pg.sessions, operation)


def test_guard_upgrade_via_migration_runner_preserves_existing_audit(identity_pg, tmp_path, monkeypatch):
    from pathlib import Path

    from app import migrations_runner

    pg = identity_pg
    setup_api(pg)
    assert pg.client.post(PATH + "/correct", json=request(pg)).status_code == 200
    filename = "zz_20261029_participant_correction_guards_postgres.sql"
    (tmp_path / filename).write_text((Path("migrations") / filename).read_text())
    monkeypatch.setattr(migrations_runner, "MIGRATIONS_DIR", tmp_path)
    with pg.engine.begin() as conn:
        conn.execute(text("DROP TRIGGER immutable_participant_audit ON participant_correction_audits"))
        conn.execute(text("CREATE TABLE schema_migrations (filename VARCHAR PRIMARY KEY, applied_at VARCHAR)"))
        conn.execute(
            text(
                "INSERT INTO schema_migrations VALUES ('zz_20261029_participant_correction_audit_postgres.sql', 'before')"
            )
        )
    assert migrations_runner.run_sql_migrations(pg.engine) == {"applied": [filename], "failed": []}
    assert migrations_runner.run_sql_migrations(pg.engine) == {"applied": [], "failed": []}
    for operation in MUTATIONS + ["TRUNCATE TABLE participant_correction_audits CASCADE"]:
        assert_audit_guard(pg.sessions, operation)


def test_physical_audit_insert_failure_rolls_back_entire_transaction(identity_pg):
    pg = identity_pg
    setup_api(pg)
    body = request(pg)
    with pg.engine.begin() as conn:
        conn.execute(
            text(
                "CREATE FUNCTION reject_participant_audit() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'synthetic audit failure'; END $$"
            )
        )
        conn.execute(
            text(
                "CREATE TRIGGER reject_participant_audit BEFORE INSERT ON participant_correction_audits FOR EACH ROW EXECUTE FUNCTION reject_participant_audit()"
            )
        )
    before = pg.snapshot()
    response = pg.client.post(PATH + "/correct", json=body)
    assert response.status_code == 500
    assert pg.snapshot() == before
    with pg.sessions() as db:
        assert db.query(models.ParticipantCorrectionAudit).count() == 0
