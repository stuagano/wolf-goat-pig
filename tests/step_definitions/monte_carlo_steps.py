"""
Step definitions for Monte Carlo simulation BDD tests
"""

import asyncio
import re
import time
from playwright.async_api import Page, expect
from pytest_bdd import given, when, then, scenarios, parsers

# Import all scenarios from the feature file
scenarios('../features/monte_carlo_simulation.feature')

class MonteCarloTestHelper:
    def __init__(self, page: Page):
        self.page = page
        self.base_url = "http://localhost:3000"
        self.simulation_results = None
        
    async def wait_for_app_ready(self):
        """Wait for the app to be fully loaded"""
        await self.page.wait_for_load_state('networkidle')
        await self.page.wait_for_selector('nav', timeout=10000)

# Background steps
@given('the Wolf Goat Pig application is running')
async def app_is_running(page: Page):
    helper = MonteCarloTestHelper(page)
    await page.goto(helper.base_url)
    await helper.wait_for_app_ready()
    # Store helper in page context for other steps
    page.test_helper = helper

@given('I navigate to the Monte Carlo simulation page')
async def navigate_to_monte_carlo(page: Page):
    await page.click('button:has-text("🎲 Monte Carlo")')
    await page.wait_for_url('**/monte-carlo')
    await page.wait_for_selector('h2:has-text("Monte Carlo Simulation")')

# Configuration steps
@given('I am on the Monte Carlo simulation page')
async def on_monte_carlo_page(page: Page):
    # This step is handled by the background
    await page.wait_for_selector('.monte-carlo-container')

@when(parsers.parse('I configure the human player as "{name}" with handicap "{handicap}"'))
async def configure_human_player(page: Page, name: str, handicap: str):
    # Fill human player name
    human_name_input = page.locator('input[type="text"]').first
    await human_name_input.clear()
    await human_name_input.fill(name)
    
    # Fill human player handicap
    human_handicap_input = page.locator('input[type="number"]').first
    await human_handicap_input.clear()
    await human_handicap_input.fill(handicap)

@when(parsers.parse('I configure computer opponent {opponent_num:d} as "{name}" with handicap "{handicap}" and "{personality}" personality'))
async def configure_computer_opponent(page: Page, opponent_num: int, name: str, handicap: str, personality: str):
    # Computer opponents are in the computer player section
    opponent_index = opponent_num - 1  # Convert to 0-based index
    
    # Find the computer player rows
    computer_rows = page.locator('.computer-player-row')
    target_row = computer_rows.nth(opponent_index)
    
    # Fill name
    name_input = target_row.locator('input[type="text"]')
    await name_input.clear()
    await name_input.fill(name)
    
    # Fill handicap
    handicap_input = target_row.locator('input[type="number"]')
    await handicap_input.clear()
    await handicap_input.fill(handicap)
    
    # Select personality
    personality_select = target_row.locator('select')
    await personality_select.select_option(personality.lower())

@when(parsers.parse('I set the number of simulations to "{num_sims}"'))
async def set_simulation_count(page: Page, num_sims: str):
    sim_input = page.locator('input[type="number"]').last
    await sim_input.clear()
    await sim_input.fill(num_sims)

# Validation steps
@then('the simulation setup should be valid')
async def simulation_setup_valid(page: Page):
    # Check that all required fields are filled
    human_name = await page.locator('.player-section input[type="text"]').first.input_value()
    assert human_name.strip() != "", "Human player name should be filled"
    
    human_handicap = await page.locator('.player-section input[type="number"]').first.input_value()
    assert human_handicap.strip() != "", "Human player handicap should be filled"

@then(parsers.parse('the "{button_text}" button should be enabled'))
async def button_should_be_enabled(page: Page, button_text: str):
    button = page.locator(f'button:has-text("{button_text}")')
    await expect(button).to_be_enabled()

