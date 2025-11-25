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

    def test_import_managers_package(self):
        """Test that the managers package exports all required modules."""
        try:
            from app.managers import (
                RuleManager,
                RuleViolationError,
                ScoringManager,
                get_scoring_manager,
                WebSocketManager,
                manager,
            )

            assert RuleManager is not None
            assert RuleViolationError is not None
            assert ScoringManager is not None
            assert get_scoring_manager is not None
            assert WebSocketManager is not None
            assert manager is not None
        except ModuleNotFoundError as e:
            pytest.fail(f"Failed to import from managers package: {e}")
        except ImportError as e:
            pytest.fail(f"Import error in managers package: {e}")

    def test_import_websocket_manager_directly(self):
        """Test that websocket_manager can be imported directly."""
        try:
            from app.managers.websocket_manager import WebSocketManager, manager

            assert WebSocketManager is not None
            assert manager is not None
            assert isinstance(manager, WebSocketManager)
        except ModuleNotFoundError as e:
            pytest.fail(f"Failed to import websocket_manager: {e}")
        except ImportError as e:
            pytest.fail(f"Import error in websocket_manager: {e}")

    def test_import_rule_manager(self):
        """Test that rule_manager can be imported directly."""
        try:
            from app.managers.rule_manager import RuleManager, RuleViolationError

            assert RuleManager is not None
            assert RuleViolationError is not None
        except ModuleNotFoundError as e:
            pytest.fail(f"Failed to import rule_manager: {e}")
        except ImportError as e:
            pytest.fail(f"Import error in rule_manager: {e}")

    def test_import_scoring_manager(self):
        """Test that scoring_manager can be imported directly."""
        try:
            from app.managers.scoring_manager import ScoringManager, get_scoring_manager

            assert ScoringManager is not None
            assert get_scoring_manager is not None
        except ModuleNotFoundError as e:
            pytest.fail(f"Failed to import scoring_manager: {e}")
        except ImportError as e:
            pytest.fail(f"Import error in scoring_manager: {e}")

    def test_import_database_models(self):
        """Test that database models can be imported."""
        try:
            from app import models

            assert models is not None
            assert hasattr(models, 'GameRecord')
            assert hasattr(models, 'GamePlayer')
            assert hasattr(models, 'Course')
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
            assert hasattr(app, 'routes'), "App should have routes"
            assert hasattr(app, 'router'), "App should have router"
            assert len(app.routes) > 0, "App should have at least one route"
        except Exception as e:
            pytest.fail(f"Failed to create FastAPI app: {e}")

    def test_all_routes_registered(self):
        """Test that critical routes are registered."""
        try:
            from app.main import app

            # Get all route paths
            route_paths = [route.path for route in app.routes]

            # Check for critical routes
            assert any('/games' in path for path in route_paths), "Games routes should be registered"
            assert any('/health' in path for path in route_paths), "Health route should be registered"
        except Exception as e:
            pytest.fail(f"Failed to verify routes: {e}")

    def test_managers_initialized(self):
        """Test that managers are properly initialized."""
        try:
            from app.managers import manager as websocket_manager
            from app.managers.rule_manager import RuleManager

            # Verify managers can be instantiated/accessed
            assert websocket_manager is not None

            # RuleManager is a singleton, verify it can be accessed
            rule_manager = RuleManager()
            assert rule_manager is not None
        except Exception as e:
            pytest.fail(f"Failed to initialize managers: {e}")


class TestPackageExports:
    """Test that packages properly export their modules."""

    def test_managers_package_all_exports(self):
        """Test that managers package __all__ contains all exports."""
        from app import managers

        # Verify __all__ is defined
        assert hasattr(managers, '__all__'), "managers package should define __all__"

        # Verify all listed exports are actually available
        for export_name in managers.__all__:
            assert hasattr(managers, export_name), \
                f"managers package should export {export_name}"

    def test_managers_websocket_in_all(self):
        """Test that websocket_manager exports are in __all__."""
        from app import managers

        assert 'WebSocketManager' in managers.__all__, \
            "WebSocketManager should be in managers.__all__"
        assert 'manager' in managers.__all__, \
            "manager should be in managers.__all__"
