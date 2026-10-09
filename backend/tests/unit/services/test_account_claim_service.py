"""Claim storage and the rules for when picking a taken name becomes a claim."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import AccountClaim, LegacyRosterPlayer, PlayerProfile
from app.services import account_claim_service as svc
from app.services.legacy_player_service import link_profile_to_canonical_name


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    for name in ["Gregg Colburn", "Kevin Gent", "Dom Damico", "Chip Halbert"]:
        session.add(LegacyRosterPlayer(name=name, source="seed", added_at="2026-01-01"))
    session.add_all(
        [
            PlayerProfile(id=1, name="Gregg Colburn", legacy_name="Gregg Colburn", created_at="2025-01-01"),
            PlayerProfile(
                id=2,
                name="gregg@example.com",
                email="gregg@example.com",
                preferences={"auth0_id": "auth0|gregg"},
                created_at="2026-10-09",
            ),
            PlayerProfile(
                id=3,
                name="Kevin Gent",
                legacy_name="Kevin Gent",
                preferences={"auth0_id": "google-oauth2|kevin"},
                created_at="2025-01-01",
            ),
            PlayerProfile(id=4, name="old stray", legacy_name="Dom Damico", is_active=0, created_at="2026-01-01"),
            PlayerProfile(id=5, name="Chip Halbert", legacy_name="Chip Halbert", created_at="2025-01-01"),
        ]
    )
    session.commit()
    yield session
    session.close()
    engine.dispose()


def test_holder_lookup_ignores_retired_profiles(db):
    assert svc.find_name_holder(db, "gregg colburn").id == 1
    assert svc.find_name_holder(db, "Dom Damico") is None


def test_retired_profile_no_longer_blocks_linking_its_name(db):
    result = link_profile_to_canonical_name(db, 2, "Dom Damico")
    assert result["linked"] is True


def test_name_held_by_login_less_original_becomes_a_pending_claim(db):
    out = svc.request_claim_for_name(
        db, db.get(PlayerProfile, 2), "Gregg Colburn", email="gregg@example.com", email_verified=True
    )
    db.commit()
    assert out["status"] == "pending" and out["created"] is True
    claim = out["claim"]
    assert (claim.requester_profile_id, claim.target_profile_id, claim.canonical_name, claim.status) == (
        2,
        1,
        "Gregg Colburn",
        "pending",
    )
    assert claim.requester_email == "gregg@example.com"
    assert svc.pending_claim_for(db, 2).id == claim.id


def test_repeat_request_reuses_the_pending_claim(db):
    first = svc.request_claim_for_name(
        db, db.get(PlayerProfile, 2), "Gregg Colburn", email="g@x.com", email_verified=True
    )
    again = svc.request_claim_for_name(
        db, db.get(PlayerProfile, 2), "Gregg Colburn", email="g@x.com", email_verified=True
    )
    db.commit()
    assert again["created"] is False and again["claim"].id == first["claim"].id
    assert db.query(AccountClaim).count() == 1


def test_picking_a_different_name_supersedes_the_old_claim(db):
    first = svc.request_claim_for_name(
        db, db.get(PlayerProfile, 2), "Gregg Colburn", email="g@x.com", email_verified=True
    )
    second = svc.request_claim_for_name(
        db, db.get(PlayerProfile, 2), "Chip Halbert", email="g@x.com", email_verified=True
    )
    db.commit()
    assert second["created"] is True and second["claim"].target_profile_id == 5
    old = db.get(AccountClaim, first["claim"].id)
    assert (old.status, old.resolved_by) == ("dismissed", "superseded")
    assert svc.pending_claim_for(db, 2).id == second["claim"].id


def test_name_held_by_a_profile_with_a_login_is_taken(db):
    out = svc.request_claim_for_name(db, db.get(PlayerProfile, 2), "Kevin Gent", email="g@x.com", email_verified=True)
    assert out == {"status": "taken"}
    assert db.query(AccountClaim).count() == 0


def test_unverified_requester_cannot_claim(db):
    out = svc.request_claim_for_name(
        db, db.get(PlayerProfile, 2), "Gregg Colburn", email="g@x.com", email_verified=False
    )
    assert out == {"status": "unverified"}
    assert db.query(AccountClaim).count() == 0
