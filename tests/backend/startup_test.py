import uvicorn
from app.main import app
import multiprocessing
import time
import httpx

def run_app():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

async def test_server():
    server_process = multiprocessing.Process(target=run_app)
    server_process.start()
    time.sleep(5)  # Give the server a moment to start

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:8000/health")
            print(f"Health check response: {response.status_code}")
            if response.status_code == 200:
                print("Server is healthy!")
                print(response.json())
            else:
                print("Server is not healthy.")
                print(response.text)
    except Exception as e:
        print(f"Error connecting to server: {e}")
    finally:
        server_process.terminate()
        server_process.join()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_server())
