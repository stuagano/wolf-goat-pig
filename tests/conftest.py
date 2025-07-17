"""
Configuration for BDD tests with Playwright
"""

import asyncio
import pytest
import pytest_asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import subprocess
import time
import requests
import os
import signal

# Test configuration
BACKEND_PORT = 8000
FRONTEND_PORT = 3000
BASE_URL = f"http://localhost:{FRONTEND_PORT}"
API_URL = f"http://localhost:{BACKEND_PORT}"

class TestServers:
    """Manages backend and frontend servers for testing"""
    
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        
    def start_backend(self):
        """Start the FastAPI backend server"""
        print("🚀 Starting backend server...")
        cmd = [
            "python", "-m", "uvicorn", 
            "backend.app.main:app", 
            "--host", "0.0.0.0", 
            "--port", str(BACKEND_PORT),
            "--reload"
        ]
        
        self.backend_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )
        
        # Wait for backend to be ready
        self._wait_for_service(API_URL, "backend", timeout=30)
        
    def start_frontend(self):
        """Start the React frontend server"""
        print("🚀 Starting frontend server...")
        
        # Change to frontend directory and start
        cmd = ["npm", "start"]
        env = os.environ.copy()
        env["PORT"] = str(FRONTEND_PORT)
        env["BROWSER"] = "none"  # Don't open browser automatically
        
        self.frontend_process = subprocess.Popen(
            cmd,
            cwd="frontend",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None
        )
        
        # Wait for frontend to be ready
        self._wait_for_service(BASE_URL, "frontend", timeout=60)
        
    def _wait_for_service(self, url, service_name, timeout=30):
        """Wait for a service to become available"""
        print(f"⏳ Waiting for {service_name} to be ready at {url}...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{url}/", timeout=5)
                if response.status_code < 500:  # Accept any non-server-error response
                    print(f"✅ {service_name.title()} server ready!")
                    return
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
        
        raise TimeoutError(f"❌ {service_name.title()} server failed to start within {timeout} seconds")
    
    def stop_servers(self):
        """Stop both servers"""
        if self.backend_process:
            print("🛑 Stopping backend server...")
            try:
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(self.backend_process.pid), signal.SIGTERM)
                else:
                    self.backend_process.terminate()
                self.backend_process.wait(timeout=10)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(self.backend_process.pid), signal.SIGKILL)
                else:
                    self.backend_process.kill()
            
        if self.frontend_process:
            print("🛑 Stopping frontend server...")
            try:
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(self.frontend_process.pid), signal.SIGTERM)
                else:
                    self.frontend_process.terminate()
                self.frontend_process.wait(timeout=10)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                if hasattr(os, 'killpg'):
                    os.killpg(os.getpgid(self.frontend_process.pid), signal.SIGKILL)
                else:
                    self.frontend_process.kill()

# Global test servers instance
test_servers = None

def pytest_configure(config):
    """Configure pytest - start servers before any tests"""
    global test_servers
    test_servers = TestServers()
    
    # Only start servers if we're running BDD tests
    if config.getoption("--tb") or "monte_carlo" in str(config.args):
        try:
            test_servers.start_backend()
            test_servers.start_frontend()
        except Exception as e:
            print(f"❌ Failed to start test servers: {e}")
            raise

