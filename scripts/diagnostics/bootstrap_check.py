#!/usr/bin/env python3
"""Repository bootstrap checks used during diagnostics."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]


def _resolve(paths: Iterable[str]) -> list[Path]:
    return [REPO_ROOT / path for path in paths]


def check_required_files() -> bool:
    """Ensure critical backend and frontend files exist."""

    required_paths = _resolve(
        [
            "backend/app/main.py",
            "backend/app/seed_data.py",
            "backend/app/game_state.py",
            "backend/startup.py",
            "backend/requirements.txt",
            "frontend/src/App.js",
            "frontend/package.json",
        ]
    )

    print("🔍 Verifying core file layout...")
    missing = [path.relative_to(REPO_ROOT) for path in required_paths if not path.exists()]

    for path in required_paths:
        if path.exists():
            print(f"✅ {path.relative_to(REPO_ROOT)}")

    if missing:
        print(f"❌ Missing files: {', '.join(str(path) for path in missing)}")
        return False

    print("✅ Repository layout looks good")
    return True


def check_frontend_package() -> bool:
    """Validate that the frontend package.json is well-formed."""

    package_json = REPO_ROOT / "frontend/package.json"
    print("🔍 Validating frontend/package.json...")

    try:
        data = json.loads(package_json.read_text())
    except FileNotFoundError:
        print("❌ frontend/package.json not found")
        return False
    except json.JSONDecodeError as exc:
        print(f"❌ Invalid JSON in frontend/package.json: {exc}")
        return False

    scripts = data.get("scripts", {})
    required_scripts = {"start", "build", "test"}
    missing_scripts = sorted(required_scripts - set(scripts))

    if missing_scripts:
        print(f"⚠️ Missing npm scripts: {', '.join(missing_scripts)}")
    else:
        print("✅ Required npm scripts present")

    return True


def check_startup_module() -> bool:
    """Ensure the backend startup helper exposes expected hooks."""

    startup_path = REPO_ROOT / "backend/startup.py"
    print("🔍 Inspecting backend/startup.py...")

    if not startup_path.exists():
        print("⚠️ backend/startup.py not found")
        return False

    content = startup_path.read_text()
    required_tokens = ["BootstrapManager", "check_dependencies", "seed_data"]

    missing_tokens = [token for token in required_tokens if token not in content]

    if missing_tokens:
        print(f"⚠️ Missing expected helpers: {', '.join(missing_tokens)}")
        return False

    print("✅ Startup helpers detected")
    return True


def main() -> bool:
    """Run all bootstrap validations."""

    checks = [check_required_files(), check_frontend_package(), check_startup_module()]
    success = all(checks)

    if success:
        print("\n🎉 Bootstrap diagnostics passed")
    else:
        print("\n⚠️ Bootstrap diagnostics reported issues")

    return success


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
