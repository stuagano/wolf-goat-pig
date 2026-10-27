import asyncio
import multiprocessing
from time import monotonic
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
import uvicorn

from app.main import app


def run_app():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


@pytest.mark.asyncio
async def test_server():
    server_process = multiprocessing.Process(target=run_app)
    server_process.start()

    try:
        async with httpx.AsyncClient() as client:
            response = await wait_for_health(server_process, client)
            # Server may return 200 (fully healthy) or 503 (unhealthy components)
            # depending on environment; either proves the server started successfully.
            assert response.status_code in (200, 503)
    finally:
        server_process.terminate()
        server_process.join(timeout=5)
        if server_process.is_alive():
            server_process.kill()
            server_process.join(timeout=5)


async def wait_for_health(process, client, startup_budget=30):
    """Wait for normal startup, never treating a live child as proof of readiness."""
    started = monotonic()
    deadline = started + startup_budget
    last_error = "none"
    while True:
        remaining = deadline - monotonic()
        if not process.is_alive():
            reason = "child exited"
        elif remaining <= 0:
            reason = "readiness deadline exceeded"
        else:
            try:
                return await client.get("http://127.0.0.1:8000/health", timeout=min(1, remaining))
            except httpx.TransportError as error:
                # Exception text/URLs may contain sensitive data; report only the type.
                last_error = type(error).__name__
            await asyncio.sleep(min(0.1, max(0, deadline - monotonic())))
            continue
        raise AssertionError(
            f"{reason}; elapsed={monotonic() - started:.2f}s; exitcode={process.exitcode}; last_error={last_error}"
        )


@pytest.mark.asyncio
async def test_readiness_retries_until_health_response(monkeypatch):
    process = SimpleNamespace(is_alive=lambda: True, exitcode=None)
    client = SimpleNamespace(
        get=AsyncMock(side_effect=[httpx.ConnectError("not ready"), SimpleNamespace(status_code=503)])
    )
    sleep = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep)

    response = await wait_for_health(process, client)

    assert response.status_code == 503
    assert client.get.await_count == 2
    sleep.assert_awaited_once()


@pytest.mark.asyncio
async def test_readiness_reports_early_child_exit_without_request():
    process = SimpleNamespace(is_alive=lambda: False, exitcode=1)
    client = SimpleNamespace(get=AsyncMock())

    with pytest.raises(AssertionError, match=r"child exited.*exitcode=1"):
        await wait_for_health(process, client)

    client.get.assert_not_awaited()


@pytest.mark.asyncio
async def test_readiness_deadline_is_bounded_and_sanitized(monkeypatch):
    process = SimpleNamespace(is_alive=lambda: True, exitcode=None)
    client = SimpleNamespace(get=AsyncMock(side_effect=httpx.ConnectError("SECRET_SENTINEL")))
    ticks = iter([0.0, 0.0, 31.0, 31.0, 31.0])
    monkeypatch.setitem(wait_for_health.__globals__, "monotonic", lambda: next(ticks))
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())

    with pytest.raises(AssertionError, match=r"deadline.*last_error=ConnectError") as error:
        await wait_for_health(process, client)

    assert "SECRET_SENTINEL" not in str(error.value)
    client.get.assert_awaited_once()


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_server())
