"""Unit tests for shared router request-validation helpers."""

import pytest

from app.routers._validators import non_blank


def test_non_blank_strips_surrounding_whitespace():
    assert non_blank("  hello  ") == "hello"


def test_non_blank_returns_unchanged_when_clean():
    assert non_blank("hello") == "hello"


def test_non_blank_rejects_empty_string():
    with pytest.raises(ValueError):
        non_blank("")


def test_non_blank_rejects_whitespace_only():
    with pytest.raises(ValueError):
        non_blank("   ")
