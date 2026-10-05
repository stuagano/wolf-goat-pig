"""Unit tests for honor-system group posting and historical peer attestation.

Covers atomic group posting, immediate standings/history, participant identity,
duplicate rejection, and legacy pending records without rewriting old results.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.routers.member_rounds as member_rounds_module
from app.database import Base, get_db
from app.main import app
from app.models import LegacyRosterPlayer, PlayerProfile
from app.services.auth_service import get_current_user
from app.utils.admin_auth import require_admin

ROSTER = ["Stuart Gano", "Jeff Smith", "Bob Jones", "Alice Park"]


@pytest.fixture
def db_session():
    """A fresh in-memory SQLite DB with the full schema (incl. new columns)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    # Seed canonical roster + profiles (with emails so attestation emails resolve).
    for i, name in enumerate(ROSTER, start=1):
        session.add(LegacyRosterPlayer(name=name, source="seed", added_at="2026-01-01T00:00:00"))
        session.add(
            PlayerProfile(
                id=i,
                name=name,
                legacy_name=name,
                email=f"{name.split()[0].lower()}@example.com",
                created_at="2026-01-01T00:00:00",
            )
        )
    session.commit()

    yield session, TestingSessionLocal
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session, monkeypatch):
    """TestClient wired to the temp DB with no real emails sent."""
    session, TestingSessionLocal = db_session

    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[require_admin] = lambda: None

    # No real emails / in-app notifications.
    fake_email = MagicMock()
    fake_email.send_attestation_request.return_value = True
    monkeypatch.setattr("app.services.email_service.get_email_service", lambda: fake_email)

    fake_notify = MagicMock()
    fake_notify.send_notification.return_value = {"id": 1}
    monkeypatch.setattr("app.services.notification_service.get_notification_service", lambda: fake_notify)

    test_client = TestClient(app)
    test_client.fake_email = fake_email  # type: ignore[attr-defined]
    test_client.fake_notify = fake_notify  # type: ignore[attr-defined]
    yield test_client

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(require_admin, None)
    app.dependency_overrides.pop(get_current_user, None)


def _login(player_id: int, legacy_name: str | None):
    """Override get_current_user with a minimal profile."""
    user = MagicMock(spec=PlayerProfile)
    user.id = player_id
    user.legacy_name = legacy_name
    user.name = legacy_name
    app.dependency_overrides[get_current_user] = lambda: user
    return user


# Profile ids per ROSTER seeding order.
STUART, JEFF, BOB, ALICE = 1, 2, 3, 4


# ── POST /players/me/round ───────────────────────────────────────────────────


def group_payload(names=ROSTER, scores=(5, -3, -2, 0)):
    return {
        "date": "2026-06-15",
        "results": [{"member": name, "score": score} for name, score in zip(names, scores)],
        "location": "Wing Point",
    }


def test_one_person_posts_all_players_immediately_without_notifications(client, db_session):
    from app.models import LegacyRound
    from app.services.unified_data_service import UnifiedDataService

    _login(STUART, "Stuart Gano")
    response = client.post("/players/me/round", json=group_payload())
    assert response.status_code == 201, response.text
    posted = response.json()["rounds"]
    assert {r["member"]: r["score"] for r in posted} == dict(zip(ROSTER, (5, -3, -2, 0)))
    assert all(r["status"] == "posted" and r["attested_by"] is None for r in posted)
    session, _ = db_session
    rows = session.query(LegacyRound).all()
    assert len(rows) == 4
    assert {r.player_profile_id for r in rows} == {STUART, JEFF, BOB, ALICE}
    assert all(r.submitted_by_profile_id == STUART for r in rows)
    client.fake_email.send_attestation_request.assert_not_called()
    client.fake_notify.send_notification.assert_not_called()
    for player_id, name in enumerate(ROSTER, 1):
        _login(player_id, name)
        mine = client.get("/players/me/rounds").json()
        assert len(mine) == 1 and mine[0]["member"] == name
        assert client.get("/rounds/pending-attestation").json() == []
    assert len(UnifiedDataService(db=session).get_all_rounds(include_database=False)) == 4
    board = client.get("/admin/spreadsheet/leaderboard").json()
    assert {r["member"]: r["quarters"] for r in board} == dict(zip(ROSTER, (5, -3, -2, 0)))


