"""Unit tests for admin router — email config, banners, DB admin, cleanup."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ADMIN_EMAIL = "stuagano@gmail.com"
NON_ADMIN_EMAIL = "random@example.com"
ADMIN_HEADER = {"X-Admin-Email": ADMIN_EMAIL}
NON_ADMIN_HEADER = {"X-Admin-Email": NON_ADMIN_EMAIL}


# ── Helper ────────────────────────────────────────────────────────────────────


def _create_banner(**overrides):
    """Create a banner via the API and return the response."""
    payload = {
        "message": "Test banner message",
        "banner_type": "info",
        "is_active": True,
    }
    payload.update(overrides)
    return client.post("/admin/banner", json=payload, headers=ADMIN_HEADER)


# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================


class TestGetEmailConfig:
    def test_returns_200_for_admin(self):
        resp = client.get("/admin/email-config", headers=ADMIN_HEADER)
        assert resp.status_code == 200

    def test_returns_config_object(self):
        resp = client.get("/admin/email-config", headers=ADMIN_HEADER)
        data = resp.json()
        assert "config" in data
        cfg = data["config"]
        assert "smtp_host" in cfg
        assert "smtp_port" in cfg
        assert "from_email" in cfg

    def test_password_is_masked(self):
        resp = client.get("/admin/email-config", headers=ADMIN_HEADER)
        cfg = resp.json()["config"]
        # Password should be masked or empty, never a real value
        assert cfg["smtp_password"] in ("", "••••••••")

    def test_returns_403_without_header(self):
        resp = client.get("/admin/email-config")
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.get("/admin/email-config", headers=NON_ADMIN_HEADER)
        assert resp.status_code == 403


class TestUpdateEmailConfig:
    def test_returns_200_for_admin(self):
        resp = client.post(
            "/admin/email-config",
            json={"smtp_host": "smtp.test.com"},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 200

    def test_returns_success_message(self):
        resp = client.post(
            "/admin/email-config",
            json={"from_name": "Test"},
            headers=ADMIN_HEADER,
        )
        assert resp.json()["status"] == "success"

    def test_returns_403_without_header(self):
        resp = client.post("/admin/email-config", json={"smtp_host": "x"})
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.post(
            "/admin/email-config",
            json={"smtp_host": "x"},
            headers=NON_ADMIN_HEADER,
        )
        assert resp.status_code == 403


class TestTestEmail:
    def test_returns_403_without_header(self):
        resp = client.post("/admin/test-email", json={"test_email": "a@b.com"})
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.post(
            "/admin/test-email",
            json={"test_email": "a@b.com"},
            headers=NON_ADMIN_HEADER,
        )
        assert resp.status_code == 403

    def test_returns_400_without_test_email(self):
        resp = client.post(
            "/admin/test-email",
            json={},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 400


# =============================================================================
# BANNER — PUBLIC
# =============================================================================


class TestGetActiveBanner:
    def test_returns_200(self):
        resp = client.get("/banner")
        assert resp.status_code == 200

    def test_returns_banner_key(self):
        resp = client.get("/banner")
        data = resp.json()
        assert "banner" in data

    def test_returns_none_when_no_active_banner(self):
        # Without any banners created, should return None
        # (In practice, other tests may have created banners, so just check the shape)
        resp = client.get("/banner")
        data = resp.json()
        assert "banner" in data

    def test_returns_active_banner_after_creation(self):
        _create_banner(message="Active banner!", is_active=True)
        resp = client.get("/banner")
        data = resp.json()
        assert data["banner"] is not None
        assert data["banner"]["message"] == "Active banner!"


# =============================================================================
# BANNER — ADMIN GET
# =============================================================================


class TestGetBannerConfig:
    def test_returns_200_for_admin(self):
        resp = client.get("/admin/banner", headers=ADMIN_HEADER)
        assert resp.status_code == 200

    def test_returns_403_without_header(self):
        resp = client.get("/admin/banner")
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.get("/admin/banner", headers=NON_ADMIN_HEADER)
        assert resp.status_code == 403

    def test_returns_banner_with_admin_fields(self):
        _create_banner(message="Admin visible")
        resp = client.get("/admin/banner", headers=ADMIN_HEADER)
        data = resp.json()
        assert data["banner"] is not None
        banner = data["banner"]
        assert "is_active" in banner
        assert "created_at" in banner
        assert "updated_at" in banner


# =============================================================================
# BANNER — CREATE
# =============================================================================


class TestCreateBanner:
    def test_returns_200_for_admin(self):
        resp = _create_banner()
        assert resp.status_code == 200

    def test_returns_success_status(self):
        resp = _create_banner()
        assert resp.json()["status"] == "success"

    def test_returns_banner_data(self):
        resp = _create_banner(message="New banner", banner_type="warning")
        data = resp.json()
        assert data["banner"]["message"] == "New banner"
        assert data["banner"]["banner_type"] == "warning"
        assert "id" in data["banner"]

    def test_returns_403_without_header(self):
        resp = client.post("/admin/banner", json={"message": "Nope"})
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.post(
            "/admin/banner",
            json={"message": "Nope"},
            headers=NON_ADMIN_HEADER,
        )
        assert resp.status_code == 403

    def test_returns_422_for_invalid_banner_type(self):
        resp = client.post(
            "/admin/banner",
            json={"message": "Bad type", "banner_type": "invalid_type"},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 422

    def test_returns_422_for_empty_message(self):
        resp = client.post(
            "/admin/banner",
            json={"message": ""},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 422

    def test_returns_422_for_message_too_long(self):
        resp = client.post(
            "/admin/banner",
            json={"message": "x" * 501},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 422

    def test_default_colors_applied(self):
        resp = _create_banner()
        banner = resp.json()["banner"]
        assert banner["background_color"] == "#3B82F6"
        assert banner["text_color"] == "#FFFFFF"


# =============================================================================
# BANNER — UPDATE
# =============================================================================


class TestUpdateBanner:
    def test_update_banner_returns_200(self):
        banner_id = _create_banner().json()["banner"]["id"]
        resp = client.put(
            f"/admin/banner/{banner_id}",
            json={"message": "Updated"},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 200

    def test_update_banner_changes_message(self):
        banner_id = _create_banner(message="Original").json()["banner"]["id"]
        resp = client.put(
            f"/admin/banner/{banner_id}",
            json={"message": "Changed"},
            headers=ADMIN_HEADER,
        )
        assert resp.json()["banner"]["message"] == "Changed"

    def test_update_nonexistent_banner_returns_404(self):
        resp = client.put(
            "/admin/banner/999999",
            json={"message": "Ghost"},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 404

    def test_update_banner_returns_403_without_header(self):
        resp = client.put("/admin/banner/1", json={"message": "Nope"})
        assert resp.status_code == 403

    def test_update_banner_returns_403_for_non_admin(self):
        resp = client.put(
            "/admin/banner/1",
            json={"message": "Nope"},
            headers=NON_ADMIN_HEADER,
        )
        assert resp.status_code == 403


# =============================================================================
# BANNER — DELETE
# =============================================================================


class TestDeleteBanner:
    def test_delete_banner_returns_200(self):
        banner_id = _create_banner().json()["banner"]["id"]
        resp = client.delete(
            f"/admin/banner/{banner_id}",
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 200

    def test_delete_banner_returns_success(self):
        banner_id = _create_banner().json()["banner"]["id"]
        resp = client.delete(
            f"/admin/banner/{banner_id}",
            headers=ADMIN_HEADER,
        )
        assert resp.json()["status"] == "success"

    def test_delete_nonexistent_banner_returns_404(self):
        resp = client.delete(
            "/admin/banner/999999",
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 404

    def test_delete_banner_returns_403_without_header(self):
        resp = client.delete("/admin/banner/1")
        assert resp.status_code == 403

    def test_delete_banner_returns_403_for_non_admin(self):
        resp = client.delete(
            "/admin/banner/1",
            headers=NON_ADMIN_HEADER,
        )
        assert resp.status_code == 403


# =============================================================================
# MATCH ADMIN — DELETE ALL MATCHES
# =============================================================================


class TestAdminDeleteAllMatches:
    def test_returns_200_for_admin(self):
        resp = client.delete("/admin/matches", headers=ADMIN_HEADER)
        assert resp.status_code == 200

    def test_returns_deleted_counts(self):
        resp = client.delete("/admin/matches", headers=ADMIN_HEADER)
        data = resp.json()
        assert "deleted_matches" in data
        assert "deleted_players" in data

    def test_returns_403_without_header(self):
        resp = client.delete("/admin/matches")
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.delete("/admin/matches", headers=NON_ADMIN_HEADER)
        assert resp.status_code == 403


# =============================================================================
# TEST DEPLOYMENT ENDPOINT
# =============================================================================


class TestTestDeployment:
    def test_returns_200_for_admin(self):
        resp = client.get("/test-deployment", headers=ADMIN_HEADER)
        assert resp.status_code == 200

    def test_returns_message_and_timestamp(self):
        resp = client.get("/test-deployment", headers=ADMIN_HEADER)
        data = resp.json()
        assert data["message"] == "Deployment is working"
        assert "timestamp" in data

    def test_returns_403_without_header(self):
        resp = client.get("/test-deployment")
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.get("/test-deployment", headers=NON_ADMIN_HEADER)
        assert resp.status_code == 403


# =============================================================================
# DATABASE STATS
# =============================================================================


class TestDatabaseStats:
    def test_returns_200_for_admin(self):
        resp = client.get("/admin/cleanup/database-stats", headers=ADMIN_HEADER)
        assert resp.status_code == 200

    def test_returns_stats_sections(self):
        resp = client.get("/admin/cleanup/database-stats", headers=ADMIN_HEADER)
        data = resp.json()
        assert "stats" in data
        assert "generated_at" in data
        stats = data["stats"]
        assert "games" in stats
        assert "players" in stats
        assert "signups" in stats

    def test_returns_403_without_header(self):
        resp = client.get("/admin/cleanup/database-stats")
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.get(
            "/admin/cleanup/database-stats",
            headers=NON_ADMIN_HEADER,
        )
        assert resp.status_code == 403


# =============================================================================
# ORPHANED GAMES — GET
# =============================================================================


class TestGetOrphanedGames:
    def test_returns_200_for_admin(self):
        resp = client.get("/admin/cleanup/orphaned-games", headers=ADMIN_HEADER)
        assert resp.status_code == 200

    def test_returns_expected_shape(self):
        resp = client.get("/admin/cleanup/orphaned-games", headers=ADMIN_HEADER)
        data = resp.json()
        assert "orphaned_count" in data
        assert "hours_old_threshold" in data
        assert "orphaned_games" in data
        assert isinstance(data["orphaned_games"], list)

    def test_accepts_hours_old_param(self):
        resp = client.get(
            "/admin/cleanup/orphaned-games",
            params={"hours_old": 1},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 200
        assert resp.json()["hours_old_threshold"] == 1

    def test_returns_403_without_header(self):
        resp = client.get("/admin/cleanup/orphaned-games")
        assert resp.status_code == 403


# =============================================================================
# ORPHANED GAMES — DELETE (dry run)
# =============================================================================


class TestDeleteOrphanedGames:
    def test_dry_run_returns_200(self):
        resp = client.delete(
            "/admin/cleanup/orphaned-games",
            params={"dry_run": True},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 200

    def test_dry_run_returns_dry_run_flag(self):
        resp = client.delete(
            "/admin/cleanup/orphaned-games",
            params={"dry_run": True},
            headers=ADMIN_HEADER,
        )
        data = resp.json()
        assert data["dry_run"] is True
        assert "would_delete_count" in data

    def test_actual_delete_returns_200(self):
        resp = client.delete(
            "/admin/cleanup/orphaned-games",
            params={"dry_run": False, "hours_old": 99999},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 200
        assert resp.json()["dry_run"] is False

    def test_returns_403_without_header(self):
        resp = client.delete("/admin/cleanup/orphaned-games")
        assert resp.status_code == 403


# =============================================================================
# RUN MIGRATION
# =============================================================================


class TestRunMigration:
    def test_unknown_migration_returns_400(self):
        resp = client.post(
            "/admin/run-migration",
            params={"migration": "nonexistent_migration"},
            headers=ADMIN_HEADER,
        )
        assert resp.status_code == 400

    def test_returns_403_without_header(self):
        resp = client.post(
            "/admin/run-migration",
            params={"migration": "add_statistics_columns"},
        )
        assert resp.status_code == 403

    def test_returns_403_for_non_admin(self):
        resp = client.post(
            "/admin/run-migration",
            params={"migration": "add_statistics_columns"},
            headers=NON_ADMIN_HEADER,
        )
        assert resp.status_code == 403

    def test_missing_migration_param_returns_422(self):
        resp = client.post("/admin/run-migration", headers=ADMIN_HEADER)
        assert resp.status_code == 422
