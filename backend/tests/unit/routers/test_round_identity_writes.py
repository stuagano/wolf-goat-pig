"""Canonical HTTP writes: durable receipts, evidence, and accepted revisions."""

from types import SimpleNamespace
from uuid import UUID

import pytest

from app import models
from app.routers import member_rounds
from app.services.auth_service import get_current_user
from tests.unit.routers.test_round_posting_p1 import round_api, scores, sign_in


@pytest.fixture
def canonical_api(round_api):
    client, app, sessions = round_api
    app.include_router(member_rounds.router)
    with sessions() as db:
        db.query(models.GameStateModel).delete()
        db.add(models.AppConfig(name="round_identity", value={"mode": "canonical", "epoch": 5}))
        for i in range(1, 5):
            db.add(models.LegacyRosterPlayer(name=f"Player {i}"))
            db.add(
                models.PlayerProfile(id=i, name=f"Player {i}", legacy_name=f"Player {i}", email=f"p{i}@example.invalid")
            )
        db.commit()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=1, legacy_name="Player 1", name="Player 1", preferences={}, admin_granted=False, is_active=True
    )
    return client, app, sessions


def manual_body():
    return {
        "date": "2026-10-25",
        "group": "B",
        "location": "Example",
        "results": [{"member": f"Player {i}", "score": q} for i, q in enumerate([3, -3, 0, 0], 1)],
    }


def test_manual_retry_returns_same_uuid(canonical_api):
    client, _, sessions = canonical_api
    headers = {"Idempotency-Key": "manual-fixture-1"}
    a = client.post("/players/me/round", json=manual_body(), headers=headers)
    b = client.post("/players/me/round", json=manual_body(), headers=headers)
    assert a.status_code == b.status_code == 201, (a.text, b.text)
    assert a.json() == b.json()
    UUID(a.json()["game_id"])
    with sessions() as db:
        assert db.query(models.GameStateModel).count() == 1
        assert db.query(models.GamePlayerResult).count() == 4
        assert db.query(models.RoundObservation).count() == 1
        assert db.query(models.LegacyRound).count() == 4
        assert {r.game_id for r in db.query(models.LegacyRound)} == {a.json()["game_id"]}
        assert db.query(models.GameRecord).one().total_holes_played is None


def test_key_mismatch_and_missing_key_rejected(canonical_api):
    client, _, _ = canonical_api
    body = manual_body()
    assert client.post("/players/me/round", json=body).status_code == 400
    headers = {"Idempotency-Key": "same"}
    assert client.post("/players/me/round", json=body, headers=headers).status_code == 201
    body["results"][0]["score"] = 4
    assert client.post("/players/me/round", json=body, headers=headers).status_code == 409


def test_canonical_creation_preserves_participant_authorization(canonical_api):
    client, app, sessions = canonical_api
    body = manual_body()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=9, legacy_name="Outsider", name="Outsider", preferences={}, admin_granted=False, is_active=True
    )
    headers = {"Idempotency-Key": "unauthorized"}
    assert client.post("/players/me/round", json=body, headers=headers).status_code == 400
    scan = {
        "players": [
            {"name": p["member"], "player_profile_id": i, "quarters": p["score"]}
            for i, p in enumerate(body["results"], 1)
        ],
        "detail_coverage": "totals_only",
    }
    assert client.post("/games/from-scorecard", json=scan, headers=headers).status_code == 403
    with sessions() as db:
        assert db.query(models.RoundObservation).count() == 0
        assert db.query(models.RoundRequest).count() == 0


def test_ambiguous_creation_retains_evidence_without_new_uuid(canonical_api):
    client, _, sessions = canonical_api
    body = manual_body()
    assert client.post("/players/me/round", json=body, headers={"Idempotency-Key": "first"}).status_code == 201
    second = client.post("/players/me/round", json=body, headers={"Idempotency-Key": "second"})
    assert second.status_code == 202, second.text
    assert second.json()["game_id"] is None
    assert second.json()["issue_ids"]
    with sessions() as db:
        assert db.query(models.GameStateModel).count() == 1
        assert db.query(models.RoundRequest).count() == 2


def test_completed_scores_stage_proposal_and_stale_revision(canonical_api):
    client, app, sessions = canonical_api
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
    sign_in(app)
    first = client.post("/games/round/scores", json={**scores(), "expected_revision": 0})
    assert first.status_code == 200, first.text
    revision = first.json()["revision"]
    completed = client.post("/games/round/complete")
    assert completed.status_code == 200, completed.text
    assert completed.json()["revision"] == revision
    proposed = client.post("/games/round/scores", json={**scores(2), "expected_revision": revision})
    assert proposed.status_code == 409, proposed.text
    assert proposed.json()["detail"]["issue_ids"]
    with sessions() as db:
        assert db.query(models.GameRecord).one().final_scores["p1"] == 18
        assert db.query(models.HoleEvent).filter_by(hole_number=1, player_id="p1").one().quarters == 1
        assert db.query(models.RoundIssue).filter_by(status="open").count() > 0
    stale = client.post("/games/round/scores", json={**scores(3), "expected_revision": revision - 1})
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "stale_round"


def test_totals_scan_requires_explicit_totals_and_valid_date(canonical_api):
    client, _, _ = canonical_api
    body = {
        "players": [{"name": f"Player {i}", "player_profile_id": i} for i in range(1, 5)],
        "detail_coverage": "totals_only",
    }
    headers = {"Idempotency-Key": "invalid-scan"}
    assert client.post("/games/from-scorecard", json=body, headers=headers).status_code == 400
    for player in body["players"]:
        player["quarters"] = 0
    body["played_at"] = "not-a-date"
    assert client.post("/games/from-scorecard", json=body, headers=headers).status_code == 422


def test_totals_scan_has_no_fabricated_holes(canonical_api):
    client, _, sessions = canonical_api
    body = {
        "players": [
            {"name": f"Player {i}", "player_profile_id": i, "quarters": q} for i, q in enumerate([1.5, -1.5, 0, 0], 1)
        ],
        "detail_coverage": "totals_only",
        "played_at": "2026-10-25",
    }
    headers = {"Idempotency-Key": "scan-one"}
    a = client.post("/games/from-scorecard", json=body, headers=headers)
    b = client.post("/games/from-scorecard", json=body, headers=headers)
    assert a.status_code == b.status_code == 200, (a.text, b.text)
    assert a.json()["game_id"] == b.json()["game_id"]
    with sessions() as db:
        assert db.query(models.GameRecord).one().final_scores["p1"] == 1.5
        assert db.query(models.HoleEvent).count() == 0
        assert not db.query(models.GameStateModel).one().state.get("hole_history")
