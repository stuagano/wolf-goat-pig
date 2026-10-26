"""A correction to a finished round must be durable, atomic, and provable.

These tests run against real PostgreSQL with production session defaults, and
verify every claim from a separate connection — the only way to catch a save
that reports success while the rows never changed.
"""

import json
import logging

import pytest
from sqlalchemy import event, text

from tests.unit.score_save_postgres_support import (
    correction_payload,
    score_pg,
    snapshot,
)

CORRECTED_STANDINGS = {"p1": -6.0, "p2": 6.0, "p3": 0.0, "p4": 0.0}


def _save(harness, payload, **kwargs):
    return harness.client.post(f"/games/{harness.game_id}/scores", json=payload, **kwargs)


def _hole7(rows):
    return {row["player_id"]: row["quarters"] for row in rows["hole_events"] if row["hole_number"] == 7}


# ── Durability: the correction must survive on its own connection ─────────────


def test_correction_is_durable_and_readable_from_a_separate_connection(score_pg):
    before = snapshot(score_pg)

    response = _save(score_pg, correction_payload())

    assert response.status_code == 200, response.text
    assert response.json()["standings"] == CORRECTED_STANDINGS
    after = snapshot(score_pg)

    assert _hole7(after) == {"p1": -23.0, "p2": 23.0, "p3": 0.0, "p4": 0.0}
    assert len(after["hole_events"]) == 72
    assert {row["id"] for row in after["hole_events"]} == {row["id"] for row in before["hole_events"]}
    assert after["game_state"][0]["state"]["standings"] == CORRECTED_STANDINGS
    assert {p["id"]: p["total_points"] for p in after["game_state"][0]["state"]["players"]} == CORRECTED_STANDINGS
    assert after["game_state"][0]["state"]["current_hole"] == 19
    assert len(after["game_state"][0]["state"]["hole_history"]) == 18

    assert [row["id"] for row in after["game_records"]] == [row["id"] for row in before["game_records"]]
    assert after["game_records"][0]["final_scores"] == CORRECTED_STANDINGS
    assert after["game_records"][0]["created_at"] == before["game_records"][0]["created_at"]
    assert after["game_records"][0]["completed_at"] == before["game_records"][0]["completed_at"]
    assert after["game_records"][0]["total_holes_played"] == 18
    assert after["game_state"][0]["game_status"] == "completed"
    assert after["game_state"][0]["created_at"] == before["game_state"][0]["created_at"]
    fresh_get = score_pg.client.get(f"/games/{score_pg.game_id}/state")
    assert fresh_get.status_code == 200
    assert fresh_get.json() == after["game_state"][0]["state"]
    assert len({id(session) for session in score_pg.sessions}) == len(score_pg.sessions)
    assert len(set(score_pg.request_pids)) == len(score_pg.request_pids)
    for hole in correction_payload()["holes"]:
        entry = next(h for h in fresh_get.json()["hole_history"] if h["hole"] == hole["hole_number"])
        assert entry["points_delta"] == hole["quarters"]
        assert entry["gross_scores"] == hole["gross_scores"]
        for row in after["hole_events"]:
            if row["hole_number"] == hole["hole_number"]:
                assert row["quarters"] == hole["quarters"][row["player_id"]]
                assert row["score"] == hole["gross_scores"][row["player_id"]]
                assert row["recorded_at"] >= before["hole_events"][0]["recorded_at"]
    assert len(after["game_player_results"]) == 4
    assert [row["id"] for row in after["game_player_results"]] == [row["id"] for row in before["game_player_results"]]
    assert {row["player_name"]: row["total_earnings"] for row in after["game_player_results"]} == {
        "private-player-1": -6.0,
        "private-player-2": 6.0,
        "private-player-3": 0.0,
        "private-player-4": 0.0,
    }
    assert {row["player_name"]: row["final_position"] for row in after["game_player_results"]} == {
        "private-player-2": 1,
        "private-player-3": 2,
        "private-player-4": 3,
        "private-player-1": 4,
    }
    corrected = next(r for r in after["game_player_results"] if r["player_name"] == "private-player-1")
    assert next(h for h in corrected["hole_scores"] if h["hole"] == 7)["quarters"] == -23.0
    assert corrected["holes_won"] == 17
    for result, old in zip(after["game_player_results"], before["game_player_results"], strict=True):
        assert result["created_at"] == old["created_at"]
        assert result["game_record_id"] == after["game_records"][0]["id"]
        assert len(result["hole_scores"]) == 18
        pid = f"p{result['player_profile_id']}"
        assert result["total_earnings"] == sum(h["quarters"] for h in result["hole_scores"])
        for hole in result["hole_scores"]:
            expected = correction_payload()["holes"][hole["hole"] - 1]
            assert hole["quarters"] == expected["quarters"][pid]
            assert hole["gross_score"] == expected["gross_scores"][pid]