# Simulation execution steps
@given('I have configured a valid simulation setup')
async def valid_simulation_setup(page: Page):
    # Configure a standard test setup
    await configure_human_player(page, "Stuart", "10")
    await configure_computer_opponent(page, 1, "Tiger Bot", "2.0", "aggressive")
    await configure_computer_opponent(page, 2, "Strategic Sam", "8.5", "strategic")
    await configure_computer_opponent(page, 3, "Conservative Carl", "15.0", "conservative")
    await set_simulation_count(page, "25")

@when('I click the "Run Monte Carlo Simulation" button')
async def click_run_simulation(page: Page):
    run_button = page.locator('button:has-text("Run Monte Carlo Simulation")')
    await run_button.click()

@then('I should see a loading indicator')
async def should_see_loading_indicator(page: Page):
    # Wait for loading indicator to appear
    loading_indicator = page.locator('.running-indicator, .spinner')
    await expect(loading_indicator).to_be_visible(timeout=5000)

@then(parsers.parse('the simulation should complete within "{timeout}" seconds'))
async def simulation_completes_within_timeout(page: Page, timeout: str):
    timeout_ms = int(timeout) * 1000
    
    # Wait for results container to appear
    results_container = page.locator('.results-container')
    await expect(results_container).to_be_visible(timeout=timeout_ms)
    
    # Wait for loading indicator to disappear
    loading_indicator = page.locator('.running-indicator')
    await expect(loading_indicator).to_be_hidden(timeout=timeout_ms)

@then('I should see the simulation results')
async def should_see_simulation_results(page: Page):
    results_container = page.locator('.results-container')
    await expect(results_container).to_be_visible()
    
    # Check for key sections
    await expect(page.locator('.insights-section')).to_be_visible()
    await expect(page.locator('.player-stats-section')).to_be_visible()

# Results validation steps
@given(parsers.parse('I have completed a Monte Carlo simulation with "{num_games}" games'))
async def completed_simulation_with_games(page: Page, num_games: str):
    await valid_simulation_setup(page)
    await set_simulation_count(page, num_games)
    await click_run_simulation(page)
    await simulation_completes_within_timeout(page, "60")

@given('I have completed a Monte Carlo simulation')
async def completed_simulation(page: Page):
    await completed_simulation_with_games(page, "25")

@then('I should see win percentages for all 4 players')
async def should_see_win_percentages(page: Page):
    # Check that all 4 player cards are visible
    player_cards = page.locator('.player-stat-card')
    await expect(player_cards).to_have_count(4)
    
    # Check that each card has win percentage
    for i in range(4):
        card = player_cards.nth(i)
        win_text = card.locator('.stat-row:has(.stat-label:has-text("Wins"))')
        await expect(win_text).to_be_visible()

@then('the win percentages should add up to approximately 100%')
async def win_percentages_add_to_100(page: Page):
    # Extract win percentages and validate they sum to ~100%
    player_cards = page.locator('.player-stat-card')
    total_percentage = 0
    
    for i in range(4):
        card = player_cards.nth(i)
        win_stat = card.locator('.stat-row:has(.stat-label:has-text("Wins")) .stat-value')
        win_text = await win_stat.text_content()
        
        # Extract percentage from text like "5 wins (20.0%)"
        percentage_match = re.search(r'\((\d+\.?\d*)\%\)', win_text)
        if percentage_match:
            total_percentage += float(percentage_match.group(1))
    
    # Allow for some rounding errors
    assert 95 <= total_percentage <= 105, f"Win percentages should sum to ~100%, got {total_percentage}%"

@then('I should see average scores for all players')
async def should_see_average_scores(page: Page):
    player_cards = page.locator('.player-stat-card')
    
    for i in range(4):
        card = player_cards.nth(i)
        avg_score = card.locator('.stat-row:has(.stat-label:has-text("Avg Score"))')
        await expect(avg_score).to_be_visible()

@then("I should see key insights about Stuart's performance")
async def should_see_stuart_insights(page: Page):
    insights_section = page.locator('.insights-section')
    await expect(insights_section).to_be_visible()
    
    insights_list = page.locator('.insights-list li')
    await expect(insights_list).to_have_count_greater_than(0)

@then('I should see strategic recommendations')
async def should_see_strategic_recommendations(page: Page):
    recommendations_section = page.locator('.recommendations-section')
    await expect(recommendations_section).to_be_visible()

