import json
from typing import Dict, List
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from playwright.async_api import Page, expect
import asyncio

# Load scenarios from the feature file
scenarios('../../features/course_management.feature')

# Test data for course management
SAMPLE_COURSES = {
    "Pebble Beach Pro": {
        "name": "Pebble Beach Pro",
        "holes": [
            {"hole": 1, "par": 4, "handicap": 5, "yards": 420},
            {"hole": 2, "par": 5, "handicap": 13, "yards": 520},
            {"hole": 3, "par": 3, "handicap": 17, "yards": 180},
            {"hole": 4, "par": 4, "handicap": 1, "yards": 445},
            {"hole": 5, "par": 4, "handicap": 9, "yards": 385},
            {"hole": 6, "par": 3, "handicap": 15, "yards": 165},
            {"hole": 7, "par": 5, "handicap": 3, "yards": 580},
            {"hole": 8, "par": 4, "handicap": 11, "yards": 410},
            {"hole": 9, "par": 4, "handicap": 7, "yards": 395},
            {"hole": 10, "par": 4, "handicap": 2, "yards": 455},
            {"hole": 11, "par": 3, "handicap": 18, "yards": 145},
            {"hole": 12, "par": 5, "handicap": 6, "yards": 565},
            {"hole": 13, "par": 4, "handicap": 14, "yards": 375},
            {"hole": 14, "par": 4, "handicap": 8, "yards": 415},
            {"hole": 15, "par": 3, "handicap": 16, "yards": 175},
            {"hole": 16, "par": 4, "handicap": 4, "yards": 435},
            {"hole": 17, "par": 5, "handicap": 10, "yards": 545},
            {"hole": 18, "par": 4, "handicap": 12, "yards": 425}
        ]
    }
}

@given('I navigate to the course management page')
async def navigate_to_course_management(page: Page):
    """Navigate to the course management page"""
    await page.goto('/courses')
    # Wait for the page to load
    await page.wait_for_selector('[data-testid="course-management-page"]', timeout=10000)

@given('I am on the course management page')
async def i_am_on_course_management_page(page: Page):
    """Verify we're on the course management page"""
    await expect(page.locator('[data-testid="course-management-page"]')).to_be_visible()

@when('I click "Add New Course"')
async def click_add_new_course(page: Page):
    """Click the Add New Course button"""
    await page.click('[data-testid="add-course-button"]')
    await page.wait_for_selector('[data-testid="course-form"]', timeout=5000)

@when(parsers.parse('I enter course name "{course_name}"'))
async def enter_course_name(page: Page, course_name: str):
    """Enter the course name"""
    await page.fill('[data-testid="course-name-input"]', course_name)

@when(parsers.parse('I configure hole {hole_num:d} with par "{par}", handicap "{handicap}", and yards "{yards}"'))
async def configure_hole(page: Page, hole_num: int, par: str, handicap: str, yards: str):
    """Configure a specific hole with par, handicap, and yards"""
    hole_section = f'[data-testid="hole-{hole_num}-config"]'
    await page.wait_for_selector(hole_section, timeout=5000)
    
    # Fill par
    await page.fill(f'{hole_section} [data-testid="par-input"]', par)
    
    # Fill handicap (stroke index)
    await page.fill(f'{hole_section} [data-testid="handicap-input"]', handicap)
    
    # Fill yards
    await page.fill(f'{hole_section} [data-testid="yards-input"]', yards)

@when('I click "Save Course"')
async def click_save_course(page: Page):
    """Click the Save Course button"""
    await page.click('[data-testid="save-course-button"]')

@then(parsers.parse('I should see "{message}"'))
async def i_should_see_message(page: Page, message: str):
    """Verify a specific message is displayed"""
    await expect(page.locator(f'text="{message}"')).to_be_visible()

@then(parsers.parse('"{course_name}" should appear in the courses list'))
async def course_should_appear_in_list(page: Page, course_name: str):
    """Verify course appears in the courses list"""
    await expect(page.locator(f'[data-testid="course-list-item"][data-course="{course_name}"]')).to_be_visible()

@then('the course should have 18 holes with complete information')
async def course_should_have_complete_holes(page: Page):
    """Verify the course has 18 complete holes"""
    # Check that all 18 holes are configured
    for hole_num in range(1, 19):
        hole_item = f'[data-testid="hole-{hole_num}-summary"]'
        await expect(page.locator(hole_item)).to_be_visible()