def test_repeating_the_same_correction_changes_nothing(score_pg):
    assert _save(score_pg, correction_payload()).status_code == 200
    first = snapshot(score_pg)

    assert _save(score_pg, correction_payload()).status_code == 200
    second = snapshot(score_pg)

    for table in ("hole_events", "game_records", "game_player_results"):
        assert [row["id"] for row in second[table]] == [row["id"] for row in first[table]]
    assert second["game_records"] == first["game_records"]
    assert second["game_player_results"] == first["game_player_results"]
    assert second["game_state"][0]["state"] == first["game_state"][0]["state"]


# ── Atomicity: a mid-transaction failure must leave the round untouched ───────


def test_failure_after_earlier_writes_rolls_back_and_the_next_save_succeeds(score_pg, caplog):
    before = snapshot(score_pg)
    executed = []
    caplog.set_level(logging.INFO, logger="app.observability.score_save")

    def record_write(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("UPDATE"):
            executed.append(statement.split()[1])

    # A PostgreSQL trigger fails the last player's UPDATE, after earlier flushes
    # have really reached the server. No mocked commit/flush or outer transaction.
    with score_pg.engine.begin() as conn:
        conn.execute(
            text("""
            CREATE FUNCTION fail_result_update() RETURNS trigger LANGUAGE plpgsql AS $$
            BEGIN
                IF NEW.player_profile_id = 1 THEN
                    RAISE EXCEPTION 'private injected result failure';
                END IF;
                RETURN NEW;
            END $$
        """)
        )
        conn.execute(
            text("""
            CREATE TRIGGER fail_result_update BEFORE UPDATE ON game_player_results
            FOR EACH ROW EXECUTE FUNCTION fail_result_update()
        """)
        )
    event.listen(score_pg.engine, "after_cursor_execute", record_write)
    try:
        response = _save(score_pg, correction_payload(), headers={"X-Request-ID": "rollback-save-123"})
    finally:
        event.remove(score_pg.engine, "after_cursor_execute", record_write)
        with score_pg.engine.begin() as conn:
            conn.execute(text("DROP TRIGGER fail_result_update ON game_player_results"))
            conn.execute(text("DROP FUNCTION fail_result_update()"))

    assert response.status_code == 500
    assert {"game_state", "hole_events", "game_records", "game_player_results"}.issubset(executed)
    assert score_pg.commits == []
    assert snapshot(score_pg) == before
    state = score_pg.client.get(f"/games/{score_pg.game_id}/state").json()
    assert state == before["game_state"][0]["state"]
    events = _events(caplog)
    assert [e["event"] for e in events] == ["score_save_attempt", "score_save_failed"]
    assert all(e["request_id"] == "rollback-save-123" for e in events)
    assert events[-1]["status_code"] == 500
    assert response.headers["X-Request-ID"] == "rollback-save-123"
    _assert_safe_diagnostics(caplog)

    assert _save(score_pg, correction_payload()).status_code == 200
    assert _hole7(snapshot(score_pg)) == {"p1": -23.0, "p2": 23.0, "p3": 0.0, "p4": 0.0}


def test_no_orm_work_happens_after_the_commit(score_pg):
    """A post-commit refresh re-opens a transaction the response never proves."""
    assert _save(score_pg, correction_payload()).status_code == 200

    assert score_pg.postcommit_queries == []
    assert score_pg.commits


# ── Authorization: real round-membership rules, only identity is injected ─────


def test_round_member_may_correct_the_card(score_pg):
    score_pg.identity.id = 3  # p3's linked profile

    assert _save(score_pg, correction_payload()).status_code == 200
    assert _hole7(snapshot(score_pg))["p1"] == -23.0


def test_admin_outside_the_round_may_correct_the_card(score_pg):
    score_pg.identity.id = 4242
    score_pg.identity.admin_granted = 1

    assert _save(score_pg, correction_payload()).status_code == 200
    assert _hole7(snapshot(score_pg))["p1"] == -23.0


def test_outsider_is_denied_and_the_card_is_unchanged(score_pg):
    before = snapshot(score_pg)
    score_pg.identity.id = 4242

    response = _save(score_pg, correction_payload())

    assert response.status_code == 403
    assert snapshot(score_pg) == before


# ── Validation: a rejected correction must not half-apply ────────────────────


@pytest.mark.parametrize(
    ("mutate", "status"),
    [
        (lambda p: p["holes"].pop(), 400),  # 17 holes on a completed round
        (lambda p: p["holes"][17].update({"hole_number": 17}), 400),  # 18 entries, missing hole 18
        (lambda p: p["holes"][17].update({"hole_number": 19}), 400),  # 18 entries, invalid hole
        (lambda p: p["holes"][6]["quarters"].update({"p1": -22}), 400),  # non-zero-sum hole
        (lambda p: p["holes"][6]["quarters"].pop("p4"), 400),  # missing roster player
        (lambda p: p["holes"][6].update({"quarters": {"p1": "x", "p2": 0, "p3": 0, "p4": 0}}), 422),
    ],
    ids=[
        "incomplete-round",
        "duplicate-hole",
        "out-of-range-hole",
        "non-zero-sum",
        "missing-player",
        "unparseable-quarters",
    ],
)
def test_invalid_corrections_are_rejected_without_touching_the_round(score_pg, mutate, status):
    before = snapshot(score_pg)
    payload = correction_payload()
    mutate(payload)

    response = _save(score_pg, payload)

    assert response.status_code == status, response.text
    assert snapshot(score_pg) == before


# ── Diagnostics: success is logged only when the commit really happened ───────


def _events(caplog):
    return [json.loads(record.message) for record in caplog.records if record.name == "app.observability.score_save"]


def _assert_safe_diagnostics(caplog):
    for private_value in ("private-player", "private-score-note", "private injected result failure", "Bearer"):
        assert private_value not in caplog.text
    for entry in _events(caplog):
        assert set(entry).issubset({"event", "request_id", "status_code"})


def test_committed_save_is_logged_as_committed_with_the_request_id(score_pg, caplog):
    caplog.set_level(logging.INFO, logger="app.observability.score_save")

    response = _save(score_pg, correction_payload(), headers={"X-Request-ID": "score-save-abc123"})

    assert response.status_code == 200
    events = _events(caplog)
    assert [e["event"] for e in events] == ["score_save_attempt", "score_save_committed"]
    assert all(e["request_id"] == "score-save-abc123" for e in events)
    assert response.headers["X-Request-ID"] == "score-save-abc123"
    committed = next(record for record in caplog.records if '"score_save_committed"' in record.message)
    assert len(score_pg.commits) == 1
    assert committed.created >= score_pg.commits[0]
    assert score_pg.postcommit_queries == []
    _assert_safe_diagnostics(caplog)


def test_rejected_save_is_never_logged_as_committed(score_pg, caplog):
    caplog.set_level(logging.INFO, logger="app.observability.score_save")
    payload = correction_payload()
    payload["holes"][6]["quarters"].update({"p1": -22})

    response = _save(score_pg, payload)

    assert response.status_code == 400
    events = _events(caplog)
    assert "score_save_committed" not in [e["event"] for e in events]
    assert [e["event"] for e in events] == ["score_save_attempt", "score_save_rejected"]
    assert events[-1]["status_code"] == 400
    assert events[-1]["request_id"] == response.headers["X-Request-ID"]
    assert score_pg.commits == []
    _assert_safe_diagnostics(caplog)


def test_untrusted_correlation_header_is_replaced(score_pg, caplog):
    caplog.set_level(logging.INFO, logger="app.observability.score_save")
    response = _save(score_pg, correction_payload(), headers={"X-Request-ID": "private-player " * 20})
    assert response.status_code == 200
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) == 32
    assert all(e["request_id"] == request_id for e in _events(caplog))
    _assert_safe_diagnostics(caplog)
