"""Trusted consent and shared authorization; no identity/provider calls."""

from datetime import timedelta

import pytest
from fastapi import HTTPException

from app import models
from app.schemas.round_identity import RecipientConfirmation, ResolutionDecision
from app.services.round_delivery import confirmed_recipient
from app.services.round_recipient import attest_recipient, revoke_attestation
from app.services.round_reconciliation import resolve_issue
from app.services.round_review import confirm_routing
from app.utils.time import utc_now
from tests.unit.routers.test_round_reconciliation_api import round_api, seed


def configure(db):
    proof = attest_recipient(
        db,
        7,
        {
            "sub": "auth0|review",
            "email": "review@example.invalid",
            "email_verified": True,
        },
    )
    confirm_routing(
        db,
        RecipientConfirmation(
            profile_id=7, attestation_id=proof["attestation_id"], confirmed=True, reason="Synthetic selection"
        ),
        db.get(models.PlayerProfile, 8),
        {},
    )
    return proof["attestation_id"]


def test_proof_immutable_audited_and_revoke_never_changes_route(round_api):
    _, _, sessions = round_api
    with sessions() as db:
        proof_id = configure(db)
        db.commit()
    with sessions() as db:
        proof = db.get(models.RoundObservation, proof_id)
        assert proof.raw_payload == {"action": "attest", "actor_profile_id": 7}
        assert proof.parsed_values["linkage"]["email_verified"] is True
        assert "review@example.invalid" not in str(proof.parsed_values)
        proof.parsed_values = {"forged": True}
        with pytest.raises(ValueError, match="immutable"):
            db.flush()
        db.rollback()
    with sessions() as db:
        before = dict(db.get(models.AppConfig, "round_identity").value)
        revoke_attestation(db, 7)
        assert confirmed_recipient(db) is None
        assert db.get(models.AppConfig, "round_identity").value == before
        assert db.query(models.RoundObservation).count() == 2
        assert db.query(models.Notification).count() == 0
        db.commit()
    with sessions() as db:
        assert db.get(models.RoundObservation, proof_id).parsed_values["action"] == "attest"
        assert confirmed_recipient(db) is None


@pytest.mark.parametrize("invalid", ["expiry", "missing", "confirmation", "linkage", "actor", "epoch"])
def test_shared_resolver_rejects_revoked_authority_with_cached_rows(round_api, monkeypatch, invalid):
    from app.services import round_recipient

    _, _, sessions = round_api
    game, issue, decision = seed(sessions)
    with sessions() as db:
        configure(db)
        db.commit()
    with sessions() as stale:
        # Retain rows in the identity map across another transaction's changes.
        config = stale.get(models.AppConfig, "round_identity")
        profile = stale.get(models.PlayerProfile, 7)
        admin = stale.get(models.PlayerProfile, 8)
        assert confirmed_recipient(stale).id == profile.id
        if invalid == "expiry":
            future = utc_now() + timedelta(days=2)
            monkeypatch.setattr(round_recipient, "utc_now", lambda: future)
        else:
            with sessions() as writer:
                row = writer.get(models.AppConfig, "round_identity")
                value = dict(row.value)
                if invalid == "missing":
                    value.pop("routing_attestation_id")
                elif invalid == "confirmation":
                    value["routing_confirmed"] = False
                elif invalid == "epoch":
                    value["epoch"] += 1
                elif invalid == "linkage":
                    writer.get(models.PlayerProfile, 7).preferences = {"auth0_id": "auth0|changed"}
                else:
                    writer.get(models.PlayerProfile, 8).admin_granted = 0
                row.value = value
                writer.commit()
        before = stale.query(models.GameRecord).filter_by(game_id=game).one().final_scores
        with pytest.raises(HTTPException) as error:
            resolve_issue(stale, issue, ResolutionDecision(**decision), actor_profile_id=7)
        assert error.value.status_code == 403
        assert stale.query(models.RoundResolution).count() == 0
        assert stale.get(models.RoundIssue, issue).status == "open"
        assert stale.query(models.GameRecord).filter_by(game_id=game).one().final_scores == before
        assert config and admin  # Keep strong references through the check.
        stale.rollback()
