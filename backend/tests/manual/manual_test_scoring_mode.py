"""
Test scoring mode through a full round using Playwright
"""
from playwright.sync_api import sync_playwright
import time
import requests

def create_test_game():
    """Create a 5-player test game via API"""
    response = requests.post("http://localhost:8000/games/create-test?player_count=5")
    data = response.json()
    return data["game_id"], data["players"]

def test_full_round():
    game_id, players = create_test_game()
    print(f"✅ Created test game: {game_id}")
    print(f"Players: {[p['name'] for p in players]}")

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Navigate to game
        game_url = f"http://localhost:3001/games/{game_id}"
        print(f"\n🌐 Navigating to: {game_url}")
        page.goto(game_url)
        time.sleep(2)

        # Take screenshot of initial state
        page.screenshot(path="screenshots/01-game-start.png")
        print("📸 Screenshot: 01-game-start.png")

        # Look for scoring mode button/link
        try:
            # Try to find and click scoring button
            scoring_button = page.locator("text=Score").first
            if scoring_button.is_visible():
                scoring_button.click()
                print("✅ Clicked 'Score' button")
                time.sleep(1)
                page.screenshot(path="screenshots/02-scoring-mode.png")
                print("📸 Screenshot: 02-scoring-mode.png")
        except Exception as e:
            print(f"⚠️ Could not find scoring button: {e}")

        # Look for hole 1 scoring
        try:
            hole1 = page.locator("text=Hole 1").first
            if hole1.is_visible():
                hole1.click()
                print("✅ Selected Hole 1")
                time.sleep(1)
                page.screenshot(path="screenshots/03-hole1-selected.png")
                print("📸 Screenshot: 03-hole1-selected.png")
        except Exception as e:
            print(f"⚠️ Could not select hole 1: {e}")

        # Try to enter scores
        try:
            # Look for score input fields
            score_inputs = page.locator("input[type='number']").all()
            if score_inputs:
                print(f"✅ Found {len(score_inputs)} score input fields")
                # Enter test scores: 4, 4, 5, 5, 4
                scores = [4, 4, 5, 5, 4]
                for i, score in enumerate(scores[:len(score_inputs)]):
                    score_inputs[i].fill(str(score))
                    print(f"  Entered score {score} for player {i+1}")

                time.sleep(1)
                page.screenshot(path="screenshots/04-scores-entered.png")
                print("📸 Screenshot: 04-scores-entered.png")
        except Exception as e:
            print(f"⚠️ Could not enter scores: {e}")

        # Look for team selection
        try:
            # Try to find partner selection
            partner_buttons = page.locator("button").all()
            partner_text_buttons = [b for b in partner_buttons if "Partner" in b.text_content() or "partner" in b.text_content()]
            if partner_text_buttons:
                partner_text_buttons[0].click()
                print("✅ Clicked partner button")
                time.sleep(1)
                page.screenshot(path="screenshots/05-partner-selected.png")
                print("📸 Screenshot: 05-partner-selected.png")
        except Exception as e:
            print(f"⚠️ Could not select partner: {e}")

        # Look for submit/complete button
        try:
            submit_buttons = page.locator("button").all()
            submit_text_buttons = [b for b in submit_buttons if any(word in b.text_content().lower() for word in ["complete", "submit", "done", "finish"])]
            if submit_text_buttons:
                submit_text_buttons[0].click()
                print("✅ Clicked complete/submit button")
                time.sleep(2)
                page.screenshot(path="screenshots/06-hole-completed.png")
                print("📸 Screenshot: 06-hole-completed.png")
        except Exception as e:
            print(f"⚠️ Could not submit hole: {e}")

        # Get final page content
        print("\n📄 Final page content:")
        print(page.content()[:500])

        # Keep browser open for inspection
        print("\n⏸️  Browser will stay open for 10 seconds for inspection...")
        time.sleep(10)

        browser.close()
        print("\n✅ Test completed!")

if __name__ == "__main__":
    import os
    os.makedirs("screenshots", exist_ok=True)
    test_full_round()