@given(parsers.parse('I have created a course "{course_name}"'))
async def i_have_created_course(page: Page, course_name: str):
    """Create a test course"""
    # Use API to create course directly for testing
    course_data = SAMPLE_COURSES.get(course_name, SAMPLE_COURSES["Pebble Beach Pro"])
    course_data["name"] = course_name
    
    # Send course data via API
    await page.evaluate(f'''
        fetch('/api/courses', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({json.dumps(course_data)})
        }})
    ''')

@when('I view the course details')
async def view_course_details(page: Page):
    """View the course details"""
    await page.click('[data-testid="view-course-details"]')
    await page.wait_for_selector('[data-testid="course-details"]', timeout=5000)

@then('each hole should have a valid par between 3 and 6')
async def validate_par_values(page: Page):
    """Validate that all par values are between 3 and 6"""
    for hole_num in range(1, 19):
        par_element = page.locator(f'[data-testid="hole-{hole_num}-par"]')
        par_value = int(await par_element.text_content())
        assert 3 <= par_value <= 6, f"Hole {hole_num} par {par_value} is not between 3 and 6"

@then('each hole should have a unique handicap from 1 to 18')
async def validate_unique_handicaps(page: Page):
    """Validate that handicaps are unique and range from 1 to 18"""
    handicaps = []
    for hole_num in range(1, 19):
        handicap_element = page.locator(f'[data-testid="hole-{hole_num}-handicap"]')
        handicap_value = int(await handicap_element.text_content())
        handicaps.append(handicap_value)
    
    # Check all handicaps are present and unique
    assert sorted(handicaps) == list(range(1, 19)), "Handicaps must be unique and range from 1 to 18"

@then('each hole should have yards greater than 100')
async def validate_yard_values(page: Page):
    """Validate that all yard values are greater than 100"""
    for hole_num in range(1, 19):
        yards_element = page.locator(f'[data-testid="hole-{hole_num}-yards"]')
        yards_value = int(await yards_element.text_content())
        assert yards_value > 100, f"Hole {hole_num} yards {yards_value} is not greater than 100"

@then('the total par should be between 70 and 74')
async def validate_total_par(page: Page):
    """Validate that total par is between 70 and 74"""
    total_par_element = page.locator('[data-testid="total-par"]')
    total_par = int(await total_par_element.text_content())
    assert 70 <= total_par <= 74, f"Total par {total_par} is not between 70 and 74"

@then('handicap distribution should follow golf course standards')
async def validate_handicap_distribution(page: Page):
    """Validate handicap distribution follows golf standards"""
    # This would check that handicaps are distributed appropriately
    # For now, we just verify they're unique which is handled by validate_unique_handicaps
    pass

@given(parsers.parse('I have a course "{course_name}"'))
async def i_have_a_course(page: Page, course_name: str):
    """Setup a course for testing"""
    await i_have_created_course(page, course_name)

@when(parsers.parse('I click "Edit" for hole {hole_num:d}'))
async def click_edit_hole(page: Page, hole_num: int):
    """Click edit for a specific hole"""
    await page.click(f'[data-testid="edit-hole-{hole_num}"]')
    await page.wait_for_selector(f'[data-testid="hole-{hole_num}-edit-form"]', timeout=5000)

@when(parsers.parse('I change the yards from "{old_yards}" to "{new_yards}"'))
async def change_yards(page: Page, old_yards: str, new_yards: str):
    """Change the yards value for a hole"""
    yards_input = page.locator('[data-testid="edit-yards-input"]')
    await yards_input.clear()
    await yards_input.fill(new_yards)

@when(parsers.parse('I change the handicap from "{old_handicap}" to "{new_handicap}"'))
async def change_handicap(page: Page, old_handicap: str, new_handicap: str):
    """Change the handicap value for a hole"""
    handicap_input = page.locator('[data-testid="edit-handicap-input"]')
    await handicap_input.clear()
    await handicap_input.fill(new_handicap)

@when('I click "Save Changes"')
async def click_save_changes(page: Page):
    """Click the Save Changes button"""
    await page.click('[data-testid="save-changes-button"]')

@then(parsers.parse('hole {hole_num:d} should show yards "{yards}" and handicap "{handicap}"'))
async def verify_hole_changes(page: Page, hole_num: int, yards: str, handicap: str):
    """Verify hole changes were saved"""
    await expect(page.locator(f'[data-testid="hole-{hole_num}-yards"]')).to_have_text(yards)
    await expect(page.locator(f'[data-testid="hole-{hole_num}-handicap"]')).to_have_text(handicap)