# Specific result analysis steps
@then("I should see Stuart's win percentage")
async def should_see_stuart_win_percentage(page: Page):
    # Find Stuart's card (should be highlighted as human player)
    stuart_card = page.locator('.player-stat-card.human-player')
    await expect(stuart_card).to_be_visible()
    
    win_stat = stuart_card.locator('.stat-row:has(.stat-label:has-text("Wins"))')
    await expect(win_stat).to_be_visible()

@then("I should see Stuart's average score per game")
async def should_see_stuart_average_score(page: Page):
    stuart_card = page.locator('.player-stat-card.human-player')
    avg_score = stuart_card.locator('.stat-row:has(.stat-label:has-text("Avg Score"))')
    await expect(avg_score).to_be_visible()

@then("I should see Stuart's best and worst game scores")
async def should_see_stuart_best_worst(page: Page):
    stuart_card = page.locator('.player-stat-card.human-player')
    
    best_score = stuart_card.locator('.stat-row:has(.stat-label:has-text("Best Game"))')
    await expect(best_score).to_be_visible()
    
    worst_score = stuart_card.locator('.stat-row:has(.stat-label:has-text("Worst Game"))')
    await expect(worst_score).to_be_visible()

@then('I should see score distribution for Stuart')
async def should_see_stuart_score_distribution(page: Page):
    stuart_card = page.locator('.player-stat-card.human-player')
    score_distribution = stuart_card.locator('.score-distribution')
    await expect(score_distribution).to_be_visible()

@then('the human player card should be visually highlighted')
async def human_player_card_highlighted(page: Page):
    human_card = page.locator('.player-stat-card.human-player')
    await expect(human_card).to_be_visible()
    
    # Check that it has the human-player class (which gives it special styling)
    await expect(human_card).to_have_class(re.compile(r'human-player'))

# Error handling steps
@when(parsers.parse('I clear the name field for computer opponent {opponent_num:d}'))
async def clear_opponent_name(page: Page, opponent_num: int):
    opponent_index = opponent_num - 1
    computer_rows = page.locator('.computer-player-row')
    target_row = computer_rows.nth(opponent_index)
    name_input = target_row.locator('input[type="text"]')
    await name_input.clear()

@then('I should see an error message')
async def should_see_error_message(page: Page):
    error_message = page.locator('.error-message')
    await expect(error_message).to_be_visible(timeout=5000)

@then('the simulation should not run')
async def simulation_should_not_run(page: Page):
    # Make sure no results container appears
    results_container = page.locator('.results-container')
    await expect(results_container).to_be_hidden()

# Performance and advanced tests
@then(parsers.parse('I should see results for {num_games:d} games'))
async def should_see_results_for_games(page: Page, num_games: int):
    simulation_details = page.locator('.simulation-details')
    total_games_text = simulation_details.locator('.detail-row:has-text("Total Games Played")')
    await expect(total_games_text).to_contain_text(str(num_games))

@given(parsers.parse('I have configured Stuart with handicap "{handicap}"'))
async def configure_stuart_handicap(page: Page, handicap: str):
    await configure_human_player(page, "Stuart", handicap)

@given(parsers.parse('I have configured three computer opponents with handicaps "{h1}", "{h2}", and "{h3}"'))
async def configure_three_opponents_handicaps(page: Page, h1: str, h2: str, h3: str):
    await configure_computer_opponent(page, 1, "Opponent 1", h1, "balanced")
    await configure_computer_opponent(page, 2, "Opponent 2", h2, "balanced")
    await configure_computer_opponent(page, 3, "Opponent 3", h3, "balanced")

@when(parsers.parse('I run a simulation with "{num_games}" games'))
async def run_simulation_with_games(page: Page, num_games: str):
    await set_simulation_count(page, num_games)
    await click_run_simulation(page)
    await simulation_completes_within_timeout(page, "90")

