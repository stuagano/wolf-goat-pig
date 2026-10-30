"""Authorized review adapters. Services own rules; HTTP owns transactions."""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import ValidationError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.routers.notifications import RoundRequeue, requeue_round_alerts, round_delivery_health
from app.schemas.round_identity import (
    IngestOutcome,
    RecipientAttestation,
    RecipientConfirmation,
    ResolutionDecision,
    RoundAliasResult,
    read_round_identity_config,
)
from app.services.auth_service import get_current_auth0_user, get_current_user
from app.services.round_identity import resolve_round_alias
from app.services.round_reconciliation import resolve_issue
from app.services.round_review import confirm_routing, public_round, require_reviewer
from app.services.round_writes import writer_mode
from app.utils.admin_auth import is_admin_profile

router = APIRouter(prefix="/round-reconciliation", tags=["round-reconciliation"])


def reviewer(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return require_reviewer(db, user)


def administrator(user=Depends(get_current_user)):
    if not user.is_active or not is_admin_profile(user):
        raise HTTPException(403, "Active administrator required")
    return user


def issue_view(issue):
    return {
        key: getattr(issue, key)
        for key in (
            "id",
            "game_id",
            "kind",
            "participant_id",
            "field",
            "candidate_game_ids",
            "status",
            "revision",
            "head_revision",
            "baseline_revision",
            "accepted_present",
            "accepted_value",
            "proposed_present",
            "proposed_value",
            "created_at",
            "last_seen_at",
        )
    }


@router.get("/aliases", response_model=RoundAliasResult)
def aliases(date: str, group: str, location: str = "", db: Session = Depends(get_db)):
    accessible = []
    for game_id in resolve_round_alias(db, date, group, location):
        try:
            public_round(db, game_id)
        except HTTPException as exc:
            if exc.status_code != 404:
                raise
        else:
            accessible.append(game_id)
    ids = sorted(set(accessible))
    return {"status": "resolved" if len(ids) == 1 else "ambiguous" if ids else "missing", "game_ids": ids}


@router.get("/health")
def health(user=Depends(reviewer), db: Session = Depends(get_db)):
    delivery = round_delivery_health(user, db)
    config = read_round_identity_config(db)
    return {
        **delivery,
        "mode": config.mode,
        "epoch": config.epoch,
        "issues": [
            {"status": status, "count": count}
            for status, count in db.query(models.RoundIssue.status, func.count(models.RoundIssue.id)).group_by(
                models.RoundIssue.status
            )
        ],
        "manifest_verifier_available": False,
    }


@router.post("/recipient/attest")
def attest(
    request: RecipientAttestation,
    user=Depends(get_current_user),
    claims=Depends(get_current_auth0_user),
    db: Session = Depends(get_db),
):
    from app.services.round_recipient import attest_recipient

    try:
        result = attest_recipient(db, user.id, claims)
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise


@router.post("/recipient/attest/revoke")
def revoke(user=Depends(get_current_user), db: Session = Depends(get_db)):
    from app.services.round_recipient import revoke_attestation

    try:
        revoke_attestation(db, user.id)
        db.commit()
        return {"revoked": True}
    except Exception:
        db.rollback()
        raise


@router.put("/recipient")
def recipient(
    request: RecipientConfirmation,
    user=Depends(administrator),
    claims=Depends(get_current_auth0_user),
    db: Session = Depends(get_db),
):
    try:
        result = confirm_routing(db, request, user, claims)
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise


@router.post("/requeue")
def requeue(request: RoundRequeue, user=Depends(administrator), db: Session = Depends(get_db)):
    if not request.reason.strip():
        raise HTTPException(422, "A requeue reason is required")
    # Reuse Task 6's exact selection, audit and commit/rollback semantics.
    return requeue_round_alerts(request, user, db)


@router.get("/issues")
def issues(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: str | None = None,
    user=Depends(reviewer),
    db: Session = Depends(get_db),
):
    query = db.query(models.RoundIssue)
    if status is not None:
        if status not in {"open", "resolved", "superseded"}:
            raise HTTPException(422, "Invalid issue status")
        query = query.filter_by(status=status)
    total = query.count()
    rows = query.order_by(models.RoundIssue.created_at, models.RoundIssue.id).offset(offset).limit(limit).all()
    return {"items": [issue_view(row) for row in rows], "total": total, "offset": offset, "limit": limit}


@router.get("/issues/{issue_id}")
def issue_detail(issue_id: str, user=Depends(reviewer), db: Session = Depends(get_db)):
    issue = db.get(models.RoundIssue, issue_id)
    if not issue:
        raise HTTPException(404, "Issue unavailable")
    observation = db.get(models.RoundObservation, issue.observation_id) if issue.observation_id else None
    source = db.get(models.RoundSource, issue.source_id)
    audit = (
        db.query(models.RoundResolution).filter_by(issue_id=issue_id).order_by(models.RoundResolution.created_at).all()
    )
    game = db.query(models.GameStateModel).filter_by(game_id=issue.game_id).one_or_none() if issue.game_id else None
    head = (
        db.query(models.RoundFieldHead)
        .filter_by(source_id=issue.source_id, participant_id=issue.participant_id, field=issue.field)
        .one_or_none()
    )
    return {
        **issue_view(issue),
        "game_revision": game.revision if game else None,
        "current_head_revision": head.revision if head else source.revision,
        "source": {
            key: getattr(source, key)
            for key in ("id", "kind", "scope", "round_token", "game_id", "revision", "binding_evidence")
        },
        "observation": {
            key: getattr(observation, key)
            for key in ("id", "raw_payload", "parsed_values", "present_fields", "continuity_verified", "observed_at")
        }
        if observation
        else None,
        "audit": [
            {
                key: getattr(row, key)
                for key in (
                    "id",
                    "actor_profile_id",
                    "action",
                    "reason",
                    "value",
                    "value_present",
                    "target_game_id",
                    "game_revision",
                    "issue_revision",
                    "head_revision",
                    "baseline_revision",
                    "observation_ids",
                    "created_at",
                )
            }
            for row in audit
        ],
    }


@router.post(
    "/issues/{issue_id}/resolve",
    response_model=IngestOutcome,
    responses={
        202: {"model": IngestOutcome, "description": "Accepted decision; outstanding evidence held"},
        404: {"description": "Issue or target unavailable"},
        409: {"description": "Stale revision or paused writer fence"},
    },
)
def resolve(
    issue_id: str,
    decision: ResolutionDecision,
    response: Response,
    user=Depends(reviewer),
    db: Session = Depends(get_db),
):
    try:
        writer_mode(db)  # Acquires the shared fence; review cannot bypass pause.
        # Authorization is revalidated under that lock from refreshed rows: a
        # revoked confirmation/linkage before the lock must not still resolve.
        require_reviewer(db, user)
        outcome = resolve_issue(db, issue_id, decision, actor_profile_id=user.id)
        db.commit()
        if outcome.status == "held":
            response.status_code = 202
        return outcome
    except HTTPException as exc:
        db.rollback()
        if exc.status_code == 400:
            raise HTTPException(422, exc.detail) from exc
        raise
    except (ValidationError, ValueError, TypeError, KeyError, StopIteration) as exc:
        db.rollback()
        raise HTTPException(422, "Invalid reviewed value") from exc
    except Exception:
        db.rollback()
        raise