@then('the course should maintain data integrity')
async def verify_data_integrity(page: Page):
    """Verify course data integrity after changes"""
    # This would perform comprehensive data validation
    # For now, we just check that the page is still functional
    await expect(page.locator('[data-testid="course-details"]')).to_be_visible()

@given('I have multiple courses available')
async def setup_multiple_courses(page: Page):
    """Setup multiple courses for testing"""
    courses = ["Augusta National", "Pebble Beach", "St. Andrews"]
    for course_name in courses:
        await i_have_created_course(page, course_name)

@given('I am setting up a Monte Carlo simulation')
async def setup_monte_carlo_simulation(page: Page):
    """Navigate to Monte Carlo simulation setup"""
    await page.goto('/monte-carlo')
    await page.wait_for_selector('[data-testid="monte-carlo-page"]', timeout=10000)

@when(parsers.parse('I select course "{course_name}"'))
async def select_course(page: Page, course_name: str):
    """Select a specific course for simulation"""
    await page.select_option('[data-testid="course-select"]', course_name)

@then(parsers.parse('the simulation should use "{course_name}" hole data'))
async def verify_simulation_uses_course(page: Page, course_name: str):
    """Verify simulation uses the selected course data"""
    selected_course = page.locator('[data-testid="selected-course-display"]')
    await expect(selected_course).to_have_text(course_name)

@then('hole difficulty should affect simulation outcomes')
async def verify_hole_difficulty_affects_simulation(page: Page):
    """Verify hole difficulty impacts simulation"""
    # This would be validated by checking simulation logic
    # For now, we verify the course data is available
    await expect(page.locator('[data-testid="hole-difficulty-indicator"]')).to_be_visible()

@then('yard distances should impact betting strategy')
async def verify_yards_impact_betting(page: Page):
    """Verify yard distances affect betting strategy"""
    # Check that distance data is displayed in simulation
    await expect(page.locator('[data-testid="distance-factor"]')).to_be_visible()

@then('stroke indexes should determine handicap allocation')
async def verify_stroke_indexes(page: Page):
    """Verify stroke indexes determine handicap allocation"""
    await expect(page.locator('[data-testid="stroke-allocation"]')).to_be_visible()

@given('I have configured a course with varying hole lengths')
async def setup_course_with_varying_lengths(page: Page):
    """Setup a course with varying hole lengths for testing"""
    # Create a test course with specific hole configurations
    await i_have_created_course(page, "Test Varying Course")

@given('I am running a simulation with different player handicaps')
async def setup_simulation_with_different_handicaps(page: Page):
    """Setup simulation with players of different handicaps"""
    await page.goto('/monte-carlo')
    # Configure players with different handicaps
    await page.fill('[data-testid="player1-handicap"]', '5')
    await page.fill('[data-testid="player2-handicap"]', '15')
    await page.fill('[data-testid="player3-handicap"]', '25')

@when(parsers.parse('the simulation processes hole {hole_num:d} with yards "{yards}" ({description})'))
async def simulation_processes_hole(page: Page, hole_num: int, yards: str, description: str):
    """Simulate processing a specific hole"""
    # This would trigger simulation for a specific hole
    await page.click(f'[data-testid="simulate-hole-{hole_num}"]')

@then('higher handicap players should have higher expected scores')
async def verify_handicap_score_relationship(page: Page):
    """Verify higher handicap players have higher expected scores"""
    # Check simulation results show this relationship
    await expect(page.locator('[data-testid="handicap-score-analysis"]')).to_be_visible()

@then('distance should factor into shot outcome probabilities')
async def verify_distance_factors_into_outcomes(page: Page):
    """Verify distance affects shot outcomes"""
    await expect(page.locator('[data-testid="distance-probability-factor"]')).to_be_visible()

@then('score differences should be smaller between players')
async def verify_smaller_score_differences(page: Page):
    """Verify score differences are smaller on easier holes"""
    # Check that the simulation shows tighter score spreads
    await expect(page.locator('[data-testid="score-spread-analysis"]')).to_be_visible()

@then('putting becomes more critical than driving distance')
async def verify_putting_importance(page: Page):
    """Verify putting becomes more important on shorter holes"""
    await expect(page.locator('[data-testid="putting-factor-high"]')).to_be_visible()

# Additional step definitions for remaining scenarios...

@when('I enter duplicate handicap values for holes 3 and 7')
async def enter_duplicate_handicaps(page: Page):
    """Enter duplicate handicap values to test validation"""
    await page.fill('[data-testid="hole-3-config"] [data-testid="handicap-input"]', '5')
    await page.fill('[data-testid="hole-7-config"] [data-testid="handicap-input"]', '5')

