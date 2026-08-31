"""Issue #319: audit incomplete identities without guessing or merging users."""

import pytest
from backend.app.models import DailySignup, LegacyRosterPlayer, PlayerProfile
from scripts.diagnostics import audit_signup_identities as audit_script
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db(monkeypatch):
    engine = create_engine("sqlite://")
    for model in (PlayerProfile, DailySignup, LegacyRosterPlayer):
        model.__table__.create(engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(audit_script, "SessionLocal", factory)
    with factory() as session:
        for player_id, name in ((9, "Brett Saks"), (11, "Jeff Green"), (8, "Steve Sutorius")):
            session.add(LegacyRosterPlayer(name=name, source="test"))
            session.add(
                PlayerProfile(
                    id=player_id,
                    name=name,
                    legacy_name=name,
                    email=f"player{player_id}@example.com",
                    preferences={"auth0_id": f"auth0|test-{player_id}"},
                )
            )
        session.commit()
        yield session
    engine.dispose()


def test_audit_distinct_identities_is_read_only(db):
    assert audit_script.audit(audit_script.DEFAULT_NAMES) == 0
    db.expire_all()
    assert db.query(PlayerProfile).count() == 3
    assert db.get(PlayerProfile, 8).legacy_name == "Steve Sutorius"


@pytest.mark.parametrize("field", ["legacy_name", "email", "preferences"])
def test_audit_does_not_call_missing_identity_evidence_clean(db, capsys, field):
    setattr(db.get(PlayerProfile, 9), field, None)
    db.commit()
    assert audit_script.audit(audit_script.DEFAULT_NAMES) > 0
    assert "missing" in capsys.readouterr().out.lower()
    db.expire_all()
    assert getattr(db.get(PlayerProfile, 9), field) is None


def test_audit_reports_a_missing_requested_player(db, capsys):
    db.delete(db.get(PlayerProfile, 9))
    db.commit()
    assert audit_script.audit(audit_script.DEFAULT_NAMES) > 0
    assert "no matching profile" in capsys.readouterr().out.lower()


def test_audit_detects_shared_auth0_subject_without_repairing_it(db, capsys):
    db.get(PlayerProfile, 9).preferences = {"auth0_id": "auth0|test-8"}
    db.commit()
    assert audit_script.audit(audit_script.DEFAULT_NAMES) > 0
    assert "shared auth0_id" in capsys.readouterr().out.lower()
    db.expire_all()
    assert db.get(PlayerProfile, 9).preferences["auth0_id"] == "auth0|test-8"


def test_audit_detects_case_insensitive_duplicate_email(db, capsys):
    db.get(PlayerProfile, 9).email = "PLAYER8@example.com"
    db.commit()
    assert audit_script.audit(audit_script.DEFAULT_NAMES) > 0
    assert "shared email" in capsys.readouterr().out.lower()


def test_audit_flags_swapped_canonical_links_without_guessing_a_repair(db, capsys):
    db.get(PlayerProfile, 9).legacy_name = "Steve Sutorius"
    db.get(PlayerProfile, 8).legacy_name = "Brett Saks"
    db.commit()
    assert audit_script.audit(audit_script.DEFAULT_NAMES) > 0
    assert "disagrees with canonical profile name" in capsys.readouterr().out
    db.expire_all()
    assert db.get(PlayerProfile, 9).legacy_name == "Steve Sutorius"
    assert db.get(PlayerProfile, 8).legacy_name == "Brett Saks"


def test_audit_reports_orphans_and_lists_consistent_steve_rows_without_cancelling(db, capsys):
    db.add_all(
        [
            DailySignup(id=14, date="2026-07-20", player_profile_id=999, player_name="Steve Sutorius"),
            DailySignup(id=19, date="2026-07-25", player_profile_id=8, player_name="Steve Sutorius"),
        ]
    )
    db.commit()
    assert audit_script.audit(audit_script.DEFAULT_NAMES) > 0
    report = capsys.readouterr().out
    assert "signup id=14" in report and "missing profile" in report
    assert "signup id=19" in report and "2026-07-25" in report
    db.expire_all()
    assert db.get(DailySignup, 14).status == "signed_up"
    assert db.get(DailySignup, 19).status == "signed_up"


def test_audit_reports_wrong_owner_even_when_owner_is_outside_name_filter(db, capsys):
    db.add(PlayerProfile(id=63, name="Billy Moses"))
    db.add(DailySignup(id=20, date="2026-07-24", player_profile_id=63, player_name="Steve Sutorius"))
    db.commit()
    assert audit_script.audit(audit_script.DEFAULT_NAMES) > 0
    report = capsys.readouterr().out
    assert "signup id=20" in report and "Billy Moses" in report


@pytest.mark.parametrize("already_linked", [False, True])
def test_repair_refuses_another_players_claimed_name(db, already_linked):
    if already_linked:
        db.get(PlayerProfile, 9).legacy_name = "Steve Sutorius"
        db.commit()
    with pytest.raises(SystemExit, match="already claimed"):
        audit_script.repair_legacy_name("9=steve sutorius", confirmed=True)
    db.expire_all()
    assert db.get(PlayerProfile, 9).legacy_name == ("Steve Sutorius" if already_linked else "Brett Saks")
    assert db.get(PlayerProfile, 8).legacy_name == "Steve Sutorius"


def test_repair_dry_run_then_changes_only_the_link_and_is_repeatable(db):
    db.get(PlayerProfile, 9).legacy_name = "Steve Sutorius"
    db.commit()
    audit_script.repair_legacy_name("9=Brett Saks", confirmed=False)
    db.expire_all()
    assert db.get(PlayerProfile, 9).legacy_name == "Steve Sutorius"
    for _ in range(2):
        audit_script.repair_legacy_name("9=Brett Saks", confirmed=True)
    db.expire_all()
    brett = db.get(PlayerProfile, 9)
    assert brett.legacy_name == "Brett Saks"
    assert brett.email == "player9@example.com"
    assert brett.preferences == {"auth0_id": "auth0|test-9"}
    assert db.get(PlayerProfile, 8).legacy_name == "Steve Sutorius"
    assert db.query(PlayerProfile).count() == 3


@pytest.mark.parametrize("spec", ["not-an-id=Brett Saks", "9=Not A Roster Player", "999=Brett Saks"])
def test_invalid_repair_never_writes(db, spec):
    with pytest.raises(SystemExit):
        audit_script.repair_legacy_name(spec, confirmed=True)
    db.expire_all()
    assert db.get(PlayerProfile, 9).legacy_name == "Brett Saks"
