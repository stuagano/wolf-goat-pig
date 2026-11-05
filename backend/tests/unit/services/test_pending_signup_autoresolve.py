"""A pending sign-up must not stay an admin task once the golfer is linked.

Regression: a new golfer whose Auth0 name didn't match the roster was captured
into Pending Sign-ups, then picked their roster name in onboarding. The profile
linked, but the pending row stayed, so admins still saw a manual task.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, LegacyRosterPlayer, PendingLegacyPlayer, PlayerProfile
from app.services import legacy_player_service as svc

TEST_DATABASE_URL = "sqlite:///./test_pending_autoresolve.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _new_signup(db, *, name="newgolfer@example.com", legacy_name=None, is_active=1):
    db.add(LegacyRosterPlayer(name="Pat Golfer", source="seed"))
    profile = PlayerProfile(name=name, email="newgolfer@example.com", legacy_name=legacy_name, is_active=is_active)
    db.add(profile)
    db.flush()
    row = PendingLegacyPlayer(
        name=name, email="newgolfer@example.com", player_profile_id=profile.id, status="pending", created_at="t"
    )
    db.add(row)
    db.commit()
    return profile, row


def test_linking_the_profile_resolves_its_pending_row(db):
    profile, row = _new_signup(db)

    result = svc.link_profile_to_canonical_name(db, profile.id, "Pat Golfer", allow_relink=True)
    db.commit()

    assert result["linked"] is True
    db.refresh(row)
    assert row.status == "promoted"
    assert row.resolved_at
    assert svc.list_pending_players(db=db) == []


def test_failed_link_leaves_the_pending_row(db):
    profile, row = _new_signup(db)
    db.add(PlayerProfile(name="Pat Golfer", legacy_name="Pat Golfer"))
    db.commit()

    result = svc.link_profile_to_canonical_name(db, profile.id, "Pat Golfer", allow_relink=True)
    db.commit()

    assert result["status"] == "claimed"
    db.refresh(row)
    assert row.status == "pending"


def test_listing_heals_rows_whose_profile_is_already_linked(db):
    _profile, row = _new_signup(db, legacy_name="Pat Golfer")

    assert svc.list_pending_players(db=db) == []
    db.refresh(row)
    assert row.status == "promoted"


def test_listing_dismisses_rows_whose_profile_was_retired(db):
    _profile, row = _new_signup(db, is_active=0)

    assert svc.list_pending_players(db=db) == []
    db.refresh(row)
    assert row.status == "dismissed"


def test_listing_keeps_genuinely_unlinked_signups(db):
    _profile, row = _new_signup(db)

    pending = svc.list_pending_players(db=db)

    assert [p["id"] for p in pending] == [row.id]


def test_email_shaped_legacy_name_is_not_a_real_link(db):
    _new_signup(db, legacy_name="newgolfer@example.com")

    assert len(svc.list_pending_players(db=db)) == 1


# ── Email-named sign-ups (Auth0 profile had no display name) ─────────────────


def test_promote_email_named_signup_without_a_name_is_rejected(db):
    _, row = _new_signup(db)

    result = svc.promote_pending_player(row.id, db=db)

    assert result["promoted"] is False
    assert result["invalid"] is True
    assert "Enter the golfer's name" in result["message"]
    db.refresh(row)
    assert row.status == "pending"


def test_promote_email_named_signup_with_new_name_adds_and_links(db):
    profile, row = _new_signup(db)

    result = svc.promote_pending_player(row.id, db=db, name="  Jordan Fish ")

    assert result["promoted"] is True
    assert result["canonical_name"] == "Jordan Fish"
    assert result["profile_linked"] is True
    assert svc.get_canonical_name("Jordan Fish", db) == "Jordan Fish"
    db.refresh(profile)
    db.refresh(row)
    assert profile.legacy_name == "Jordan Fish"
    assert row.status == "promoted"


def test_promote_with_existing_roster_name_links_to_that_player(db):
    profile, row = _new_signup(db)

    result = svc.promote_pending_player(row.id, db=db, name="pat golfer")

    assert result["promoted"] is True
    assert result["canonical_name"] == "Pat Golfer"
    db.refresh(profile)
    assert profile.legacy_name == "Pat Golfer"


def test_email_placeholder_legacy_name_does_not_block_linking(db):
    profile, row = _new_signup(db, legacy_name="newgolfer@example.com")

    result = svc.promote_pending_player(row.id, db=db, name="Pat Golfer")

    assert result["profile_link_status"] == "linked"
    db.refresh(profile)
    assert profile.legacy_name == "Pat Golfer"
