"""Real-session regressions for independently reviewed reconciliation transitions."""

import pytest
from fastapi import HTTPException

from app import models
from app.schemas.round_identity import ResolutionDecision
from app.services.round_reconciliation import resolve_issue
from tests.unit.services.test_round_reconciliation import db, decide, draft, observe, source


def issue_for(db, outcome, field, participant=""):
    return next(
        issue
        for iid in outcome.issue_ids
        if (issue := db.get(models.RoundIssue, iid)).field == field and issue.participant_id == participant
    )


@pytest.mark.parametrize("same_key", [False, True])
@pytest.mark.parametrize("other_total", [2, 3])
def test_cross_source_baseline_refresh_and_satisfied_retirement(db, other_total, same_key):
    first = observe(db)
    second = source("second")
    held = observe(db, ref=second)
    binding = issue_for(db, held, "identity")
    resolve_issue(
        db,
        binding.id,
        ResolutionDecision(
            action="bind_existing",
            target_game_id=first.game_id,
            reason="Reviewed second source",
            expected_game_revision=None,
            expected_target_game_revision=first.revision,
            expected_issue_revision=binding.revision,
            expected_head_revision=binding.head_revision,
        ),
        actor_profile_id=7,
    )
    proposal = draft()
    proposal.players[0].quarters = 2
    old = issue_for(db, observe(db, proposal, "s1-b"), "quarters", "a")
    other = draft()
    other.players[0].quarters = other_total
    conflict = issue_for(db, observe(db, other, "s2-change", ref=second), "quarters", "a")
    decide(db, conflict, "accept")
    refreshed = observe(db, proposal, "s1-b" if same_key else "s1-poll")
    assert old.status == "superseded"
    if other_total == 2:
        assert not [
            db.get(models.RoundIssue, iid)
            for iid in refreshed.issue_ids
            if db.get(models.RoundIssue, iid).field == "quarters"
        ]
    else:
        current = issue_for(db, refreshed, "quarters", "a")
        assert current.id != old.id and current.accepted_value == 3 and current.proposed_value == 2
        count = db.query(models.RoundDelivery).count()
        assert current.id in observe(db, proposal, "s1-stable").issue_ids
        assert db.query(models.RoundDelivery).count() == count
        decide(db, current, "accept")
    db.commit()
    db.expire_all()
    assert db.query(models.GamePlayerResult).filter_by(participant_id="a").one().total_earnings == 2


@pytest.mark.parametrize("action", ["accept", "correct"])
def test_reviewed_false_completeness_is_physically_materialized(db, action):
    observe(db)
    conflict = issue_for(db, observe(db, draft(roster_complete=False), "incomplete"), "roster_complete")
    assert db.query(models.GameRecord).one().score_eligible
    decide(db, conflict, action, value=False)
    db.commit()
    db.expire_all()
    record = db.query(models.GameRecord).one()
    assert record.roster_complete is False and record.score_eligible is False
    assert record.final_scores == {"a": 1, "b": -1}
    resolution = db.query(models.RoundResolution).one()
    assert resolution.action == action and resolution.value is False


@pytest.mark.parametrize("stale", [None, "target", "old", "binding"])
def test_rebind_checks_old_and_target_revisions_independently(db, stale):
    first = observe(db)
    target = observe(db, draft(played_on="2026-04-01"), ref=source("target"))
    target_game = db.query(models.GameStateModel).filter_by(game_id=target.game_id).one()
    target_game.revision += 4
    db.flush()
    outcome = observe(db, key="continuity-lost", continuity=False)
    issue = issue_for(db, outcome, "continuity")
    old_game = db.query(models.GameStateModel).filter_by(game_id=first.game_id).one()
    decision = ResolutionDecision(
        action="bind_existing",
        target_game_id=target.game_id,
        reason="Reviewed rebind",
        expected_game_revision=old_game.revision - int(stale == "old"),
        expected_target_game_revision=target_game.revision - int(stale == "target"),
        expected_issue_revision=issue.revision,
        expected_head_revision=issue.head_revision,
    )
    if stale == "binding":
        db.query(models.RoundSource).filter_by(round_token="round-1").one().game_id = target.game_id
        db.flush()
    if stale:
        with pytest.raises(HTTPException) as error:
            resolve_issue(db, issue.id, decision, actor_profile_id=7)
        assert error.value.status_code == 409
        assert db.query(models.RoundSource).filter_by(round_token="round-1").one().game_id == (
            target.game_id if stale == "binding" else first.game_id
        )
        assert db.query(models.RoundResolution).count() == 0
    else:
        result = resolve_issue(db, issue.id, decision, actor_profile_id=7)
        assert result.game_id == target.game_id
        db.commit()
        db.expire_all()
        assert db.query(models.RoundSource).filter_by(round_token="round-1").one().game_id == target.game_id
        assert db.query(models.RoundResolution).one().target_game_id == target.game_id


