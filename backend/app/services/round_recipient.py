"""Trusted prospective-recipient proof using existing immutable observations.

Proof is valid for at most 24 hours, only for its unique current linkage, current
writer epoch and latest consent event. Selection additionally requires unchanged
routing configuration since attestation. Revocation appends evidence; neither
attestation nor revocation silently selects a recipient or sends alerts.
"""

from datetime import datetime, timedelta
from hashlib import sha256
from uuid import uuid4

from fastapi import HTTPException

from app import models
from app.schemas.round_identity import read_round_identity_config
from app.services.round_evidence import fingerprint
from app.services.round_identity import acquire_reconciliation_lock
from app.utils.time import utc_now


def fresh_profile(db, profile_id):
    return db.query(models.PlayerProfile).filter_by(id=profile_id).populate_existing().one_or_none()


def fresh_config(db):
    row = db.query(models.AppConfig).filter_by(name="round_identity").populate_existing().one_or_none()
    return row, read_round_identity_config(db)


def linkage(db, profile):
    subject = (profile.preferences or {}).get("auth0_id") if profile else None
    if not (profile and profile.is_active and not profile.is_ai and profile.email and subject):
        return None
    matches = (
        db.query(models.PlayerProfile)
        .filter(models.PlayerProfile.preferences["auth0_id"].as_string() == subject)
        .populate_existing()
        .all()
    )
    if len(matches) != 1 or matches[0].id != profile.id:
        return None
    return {
        "auth0_id": subject,
        "email_verified": True,
        "email_sha256": sha256(profile.email.strip().lower().encode()).hexdigest(),
    }


def routing_stamp(row):
    value = row.value if row else {}
    return fingerprint(
        {
            key: value.get(key)
            for key in (
                "reviewer_profile_id",
                "routing_confirmed",
                "routing_confirmed_at",
                "routing_attestation_id",
                "routing_confirmed_by_profile_id",
                "routing_linkage_evidence",
                "routing_audit",
            )
        }
    )


def attest_recipient(db, actor_id, claims):
    acquire_reconciliation_lock(db)
    actor = fresh_profile(db, actor_id)
    evidence = linkage(db, actor)
    if not (
        evidence
        and claims.get("sub") == evidence["auth0_id"]
        and claims.get("email_verified") is True
        and (claims.get("email") or "").strip().lower() == actor.email.strip().lower()
    ):
        raise HTTPException(422, "Active unique verified own-account linkage required")
    return _event(db, actor_id, "attest", evidence)


def revoke_attestation(db, actor_id):
    acquire_reconciliation_lock(db)
    actor = fresh_profile(db, actor_id)
    if not actor or not actor.is_active:
        raise HTTPException(403, "Active account required")
    return _event(db, actor_id, "revoke", {})


def _event(db, profile_id, action, evidence):
    source = (
        db.query(models.RoundSource)
        .filter_by(kind="recipient_consent", scope="profile", round_token=str(profile_id))
        .populate_existing()
        .one_or_none()
    )
    if source is None:
        source = models.RoundSource(kind="recipient_consent", scope="profile", round_token=str(profile_id))
        db.add(source)
        db.flush()
    row, config = fresh_config(db)
    now = utc_now()
    key = str(uuid4())
    proof = models.RoundObservation(
        source_id=source.id,
        observation_key=key,
        raw_payload={"action": action, "actor_profile_id": profile_id},
        parsed_values={
            "action": action,
            "profile_id": profile_id,
            "linkage": evidence,
            "epoch": config.epoch,
            "routing_stamp": routing_stamp(row),
            "attested_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=24)).isoformat(),
        },
        continuity_verified=True,
    )
    db.add(proof)
    source.revision += 1
    source.latest_observation_key = key
    db.flush()
    return {"attestation_id": proof.id, "expires_at": proof.parsed_values["expires_at"]}


def valid_attestation(db, proof_id, profile, *, for_selection=False):
    proof = db.get(models.RoundObservation, proof_id) if proof_id else None
    if not proof:
        return None
    source = db.query(models.RoundSource).filter_by(id=proof.source_id).populate_existing().one_or_none()
    value = proof.parsed_values or {}
    row, config = fresh_config(db)
    try:
        timely = datetime.fromisoformat(value["attested_at"]) <= utc_now() < datetime.fromisoformat(value["expires_at"])
    except (ValueError, KeyError, TypeError):
        return None
    if not (
        source
        and source.kind == "recipient_consent"
        and source.scope == "profile"
        and source.round_token == str(profile.id)
        and source.latest_observation_key == proof.observation_key
        and value.get("action") == "attest"
        and value.get("profile_id") == profile.id
        and value.get("epoch") == config.epoch
        and timely
        and value.get("linkage") == linkage(db, profile)
        and (not for_selection or value.get("routing_stamp") == routing_stamp(row))
    ):
        return None
    return value["linkage"]
