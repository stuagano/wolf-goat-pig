"""Reconciliation uses real isolated sessions; no transport or production data."""

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app import models
from app.schemas.round_identity import ResolutionDecision, RoundDraft, SourceRef


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    models.Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(models.PlayerProfile(id=7, name="Reviewer", is_active=1, admin_granted=1))
        session.commit()
        yield session
    engine.dispose()


def draft(**updates):
    value = {
        "played_on": "2026-01-02",
        "course_name": "Wing Point",
        "group": "A",
        "roster_complete": True,
        "players": [
            {"participant_id": "a", "name": "Guest", "quarters": 1},
            {"participant_id": "b", "name": "Guest", "quarters": -1},
        ],
    }
    value.update(updates)
    return RoundDraft(**value)


def source(round_id="round-1", scope="fixture"):
    return SourceRef(kind="sheet", scope=scope, round_token=round_id)


def observe(db, value=None, key="initial", ref=None, continuity=True, raw=None):
    from app.services.round_reconciliation import observe_round

    return observe_round(
        db,
        ref or source(),
        value or draft(),
        observation_key=key,
        raw_payload=raw or {},
        continuity_verified=continuity,
    )


def decide(db, issue, action="keep", value=None, target=None):
    from app.services.round_reconciliation import resolve_issue

    game = db.query(models.GameStateModel).filter_by(game_id=issue.game_id).one_or_none()
    return resolve_issue(
        db,
        issue.id,
        ResolutionDecision(
            action=action,
            value=value,
            target_game_id=target,
            reason="Reviewed fixture evidence",
            expected_game_revision=game.revision if game else None,
            expected_target_game_revision=(
                db.query(models.GameStateModel).filter_by(game_id=target).one().revision
                if target and db.query(models.GameStateModel).filter_by(game_id=target).count()
                else None
            ),
            expected_issue_revision=issue.revision,
            expected_head_revision=issue.head_revision,
        ),
        actor_profile_id=7,
    )


def test_changed_total_preserves_accepted_value(db):
    first = observe(db)
    value = draft()
    value.players[0].quarters = 12
    result = observe(db, value, "change-1")
    assert result.game_id == first.game_id
    assert result.issue_ids
    assert db.query(models.GamePlayerResult).filter_by(participant_id="a").one().total_earnings == 1
    deliveries = db.query(models.RoundDelivery).all()
    assert {d.channel for d in deliveries} == {"email", "in_app"}
    assert all(d.recipient_profile_id is None and d.status == "unconfigured" and d.delivery_key for d in deliveries)


@pytest.mark.parametrize("fresh_key", [False, True])
def test_repeated_import_order_and_poll_metadata_are_unchanged(db, fresh_key):
    first = observe(db)
    value = draft()
    value.players.reverse()
    result = observe(db, value, "poll-2" if fresh_key else "initial", raw={"poll_time": "later"})
    assert result.game_id == first.game_id
    assert result.status == "unchanged"
    assert db.query(models.GameRecord).count() == 1
    assert db.query(models.GamePlayerResult).count() == 2
    assert db.query(models.RoundIssue).count() == 0


def test_blank_zero_guests_and_verified_unknown_fill(db):
    value = draft()
    value.players[0].quarters = None
    value.players[1].quarters = 0
    first = observe(db, value)
    rows = db.query(models.GamePlayerResult).order_by(models.GamePlayerResult.participant_id).all()
    assert [r.total_earnings for r in rows] == [None, 0]
    assert len({r.id for r in rows}) == 2
    value.players[0].quarters = 0
    held = observe(db, value, "untrusted", continuity=False)
    assert held.status == "held" and rows[0].total_earnings is None
    observe(db, value, "trusted")
    assert rows[0].total_earnings == 0
    assert first.game_id is not None


def test_candidate_does_not_merge_or_add_count_even_with_equal_scores(db):
    first = observe(db)
    held = observe(db, ref=source("second"))
    assert held.status == "held" and held.game_id is None
    assert db.query(models.GameRecord).count() == 1
    issue = db.get(models.RoundIssue, held.issue_ids[0])
    assert first.game_id in issue.candidate_game_ids
    distinct = decide(db, issue, "confirm_distinct")
    assert distinct.game_id != first.game_id
    assert db.query(models.GameRecord).count() == 2


def test_score_signature_alone_is_never_identity(db):
    observe(db)
    other = observe(db, draft(played_on="2026-03-04", course_name="Other Course"), ref=source("second"))
    assert other.status == "accepted"
    assert db.query(models.GameRecord).count() == 2


def test_unknown_day_does_not_escape_candidate_coordination(db):
    observe(db)
    result = observe(db, draft(played_on=None), ref=source("second"))
    assert result.status == "held"
    assert db.query(models.GameRecord).count() == 1


