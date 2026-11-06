"""UI decision payloads exercised against the shared resolver over real sessions."""

import pytest

from app import models
from app.schemas.round_identity import RoundDraft, SourceRef
from app.services.round_reconciliation import observe_round
from tests.unit.routers.test_round_reconciliation_api import login, round_api, seed


def decision(detail, action, **extra):
    return {
        "action": action,
        "reason": "Explicit local review",
        "expected_game_revision": detail["game_revision"],
        "expected_issue_revision": detail["revision"],
        "expected_head_revision": detail["current_head_revision"],
        **extra,
    }


def test_bound_continuity_rebind_payload_and_stale_target(round_api):
    client, app, sessions = round_api
    original, *_ = seed(sessions)
    login(app, sessions)
    with sessions() as db:
        source = db.query(models.RoundSource).one()
        observation = db.query(models.RoundObservation).filter_by(source_id=source.id).first()
        draft = RoundDraft.model_validate(observation.parsed_values)
        target_hold = observe_round(
            db,
            SourceRef(kind="manual", scope="local", round_token="other"),
            draft,
            observation_key="target",
            raw_payload={},
            continuity_verified=True,
            create_without_candidate=True,
        )
        from app.schemas.round_identity import ResolutionDecision
        from app.services.round_reconciliation import resolve_issue

        target_issue = db.get(models.RoundIssue, target_hold.issue_ids[0])
        target = resolve_issue(
            db,
            target_issue.id,
            ResolutionDecision(
                action="confirm_distinct",
                reason="Separate local fixture round",
                expected_issue_revision=target_issue.revision,
                expected_head_revision=target_issue.head_revision,
            ),
            actor_profile_id=8,
        ).game_id
        held = observe_round(
            db,
            SourceRef(kind=source.kind, scope=source.scope, round_token=source.round_token),
            draft,
            observation_key="continuity",
            raw_payload={},
            continuity_verified=False,
        )
        issue_id = next(i for i in held.issue_ids if db.get(models.RoundIssue, i).kind == "continuity")
        db.commit()
    detail = client.get(f"/round-reconciliation/issues/{issue_id}").json()
    assert detail["kind"] == "continuity" and detail["game_id"] == original
    target_revision = client.get(f"/games/{target}/round-summary").json()["revision"]
    payload = decision(detail, "bind_existing", target_game_id=target, expected_target_game_revision=target_revision)
    stale = client.post(
        f"/round-reconciliation/issues/{issue_id}/resolve",
        json={**payload, "expected_target_game_revision": target_revision + 1},
    )
    assert stale.status_code == 409, stale.text
    for action in ("accept", "correct"):
        rejected = client.post(
            f"/round-reconciliation/issues/{issue_id}/resolve", json=decision(detail, action, value=1)
        )
        assert rejected.status_code == 422, rejected.text
    response = client.post(f"/round-reconciliation/issues/{issue_id}/resolve", json=payload)
    assert response.status_code == 200, response.text
    with sessions() as db:
        assert db.query(models.RoundSource).filter_by(kind="sheet").one().game_id == target
        assert db.query(models.RoundResolution).filter_by(issue_id=issue_id).one().action == "bind_existing"
    assert client.post(f"/round-reconciliation/issues/{issue_id}/resolve", json=payload).status_code == 409


@pytest.mark.parametrize("bound", [False, True])
def test_parse_hold_payload_supports_keep_but_not_value_or_binding(round_api, bound):
    client, app, sessions = round_api
    if bound:
        seed(sessions)
    login(app, sessions)
    with sessions() as db:
        source = db.query(models.RoundSource).first() if bound else None
        ref = (
            SourceRef(kind=source.kind, scope=source.scope, round_token=source.round_token)
            if source
            else SourceRef(kind="sheet", scope="local", round_token="parse")
        )
        outcome = observe_round(
            db,
            ref,
            RoundDraft(players=[], roster_complete=False),
            observation_key="parse-hold",
            raw_payload={"parse_errors": ["Unreadable cells"]},
            continuity_verified=True,
        )
        issue_id = next(i for i in outcome.issue_ids if db.get(models.RoundIssue, i).kind == "parse")
        db.commit()
    detail = client.get(f"/round-reconciliation/issues/{issue_id}").json()
    assert detail["kind"] == "parse" and bool(detail["game_id"]) == bound
    for action in ("accept", "correct", "bind_existing", "confirm_distinct"):
        response = client.post(
            f"/round-reconciliation/issues/{issue_id}/resolve", json=decision(detail, action, value=1)
        )
        assert response.status_code == 422, response.text
    response = client.post(f"/round-reconciliation/issues/{issue_id}/resolve", json=decision(detail, "keep"))
    assert response.status_code == (202 if bound else 200), response.text
    with sessions() as db:
        assert db.query(models.RoundResolution).filter_by(issue_id=issue_id).count() == 1
        assert db.query(models.GameRecord).count() == (1 if bound else 0)
