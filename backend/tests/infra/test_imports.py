"""
Test that all critical modules can be imported successfully.

This prevents ModuleNotFoundError and ImportError from reaching production.
"""

import pytest


class TestCriticalImports:
    """Test that critical application modules can be imported."""

    def test_import_main_app(self):
        """Test that the main FastAPI app can be imported."""
        try:
            from app.main import app

            assert app is not None, "FastAPI app should be defined"
        except ModuleNotFoundError as e:
            pytest.fail(f"Failed to import main app: {e}")
        except ImportError as e:
            pytest.fail(f"Import error in main app: {e}")

    def test_import_database_models(self):
        """Test that database models can be imported."""
        try:
            from app import models

            assert models is not None
            assert hasattr(models, "GameRecord")
            assert hasattr(models, "GamePlayer")
            assert hasattr(models, "Course")
        except ModuleNotFoundError as e:
            pytest.fail(f"Failed to import models: {e}")
        except ImportError as e:
            pytest.fail(f"Import error in models: {e}")

    def test_import_services(self):
        """Test that critical services can be imported."""
        try:
            from app.services.game_lifecycle_service import get_game_lifecycle_service
            from app.services.notification_service import NotificationService

            assert get_game_lifecycle_service is not None
            assert NotificationService is not None
        except ModuleNotFoundError as e:
            pytest.fail(f"Failed to import services: {e}")
        except ImportError as e:
            pytest.fail(f"Import error in services: {e}")


class TestApplicationStartup:
    """Test that the application can start without errors."""

    def test_app_creation(self):
        """Test that the FastAPI app can be created successfully."""
        try:
            from app.main import app

            # Verify the app has required attributes
            assert hasattr(app, "routes"), "App should have routes"
            assert hasattr(app, "router"), "App should have router"
            assert len(app.routes) > 0, "App should have at least one route"
        except Exception as e:
            pytest.fail(f"Failed to create FastAPI app: {e}")

    def test_all_routes_registered(self):
        """Test that critical routes are registered."""
        try:
            from app.main import app

            # OpenAPI intentionally omits operational probes. Resolve those by
            # route name while keeping schema checks for the public API.
            route_paths = app.openapi().get("paths", {})
            assert any("/games" in path for path in route_paths), "Games routes should be registered"
            assert str(app.url_path_for("health_check")) == "/health"
        except Exception as e:
            pytest.fail(f"Failed to verify routes: {e}")
