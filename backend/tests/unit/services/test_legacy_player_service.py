"""Unit tests for the DB-backed legacy player service.

Covers the canonical roster (seed, add, validate, fuzzy-match), the pending
capture queue, and the load-bearing invariant: a captured-but-unpromoted
player must NEVER read as canonical (otherwise their signups would silently
fail at the legacy CGI).
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, LegacyRosterPlayer, PendingLegacyPlayer
from app.services import legacy_player_service as svc

TEST_DATABASE_URL = "sqlite:///./test_legacy_roster.db"
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


# ── Seeding ──────────────────────────────────────────────────────────────────


def test_seed_roster_if_empty_populates_table(db):
    inserted = svc.seed_roster_if_empty(db)
    assert inserted > 0
    assert db.query(LegacyRosterPlayer).count() == inserted


def test_seed_roster_if_empty_is_idempotent(db):
    first = svc.seed_roster_if_empty(db)
    second = svc.seed_roster_if_empty(db)
    assert first > 0
    assert second == 0
    assert db.query(LegacyRosterPlayer).count() == first


# ── Canonical reads ──────────────────────────────────────────────────────────


def test_add_and_get_canonical_name_is_case_insensitive(db):
    svc.add_legacy_player("Tiger Woods", db=db)
    assert svc.get_canonical_name("tiger woods", db) == "Tiger Woods"
    assert svc.get_canonical_name("TIGER WOODS", db) == "Tiger Woods"


def test_is_valid_legacy_player(db):
    svc.add_legacy_player("Phil Mickelson", db=db)
    assert svc.is_valid_legacy_player("phil mickelson", db) is True
    assert svc.is_valid_legacy_player("Nobody Here", db) is False


def test_get_legacy_players_is_sorted(db):
    svc.add_legacy_player("Zed Zee", db=db)
    svc.add_legacy_player("Aaron Able", db=db)
    players = svc.get_legacy_players(db)
    assert players == sorted(players)
    assert "Aaron Able" in players and "Zed Zee" in players


def test_find_similar_players_fuzzy_matches(db):
    svc.add_legacy_player("Jonathan Smith", db=db)
    matches = svc.find_similar_players("Jonathon Smith", db=db)
    assert "Jonathan Smith" in matches


def test_validate_valid_player(db):
    svc.add_legacy_player("Rory McIlroy", db=db)
    result = svc.validate_player_for_legacy("rory mcilroy", db)
    assert result["valid"] is True
    assert result["canonical_name"] == "Rory McIlroy"


def test_validate_unknown_player_with_suggestion(db):
    svc.add_legacy_player("Brooks Koepka", db=db)
    result = svc.validate_player_for_legacy("Brook Koepka", db)
    assert result["valid"] is False
    assert "Brooks Koepka" in result["suggestions"]


# ── Canonical writes ─────────────────────────────────────────────────────────


def test_add_legacy_player_dedups(db):
    first = svc.add_legacy_player("Dustin Johnson", db=db)
    second = svc.add_legacy_player("dustin johnson", db=db)
    assert first["added"] is True
    assert second["added"] is False
    assert db.query(LegacyRosterPlayer).filter(LegacyRosterPlayer.name == "Dustin Johnson").count() == 1


# ── Pending capture queue ────────────────────────────────────────────────────


def test_capture_pending_player(db):
    result = svc.capture_pending_player("New Golfer", email="new@example.com", db=db)
    assert result["captured"] is True
    row = db.query(PendingLegacyPlayer).filter(PendingLegacyPlayer.name == "New Golfer").first()
    assert row is not None
    assert row.status == "pending"
    assert row.email == "new@example.com"


def test_capture_skips_already_canonical(db):
    svc.add_legacy_player("Existing Player", db=db)
    result = svc.capture_pending_player("existing player", db=db)
    assert result["captured"] is False
    assert result["reason"] == "already_canonical"


def test_capture_skips_duplicate_pending(db):
    svc.capture_pending_player("Repeat Golfer", db=db)
    result = svc.capture_pending_player("Repeat Golfer", db=db)
    assert result["captured"] is False
    assert result["reason"] == "already_pending"


def test_capture_skips_unknown_player(db):
    result = svc.capture_pending_player("Unknown Player", db=db)
    assert result["captured"] is False
    assert result["reason"] == "blank_or_unknown"


def test_list_pending_players(db):
    svc.capture_pending_player("Pending One", db=db)
    svc.capture_pending_player("Pending Two", db=db)
    pending = svc.list_pending_players(db=db)
    names = {p["name"] for p in pending}
    assert {"Pending One", "Pending Two"} <= names


def test_promote_pending_player_makes_canonical(db):
    captured = svc.capture_pending_player("Promote Me", db=db)
    pending_id = captured["pending_id"]

    # Invariant precondition: not canonical while pending.
    assert svc.get_canonical_name("Promote Me", db) is None
    assert svc.validate_player_for_legacy("Promote Me", db)["valid"] is False

    result = svc.promote_pending_player(pending_id, db=db)
    assert result["promoted"] is True
    assert svc.get_canonical_name("Promote Me", db) == "Promote Me"

    row = db.query(PendingLegacyPlayer).filter(PendingLegacyPlayer.id == pending_id).first()
    assert row.status == "promoted"
    assert row.resolved_at is not None


def test_dismiss_pending_player(db):
    captured = svc.capture_pending_player("Dismiss Me", db=db)
    result = svc.dismiss_pending_player(captured["pending_id"], db=db)
    assert result["dismissed"] is True
    row = db.query(PendingLegacyPlayer).filter(PendingLegacyPlayer.id == captured["pending_id"]).first()
    assert row.status == "dismissed"


# ── The load-bearing invariant ───────────────────────────────────────────────


def test_pending_player_never_reads_as_canonical(db):
    """A captured pending player must not leak into any canonical read."""
    svc.add_legacy_player("Anchor Player", db=db)  # non-empty table → no JSON fallback
    svc.capture_pending_player("Ghost Golfer", db=db)

    assert svc.get_canonical_name("Ghost Golfer", db) is None
    assert svc.is_valid_legacy_player("Ghost Golfer", db) is False
    assert "Ghost Golfer" not in svc.get_legacy_players(db)
    assert "Ghost Golfer" not in svc.find_similar_players("Ghost Golfer", db=db)
    assert svc.validate_player_for_legacy("Ghost Golfer", db)["valid"] is False


# ── Roster auto-sync from round history ──────────────────────────────────────


def test_sync_adds_new_dropdown_shaped_members(db):
    svc.add_legacy_player("Anchor Player", db=db)
    result = svc.sync_roster_from_members(["Anchor Player", "Casey Newmember"], db=db)
    assert result["added"] == ["Casey Newmember"]
    assert svc.get_canonical_name("Casey Newmember", db) == "Casey Newmember"


def test_sync_skips_format_divergent_names(db):
    result = svc.sync_roster_from_members(["Smith, Mike", "Mike S", "Real Fullname"], db=db)
    assert "Real Fullname" in result["added"]
    assert set(result["skipped_format"]) == {"Smith, Mike", "Mike S"}
    # Divergent formats must NOT become canonical (they'd silently fail at the CGI).
    assert svc.get_canonical_name("Smith, Mike", db) is None
    assert svc.get_canonical_name("Mike S", db) is None


def test_sync_dedups_within_batch(db):
    result = svc.sync_roster_from_members(["Dup Player", "dup player", "DUP PLAYER"], db=db)
    assert result["added"] == ["Dup Player"]
    assert db.query(LegacyRosterPlayer).filter(LegacyRosterPlayer.name == "Dup Player").count() == 1


def test_sync_resolves_matching_pending(db):
    svc.capture_pending_player("Returning Golfer", db=db)
    assert svc.get_canonical_name("Returning Golfer", db) is None

    result = svc.sync_roster_from_members(["Returning Golfer"], db=db)
    assert "Returning Golfer" in result["added"]
    assert "Returning Golfer" in result["resolved"]

    row = db.query(PendingLegacyPlayer).filter(PendingLegacyPlayer.name == "Returning Golfer").first()
    assert row.status == "promoted"


def test_sync_does_not_resolve_pending_for_format_divergent_member(db):
    # A pending name that only appears in a format-divergent member string must
    # stay pending (we never confirmed it canonical).
    svc.capture_pending_player("Mike S", db=db)
    result = svc.sync_roster_from_members(["Mike S"], db=db)
    assert "Mike S" not in result["resolved"]
    row = db.query(PendingLegacyPlayer).filter(PendingLegacyPlayer.name == "Mike S").first()
    assert row.status == "pending"


def test_sync_never_deletes_existing(db):
    svc.add_legacy_player("Kept Player", db=db)
    svc.sync_roster_from_members(["Someone Else"], db=db)
    assert svc.get_canonical_name("Kept Player", db) == "Kept Player"