@then(parsers.parse('Stuart should have a win percentage greater than "{percentage}"'))
async def stuart_win_percentage_greater_than(page: Page, percentage: str):
    stuart_card = page.locator('.player-stat-card.human-player')
    win_stat = stuart_card.locator('.stat-row:has(.stat-label:has-text("Wins")) .stat-value')
    win_text = await win_stat.text_content()
    
    # Extract percentage
    percentage_match = re.search(r'\((\d+\.?\d*)\%\)', win_text)
    assert percentage_match, f"Could not extract percentage from: {win_text}"
    
    actual_percentage = float(percentage_match.group(1))
    expected_percentage = float(percentage.rstrip('%'))
    
    assert actual_percentage > expected_percentage, f"Expected > {expected_percentage}%, got {actual_percentage}%"

@then("Stuart's average score should be positive")
async def stuart_average_score_positive(page: Page):
    stuart_card = page.locator('.player-stat-card.human-player')
    avg_score_stat = stuart_card.locator('.stat-row:has(.stat-label:has-text("Avg Score")) .stat-value')
    avg_score_text = await avg_score_stat.text_content()
    
    # Extract the numeric value (handle +/- signs)
    score_match = re.search(r'([+-]?\d+\.?\d*)', avg_score_text)
    assert score_match, f"Could not extract score from: {avg_score_text}"
    
    actual_score = float(score_match.group(1))
    assert actual_score > 0, f"Expected positive score, got {actual_score}"

# UI and navigation steps
@then(parsers.parse('I should see the page title "{title}"'))
async def should_see_page_title(page: Page, title: str):
    page_title = page.locator(f'h2:has-text("{title}")')
    await expect(page_title).to_be_visible()

@then('I should see the description explaining Monte Carlo functionality')
async def should_see_monte_carlo_description(page: Page):
    description = page.locator('.description')
    await expect(description).to_be_visible()
    await expect(description).to_contain_text('Monte Carlo')

@then('I should see configuration sections for human player and computer opponents')
async def should_see_configuration_sections(page: Page):
    human_section = page.locator('.player-section:has-text("Human Player")')
    await expect(human_section).to_be_visible()
    
    computer_section = page.locator('.player-section:has-text("Computer Opponents")')
    await expect(computer_section).to_be_visible()

@then('I should see simulation parameters section')
async def should_see_simulation_parameters(page: Page):
    params_section = page.locator('.simulation-params')
    await expect(params_section).to_be_visible()

@when('I navigate away and back to the Monte Carlo page')
async def navigate_away_and_back(page: Page):
    # Navigate to home
    await page.click('button:has-text("Home")')
    await page.wait_for_url('**/')
    
    # Navigate back to Monte Carlo
    await page.click('button:has-text("🎲 Monte Carlo")')
    await page.wait_for_url('**/monte-carlo')

@then('the form should be reset to default values')
async def form_should_be_reset(page: Page):
    # Check that human player name is back to default
    human_name = await page.locator('.player-section input[type="text"]').first.input_value()
    assert human_name == "Stuart", f"Expected default name 'Stuart', got '{human_name}'"

# Responsive design steps
@when('I resize the browser to mobile dimensions')
async def resize_to_mobile(page: Page):
    await page.set_viewport_size({"width": 375, "height": 667})  # iPhone dimensions

@then('the layout should adapt to mobile view')
async def layout_adapts_to_mobile(page: Page):
    # Check that the container is still visible and properly sized
    container = page.locator('.monte-carlo-container')
    await expect(container).to_be_visible()

@then('all form elements should remain accessible')
async def form_elements_accessible_mobile(page: Page):
    # Check that key form elements are still visible and clickable
    human_name_input = page.locator('.player-section input[type="text"]').first
    await expect(human_name_input).to_be_visible()
    
    run_button = page.locator('button:has-text("Run Monte Carlo Simulation")')
    await expect(run_button).to_be_visible()

@then('the results display should be mobile-friendly')
async def results_mobile_friendly(page: Page):
    # This would be tested after running a simulation in mobile view
    # For now, just check that the container exists
    container = page.locator('.monte-carlo-container')
    await expect(container).to_be_visible()