def test_orphan_record_binding_repairs_same_uuid(db):
    db.add(models.GameRecord(game_id="orphan", played_on=draft().played_on, course_name="Wing Point"))
    db.flush()
    held = observe(db)
    assert held.status == "held"
    result = decide(db, db.get(models.RoundIssue, held.issue_ids[0]), "bind_existing", target="orphan")
    assert result.game_id == "orphan"
    assert db.query(models.GameStateModel).one().game_id == "orphan"


def test_supersession_rejection_replay_and_transition_generation(db):
    first = observe(db)
    value = draft()
    value.players[0].quarters = 2
    b = observe(db, value, "b")
    old = db.get(models.RoundIssue, b.issue_ids[0])
    value.players[0].quarters = 3
    c = observe(db, value, "c")
    assert old.status == "superseded"
    current = db.get(models.RoundIssue, c.issue_ids[0])
    assert current.id != old.id
    with pytest.raises(HTTPException) as error:
        decide(db, old, "accept")
    assert error.value.status_code == 409
    decide(db, current, "keep")
    for iid in c.issue_ids[1:]:
        decide(db, db.get(models.RoundIssue, iid), "keep")
    count = db.query(models.RoundDelivery).count()
    game = db.query(models.GameStateModel).filter_by(game_id=first.game_id).one()
    game.scorecard_image = "photo"
    game.revision += 1
    assert not observe(db, value, "same-c").issue_ids
    assert db.query(models.RoundDelivery).count() == count
    observe(db, draft(), "back-a")
    again = observe(db, value, "again-c")
    assert again.issue_ids and again.issue_ids[0] != current.id


def test_accepted_a_b_a_and_unrelated_photo_do_not_corrupt_baseline(db):
    observe(db)
    value = draft()
    value.players[0].quarters = 2
    result = observe(db, value, "b")
    issue = db.get(models.RoundIssue, result.issue_ids[0])
    decide(db, issue, "accept")
    assert db.query(models.GamePlayerResult).filter_by(participant_id="a").one().total_earnings == 2
    result = observe(db, draft(), "a-again")
    assert result.issue_ids
    assert db.query(models.RoundResolution).one().observation_ids


def test_resolution_authorization_and_optimistic_revisions(db):
    from app.services.round_reconciliation import resolve_issue

    observe(db)
    value = draft()
    value.players[0].quarters = 9
    result = observe(db, value, "b")
    issue = db.get(models.RoundIssue, result.issue_ids[0])
    decision = ResolutionDecision(
        action="accept",
        reason="fixture",
        expected_issue_revision=issue.revision,
        expected_head_revision=issue.head_revision,
        expected_game_revision=999,
    )
    with pytest.raises(HTTPException) as error:
        resolve_issue(db, issue.id, decision, actor_profile_id=123)
    assert error.value.status_code == 403
    with pytest.raises(HTTPException) as error:
        resolve_issue(db, issue.id, decision, actor_profile_id=7)
    assert error.value.status_code == 409
    assert db.query(models.RoundResolution).count() == 0


def test_rollback_leaves_no_domain_rows_or_intents(db):
    observe(db)
    value = draft()
    value.players[0].quarters = 4
    observe(db, value, "b")
    db.rollback()
    for model in (
        models.GameStateModel,
        models.GameRecord,
        models.GamePlayerResult,
        models.RoundSource,
        models.RoundObservation,
        models.RoundFieldHead,
        models.RoundIssue,
        models.RoundDelivery,
    ):
        assert db.query(model).count() == 0


def test_clear_and_removal_are_explicit_reviewed_non_destructive(db):
    observe(db)
    value = draft(clear_fields=["course_name", "players.a.quarters"], removed_participant_ids=["b"])
    result = observe(db, value, "removal")
    assert result.issue_ids
    for iid in result.issue_ids:
        issue = db.get(models.RoundIssue, iid)
        decide(db, issue, "accept")
    record = db.query(models.GameRecord).one()
    assert record.course_name is None
    assert record.final_scores == {"a": None}
    removed = db.query(models.GamePlayerResult).filter_by(participant_id="b").one()
    assert removed.is_retracted and removed.total_earnings == -1
    observe(db, draft(), "old-source")
    assert removed.is_retracted
    assert "b" not in record.final_scores


def test_aliases_retain_old_and_new_keys_and_ambiguity(db):
    from app.services.round_identity import resolve_round_alias

    first = observe(db)
    value = draft(course_name="Corrected")
    result = observe(db, value, "correction")
    decide(db, db.get(models.RoundIssue, result.issue_ids[0]), "accept")
    assert resolve_round_alias(db, "2026-01-02", "A", "Wing Point") == [first.game_id]
    assert resolve_round_alias(db, "2026-01-02", "A", "Corrected") == [first.game_id]


