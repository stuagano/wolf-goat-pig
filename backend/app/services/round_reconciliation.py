"""Transactional source observations and optimistic, authorized adjudication.

No commits, transport calls, bulk evidence updates, score-based binding or
inferred removals. The caller owns the entire transaction.
"""

from uuid import uuid4

from fastapi import HTTPException

from app import models
from app.schemas.round_identity import IngestOutcome, RoundDraft, SourceRef
from app.utils.time import utc_now

from .completed_game_service import persist_final_results
from .round_evidence import (
    accepted_draft,
    draft_values,
    fingerprint,
    issue_for,
    missing_source_slots,
    patch,
    review_signal,
)
from .round_identity import acquire_reconciliation_lock, candidate_games, retain_alias


def _game(db, game_id):
    return db.query(models.GameStateModel).filter_by(game_id=game_id).populate_existing().one_or_none()


def _bind(db, source, draft, game_id=None, actor=None):
    game_id = game_id or str(uuid4())
    game = _game(db, game_id)
    if game is None:
        game = models.GameStateModel(
            game_id=game_id, state={}, game_status="completed", created_at=utc_now().isoformat()
        )
        db.add(game)
        db.flush()
    source.game_id = game_id
    source.revision += 1
    source.bound_by_profile_id = actor
    source.bound_at = utc_now().isoformat()
    source.binding_evidence = {"kind": "reviewed" if actor else "trusted_new_token"}
    db.flush()
    if accepted_draft(db, game_id) is None:
        # An orphan record with no scores can acquire its original container;
        # legacy scored rows without stable slots must await migration review.
        record = db.query(models.GameRecord).filter_by(game_id=game_id).one_or_none()
        if record and db.query(models.GamePlayerResult).filter_by(game_record_id=record.id).count():
            raise HTTPException(409, "Legacy slots require reviewed migration mapping")
        persist_final_results(db, game, draft)
    retain_alias(db, game_id, draft)
    return game


def _head(db, source, participant, field, baseline):
    head = (
        db.query(models.RoundFieldHead)
        .filter_by(source_id=source.id, participant_id=participant, field=field)
        .one_or_none()
    )
    if head is None:
        value = baseline.get((participant, field))
        head = models.RoundFieldHead(
            source_id=source.id,
            participant_id=participant,
            field=field,
            accepted_present=value is not None,
            accepted_value=value,
            accepted_revision=1 if value is not None else 0,
        )
        db.add(head)
        db.flush()
    return head


def _outcome(db, source, issues, changed=False):
    game = _game(db, source.game_id) if source.game_id else None
    db.flush()
    return IngestOutcome(
        status="held" if issues else "accepted" if changed else "unchanged",
        game_id=source.game_id,
        issue_ids=[i.id for i in issues],
        revision=game.revision if game else None,
    )


def _hold(db, row, observation, kind, value, candidates=()):
    head = _head(db, row, "", kind, {})
    if head.raw_present and head.raw_value == value:
        current = db.query(models.RoundIssue).filter_by(source_id=row.id, field=kind, status="open").all()
        outcome = _outcome(db, row, current)
        if row.game_id is None:
            outcome.status = "held"
        return outcome
    head.raw_present, head.raw_value = True, value
    head.revision += 1
    head.observation_id = observation.id
    return _outcome(db, row, [issue_for(db, row, observation, kind, head=head, candidates=candidates, value=value)])