# Strategic recommendation validation
@given('I have completed a simulation where Stuart has low win percentage')
async def simulation_with_low_win_percentage(page: Page):
    # Configure Stuart with high handicap vs low handicap opponents for low win rate
    await configure_human_player(page, "Stuart", "20")
    await configure_computer_opponent(page, 1, "Pro 1", "0", "aggressive")
    await configure_computer_opponent(page, 2, "Pro 2", "2", "strategic")
    await configure_computer_opponent(page, 3, "Pro 3", "1", "balanced")
    await set_simulation_count(page, "25")
    await click_run_simulation(page)
    await simulation_completes_within_timeout(page, "60")

@then('I should see recommendations about partnership selection')
async def should_see_partnership_recommendations(page: Page):
    recommendations = page.locator('.recommendations-section')
    await expect(recommendations).to_contain_text('partnership')

@then('I should see advice about conservative play')
async def should_see_conservative_advice(page: Page):
    recommendations = page.locator('.recommendations-section')
    await expect(recommendations).to_contain_text('conservative')

@when('I have completed a simulation where Stuart has high win percentage')
async def simulation_with_high_win_percentage(page: Page):
    # Configure Stuart with low handicap vs high handicap opponents
    await configure_human_player(page, "Stuart", "2")
    await configure_computer_opponent(page, 1, "Beginner 1", "25", "conservative")
    await configure_computer_opponent(page, 2, "Beginner 2", "20", "conservative")
    await configure_computer_opponent(page, 3, "Beginner 3", "22", "conservative")
    await set_simulation_count(page, "25")
    await click_run_simulation(page)
    await simulation_completes_within_timeout(page, "60")

@then('I should see congratulatory insights')
async def should_see_congratulatory_insights(page: Page):
    insights = page.locator('.insights-section')
    await expect(insights).to_contain_text('performance')

@then('I should see suggestions for more aggressive play')
async def should_see_aggressive_suggestions(page: Page):
    recommendations = page.locator('.recommendations-section')
    await expect(recommendations).to_contain_text('aggressive')

# Consistency test
@given('I have configured identical simulation parameters')
async def configure_identical_parameters(page: Page):
    await valid_simulation_setup(page)
    # Store the configuration for comparison
    page.test_config = {
        "human_name": "Stuart",
        "human_handicap": "10",
        "num_sims": "10"  # Small number for faster testing
    }

@when('I run the same simulation twice')
async def run_simulation_twice(page: Page):
    # First run
    await set_simulation_count(page, page.test_config["num_sims"])
    await click_run_simulation(page)
    await simulation_completes_within_timeout(page, "30")
    
    # Store first results
    stuart_card = page.locator('.player-stat-card.human-player')
    first_win_text = await stuart_card.locator('.stat-row:has(.stat-label:has-text("Wins")) .stat-value').text_content()
    page.first_results = first_win_text
    
    # Reset and run again
    await page.reload()
    await navigate_to_monte_carlo(page)
    await valid_simulation_setup(page)
    await set_simulation_count(page, page.test_config["num_sims"])
    await click_run_simulation(page)
    await simulation_completes_within_timeout(page, "30")

@then('the results should be similar but not identical')
async def results_similar_not_identical(page: Page):
    # Get second results
    stuart_card = page.locator('.player-stat-card.human-player')
    second_win_text = await stuart_card.locator('.stat-row:has(.stat-label:has-text("Wins")) .stat-value').text_content()
    
    # Results should exist but may be different due to randomness
    assert page.first_results is not None, "First results should be stored"
    assert second_win_text is not None, "Second results should exist"
    
    # Both should be valid win percentage formats
    assert '(' in page.first_results and ')' in page.first_results, "First results should have percentage format"
    assert '(' in second_win_text and ')' in second_win_text, "Second results should have percentage format"

@then('both simulations should complete successfully')
async def both_simulations_complete(page: Page):
    # Check that we have results displayed
    results_container = page.locator('.results-container')
    await expect(results_container).to_be_visible()
    
    insights_section = page.locator('.insights-section')
    await expect(insights_section).to_be_visible()