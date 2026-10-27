"""Real HTTP regressions for Task 5 review: fences and actor attribution."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import models
from app.services.auth_service import get_current_user
from tests.unit.routers.test_round_identity_writes import canonical_api
from tests.unit.routers.test_round_posting_p1 import round_api, scores


def seed_round(sessions):
    with sessions() as db:
        db.add(
            models.GameStateModel(
                game_id="round",
                game_status="in_progress",
                state={
                    "players": [{"id": f"p{i}", "name": f"Player {i}", "player_profile_id": i} for i in range(1, 5)]
                },
            )
        )
        db.commit()


def test_browser_idempotency_preflight():
    from app.main import app

    # Exercise the real middleware without starting schedulers/source sync.
    client = TestClient(app, raise_server_exceptions=False)
    response = client.options(
        "/games/from-scorecard",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type,idempotency-key,x-request-id",
        },
    )
    assert response.status_code == 200, response.text
    assert "idempotency-key" in response.headers["access-control-allow-headers"].lower()


@pytest.mark.parametrize("mode", ["legacy", "paused", "canonical"])
def test_totals_mode_matrix(canonical_api, mode):
    client, _, sessions = canonical_api
    with sessions() as db:
        db.query(models.AppConfig).filter_by(name="round_identity").one().value = {"mode": mode, "epoch": 5}
        db.commit()
    response = client.post(
        "/games/from-scorecard",
        headers={"Idempotency-Key": "mode"},
        json={
            "detail_coverage": "totals_only",
            "players": [{"name": f"Player {i}", "player_profile_id": i, "quarters": 0} for i in range(1, 5)],
        },
    )
    assert response.status_code == (200 if mode == "canonical" else 409), response.text
    with sessions() as db:
        assert db.query(models.GameRecord).count() == (1 if mode == "canonical" else 0)
        assert db.query(models.RoundObservation).count() == (1 if mode == "canonical" else 0)


@pytest.mark.parametrize("route", ["scores", "patch"])
def test_completed_corrections_keep_two_actor_sources(canonical_api, route):
    client, app, sessions = canonical_api
    seed_round(sessions)
    first = client.post("/games/round/scores", json=scores())
    assert first.status_code == 200, first.text
    revision = first.json()["revision"]
    for actor in (1, 2):
        app.dependency_overrides[get_current_user] = lambda actor=actor: SimpleNamespace(
            id=actor, name=f"Player {actor}", preferences={}, admin_granted=False, is_active=True
        )
        if route == "scores":
            response = client.post("/games/round/scores", json={**scores(actor + 1), "expected_revision": revision})
        else:
            response = client.patch(
                "/games/round/holes/1/players/p1", json={"score": actor + 4, "expected_revision": revision}
            )
        assert response.status_code == 409, response.text
        assert response.json()["detail"]["issue_ids"]
    with sessions() as db:
        sources = db.query(models.RoundSource).filter_by(kind="card_edit").all()
        assert {s.round_token for s in sources} == {"1", "2"}
        observations = (
            db.query(models.RoundObservation)
            .filter(models.RoundObservation.source_id.in_([s.id for s in sources]))
            .all()
        )
        assert {o.raw_payload["payload"]["draft"]["actor_profile_id"] for o in observations} == {1, 2}
        issues = db.query(models.RoundIssue).filter_by(status="open").all()
        assert {i.source_id for i in issues}.issuperset({s.id for s in sources})


@pytest.mark.parametrize("mutation", ["patch", "delete"])
def test_active_mutations_invalidate_snapshot(canonical_api, mutation):
    client, _, sessions = canonical_api
    seed_round(sessions)
    body = {"holes": scores()["holes"][:2], "current_hole": 3}
    saved = client.post("/games/round/scores", json=body)
    revision = saved.json()["revision"]
    if mutation == "patch":
        changed = client.patch("/games/round/holes/1/players/p1", json={"score": 6, "expected_revision": revision})
    else:
        changed = client.delete(f"/games/round/holes/1?expected_revision={revision}")
    assert changed.status_code == 200, changed.text
    assert changed.json()["revision"] == revision + 1
    stale = client.post("/games/round/scores", json={**body, "expected_revision": revision})
    assert stale.status_code == 409, stale.text
    assert stale.json()["detail"]["revision"] == revision + 1


def test_delete_paused_and_completed_cannot_change_scores(canonical_api):
    client, _, sessions = canonical_api
    seed_round(sessions)
    first = client.post("/games/round/scores", json=scores())
    revision = first.json()["revision"]
    rejected = client.delete(f"/games/round/holes/1?expected_revision={revision}")
    assert rejected.status_code in (400, 409)
    with sessions() as db:
        assert db.query(models.GameRecord).one().final_scores["p1"] == 18
        db.query(models.AppConfig).filter_by(name="round_identity").one().value = {"mode": "paused", "epoch": 6}
        db.commit()
    paused = client.delete(f"/games/round/holes/1?expected_revision={revision}")
    assert paused.status_code == 409, paused.text