def observe_round(
    db, source, draft, *, observation_key, raw_payload, continuity_verified, create_without_candidate=False
):
    acquire_reconciliation_lock(db)
    row = db.query(models.RoundSource).filter_by(**source.model_dump()).populate_existing().one_or_none()
    if row is None:
        row = models.RoundSource(**source.model_dump())
        db.add(row)
        db.flush()
    values = draft_values(draft)
    content = fingerprint(
        [
            sorted((p, f, v) for (p, f), v in values.items()),
            sorted(draft.clear_fields),
            sorted(draft.removed_participant_ids),
            raw_payload.get("parse_errors"),
            continuity_verified,
        ]
    )
    prior = db.query(models.RoundObservation).filter_by(source_id=row.id, observation_key=observation_key).one_or_none()
    if prior and prior.content_fingerprint != content:
        raise HTTPException(409, "Observation key reused with different parsed evidence")
    if prior and (not row.game_id or row.latest_observation_key != observation_key):
        issues = db.query(models.RoundIssue).filter_by(source_id=row.id, status="open").all()
        outcome = _outcome(db, row, issues)
        if row.game_id is None:
            outcome.status = "held"
        return outcome
    observation = prior or models.RoundObservation(
        source_id=row.id,
        observation_key=observation_key,
        raw_payload={
            "payload": raw_payload,
            "operations": {
                "clear_fields": draft.clear_fields,
                "removed_participant_ids": draft.removed_participant_ids,
            },
        },
        parsed_values=draft.model_dump(mode="json"),
        present_fields={
            "round": sorted(draft.model_fields_set),
            "players": {p.participant_id: sorted(p.model_fields_set) for p in draft.players},
            "clear_fields": sorted(draft.clear_fields),
            "removed_participant_ids": sorted(draft.removed_participant_ids),
        },
        content_fingerprint=content,
        continuity_verified=continuity_verified,
    )
    db.add(observation)
    db.flush()
    changed = False
    if not continuity_verified or raw_payload.get("parse_errors"):
        return _hold(db, row, observation, "parse" if raw_payload.get("parse_errors") else "continuity", content)
    if row.game_id is None:
        candidates = candidate_games(db, draft)
        # This compatibility argument never bypasses ambiguity. Only a recorded
        # confirm_distinct resolution may do that.
        if (
            candidates
            or not source.round_token.strip()
            or not draft.players
            or draft.clear_fields
            or draft.removed_participant_ids
        ):
            return _hold(db, row, observation, "identity", content, candidates)
        _bind(db, row, draft)
        changed = True
    game = _game(db, row.game_id)
    if game is None:
        raise HTTPException(409, "Bound UUID container missing; reviewed repair required")
    accepted = accepted_draft(db, row.game_id)
    if accepted is None:
        raise HTTPException(409, "Accepted stable participant mapping missing")
    baseline = draft_values(accepted)
    for player in accepted.players:
        for field in ("name", "profile_id", "quarters"):
            baseline[(player.participant_id, field)] = getattr(player, field)
    if (game.state or {}).get("hole_history"):
        baseline[("", "detail")] = {
            "coverage": db.query(models.GameRecord).filter_by(game_id=row.game_id).one().detail_coverage,
            "holes": sorted(game.state["hole_history"], key=lambda h: h["hole"]),
        }
    baseline[("", "is_retracted")] = db.query(models.GameRecord).filter_by(game_id=row.game_id).one().is_retracted
    issues = missing_source_slots(db, row, draft, accepted, observation, _head)
    clears = set(draft.clear_fields)
    new_slots = {
        p.participant_id: p.model_dump(mode="json")
        for p in draft.players
        if not any(a.participant_id == p.participant_id for a in accepted.players)
    }
    for participant, value in new_slots.items():
        head = _head(db, row, participant, "roster", baseline)
        if not head.raw_present or head.raw_value != value:
            head.raw_present, head.raw_value = True, value
            head.revision += 1
            head.observation_id = observation.id
            head.proposed_present, head.proposed_value = True, value
            issues.append(issue_for(db, row, observation, "roster", head=head, value=value))
        else:
            issues.extend(
                db.query(models.RoundIssue)
                .filter_by(source_id=row.id, participant_id=participant, field="roster", status="open")
                .all()
            )
    for (participant, field), value in values.items():
        if participant in new_slots:
            continue
        explicit_clear = (f"players.{participant}.{field}" if participant else field) in clears
        if value is None and not explicit_clear:
            continue
        head = _head(db, row, participant, field, baseline)
        actual = baseline.get((participant, field))
        baseline_changed = head.accepted_value != actual
        if baseline_changed:
            head.accepted_value = actual
            head.accepted_present = actual is not None
            head.accepted_revision += 1
        same_raw = head.raw_present and head.raw_value == value
        if same_raw and not baseline_changed:
            current = (
                db.query(models.RoundIssue)
                .filter_by(source_id=row.id, participant_id=participant, field=field, status="open")
                .one_or_none()
            )
            if current:
                current.last_seen_at = utc_now().isoformat()
                issues.append(current)
            continue
        head.raw_present = True
        head.raw_value = value
        head.observation_id = observation.id
        head.revision += 1
        # Read the accepted projection rather than trusting another source's
        # cached baseline. Field baseline revisions change only with this field.
        if participant and baseline.get((participant, "is_retracted")) and field != "is_retracted":
            # Historical evidence of removed slots stays immutable until a
            # separate explicit restoration review; do not revive it by fill.
            continue
        for old in (
            db.query(models.RoundIssue)
            .filter_by(source_id=row.id, participant_id=participant, field=field, status="open")
            .all()
        ):
            old.status = "superseded"
            old.revision += 1
        head.proposed_present = False
        if value == actual:
            continue
        known_slot = not participant or any(p.participant_id == participant for p in accepted.players)
        record = db.query(models.GameRecord).filter_by(game_id=row.game_id).one()
        slot_retracted = bool(participant and baseline.get((participant, "is_retracted")))
        may_fill = (
            actual is None
            and value is not None
            and known_slot
            and field not in {"is_retracted", "detail", "profile_id"}
            and not record.is_retracted
            and not slot_retracted
            and head.accepted_revision == 0
            and not db.query(models.RoundFieldHead)
            .join(models.RoundSource, models.RoundFieldHead.source_id == models.RoundSource.id)
            .filter(
                models.RoundSource.game_id == row.game_id,
                models.RoundFieldHead.participant_id == participant,
                models.RoundFieldHead.field == field,
                models.RoundFieldHead.accepted_revision > 0,
            )
            .count()
        )
        if (
            may_fill
            and not db.query(models.RoundIssue)
            .filter_by(game_id=row.game_id, participant_id=participant, field=field, status="open")
            .count()
        ):
            accepted = patch(accepted, participant, field, value)
            persist_final_results(db, game, accepted)
            head.accepted_value = value
            head.accepted_present = True
            head.accepted_revision += 1
            baseline = draft_values(accepted)
            changed = True
        else:
            head.proposed_present = True
            head.proposed_value = value
            issues.append(issue_for(db, row, observation, "value" if known_slot else "roster", head=head, value=value))
    # Integrity observations never invent balancing values or infer row deletion.
    totals = [p.quarters for p in draft.players]
    integrity = [("roster_completeness", draft.roster_complete, not draft.roster_complete)]
    if totals and all(v is not None for v in totals):
        imbalanced = abs(sum(totals)) > 1e-9
        integrity.append(("non_zero_sum", sorted(totals) if imbalanced else None, imbalanced))
    for kind, value, unhealthy in integrity:
        issues.extend(
            review_signal(db, row, observation, _head(db, row, "", kind, {}), kind, value, unhealthy=unhealthy)
        )
    row.latest_observation_key = observation_key
    row.snapshot_fingerprint = content
    retain_alias(db, row.game_id, accepted)
    return _outcome(db, row, issues, changed)