def pytest_unconfigure(config):
    """Clean up after all tests"""
    global test_servers
    if test_servers:
        test_servers.stop_servers()

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def browser():
    """Create a browser instance for the test session"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,  # Set to False for debugging
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-extensions",
                "--disable-default-apps",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding"
            ]
        )
        yield browser
        await browser.close()

@pytest_asyncio.fixture(scope="function")
async def browser_context(browser: Browser):
    """Create a fresh browser context for each test"""
    context = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        ignore_https_errors=True,
        java_script_enabled=True
    )
    yield context
    await context.close()

@pytest_asyncio.fixture(scope="function") 
async def page(browser_context: BrowserContext):
    """Create a fresh page for each test"""
    page = await browser_context.new_page()
    
    # Add console logging for debugging
    def handle_console(msg):
        if msg.type in ['error', 'warning']:
            print(f"🖥️  Browser {msg.type}: {msg.text}")
    
    page.on("console", handle_console)
    
    # Add error handling
    def handle_page_error(error):
        print(f"💥 Page error: {error}")
    
    page.on("pageerror", handle_page_error)
    
    yield page
    await page.close()

@pytest.fixture(scope="session")
def base_url():
    """Base URL for the application"""
    return BASE_URL

@pytest.fixture(scope="session") 
def api_url():
    """API URL for backend testing"""
    return API_URL

# Pytest collection hooks
def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their location"""
    for item in items:
        # Add 'bdd' marker to all BDD tests
        if "features" in str(item.fspath) or "step_definitions" in str(item.fspath):
            item.add_marker(pytest.mark.bdd)
        
        # Add 'slow' marker to tests that run simulations
        if "monte_carlo" in item.name.lower() or "simulation" in item.name.lower():
            item.add_marker(pytest.mark.slow)

# Custom pytest markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "bdd: mark test as behavior-driven development test")
    config.addinivalue_line("markers", "slow: mark test as slow running") 
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "smoke: mark test as smoke test")

# Test utilities
class BDDTestHelper:
    """Helper methods for BDD tests"""
    
    @staticmethod
    async def wait_for_monte_carlo_ready(page: Page):
        """Wait for Monte Carlo page to be fully loaded"""
        await page.wait_for_selector('.monte-carlo-container', timeout=10000)
        await page.wait_for_selector('button:has-text("Run Monte Carlo Simulation")', timeout=5000)
    
    @staticmethod
    async def fill_default_simulation_config(page: Page):
        """Fill in a default simulation configuration"""
        # Human player
        human_name = page.locator('.player-section input[type="text"]').first
        await human_name.clear()
        await human_name.fill("Stuart")
        
        human_handicap = page.locator('.player-section input[type="number"]').first
        await human_handicap.clear()  
        await human_handicap.fill("10")
        
        # Computer opponents
        computer_rows = page.locator('.computer-player-row')
        
        # Opponent 1
        row1 = computer_rows.nth(0)
        await row1.locator('input[type="text"]').fill("Tiger Bot")
        await row1.locator('input[type="number"]').fill("2.0")
        await row1.locator('select').select_option("aggressive")
        
        # Opponent 2
        row2 = computer_rows.nth(1)
        await row2.locator('input[type="text"]').fill("Strategic Sam")
        await row2.locator('input[type="number"]').fill("8.5")
        await row2.locator('select').select_option("strategic")
        
        # Opponent 3
        row3 = computer_rows.nth(2)
        await row3.locator('input[type="text"]').fill("Conservative Carl")
        await row3.locator('input[type="number"]').fill("15.0")
        await row3.locator('select').select_option("conservative")
        
        # Number of simulations
        sim_count = page.locator('input[type="number"]').last
        await sim_count.clear()
        await sim_count.fill("10")  # Small number for fast testing
    
    @staticmethod
    async def verify_simulation_results(page: Page):
        """Verify that simulation results are displayed correctly"""
        # Check results container is visible
        results = page.locator('.results-container')
        assert await results.is_visible(), "Results container should be visible"
        
        # Check key sections
        insights = page.locator('.insights-section')
        assert await insights.is_visible(), "Insights section should be visible"
        
        player_stats = page.locator('.player-stats-section')
        assert await player_stats.is_visible(), "Player stats section should be visible"
        
        recommendations = page.locator('.recommendations-section')
        assert await recommendations.is_visible(), "Recommendations section should be visible"
        
        # Check that all 4 player cards are present
        player_cards = page.locator('.player-stat-card')
        card_count = await player_cards.count()
        assert card_count == 4, f"Expected 4 player cards, found {card_count}"
        
        # Check human player card is highlighted
        human_card = page.locator('.player-stat-card.human-player')
        assert await human_card.is_visible(), "Human player card should be highlighted"

@pytest.fixture
def bdd_helper():
    """Provide BDD test helper methods"""
    return BDDTestHelper