@pytest.mark.parametrize(
    "names,scores",
    [
        (["Stuart Gano"], [0]),
        (["Jeff Smith", "Bob Jones"], [1, -1]),
        (["Stuart Gano", "stuart gano"], [1, -1]),
        (["Stuart Gano", "Unknown Person"], [1, -1]),
        (ROSTER + ["Jeff Smith"], [1, -1, 0, 0, 0]),
        (["Stuart Gano", "Jeff Smith"], [1.5, -1.5]),
        (["Stuart Gano", "Jeff Smith"], [True, -1]),
        (["Stuart Gano", "Jeff Smith"], [2147483648, 0]),
    ],
)
def test_invalid_group_saves_nothing(client, db_session, names, scores):
    from app.models import LegacyRound

    _login(STUART, "Stuart Gano")
    response = client.post("/players/me/round", json=group_payload(names, scores))
    assert response.status_code in (400, 422), response.text
    assert db_session[0].query(LegacyRound).count() == 0


def test_missing_score_or_unlinked_submitter_rejected(client):
    _login(STUART, None)
    assert client.post("/players/me/round", json=group_payload()).status_code == 400
    _login(STUART, "Stuart Gano")
    payload = group_payload()
    del payload["results"][1]["score"]
    assert client.post("/players/me/round", json=payload).status_code == 422


def test_duplicate_from_any_partner_rejects_entire_group(client, db_session):
    from app.models import LegacyRound

    _login(JEFF, "Jeff Smith")
    assert client.post("/players/me/round", json=group_payload(ROSTER[1:3], [3, -3])).status_code == 201
    _login(STUART, "Stuart Gano")
    response = client.post("/players/me/round", json=group_payload())
    assert response.status_code == 409
    assert any(name in response.json()["detail"] for name in ("Jeff Smith", "Bob Jones"))
    rows = db_session[0].query(LegacyRound).all()
    assert {r.member: r.score for r in rows} == {"Jeff Smith": 3, "Bob Jones": -3}


def test_partner_without_account_can_see_result_after_linking(client, db_session):
    session, _ = db_session
    session.query(PlayerProfile).filter(PlayerProfile.id == JEFF).delete()
    session.commit()
    _login(STUART, "Stuart Gano")
    assert client.post("/players/me/round", json=group_payload()).status_code == 201
    _login(99, "Jeff Smith")
    mine = client.get("/players/me/rounds").json()
    assert len(mine) == 1 and mine[0]["score"] == -3


def test_unique_conflict_rolls_back_every_result(client, db_session, monkeypatch):
    from sqlalchemy.orm import Session

    from app.models import LegacyRound

    def conflict_on_commit(db):
        db.flush()
        raise IntegrityError(
            "INSERT", {}, Exception("UNIQUE constraint failed: legacy_rounds.member, legacy_rounds.date")
        )

    _login(STUART, "Stuart Gano")
    monkeypatch.setattr(Session, "commit", conflict_on_commit)
    response = client.post("/players/me/round", json=group_payload())
    assert response.status_code == 409
    assert db_session[0].query(LegacyRound).count() == 0


@pytest.mark.parametrize("date", ["06/15/2026", "2026-02-30", "2026-6-15"])
def test_invalid_date_saves_nothing(client, db_session, date):
    from app.models import LegacyRound

    _login(STUART, "Stuart Gano")
    payload = group_payload()
    payload["date"] = date
    assert client.post("/players/me/round", json=payload).status_code == 400
    assert db_session[0].query(LegacyRound).count() == 0


def _legacy_pending(client, payload):
    """Historical pending records remain supported; new posts no longer create them."""
    from app.models import LegacyRound

    db = next(app.dependency_overrides[get_db]())
    row = LegacyRound(
        member="Stuart Gano",
        player_profile_id=STUART,
        source="member",
        status="pending",
        synced_at="2026-06-15T00:00:00",
        created_at="2026-06-15T00:00:00",
        **payload,
    )
    db.add(row)
    db.commit()
    response = MagicMock()
    response.json.return_value = member_rounds_module._serialize(row)
    db.close()
    return response


# ── POST /rounds/{id}/attest ─────────────────────────────────────────────────


def test_attest_by_foursome_member_flips_to_attested(client):
    _login(STUART, "Stuart Gano")
    posted = _legacy_pending(
        client,
        {"date": "2026-06-15", "score": 5, "foursome": ["Jeff Smith", "Bob Jones"]},
    ).json()

    _login(BOB, "Bob Jones")
    resp = client.post(f"/rounds/{posted['id']}/attest")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "attested"
    assert data["attested_by"] == BOB
    assert data["attested_at"] is not None