@pytest.mark.parametrize("resolved", [False, True])
@pytest.mark.parametrize("field", ["non_zero_sum", "roster_completeness"])
def test_integrity_failure_healthy_failure_creates_new_event(db, resolved, field):
    observe(db)
    bad = draft()
    if field == "non_zero_sum":
        bad.players[0].quarters = 2
    else:
        bad.roster_complete = False
    old = issue_for(db, observe(db, bad, "bad"), field)
    if resolved:
        decide(db, old, "keep")
    observe(db, draft(), "healthy")
    assert old.status == ("resolved" if resolved else "superseded")
    again = issue_for(db, observe(db, bad, "bad-again"), field)
    assert again.id != old.id and again.generation > old.generation
    count = db.query(models.RoundDelivery).count()
    assert again.id in observe(db, bad, "stable-bad").issue_ids
    assert db.query(models.RoundDelivery).count() == count
    db.commit()
    db.expire_all()
    assert db.get(models.RoundIssue, again.id).status == "open"
    assert db.query(models.RoundDelivery).filter_by(issue_id=again.id).count() == 2


def test_complete_source_absence_is_reviewed_but_never_inferred_deletion(db):
    zero = draft()
    for player in zero.players:
        player.quarters = 0
    observe(db, zero)
    before = {r.participant_id: (r.id, r.total_earnings) for r in db.query(models.GamePlayerResult)}
    sparse = zero.model_copy(deep=True)
    sparse.players = sparse.players[:1]
    partial = sparse.model_copy(update={"roster_complete": False})
    partial_outcome = observe(db, partial, "partial")
    assert not any(db.get(models.RoundIssue, iid).kind == "missing_participant" for iid in partial_outcome.issue_ids)
    missing = observe(db, sparse, "complete-missing")
    absent = next(
        db.get(models.RoundIssue, iid)
        for iid in missing.issue_ids
        if db.get(models.RoundIssue, iid).kind == "missing_participant"
    )
    assert absent.participant_id == "b"
    count = db.query(models.RoundDelivery).count()
    assert absent.id in observe(db, sparse, "same-missing").issue_ids
    assert db.query(models.RoundDelivery).count() == count
    with pytest.raises(HTTPException) as error:
        decide(db, absent, "accept")
    assert error.value.status_code == 400
    db.commit()
    db.expire_all()
    assert {r.participant_id: (r.id, r.total_earnings) for r in db.query(models.GamePlayerResult)} == before
    assert all(not r.is_retracted for r in db.query(models.GamePlayerResult))
    assert db.query(models.GameRecord).one().final_scores == {"a": 0, "b": 0}
    explicit = zero.model_copy(update={"removed_participant_ids": ["b"]})
    removal = issue_for(db, observe(db, explicit, "explicit-removal"), "is_retracted", "b")
    decide(db, removal, "accept")
    db.commit()
    db.expire_all()
    assert db.query(models.GamePlayerResult).filter_by(participant_id="b").one().is_retracted
    assert db.query(models.GameRecord).one().final_scores == {"a": 0}
    assert db.query(models.RoundResolution).filter_by(issue_id=removal.id).one().action == "accept"
