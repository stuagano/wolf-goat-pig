"""Roster drift vs. Jeff's legacy dropdown, junk removal, and the email-name guard."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import LegacyRosterPlayer, PendingLegacyPlayer, PlayerProfile
from app.services import roster_drift_service
from app.services.auth_service import get_current_auth0_user
from app.services.legacy_player_service import add_legacy_player, promote_pending_player

DROPDOWN_PAGE = """
<select name="tee"><option>7:30</option><option>7:40</option></select>
<select name="player" id="player" onchange="addMember(this.value,'member')">
  <option value="">Select a player</option>
  <option value="Kevin Gent">Kevin Gent</option>
  <option>Doug Hansen
  <option value="Kevin Hallstrom (baby death star)">Kevin Hallstrom (baby death star)</option>
  <option>Dom D&#39;Amico</option>
</select>
"""


def test_parse_dropdown_reads_only_the_player_select():
    assert roster_drift_service.parse_dropdown(DROPDOWN_PAGE) == [
        "Kevin Gent",
        "Doug Hansen",
        "Kevin Hallstrom (baby death star)",
        "Dom D'Amico",
    ]


def test_parse_dropdown_without_player_select_is_empty():
    assert roster_drift_service.parse_dropdown("<html>maintenance</html>") == []


@pytest.fixture
def roster(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    with sessions() as db:
        for name in ["Kevin Gent", "Bob Silver", "tthiels", "kdgent@gmail.com", "Grew K"]:
            db.add(LegacyRosterPlayer(name=name, source="seed", added_at="2026-01-01"))
        db.add(PlayerProfile(id=1, name="Grew K", legacy_name="Grew K", created_at="2026-01-01"))
        db.commit()

    def database():
        with sessions() as db:
            yield db

    monkeypatch.setenv("SUPER_ADMIN_EMAILS", "admin@example.com")
    monkeypatch.setattr(roster_drift_service, "fetch_dropdown_names", lambda: ["Kevin Gent", "Doug Hansen"])
    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": "auth0|admin", "email": "admin@example.com"}
    yield TestClient(app), sessions
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_auth0_user, None)
    engine.dispose()


def test_drift_lists_missing_junk_and_history_only_names(roster):
    client, _ = roster
    body = client.get("/legacy-players/drift").json()
    assert body["missing"] == ["Doug Hansen"]
    assert [j["name"] for j in body["junk"]] == ["kdgent@gmail.com", "tthiels"]
    assert all(j["used_by"] == [] for j in body["junk"])
    assert body["not_on_dropdown"] == ["Bob Silver", "Grew K"]
    assert (body["dropdown_count"], body["roster_count"]) == (2, 5)


def test_drift_reports_unreachable_tee_sheet_as_502(roster, monkeypatch):
    client, _ = roster

    def boom():
        raise ValueError("No player dropdown found on the legacy tee sheet")

    monkeypatch.setattr(roster_drift_service, "fetch_dropdown_names", boom)
    resp = client.get("/legacy-players/drift")
    assert resp.status_code == 502
    assert "legacy tee sheet" in resp.json()["detail"]


def test_remove_unused_name(roster):
    client, sessions = roster
    assert client.delete("/legacy-players/tthiels").status_code == 200
    with sessions() as db:
        assert db.query(LegacyRosterPlayer).filter_by(name="tthiels").count() == 0


def test_remove_refuses_a_name_a_profile_uses(roster):
    client, sessions = roster
    resp = client.delete("/legacy-players/Grew K")
    assert resp.status_code == 409
    assert "#1" in resp.json()["detail"]
    with sessions() as db:
        assert db.query(LegacyRosterPlayer).filter_by(name="Grew K").count() == 1


def test_remove_unknown_name_is_404(roster):
    client, _ = roster
    assert client.delete("/legacy-players/Nobody Here").status_code == 404


def test_drift_and_remove_are_admin_only(roster):
    client, _ = roster
    app.dependency_overrides[get_current_auth0_user] = lambda: {"sub": "auth0|x", "email": "player@example.com"}
    assert client.get("/legacy-players/drift").status_code == 403
    assert client.delete("/legacy-players/tthiels").status_code == 403


def test_adding_an_email_as_a_roster_name_is_rejected(roster):
    client, sessions = roster
    resp = client.post("/legacy-players", json={"name": "someone@example.com"})
    assert resp.status_code == 400
    with sessions() as db:
        assert add_legacy_player("x@y.com", db=db)["added"] is False
        assert db.query(LegacyRosterPlayer).filter_by(name="x@y.com").count() == 0


def test_promoting_an_email_named_capture_is_refused_and_links_nothing(roster):
    client, sessions = roster
    with sessions() as db:
        db.add(PlayerProfile(id=2, name="ggordon@example.com", created_at="2026-01-01"))
        db.add(PendingLegacyPlayer(id=7, name="ggordon@example.com", player_profile_id=2, status="pending"))
        db.commit()
        result = promote_pending_player(7, db=db)
        assert result["promoted"] is False
        assert db.get(PlayerProfile, 2).legacy_name is None
        assert db.get(PendingLegacyPlayer, 7).status == "pending"
    resp = client.post("/legacy-players/pending/7/promote")
    assert resp.status_code == 400
