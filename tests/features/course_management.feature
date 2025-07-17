Feature: Course Management for Wolf Goat Pig
  As a golf player using Wolf Goat Pig simulation
  I want to manage golf courses with detailed hole information
  So that I can get accurate simulation results based on hole difficulty and distance

  Background:
    Given the Wolf Goat Pig application is running
    And I navigate to the course management page

  Scenario: Creating a new course with complete hole information
    Given I am on the course management page
    When I click "Add New Course"
    And I enter course name "Pebble Beach Pro"
    And I configure hole 1 with par "4", handicap "5", and yards "420"
    And I configure hole 2 with par "5", handicap "13", and yards "520"
    And I configure hole 3 with par "3", handicap "17", and yards "180"
    And I configure hole 4 with par "4", handicap "1", and yards "445"
    And I configure hole 5 with par "4", handicap "9", and yards "385"
    And I configure hole 6 with par "3", handicap "15", and yards "165"
    And I configure hole 7 with par "5", handicap "3", and yards "580"
    And I configure hole 8 with par "4", handicap "11", and yards "410"
    And I configure hole 9 with par "4", handicap "7", and yards "395"
    And I configure hole 10 with par "4", handicap "2", and yards "455"
    And I configure hole 11 with par "3", handicap "18", and yards "145"
    And I configure hole 12 with par "5", handicap "6", and yards "565"
    And I configure hole 13 with par "4", handicap "14", and yards "375"
    And I configure hole 14 with par "4", handicap "8", and yards "415"
    And I configure hole 15 with par "3", handicap "16", and yards "175"
    And I configure hole 16 with par "4", handicap "4", and yards "435"
    And I configure hole 17 with par "5", handicap "10", and yards "545"
    And I configure hole 18 with par "4", handicap "12", and yards "425"
    And I click "Save Course"
    Then I should see "Course created successfully"
    And "Pebble Beach Pro" should appear in the courses list
    And the course should have 18 holes with complete information

  Scenario: Validating course data integrity
    Given I have created a course "Test Valley Links"
    When I view the course details
    Then each hole should have a valid par between 3 and 6
    And each hole should have a unique handicap from 1 to 18
    And each hole should have yards greater than 100
    And the total par should be between 70 and 74
    And handicap distribution should follow golf course standards

  Scenario: Editing existing course hole information
    Given I have a course "Mountain View Golf Club"
    When I click "Edit" for hole 7
    And I change the yards from "520" to "540"
    And I change the handicap from "3" to "5"
    And I click "Save Changes"
    Then hole 7 should show yards "540" and handicap "5"
    And the course should maintain data integrity
    And I should see "Hole updated successfully"

  Scenario: Course selection for simulation mode
    Given I have multiple courses available
    And I am setting up a Monte Carlo simulation
    When I select course "Augusta National"
    Then the simulation should use "Augusta National" hole data
    And hole difficulty should affect simulation outcomes
    And yard distances should impact betting strategy
    And stroke indexes should determine handicap allocation

  Scenario: Distance-based betting simulation
    Given I have configured a course with varying hole lengths
    And I am running a simulation with different player handicaps
    When the simulation processes hole 1 with yards "450" (long par 4)
    Then higher handicap players should have higher expected scores
    And distance should factor into shot outcome probabilities
    When the simulation processes hole 11 with yards "140" (short par 3)
    Then score differences should be smaller between players
    And putting becomes more critical than driving distance

  Scenario: Handicap stroke allocation based on hole difficulty
    Given I have a course with proper stroke indexes
    And I have players with handicaps "5", "10", "15", and "20"
    When I view stroke allocation for hole with handicap "1" (hardest)
    Then players with handicap 15 and 20 should receive strokes
    And players with handicap 5 and 10 should receive no strokes
    When I view stroke allocation for hole with handicap "18" (easiest)
    Then only the 20 handicap player should receive a stroke
    And stroke allocation should follow standard golf rules

  Scenario: Course difficulty analysis for betting
    Given I have a course with mixed hole lengths and difficulties
    When I analyze the course for simulation purposes
    Then I should see average hole difficulty rating
    And I should see breakdown by par 3, par 4, and par 5 holes
    And I should see total yardage and course rating
    And difficult holes should show higher expected score spreads
    And easier holes should show tighter score clustering

  Scenario: Error handling for invalid course data
    Given I am creating a new course
    When I enter duplicate handicap values for holes 3 and 7
    And I click "Save Course"
    Then I should see "Error: Duplicate handicap values not allowed"
    And the course should not be saved
    When I enter yards "50" for a par 4 hole
    Then I should see "Error: Yard distance too short for par value"

  Scenario: Importing course data from external source
    Given I am on the course management page
    When I click "Import Course"
    And I upload a valid course JSON file
    Then the course should be imported with all hole data
    And I should see "Course imported successfully"
    And all holes should have par, handicap, and yards
    When I upload an invalid course file
    Then I should see "Error: Invalid course data format"

  Scenario: Course deletion and data cleanup
    Given I have a course "Old Municipal Course"
    When I click "Delete" for "Old Municipal Course"
    And I confirm the deletion
    Then "Old Municipal Course" should no longer appear in the courses list
    And any simulations using this course should fallback to default course
    And I should see "Course deleted successfully"

  Scenario: Course comparison for strategy planning
    Given I have courses "Easy Valley" and "Championship Links"
    When I compare the two courses
    Then I should see side-by-side hole statistics
    And I should see difficulty differences highlighted
    And I should see which course favors which handicap ranges
    And betting strategy recommendations should differ between courses

  Scenario: Mobile course management
    Given I am using a mobile device
    When I access course management features
    Then hole configuration should be mobile-friendly
    And I should be able to swipe between holes
    And data entry should work with mobile keyboards
    And course lists should scroll smoothly

  Scenario: Course data persistence and backup
    Given I have created multiple courses with detailed hole data
    When I restart the application
    Then all course data should be preserved
    And hole yards, handicaps, and pars should remain correct
    When I export course data
    Then I should get a complete backup file
    And the backup should include all course metadata