def test_self_attest_returns_403(client):
    _login(STUART, "Stuart Gano")
    posted = _legacy_pending(
        client,
        {"date": "2026-06-15", "score": 5, "foursome": ["Jeff Smith"]},
    ).json()
    resp = client.post(f"/rounds/{posted['id']}/attest")  # still Stuart
    assert resp.status_code == 403


def test_non_foursome_attest_returns_403(client):
    _login(STUART, "Stuart Gano")
    posted = _legacy_pending(
        client,
        {"date": "2026-06-15", "score": 5, "foursome": ["Jeff Smith"]},
    ).json()

    _login(ALICE, "Alice Park")  # not in foursome
    resp = client.post(f"/rounds/{posted['id']}/attest")
    assert resp.status_code == 403


def test_attest_nonexistent_returns_404(client):
    _login(JEFF, "Jeff Smith")
    resp = client.post("/rounds/999999/attest")
    assert resp.status_code == 404


def test_attest_already_attested_returns_409(client):
    _login(STUART, "Stuart Gano")
    posted = _legacy_pending(
        client,
        {"date": "2026-06-15", "score": 5, "foursome": ["Jeff Smith"]},
    ).json()

    _login(JEFF, "Jeff Smith")
    assert client.post(f"/rounds/{posted['id']}/attest").status_code == 200
    # Second attest of a non-pending round.
    resp = client.post(f"/rounds/{posted['id']}/attest")
    assert resp.status_code == 409


# ── GET /rounds/pending-attestation ──────────────────────────────────────────


def test_pending_attestation_lists_for_foursome_member_only(client):
    _login(STUART, "Stuart Gano")
    _legacy_pending(
        client,
        {"date": "2026-06-15", "score": 5, "foursome": ["Jeff Smith"]},
    )

    _login(JEFF, "Jeff Smith")  # in foursome → sees it
    assert len(client.get("/rounds/pending-attestation").json()) == 1

    _login(ALICE, "Alice Park")  # not in foursome → empty
    assert client.get("/rounds/pending-attestation").json() == []

    _login(STUART, "Stuart Gano")  # poster never attests own round
    assert client.get("/rounds/pending-attestation").json() == []


# ── Read-path: pending excluded, attested included ───────────────────────────


def test_pending_excluded_from_spreadsheet_leaderboard_then_included(client):
    _login(STUART, "Stuart Gano")
    posted = _legacy_pending(
        client,
        {"date": "2026-06-15", "score": 5, "foursome": ["Jeff Smith"]},
    ).json()

    # While pending, Stuart absent from the leaderboard.
    board = client.get("/admin/spreadsheet/leaderboard").json()
    assert "Stuart Gano" not in {e["member"] for e in board}
    assert client.get("/admin/spreadsheet/rounds").json() == []

    # After attestation, Stuart appears.
    _login(JEFF, "Jeff Smith")
    client.post(f"/rounds/{posted['id']}/attest")

    board = client.get("/admin/spreadsheet/leaderboard").json()
    stuart = next((e for e in board if e["member"] == "Stuart Gano"), None)
    assert stuart is not None and stuart["quarters"] == 5
    assert len(client.get("/admin/spreadsheet/rounds").json()) == 1


def test_pending_excluded_from_unified_get_all_rounds(client, db_session):
    session, _ = db_session
    from app.services.unified_data_service import UnifiedDataService

    _login(STUART, "Stuart Gano")
    posted = _legacy_pending(
        client,
        {"date": "2026-06-15", "score": 5, "foursome": ["Jeff Smith"]},
    ).json()

    service = UnifiedDataService(db=session)
    pending_rounds = service.get_all_rounds(include_database=False)
    assert all(r.member != "Stuart Gano" for r in pending_rounds)

    _login(JEFF, "Jeff Smith")
    client.post(f"/rounds/{posted['id']}/attest")

    attested_rounds = service.get_all_rounds(include_database=False)
    assert any(r.member == "Stuart Gano" and r.score == 5 for r in attested_rounds)


# ── One-per-day partial unique index ─────────────────────────────────────────


