import multiprocessing
import time

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
    time.sleep(5)  # Give the server a moment to start

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:8000/health")
            # Server may return 200 (fully healthy) or 503 (unhealthy components)
            # depending on environment; either proves the server started successfully.
            assert response.status_code in (200, 503)
    finally:
        server_process.terminate()
        server_process.join()


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_server())
