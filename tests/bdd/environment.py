"""Behave environment hooks for Wolf Goat Pig BDD tests."""

from __future__ import annotations

import sys
from pathlib import Path


def before_all(context) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    repo_str = str(repo_root)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)

