"""Shared fixtures for contract tests.

Contract tests mock every external HTTP boundary; nothing here should make a
real network call. Each test module uses `respx` (httpx) or `responses`
(requests) to intercept its service's endpoint.
"""

import pytest

# Proxy env vars that httpx honors when constructing a client. Contract tests
# mock all I/O, so a real proxy must never be involved; on machines behind a
# SOCKS proxy (e.g. the local sandbox) an unset `socksio` dep otherwise makes
# httpx raise at client construction — the same failure mode as the documented
# local-only startup_test. CI has no proxy, so this is a no-op there.
_PROXY_ENV_VARS = (
    "ALL_PROXY",
    "all_proxy",
    "HTTP_PROXY",
    "http_proxy",
    "HTTPS_PROXY",
    "https_proxy",
)


@pytest.fixture(autouse=True)
def _no_proxy_for_contract_tests(monkeypatch):
    """Ensure httpx clients in contract tests never pick up a real proxy."""
    for var in _PROXY_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def anyio_backend():
    # pytest-asyncio uses this; keep async contract tests on asyncio.
    return "asyncio"