def resolve_issue(db, issue_id, decision, *, actor_profile_id):
    acquire_reconciliation_lock(db)
    from app.services.round_review import require_reviewer

    actor = db.query(models.PlayerProfile).filter_by(id=actor_profile_id).populate_existing().one_or_none()
    if actor is None:
        raise HTTPException(403, "Active confirmed reviewer or administrator required")
    require_reviewer(db, actor)
    issue = db.query(models.RoundIssue).filter_by(id=issue_id).populate_existing().one_or_none()
    if issue is None:
        raise HTTPException(404, "Issue not found")
    row = db.query(models.RoundSource).filter_by(id=issue.source_id).populate_existing().one()
    game = _game(db, issue.game_id) if issue.game_id else None
    head = (
        db.query(models.RoundFieldHead)
        .filter_by(source_id=row.id, participant_id=issue.participant_id, field=issue.field)
        .populate_existing()
        .one_or_none()
    )
    if (
        issue.status != "open"
        or issue.revision != decision.expected_issue_revision
        or issue.head_revision != decision.expected_head_revision
        or (head and head.revision != decision.expected_head_revision)
        or (game is not None and game.revision != decision.expected_game_revision)
        or row.game_id != issue.game_id
        or (game is None and decision.expected_game_revision is not None)
    ):
        raise HTTPException(409, "Stale reconciliation decision")
    if head and game and issue.kind == "value":
        current = draft_values(accepted_draft(db, game.game_id))
        if (game.state or {}).get("hole_history"):
            current[("", "detail")] = {
                "coverage": db.query(models.GameRecord).filter_by(game_id=game.game_id).one().detail_coverage,
                "holes": sorted(game.state["hole_history"], key=lambda h: h["hole"]),
            }
        current[("", "is_retracted")] = db.query(models.GameRecord).filter_by(game_id=game.game_id).one().is_retracted
        if current.get((issue.participant_id, issue.field)) != issue.accepted_value:
            raise HTTPException(409, "Accepted field baseline advanced; review current evidence")
    observation = db.get(models.RoundObservation, issue.observation_id)
    proposed = RoundDraft.model_validate(observation.parsed_values)
    action = decision.action
    selected = issue.proposed_value if action == "accept" else decision.value
    if action == "keep":
        selected = issue.accepted_value
    if action in {"bind_existing", "confirm_distinct"}:
        if issue.kind not in {"identity", "continuity"}:
            raise HTTPException(400, "Binding decision requires an identity or continuity issue")
        target = decision.target_game_id
        if action == "confirm_distinct" and row.game_id is not None:
            raise HTTPException(409, "A bound source requires reviewed rebind, not distinct creation")
        if action == "bind_existing":
            if not target or (
                not _game(db, target) and not db.query(models.GameRecord).filter_by(game_id=target).first()
            ):
                raise HTTPException(404, "Target UUID not found")
        else:
            target = None
        if target:
            target_game = _game(db, target)
            if (target_game.revision if target_game else None) != decision.expected_target_game_revision:
                raise HTTPException(409, "Binding target revision advanced")
        previous_game_id = row.game_id
        game = _bind(db, row, proposed, target, actor_profile_id)
        if previous_game_id and previous_game_id != game.game_id:
            # Old raw observations/resolutions retain their UUID provenance;
            # mutable heads restart from the newly reviewed target baseline.
            baseline = draft_values(accepted_draft(db, game.game_id))
            for old_head in db.query(models.RoundFieldHead).filter_by(source_id=row.id):
                old_head.raw_present = False
                old_head.proposed_present = False
                old_head.accepted_value = baseline.get((old_head.participant_id, old_head.field))
                old_head.accepted_present = old_head.accepted_value is not None
                old_head.accepted_revision += 1
                old_head.revision += 1
        issue.game_id = game.game_id
        # Binding existing evidence is not acceptance of its competing values.
        # Reconcile it now under the same transaction against the target baseline.
        observe_round(
            db,
            SourceRef(kind=row.kind, scope=row.scope, round_token=row.round_token),
            proposed,
            observation_key=f"review-bind:{issue.id}",
            raw_payload=observation.raw_payload,
            continuity_verified=True,
        )
    elif action in {"accept", "correct", "retract"}:
        if game is None:
            raise HTTPException(400, "Value resolution requires a bound game")
        accepted = accepted_draft(db, game.game_id)
        if issue.kind not in {"value", "roster"} and action != "retract":
            raise HTTPException(400, "Integrity issues require keep or explicit retract, not value acceptance")
        if action == "retract":
            persist_final_results(db, game, accepted, retracted=True)
            for status_head in db.query(models.RoundFieldHead).filter_by(
                source_id=row.id, participant_id="", field="is_retracted"
            ):
                status_head.raw_present = False
            selected = True
        else:
            if issue.kind == "roster":
                from app.schemas.round_identity import RoundParticipant

                participant = RoundParticipant.model_validate(selected)
                if participant.participant_id != issue.participant_id:
                    raise HTTPException(400, "Reviewed roster must retain the stable slot")
                accepted = RoundDraft.model_validate(
                    {**accepted.model_dump(), "players": [*accepted.players, participant], "roster_complete": False}
                )
            restored = ()
            if issue.field == "is_retracted" and selected is False:
                if action != "correct":
                    raise HTTPException(400, "Restoration requires explicit corrected-value review")
                restored = (issue.participant_id,)
            if issue.field == "is_retracted" and not issue.participant_id:
                if action != "correct" or type(selected) is not bool:
                    raise HTTPException(400, "Game restoration requires explicit boolean corrected-value review")
                persist_final_results(db, game, accepted, retracted=selected)
            else:
                if issue.kind != "roster":
                    accepted = patch(accepted, issue.participant_id, issue.field, selected)
                persist_final_results(
                    db,
                    game,
                    accepted,
                    restore_participants=restored,
                    accepted_roster_complete=selected if issue.field == "roster_complete" else None,
                )
            head.accepted_value = selected
            head.accepted_present = selected is not None
            head.accepted_revision += 1
            head.proposed_present = False
            retain_alias(db, game.game_id, accepted)
    elif action != "keep":
        raise HTTPException(400, "Unsupported resolution")
    if head:
        head.proposed_present = False
    db.add(
        models.RoundResolution(
            issue_id=issue.id,
            actor_profile_id=actor_profile_id,
            action=action,
            reason=decision.reason,
            value_present=issue.accepted_present if action == "keep" else True,
            value=selected,
            target_game_id=row.game_id,
            game_revision=game.revision if game else None,
            issue_revision=issue.revision,
            head_revision=issue.head_revision,
            baseline_revision=issue.baseline_revision,
            observation_ids=[observation.id],
        )
    )
    issue.status = "resolved"
    issue.revision += 1
    db.flush()
    remaining = db.query(models.RoundIssue).filter_by(source_id=row.id, status="open").all()
    return _outcome(db, row, remaining, True)
