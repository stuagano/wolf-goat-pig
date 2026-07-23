"""Unit tests for member round-posting + peer attestation.

Covers the pinned contract: post → pending; overwrite-while-pending; 409 when
already attested; attest flips pending→attested; self/non-foursome attest 403;
attest-non-pending 409; pending excluded from leaderboard reads (both the
spreadsheet_sync router AND unified_data_service); missing legacy_name 400; and
the one-per-day partial unique index.
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
    monkeypatch.setattr(member_rounds_module, "get_email_service", lambda: fake_email)

    fake_notify = MagicMock()
    fake_notify.send_notification.return_value = {"id": 1}
    monkeypatch.setattr(member_rounds_module, "get_notification_service", lambda: fake_notify)

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


def test_post_creates_pending_round(client):
    _login(STUART, "Stuart Gano")
    resp = client.post(
        "/players/me/round",
        json={"date": "2026-06-15", "score": 5, "foursome": ["Jeff Smith", "Bob Jones"]},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["status"] == "pending"
    assert data["member"] == "Stuart Gano"
    assert data["score"] == 5
    assert data["foursome"] == ["Jeff Smith", "Bob Jones"]
    assert data["attested_by"] is None
    assert data["attested_at"] is None
    assert data["round_code"] == f"WGP-{data['id']}"
    client.fake_email.send_attestation_request.assert_called()
    assert client.fake_notify.send_notification.call_count == 2


def test_post_without_legacy_name_returns_400(client):
    _login(STUART, None)
    resp = client.post(
        "/players/me/round",
        json={"date": "2026-06-15", "score": 1, "foursome": ["Jeff Smith"]},
    )
    assert resp.status_code == 400
    assert "roster name" in resp.json()["detail"].lower()


def test_post_negative_score_allowed(client):
    _login(STUART, "Stuart Gano")
    resp = client.post(
        "/players/me/round",
        json={"date": "2026-06-15", "score": -7, "foursome": ["Jeff Smith"]},
    )
    assert resp.status_code == 201
    assert resp.json()["score"] == -7


def test_post_foursome_including_self_returns_400(client):
    _login(STUART, "Stuart Gano")
    resp = client.post(
        "/players/me/round",
        json={"date": "2026-06-15", "score": 1, "foursome": ["stuart gano"]},
    )
    assert resp.status_code == 400
    assert "yourself" in resp.json()["detail"].lower()


def test_post_invalid_foursome_name_returns_400(client):
    _login(STUART, "Stuart Gano")
    resp = client.post(
        "/players/me/round",
        json={"date": "2026-06-15", "score": 1, "foursome": ["Nobody McGhost"]},
    )
    assert resp.status_code == 400


def test_post_empty_foursome_returns_400(client):
    _login(STUART, "Stuart Gano")
    resp = client.post(
        "/players/me/round",
        json={"date": "2026-06-15", "score": 1, "foursome": []},
    )
    assert resp.status_code == 400


def test_post_bad_date_returns_400(client):
    _login(STUART, "Stuart Gano")
    resp = client.post(
        "/players/me/round",
        json={"date": "06/15/2026", "score": 1, "foursome": ["Jeff Smith"]},
    )
    assert resp.status_code == 400


def test_second_post_same_day_while_pending_overwrites(client):
    _login(STUART, "Stuart Gano")
    first = client.post(
        "/players/me/round",
        json={"date": "2026-06-15", "score": 5, "foursome": ["Jeff Smith"]},
    )
    assert first.status_code == 201
    first_id = first.json()["id"]

    second = client.post(
        "/players/me/round",
        json={"date": "2026-06-15", "score": 9, "foursome": ["Bob Jones"]},
    )
    assert second.status_code == 201
    body = second.json()
    assert body["id"] == first_id  # same row, overwritten
    assert body["score"] == 9
    assert body["foursome"] == ["Bob Jones"]

    # Only one member row exists for that day.
    mine = client.get("/players/me/rounds").json()
    assert len([r for r in mine if r["date"] == "2026-06-15"]) == 1


def test_second_post_when_attested_returns_409(client):
    _login(STUART, "Stuart Gano")
    posted = client.post(
        "/players/me/round",
        json={"date": "2026-06-15", "score": 5, "foursome": ["Jeff Smith"]},
    ).json()

    _login(JEFF, "Jeff Smith")
    attest = client.post(f"/rounds/{posted['id']}/attest")
    assert attest.status_code == 200

    _login(STUART, "Stuart Gano")
    resp = client.post(
        "/players/me/round",
        json={"date": "2026-06-15", "score": 99, "foursome": ["Bob Jones"]},
    )
    assert resp.status_code == 409


# ── POST /rounds/{id}/attest ─────────────────────────────────────────────────


def test_attest_by_foursome_member_flips_to_attested(client):
    _login(STUART, "Stuart Gano")
    posted = client.post(
        "/players/me/round",
        json={"date": "2026-06-15", "score": 5, "foursome": ["Jeff Smith", "Bob Jones"]},
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
    posted = client.post(
        "/players/me/round",
        json={"date": "2026-06-15", "score": 5, "foursome": ["Jeff Smith"]},
    ).json()
    resp = client.post(f"/rounds/{posted['id']}/attest")  # still Stuart
    assert resp.status_code == 403


def test_non_foursome_attest_returns_403(client):
    _login(STUART, "Stuart Gano")
    posted = client.post(
        "/players/me/round",
        json={"date": "2026-06-15", "score": 5, "foursome": ["Jeff Smith"]},
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
    posted = client.post(
        "/players/me/round",
        json={"date": "2026-06-15", "score": 5, "foursome": ["Jeff Smith"]},
    ).json()

    _login(JEFF, "Jeff Smith")
    assert client.post(f"/rounds/{posted['id']}/attest").status_code == 200
    # Second attest of a non-pending round.
    resp = client.post(f"/rounds/{posted['id']}/attest")
    assert resp.status_code == 409


# ── GET /rounds/pending-attestation ──────────────────────────────────────────


def test_pending_attestation_lists_for_foursome_member_only(client):
    _login(STUART, "Stuart Gano")
    client.post(
        "/players/me/round",
        json={"date": "2026-06-15", "score": 5, "foursome": ["Jeff Smith"]},
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
    posted = client.post(
        "/players/me/round",
        json={"date": "2026-06-15", "score": 5, "foursome": ["Jeff Smith"]},
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
    posted = client.post(
        "/players/me/round",
        json={"date": "2026-06-15", "score": 5, "foursome": ["Jeff Smith"]},
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
