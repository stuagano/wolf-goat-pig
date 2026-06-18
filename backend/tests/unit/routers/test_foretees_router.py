"""Unit tests for foretees router — credentials, tee times, bookings, booking, cancellation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import PlayerProfile
from app.services.auth_service import get_current_user

client = TestClient(app)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _fake_player(**overrides) -> PlayerProfile:
    """Return a minimal PlayerProfile for dependency injection."""
    p = MagicMock(spec=PlayerProfile)
    p.id = overrides.get("id", 1)
    p.foretees_username = overrides.get("foretees_username")
    p.foretees_password_encrypted = overrides.get("foretees_password_encrypted")
    return p


def _override_current_user(player=None):
    """Override the get_current_user dependency with a fake player."""
    if player is None:
        player = _fake_player()

    def _dep():
        return player

    app.dependency_overrides[get_current_user] = _dep
    return player


def _clear_overrides():
    app.dependency_overrides.pop(get_current_user, None)


# =============================================================================
# CREDENTIALS — GET
# =============================================================================


class TestGetCredentialsStatus:
    def setup_method(self):
        _clear_overrides()

    def teardown_method(self):
        _clear_overrides()

    def test_returns_401_without_auth(self):
        resp = client.get("/api/foretees/credentials")
        assert resp.status_code in (401, 403)

    def test_returns_200_when_no_credentials(self):
        _override_current_user(_fake_player(foretees_username=None, foretees_password_encrypted=None))
        resp = client.get("/api/foretees/credentials")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["configured"] is False
        assert data["data"]["username"] is None

    def test_returns_200_when_credentials_configured(self):
        _override_current_user(_fake_player(foretees_username="1453-smith", foretees_password_encrypted="enc_pass"))
        resp = client.get("/api/foretees/credentials")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["configured"] is True
        # Username should be masked
        assert "***" in data["data"]["username"]


# =============================================================================
# CREDENTIALS — PUT (save)
# =============================================================================


class TestSaveCredentials:
    def setup_method(self):
        _clear_overrides()

    def teardown_method(self):
        _clear_overrides()

    def test_returns_401_without_auth(self):
        resp = client.put(
            "/api/foretees/credentials",
            json={"username": "user", "password": "pass"},
        )
        assert resp.status_code in (401, 403)

    @patch("app.routers.foretees.create_user_foretees_service")
    def test_returns_200_on_valid_login(self, mock_create):
        player = _override_current_user()
        mock_svc = AsyncMock()
        mock_svc._ensure_session = AsyncMock(return_value=True)
        mock_svc.close = AsyncMock()
        mock_create.return_value = mock_svc

        resp = client.put(
            "/api/foretees/credentials",
            json={"username": "user", "password": "pass"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["configured"] is True

    @patch("app.routers.foretees.create_user_foretees_service")
    def test_returns_400_on_failed_login(self, mock_create):
        _override_current_user()
        mock_svc = AsyncMock()
        mock_svc._ensure_session = AsyncMock(return_value=False)
        mock_svc.close = AsyncMock()
        mock_create.return_value = mock_svc

        resp = client.put(
            "/api/foretees/credentials",
            json={"username": "user", "password": "bad"},
        )
        assert resp.status_code == 400

    def test_returns_422_for_missing_fields(self):
        _override_current_user()
        resp = client.put("/api/foretees/credentials", json={})
        assert resp.status_code == 422


# =============================================================================
# CREDENTIALS — DELETE
# =============================================================================


class TestRemoveCredentials:
    def setup_method(self):
        _clear_overrides()

    def teardown_method(self):
        _clear_overrides()

    def test_returns_401_without_auth(self):
        resp = client.delete("/api/foretees/credentials")
        assert resp.status_code in (401, 403)

    def test_returns_200_and_clears(self):
        player = _override_current_user(_fake_player(foretees_username="user", foretees_password_encrypted="enc"))
        resp = client.delete("/api/foretees/credentials")
        assert resp.status_code == 200
        assert player.foretees_username is None
        assert player.foretees_password_encrypted is None


# =============================================================================
# TEE TIMES — GET
# =============================================================================


class TestGetTeeTimes:
    def setup_method(self):
        _clear_overrides()

    def teardown_method(self):
        _clear_overrides()

    def test_returns_401_without_auth(self):
        resp = client.get("/api/foretees/tee-times", params={"date": "2025-06-01"})
        assert resp.status_code in (401, 403)

    @patch("app.routers.foretees._get_user_service")
    def test_returns_200_with_slots(self, mock_get_svc):
        _override_current_user()
        mock_svc = AsyncMock()
        mock_svc.config = MagicMock(enabled=True)
        mock_svc.get_tee_times = AsyncMock(return_value=[{"time": "08:00 AM"}])
        mock_svc.close = AsyncMock()
        mock_get_svc.return_value = mock_svc

        # Make service not equal to singleton to trigger close
        with patch("app.routers.foretees.get_foretees_service", return_value=MagicMock()):
            resp = client.get("/api/foretees/tee-times", params={"date": "2025-06-01"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 1

    @patch("app.routers.foretees._get_user_service")
    def test_returns_200_disabled(self, mock_get_svc):
        _override_current_user()
        mock_svc = MagicMock()
        mock_svc.config = MagicMock(enabled=False)
        mock_get_svc.return_value = mock_svc

        resp = client.get("/api/foretees/tee-times", params={"date": "2025-06-01"})
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_returns_422_without_date(self):
        _override_current_user()
        resp = client.get("/api/foretees/tee-times")
        assert resp.status_code == 422


# =============================================================================
# BOOKINGS — GET
# =============================================================================


class TestGetMyBookings:
    def setup_method(self):
        _clear_overrides()

    def teardown_method(self):
        _clear_overrides()

    def test_returns_401_without_auth(self):
        resp = client.get("/api/foretees/bookings")
        assert resp.status_code in (401, 403)

    @patch("app.routers.foretees._get_user_service")
    def test_returns_200_with_bookings(self, mock_get_svc):
        _override_current_user()
        mock_svc = AsyncMock()
        mock_svc.config = MagicMock(enabled=True)
        mock_svc.get_my_tee_times = AsyncMock(return_value=[{"date": "2025-06-01"}])
        mock_svc.close = AsyncMock()
        mock_get_svc.return_value = mock_svc

        with patch("app.routers.foretees.get_foretees_service", return_value=MagicMock()):
            resp = client.get("/api/foretees/bookings")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    @patch("app.routers.foretees._get_user_service")
    def test_returns_200_disabled(self, mock_get_svc):
        _override_current_user()
        mock_svc = MagicMock()
        mock_svc.config = MagicMock(enabled=False)
        mock_get_svc.return_value = mock_svc

        resp = client.get("/api/foretees/bookings")
        assert resp.status_code == 200
        assert resp.json()["data"] == []


# =============================================================================
# BOOK TEE TIME — POST
# =============================================================================


class TestBookTeeTime:
    def setup_method(self):
        _clear_overrides()

    def teardown_method(self):
        _clear_overrides()

    def test_returns_401_without_auth(self):
        resp = client.post(
            "/api/foretees/book",
            json={"ttdata": "abc123", "transport_mode": "CRT"},
        )
        assert resp.status_code in (401, 403)

    @patch("app.routers.foretees._get_user_service")
    def test_returns_200_on_successful_booking(self, mock_get_svc):
        _override_current_user()
        mock_svc = AsyncMock()
        mock_svc.config = MagicMock(enabled=True)
        mock_svc.book_tee_time = AsyncMock(return_value={"success": True, "messages": ["Booking confirmed"]})
        mock_svc.close = AsyncMock()
        mock_get_svc.return_value = mock_svc

        with patch("app.routers.foretees.get_foretees_service", return_value=MagicMock()):
            resp = client.post(
                "/api/foretees/book",
                json={"ttdata": "abc123", "transport_mode": "CRT"},
            )
        assert resp.status_code == 200

    @patch("app.routers.foretees._get_user_service")
    def test_returns_400_on_failed_booking(self, mock_get_svc):
        _override_current_user()
        mock_svc = AsyncMock()
        mock_svc.config = MagicMock(enabled=True)
        mock_svc.book_tee_time = AsyncMock(return_value={"success": False, "error": "Slot taken"})
        mock_svc.close = AsyncMock()
        mock_get_svc.return_value = mock_svc

        with patch("app.routers.foretees.get_foretees_service", return_value=MagicMock()):
            resp = client.post(
                "/api/foretees/book",
                json={"ttdata": "abc123"},
            )
        assert resp.status_code == 400

    @patch("app.routers.foretees._get_user_service")
    def test_returns_400_when_disabled(self, mock_get_svc):
        _override_current_user()
        mock_svc = MagicMock()
        mock_svc.config = MagicMock(enabled=False)
        mock_get_svc.return_value = mock_svc

        resp = client.post(
            "/api/foretees/book",
            json={"ttdata": "abc123"},
        )
        assert resp.status_code == 400

    def test_returns_422_for_invalid_transport_mode(self):
        _override_current_user()
        resp = client.post(
            "/api/foretees/book",
            json={"ttdata": "abc123", "transport_mode": "BIKE"},
        )
        assert resp.status_code == 422

    def test_returns_422_for_empty_ttdata(self):
        _override_current_user()
        resp = client.post(
            "/api/foretees/book",
            json={"ttdata": "", "transport_mode": "WLK"},
        )
        assert resp.status_code == 422


# =============================================================================
# CANCEL TEE TIME — POST
# =============================================================================


class TestCancelTeeTime:
    def setup_method(self):
        _clear_overrides()

    def teardown_method(self):
        _clear_overrides()

    def test_returns_401_without_auth(self):
        resp = client.post(
            "/api/foretees/cancel",
            json={"date": "2025-06-01"},
        )
        assert resp.status_code in (401, 403)

    @patch("app.routers.foretees._get_user_service")
    def test_returns_200_on_successful_cancel(self, mock_get_svc):
        _override_current_user()
        mock_svc = AsyncMock()
        mock_svc.config = MagicMock(enabled=True)
        mock_svc.cancel_tee_time = AsyncMock(return_value={"success": True, "messages": ["Cancelled"]})
        mock_svc.close = AsyncMock()
        mock_get_svc.return_value = mock_svc

        with patch("app.routers.foretees.get_foretees_service", return_value=MagicMock()):
            resp = client.post(
                "/api/foretees/cancel",
                json={"date": "2025-06-01", "time": "08:00 AM"},
            )
        assert resp.status_code == 200

    @patch("app.routers.foretees._get_user_service")
    def test_returns_400_on_failed_cancel(self, mock_get_svc):
        _override_current_user()
        mock_svc = AsyncMock()
        mock_svc.config = MagicMock(enabled=True)
        mock_svc.cancel_tee_time = AsyncMock(return_value={"success": False, "error": "Not found"})
        mock_svc.close = AsyncMock()
        mock_get_svc.return_value = mock_svc

        with patch("app.routers.foretees.get_foretees_service", return_value=MagicMock()):
            resp = client.post(
                "/api/foretees/cancel",
                json={"date": "2025-06-01"},
            )
        assert resp.status_code == 400

    @patch("app.routers.foretees._get_user_service")
    def test_returns_400_when_disabled(self, mock_get_svc):
        _override_current_user()
        mock_svc = MagicMock()
        mock_svc.config = MagicMock(enabled=False)
        mock_get_svc.return_value = mock_svc

        resp = client.post(
            "/api/foretees/cancel",
            json={"date": "2025-06-01"},
        )
        assert resp.status_code == 400

    def test_returns_422_for_missing_date(self):
        _override_current_user()
        resp = client.post("/api/foretees/cancel", json={})
        assert resp.status_code == 422
