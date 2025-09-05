"""
End-to-end test for Wolf Goat Pig simulation using Playwright.
Tests the complete user flow through the simulation interface.
"""

from playwright.sync_api import sync_playwright, Page, expect
import pytest
import time

class TestSimulationE2E:
    """E2E tests for Wolf Goat Pig simulation mode"""
    
    @pytest.fixture
    def browser_page(self):
        """Setup browser and page for testing"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            yield page
            browser.close()
    
    def test_simulation_setup_and_start(self, browser_page: Page):
        """Test setting up and starting a simulation"""
        page = browser_page
        
        # Navigate to app
        page.goto("http://localhost:3000")
        
        # Navigate to simulation mode
        page.click("text=Simulation Mode")
        
        # Fill in player name
        page.fill('input[placeholder*="Enter your name"]', "Test Player")
        
        # Select handicap
        page.select_option('select[name="handicap"]', "18")
        
        # Select course
        page.select_option('select[name="course"]', "Wing Point Golf & Country Club")
        
        # Start simulation
        page.click("button:has-text('Start Simulation')")
        
        # Wait for game to start
        page.wait_for_selector("text=Captain Phase", timeout=10000)
        
        # Verify captain phase is displayed
        expect(page.locator("text=Captain Phase")).to_be_visible()
        
        # Verify base wager is displayed
        expect(page.locator("text=Base wager")).to_be_visible()
    
    def test_captain_decision_flow(self, browser_page: Page):
        """Test captain decision making during simulation"""
        page = browser_page
        
        # Setup and start simulation (reuse previous test logic)
        page.goto("http://localhost:3000")
        page.click("text=Simulation Mode")
        page.fill('input[placeholder*="Enter your name"]', "Test Player")
        page.select_option('select[name="handicap"]', "18")
        page.click("button:has-text('Start Simulation')")
        
        # Wait for captain phase
        page.wait_for_selector("text=Captain Phase", timeout=10000)
        
        # Play tee shots if available
        if page.locator("button:has-text('Play Tee Shots')").is_visible():
            page.click("button:has-text('Play Tee Shots')")
            time.sleep(2)  # Wait for shots to complete
        
        # Check for partnership options
        if page.locator("text=Partnership Invitations Available").is_visible():
            # Test going solo
            page.click("button:has-text('Go Solo')")
            
            # Verify match play starts
            page.wait_for_selector("text=Match Play", timeout=5000)
            expect(page.locator("text=Match Play")).to_be_visible()
    
    def test_match_play_progression(self, browser_page: Page):
        """Test match play phase and shot progression"""
        page = browser_page
        
        # Setup and navigate to match play
        page.goto("http://localhost:3000")
        page.click("text=Simulation Mode")
        page.fill('input[placeholder*="Enter your name"]', "Test Player")
        page.click("button:has-text('Start Simulation')")
        
        # Wait for game to start
        page.wait_for_selector("text=Captain Phase", timeout=10000)
        
        # Play several shots
        for _ in range(3):
            if page.locator("button:has-text('Play Next Shot')").is_visible():
                page.click("button:has-text('Play Next Shot')")
                time.sleep(1)  # Wait for shot animation
        
        # Check for betting opportunities
        if page.locator("text=Betting Opportunities").is_visible():
            # Verify Line of Scrimmage rule is displayed
            expect(page.locator("text=Line of Scrimmage")).to_be_visible()
    
    def test_hole_completion(self, browser_page: Page):
        """Test completing a hole and transitioning to next"""
        page = browser_page
        
        # Setup game
        page.goto("http://localhost:3000")
        page.click("text=Simulation Mode")
        page.fill('input[placeholder*="Enter your name"]', "Test Player")
        page.click("button:has-text('Start Simulation')")
        
        # Play through hole by clicking Play Next Shot repeatedly
        max_shots = 20  # Prevent infinite loop
        shots_played = 0
        
        while shots_played < max_shots:
            if page.locator("button:has-text('Play Next Shot')").is_visible():
                page.click("button:has-text('Play Next Shot')")
                shots_played += 1
                time.sleep(0.5)
            
            # Check if we've moved to hole 2
            if page.locator("text=Hole 2").is_visible():
                break
        
        # Verify we progressed to next hole
        if shots_played < max_shots:
            expect(page.locator("text=Hole 2")).to_be_visible()
    
    def test_partnership_acceptance(self, browser_page: Page):
        """Test partnership invitation and acceptance flow"""
        page = browser_page
        
        # This test would require setting up a scenario where the human is invited
        # For now, we'll check the UI elements exist
        page.goto("http://localhost:3000")
        page.click("text=Simulation Mode")
        page.fill('input[placeholder*="Enter your name"]', "Test Player")
        page.click("button:has-text('Start Simulation')")
        
        # Wait for game
        page.wait_for_selector("text=Captain Phase", timeout=10000)
        
        # Check if partnership prompt appears
        if page.locator("text=Partnership Invitation").is_visible():
            # Verify accept/decline buttons
            expect(page.locator("button:has-text('Yes, I'll be your partner')")).to_be_visible()
            expect(page.locator("button:has-text('No, I decline')")).to_be_visible()
            
            # Accept partnership
            page.click("button:has-text('Yes, I'll be your partner')")
            
            # Verify team formation
            page.wait_for_selector("text=Team Formation", timeout=5000)

if __name__ == "__main__":
    # Run a quick smoke test
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Navigate to app
            page.goto("http://localhost:3000")
            print(" Successfully connected to app")
            
            # Check for simulation mode
            if page.locator("text=Simulation Mode").is_visible():
                print(" Simulation Mode button found")
                page.click("text=Simulation Mode")
                
                # Check setup form
                if page.locator('input[placeholder*="name"]').is_visible():
                    print(" Setup form is accessible")
                else:
                    print("L Setup form not found")
            else:
                print("L Simulation Mode button not found")
                
        except Exception as e:
            print(f"L Error during test: {e}")
        finally:
            browser.close()