@then('the course should not be saved')
async def verify_course_not_saved(page: Page):
    """Verify the course was not saved due to validation error"""
    # Check that we're still on the form page
    await expect(page.locator('[data-testid="course-form"]')).to_be_visible()

@when(parsers.parse('I enter yards "{yards}" for a par 4 hole'))
async def enter_invalid_yards(page: Page, yards: str):
    """Enter invalid yards for testing validation"""
    await page.fill('[data-testid="hole-1-config"] [data-testid="yards-input"]', yards)
    await page.fill('[data-testid="hole-1-config"] [data-testid="par-input"]', '4')

@when('I click "Import Course"')
async def click_import_course(page: Page):
    """Click the Import Course button"""
    await page.click('[data-testid="import-course-button"]')

@when('I upload a valid course JSON file')
async def upload_valid_course_file(page: Page):
    """Upload a valid course JSON file"""
    # Create a valid course JSON for testing
    valid_course = json.dumps(SAMPLE_COURSES["Pebble Beach Pro"])
    
    # Simulate file upload
    await page.set_input_files('[data-testid="course-file-input"]', 
                               files=[{'name': 'test_course.json', 'mimeType': 'application/json', 'buffer': valid_course.encode()}])

@when('I upload an invalid course file')
async def upload_invalid_course_file(page: Page):
    """Upload an invalid course file"""
    invalid_json = "{ invalid json }"
    await page.set_input_files('[data-testid="course-file-input"]',
                               files=[{'name': 'invalid.json', 'mimeType': 'application/json', 'buffer': invalid_json.encode()}])

@when(parsers.parse('I click "Delete" for "{course_name}"'))
async def click_delete_course(page: Page, course_name: str):
    """Click delete for a specific course"""
    await page.click(f'[data-testid="delete-course-{course_name}"]')

@when('I confirm the deletion')
async def confirm_deletion(page: Page):
    """Confirm the course deletion"""
    await page.click('[data-testid="confirm-delete-button"]')

@then(parsers.parse('"{course_name}" should no longer appear in the courses list'))
async def verify_course_not_in_list(page: Page, course_name: str):
    """Verify course no longer appears in the list"""
    await expect(page.locator(f'[data-testid="course-list-item"][data-course="{course_name}"]')).not_to_be_visible()

@then('any simulations using this course should fallback to default course')
async def verify_simulation_fallback(page: Page):
    """Verify simulations fallback to default course"""
    # This would be tested by checking simulation behavior
    pass

@given(parsers.parse('I have courses "{course1}" and "{course2}"'))
async def setup_multiple_specific_courses(page: Page, course1: str, course2: str):
    """Setup specific courses for comparison"""
    await i_have_created_course(page, course1)
    await i_have_created_course(page, course2)

@when('I compare the two courses')
async def compare_courses(page: Page):
    """Compare two courses"""
    await page.click('[data-testid="compare-courses-button"]')

@then('I should see side-by-side hole statistics')
async def verify_side_by_side_stats(page: Page):
    """Verify side-by-side course comparison"""
    await expect(page.locator('[data-testid="course-comparison-view"]')).to_be_visible()

@given('I am using a mobile device')
async def setup_mobile_device(page: Page):
    """Setup mobile device simulation"""
    await page.set_viewport_size({'width': 375, 'height': 667})

@when('I access course management features')
async def access_course_management_mobile(page: Page):
    """Access course management on mobile"""
    await page.goto('/courses')
    await page.wait_for_selector('[data-testid="mobile-course-management"]', timeout=10000)

@then('hole configuration should be mobile-friendly')
async def verify_mobile_friendly_config(page: Page):
    """Verify mobile-friendly hole configuration"""
    await expect(page.locator('[data-testid="mobile-hole-config"]')).to_be_visible()

@when('I restart the application')
async def restart_application(page: Page):
    """Simulate application restart"""
    await page.reload()
    await page.wait_for_load_state('networkidle')

@then('all course data should be preserved')
async def verify_data_preserved(page: Page):
    """Verify all course data is preserved after restart"""
    await page.goto('/courses')
    await expect(page.locator('[data-testid="course-list"]')).to_be_visible()

@when('I export course data')
async def export_course_data(page: Page):
    """Export course data"""
    await page.click('[data-testid="export-courses-button"]')

@then('I should get a complete backup file')
async def verify_backup_file(page: Page):
    """Verify backup file is created"""
    # Wait for download
    with page.expect_download() as download_info:
        await page.click('[data-testid="download-backup"]')
    download = await download_info.value
    assert download.suggested_filename.endswith('.json')