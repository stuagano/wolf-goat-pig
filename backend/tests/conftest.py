"""Shared test configuration for backend test suite.

Ensures the backend package is importable from the repository root and keeps
test-only endpoints disabled by default so unit suites reflect production
behavior.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _ensure_repo_root_on_path() -> None:
    """Add the repository root to sys.path when missing."""
    repo_root = Path(__file__).resolve().parents[2]
    repo_root_str = str(repo_root)

    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


_ensure_repo_root_on_path()

# Harden default environment for backend tests.
os.environ.setdefault("ENABLE_TEST_ENDPOINTS", "false")
