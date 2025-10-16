"""Behave environment hooks for Wolf Goat Pig BDD tests."""

from __future__ import annotations

import sys
import os
from pathlib import Path


def before_all(context) -> None:
    """Ensure the repository root is importable and test env vars are set."""

    repo_root = Path(__file__).resolve().parents[2]
    repo_str = str(repo_root)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)

    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("DATABASE_URL", "sqlite:///./reports/wolf_goat_pig.db")


def before_scenario(context, scenario) -> None:  # pragma: no cover - Behave hook
    """Reset scenario-scoped attributes so state never bleeds between tests."""

    context.response = None
    context.responses = []
    context.current_state = None
    context.setup_response = None


def after_scenario(context, scenario) -> None:  # pragma: no cover - Behave hook
    """Tear down scenario-level state."""

    context.response = None
    context.current_state = None
    context.setup_response = None
    if hasattr(context, "responses"):
        context.responses.clear()