def test_one_member_round_per_day_unique_index(db_session):
    session, _ = db_session
    from app.models import LegacyRound

    session.add(
        LegacyRound(
            date="2026-06-15",
            member="Stuart Gano",
            score=1,
            source="member",
            status="pending",
            synced_at="2026-06-15T00:00:00",
            created_at="2026-06-15T00:00:00",
        )
    )
    session.commit()

    session.add(
        LegacyRound(
            date="2026-06-15",
            member="Stuart Gano",
            score=2,
            source="member",
            status="pending",
            synced_at="2026-06-15T00:00:00",
            created_at="2026-06-15T00:00:00",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    # Sheet rows (different source) are NOT constrained — duplicates allowed.
    session.add_all(
        [
            LegacyRound(
                date="2026-06-15",
                member="Stuart Gano",
                score=3,
                source="primary_sheet",
                status="attested",
                synced_at="x",
                created_at="x",
            ),
            LegacyRound(
                date="2026-06-15",
                member="Stuart Gano",
                score=4,
                source="primary_sheet",
                status="attested",
                synced_at="x",
                created_at="x",
            ),
        ]
    )
    session.commit()  # no error


# ── GET /players/me/history ──────────────────────────────────────────────────


def test_history_aggregates_club_rounds(client, monkeypatch):
    from app.services.unified_data_service import UnifiedRound

    _login(STUART, "Stuart Gano")
    rounds = [
        UnifiedRound("24-Aug", "2026-08-24", "A", "Stuart Gano", -58, "Wing Point", source="primary_sheet"),
        UnifiedRound("10-Aug", "2026-08-10", "C", "Stuart Gano", 80, "Wing Point", source="primary_sheet"),
        UnifiedRound("27-Jul", "2026-07-27", "A", "Stuart Gano", 153, "Wing Point", source="primary_sheet"),
    ]
    fake = MagicMock()
    fake.get_player_history.return_value = rounds
    monkeypatch.setattr(member_rounds_module, "get_unified_data_service", lambda db=None: fake)

    resp = client.get("/players/me/history")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["found"] is True
    assert data["rounds_played"] == 3
    assert "games_won" not in data
    assert data["total_quarters"] == -58 + 80 + 153
    assert data["average_per_round"] == round((-58 + 80 + 153) / 3, 1)
    assert data["best_round"] == 153
    assert data["worst_round"] == -58
    assert len(data["recent_rounds"]) == 3
    assert data["recent_rounds"][0] == {
        "date": "2026-08-24",
        "date_display": "24-Aug",
        "score": -58,
        "location": "Wing Point",
        "group": "A",
        "source": "primary_sheet",
    }
    fake.get_player_history.assert_called_once_with("Stuart Gano")


def test_history_honors_recent_limit(client, monkeypatch):
    from app.services.unified_data_service import UnifiedRound

    _login(STUART, "Stuart Gano")
    rounds = [
        UnifiedRound(f"{i}-Jan", f"2026-01-{i:02d}", "A", "Stuart Gano", i, "Wing Point") for i in range(10, 0, -1)
    ]
    fake = MagicMock()
    fake.get_player_history.return_value = rounds
    monkeypatch.setattr(member_rounds_module, "get_unified_data_service", lambda db=None: fake)

    resp = client.get("/players/me/history?recent_limit=2")
    assert resp.status_code == 200
    assert len(resp.json()["recent_rounds"]) == 2


def test_history_empty_when_no_rounds(client, monkeypatch):
    _login(STUART, "Stuart Gano")
    fake = MagicMock()
    fake.get_player_history.return_value = []
    monkeypatch.setattr(member_rounds_module, "get_unified_data_service", lambda db=None: fake)

    resp = client.get("/players/me/history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["found"] is False
    assert data["rounds_played"] == 0
    assert data["recent_rounds"] == []
    assert data["best_round"] is None


def test_history_falls_back_to_display_name(client, monkeypatch):
    user = _login(STUART, None)
    user.name = "Stuart Gano"
    fake = MagicMock()
    fake.get_player_history.return_value = []
    monkeypatch.setattr(member_rounds_module, "get_unified_data_service", lambda db=None: fake)

    resp = client.get("/players/me/history")
    assert resp.status_code == 200
    fake.get_player_history.assert_called_once_with("Stuart Gano")


def test_history_rejects_invalid_recent_limit(client):
    _login(STUART, "Stuart Gano")
    assert client.get("/players/me/history?recent_limit=0").status_code == 400
    assert client.get("/players/me/history?recent_limit=99").status_code == 400
