#!/usr/bin/env python3
"""
Validate that all Python modules can be imported successfully.

This script is used as a pre-commit hook to catch import errors before they
reach production.

Exit codes:
    0: All imports successful
    1: Import errors detected
"""
import sys
import importlib
from pathlib import Path
import os

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


def validate_critical_imports():
    """Validate that all critical modules can be imported."""
    errors = []

    critical_imports = [
        "app.main",
        "app.managers",
        "app.managers.websocket_manager",
        "app.managers.rule_manager",
        "app.managers.scoring_manager",
        "app.models",
        "app.database",
        "app.schemas",
    ]

    print("🔍 Validating critical imports...")

    for module_name in critical_imports:
        try:
            importlib.import_module(module_name)
            print(f"  ✅ {module_name}")
        except ModuleNotFoundError as e:
            errors.append(f"  ❌ {module_name}: ModuleNotFoundError - {e}")
        except ImportError as e:
            errors.append(f"  ❌ {module_name}: ImportError - {e}")
        except Exception as e:
            errors.append(f"  ❌ {module_name}: {type(e).__name__} - {e}")

    return errors


def validate_managers_package():
    """Validate that managers package exports are correct."""
    errors = []

    print("\n🔍 Validating managers package exports...")

    try:
        import app.managers as managers

        required_exports = [
            "RuleManager",
            "RuleViolationError",
            "ScoringManager",
            "get_scoring_manager",
            "WebSocketManager",
            "manager",
        ]

        # Check __all__ exists
        if not hasattr(managers, '__all__'):
            errors.append("  ❌ managers package missing __all__ attribute")
            return errors

        # Check all required exports are in __all__
        for export_name in required_exports:
            if export_name not in managers.__all__:
                errors.append(f"  ❌ {export_name} not in managers.__all__")
            elif not hasattr(managers, export_name):
                errors.append(f"  ❌ {export_name} defined in __all__ but not exported")
            else:
                print(f"  ✅ {export_name}")

    except Exception as e:
        errors.append(f"  ❌ Failed to validate managers package: {e}")

    return errors


def validate_app_startup():
    """Validate that FastAPI app can be created."""
    print("\n🔍 Validating FastAPI app startup...")

    try:
        from app.main import app

        # Verify basic app structure
        if not hasattr(app, 'routes'):
            return ["  ❌ FastAPI app missing routes attribute"]

        if len(app.routes) == 0:
            return ["  ❌ FastAPI app has no routes registered"]

        print(f"  ✅ FastAPI app created with {len(app.routes)} routes")
        return []

    except Exception as e:
        return [f"  ❌ Failed to create FastAPI app: {e}"]


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("Python Import Validation")
    print("=" * 60)

    all_errors = []

    # Run validation checks
    all_errors.extend(validate_critical_imports())
    all_errors.extend(validate_managers_package())
    all_errors.extend(validate_app_startup())

    # Print results
    print("\n" + "=" * 60)
    if all_errors:
        print("❌ VALIDATION FAILED")
        print("=" * 60)
        print("\nErrors detected:")
        for error in all_errors:
            print(error)
        print("\nPlease fix these import errors before committing.")
        return 1
    else:
        print("✅ ALL VALIDATIONS PASSED")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    sys.exit(main())
