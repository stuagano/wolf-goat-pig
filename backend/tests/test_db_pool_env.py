"""Tests for the env-configurable DB pool helper (Phase 2 — Cloud SQL readiness)."""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.database import _int_env


def test_returns_default_when_unset(monkeypatch):
    monkeypatch.delenv("DB_POOL_SIZE", raising=False)
    assert _int_env("DB_POOL_SIZE", 5) == 5


def test_reads_valid_int(monkeypatch):
    monkeypatch.setenv("DB_POOL_SIZE", "20")
    assert _int_env("DB_POOL_SIZE", 5) == 20


def test_blank_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("DB_POOL_SIZE", "   ")
    assert _int_env("DB_POOL_SIZE", 5) == 5


def test_invalid_int_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("DB_MAX_OVERFLOW", "not-a-number")
    assert _int_env("DB_MAX_OVERFLOW", 10) == 10
