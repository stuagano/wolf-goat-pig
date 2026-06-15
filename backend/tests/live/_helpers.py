"""Helpers for the live external-service suite."""

import os

import pytest


def require_env(*names: str) -> dict[str, str]:
    """Return the requested env vars, or skip the test if any is missing/empty.

    Usage:
        env = require_env("GROQ_API_KEY")
        key = env["GROQ_API_KEY"]
    """
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        pytest.skip(f"live: not configured (missing {', '.join(missing)})")
    return {n: os.environ[n] for n in names}
