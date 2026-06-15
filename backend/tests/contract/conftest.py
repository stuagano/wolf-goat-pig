"""Shared fixtures for contract tests.

Contract tests mock every external HTTP boundary; nothing here should make a
real network call. Each test module uses `respx` (httpx) or `responses`
(requests) to intercept its service's endpoint.
"""

import pytest


@pytest.fixture
def anyio_backend():
    # pytest-asyncio uses this; keep async contract tests on asyncio.
    return "asyncio"