def test_whole_game_retraction_survives_import_and_explicit_review_restores(db):
    observe(db)
    value = draft()
    value.players[0].quarters = 5
    conflict = observe(db, value, "changed")
    decide(db, db.get(models.RoundIssue, conflict.issue_ids[0]), "retract")
    record = db.query(models.GameRecord).one()
    game = db.query(models.GameStateModel).one()
    uuid = game.game_id
    assert record.is_retracted and not record.score_eligible
    result = observe(db, draft(), "after-retract")
    assert record.is_retracted and not record.score_eligible
    issue = next(
        db.get(models.RoundIssue, i) for i in result.issue_ids if db.get(models.RoundIssue, i).field == "is_retracted"
    )
    decide(db, issue, "correct", value=False)
    assert not record.is_retracted and record.score_eligible
    assert game.game_id == uuid


def test_missing_participant_never_means_removal(db):
    observe(db)
    value = draft()
    value.players = value.players[:1]
    value.roster_complete = False
    observe(db, value, "partial")
    row = db.query(models.GamePlayerResult).filter_by(participant_id="b").one()
    assert not row.is_retracted and row.total_earnings == -1


def test_new_slot_requires_review_and_preserves_existing_ids(db):
    observe(db)
    original = {r.participant_id: r.id for r in db.query(models.GamePlayerResult)}
    value = draft()
    from app.schemas.round_identity import RoundParticipant

    value.players.append(RoundParticipant(participant_id="c", name="Guest", quarters=0))
    result = observe(db, value, "roster-change")
    assert db.query(models.GamePlayerResult).count() == 2
    issue = next(
        db.get(models.RoundIssue, i) for i in result.issue_ids if db.get(models.RoundIssue, i).kind == "roster"
    )
    decide(db, issue, "accept")
    assert db.query(models.GamePlayerResult).count() == 3
    assert {
        r.participant_id: r.id for r in db.query(models.GamePlayerResult) if r.participant_id in original
    } == original


def test_no_alert_reopen_after_photo_or_row_order_change(db):
    observe(db)
    value = draft()
    value.players[0].quarters = 6
    result = observe(db, value, "conflict")
    game = db.query(models.GameStateModel).one()
    game.revision += 1
    game.scorecard_image = "photo"
    value.players.reverse()
    repeated = observe(db, value, "poll-again", raw={"poll_time": "changed"})
    assert set(repeated.issue_ids) == set(result.issue_ids)
    assert db.query(models.RoundDelivery).count() == 2 * len(result.issue_ids)


def test_delivery_key_is_unique_even_without_recipient(db):
    from sqlalchemy.exc import IntegrityError

    observe(db)
    value = draft(course_name="Changed")
    result = observe(db, value, "conflict")
    delivery = db.query(models.RoundDelivery).first()
    assert result.issue_ids and delivery.recipient_profile_id is None
    with pytest.raises(IntegrityError), db.begin_nested():
        db.add(
            models.RoundDelivery(
                issue_event_key=delivery.issue_event_key,
                issue_id=delivery.issue_id,
                recipient_profile_id=None,
                channel=delivery.channel,
                delivery_key=delivery.delivery_key,
                status="unconfigured",
            )
        )
        db.flush()


def test_profile_reassignment_and_slot_rename_require_review(db):
    observe(db)
    value = draft()
    value.players[0].name = "Renamed"
    value.players[0].profile_id = 42
    result = observe(db, value, "profile-change")
    row = db.query(models.GamePlayerResult).filter_by(participant_id="a").one()
    assert row.player_name == "Guest" and row.player_profile_id is None
    assert {db.get(models.RoundIssue, i).field for i in result.issue_ids} >= {"name", "profile_id"}


def test_identity_keep_replay_never_enqueues_or_creates_again(db):
    observe(db)
    result = observe(db, ref=source("possible-copy"))
    decide(db, db.get(models.RoundIssue, result.issue_ids[0]), "keep")
    count = db.query(models.RoundDelivery).count()
    result = observe(db, ref=source("possible-copy"), key="new-poll")
    assert result.status == "held" and result.game_id is None
    assert db.query(models.RoundDelivery).count() == count
    assert db.query(models.GameRecord).count() == 1


def test_parse_error_is_retained_and_held_before_any_game_creation(db):
    result = observe(db, raw={"parse_errors": ["bad score"]})
    assert result.status == "held" and result.game_id is None
    assert db.query(models.GameRecord).count() == 0
    observation = db.query(models.RoundObservation).one()
    assert observation.raw_payload["payload"]["parse_errors"]


@pytest.mark.parametrize(
    "changes",
    [
        {"clear_fields": ["revision"]},
        {"clear_fields": ["players.x.quarters"]},
        {"removed_participant_ids": ["missing"]},
    ],
)
def test_explicit_operation_contract_rejects_unknown_slots_and_fields(changes):
    with pytest.raises(ValueError):
        draft(**changes)
