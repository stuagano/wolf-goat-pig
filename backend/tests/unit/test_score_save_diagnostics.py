"""Score-save diagnostics correlate outcomes without recording score bodies."""

import json
import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.observability.score_save import ScoreSaveDiagnostics, log_score_commit


def _events(caplog):
    return [json.loads(record.message) for record in caplog.records]


def _client(handler, *, raise_server_exceptions=True):
    app = FastAPI()
    app.add_middleware(ScoreSaveDiagnostics)
    app.post("/games/{game_id}/scores")(handler)
    return TestClient(app, raise_server_exceptions=raise_server_exceptions)


def test_commit_is_logged_only_after_the_write_and_without_the_payload(caplog):
    def save(game_id: str, body: dict):
        log_score_commit()
        return {"success": True}

    caplog.set_level(logging.INFO, logger="app.observability.score_save")
    response = _client(save).post(
        "/games/round-7/scores",
        headers={"X-Request-ID": "score-attempt-123"},
        json={"notes": "Stu beat Bob", "token": "header.body.signature"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "score-attempt-123"
    events = _events(caplog)
    assert [e["event"] for e in events] == ["score_save_attempt", "score_save_committed"]
    assert {e["request_id"] for e in events} == {"score-attempt-123"}
    assert "Stu" not in caplog.text
    assert "signature" not in caplog.text


def test_rejected_save_is_correlated_and_never_logged_as_committed(caplog):
    def reject(game_id: str):
        raise HTTPException(400, "Zero-sum validation failed")

    caplog.set_level(logging.INFO, logger="app.observability.score_save")
    response = _client(reject).post("/games/round-7/scores", json={})

    assert response.status_code == 400
    events = _events(caplog)
    assert [e["event"] for e in events] == ["score_save_attempt", "score_save_rejected"]
    assert events[-1]["status_code"] == 400
    assert events[-1]["request_id"] == response.headers["X-Request-ID"]


def test_failed_save_is_correlated_without_the_exception_text(caplog):
    def fail(game_id: str):
        raise RuntimeError("UPDATE game_player_results SET total_earnings=4.0")

    caplog.set_level(logging.INFO, logger="app.observability.score_save")
    response = _client(fail, raise_server_exceptions=False).post("/games/round-7/scores", json={})

    assert response.status_code == 500
    assert response.headers["X-Request-ID"]
    events = _events(caplog)
    assert [e["event"] for e in events] == ["score_save_attempt", "score_save_failed"]
    assert "total_earnings" not in caplog.text


def test_untrusted_correlation_header_is_replaced_with_a_generated_id(caplog):
    def save(game_id: str):
        log_score_commit()
        return {"success": True}

    caplog.set_level(logging.INFO, logger="app.observability.score_save")
    response = _client(save).post(
        "/games/round-7/scores",
        headers={"X-Request-ID": "player bob@example.com edited hole 7"},
        json={},
    )

    assert len(response.headers["X-Request-ID"]) == 32
    assert "bob@example.com" not in caplog.text
    assert all(e["request_id"] == response.headers["X-Request-ID"] for e in _events(caplog))


def test_failure_before_the_route_is_still_correlated(caplog):
    """An authorization/database failure outside the handler needs a reference too."""
    app = FastAPI()
    app.add_middleware(ScoreSaveDiagnostics)

    def broken_dependency():
        raise RuntimeError("could not connect to server: scores")

    @app.post("/games/{game_id}/scores", dependencies=[Depends(broken_dependency)])
    def save(game_id: str):  # pragma: no cover - dependency fails first
        return {"success": True}

    caplog.set_level(logging.INFO, logger="app.observability.score_save")
    response = TestClient(app, raise_server_exceptions=False).post(
        "/games/round-7/scores", headers={"X-Request-ID": "dependency-failure-1"}, json={}
    )

    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "dependency-failure-1"
    events = _events(caplog)
    assert [e["event"] for e in events] == ["score_save_attempt", "score_save_failed"]
    assert events[-1]["error_class"] == "RuntimeError"
    assert set(events[-1]) == {"event", "request_id", "status_code", "error_class"}
    assert "could not connect" not in caplog.text + response.text


def test_real_app_exposes_request_reference_to_credentialed_browser():
    from app.main import app

    response = TestClient(app).post(
        "/games/missing/scores",
        headers={"Origin": "https://seventh-country-232522.web.app", "X-Request-ID": "browser-save-123"},
        json={},
    )
    assert response.status_code in (401, 403)
    assert response.headers["X-Request-ID"] == "browser-save-123"
    assert "X-Request-ID" in response.headers["Access-Control-Expose-Headers"]
    assert response.headers["Access-Control-Allow-Credentials"] == "true"


def test_real_app_dependency_failure_is_safe_and_cors_correlated(caplog, monkeypatch):
    from app.main import app
    from app.utils.round_card import require_round_member_or_admin

    def fail():
        raise RuntimeError("secret-score-parameters")

    monkeypatch.setitem(app.dependency_overrides, require_round_member_or_admin, fail)
    caplog.set_level(logging.INFO)
    response = TestClient(app, raise_server_exceptions=False).post(
        "/games/missing/scores",
        headers={"Origin": "https://seventh-country-232522.web.app", "X-Request-ID": "failed-browser-save-123"},
        json={},
    )
    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == "failed-browser-save-123"
    assert "X-Request-ID" in response.headers["Access-Control-Expose-Headers"]
    assert "secret-score-parameters" not in caplog.text + response.text


def test_real_app_validation_does_not_log_payload_keys(caplog, monkeypatch):
    from app.main import app
    from app.utils.round_card import require_round_member_or_admin

    monkeypatch.setitem(app.dependency_overrides, require_round_member_or_admin, lambda: None)
    caplog.set_level(logging.INFO)
    response = TestClient(app).post(
        "/games/missing/scores", json={"holes": [{"hole_number": 1, "quarters": {"private-player-key": "invalid"}}]}
    )
    assert response.status_code == 422
    assert "private-player-key" not in caplog.text
    assert response.headers["X-Request-ID"]


def test_unrelated_endpoints_are_not_instrumented(caplog):
    app = FastAPI()
    app.add_middleware(ScoreSaveDiagnostics)

    @app.post("/games/{game_id}/complete")
    def complete(game_id: str):
        log_score_commit()
        return {"success": True}

    caplog.set_level(logging.INFO, logger="app.observability.score_save")
    response = TestClient(app).post("/games/round-7/complete")

    assert response.status_code == 200
    assert "X-Request-ID" not in response.headers
    assert _events(caplog) == []
