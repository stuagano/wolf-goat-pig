Feature: Monte Carlo Simulation for Wolf Goat Pig
  As a golf player wanting to improve my Wolf Goat Pig strategy
  I want to run Monte Carlo simulations
  So that I can understand my long-term performance expectations

  Background:
    Given the Wolf Goat Pig application is running
    And I navigate to the Monte Carlo simulation page

  Scenario: Basic Monte Carlo simulation setup
    Given I am on the Monte Carlo simulation page
    When I configure the human player as "Stuart" with handicap "10"
    And I configure computer opponent 1 as "Tiger Bot" with handicap "2.0" and "aggressive" personality
    And I configure computer opponent 2 as "Strategic Sam" with handicap "8.5" and "strategic" personality  
    And I configure computer opponent 3 as "Conservative Carl" with handicap "15.0" and "conservative" personality
    And I set the number of simulations to "25"
    Then the simulation setup should be valid
    And the "Run Monte Carlo Simulation" button should be enabled

  Scenario: Running a small Monte Carlo simulation
    Given I have configured a valid simulation setup
    When I click the "Run Monte Carlo Simulation" button
    Then I should see a loading indicator
    And the simulation should complete within "30" seconds
    And I should see the simulation results

  Scenario: Validating simulation results
    Given I have completed a Monte Carlo simulation with "25" games
    Then I should see win percentages for all 4 players
    And the win percentages should add up to approximately 100%
    And I should see average scores for all players
    And I should see key insights about Stuart's performance
    And I should see strategic recommendations

  Scenario: Simulation results analysis
    Given I have completed a Monte Carlo simulation
    Then I should see Stuart's win percentage
    And I should see Stuart's average score per game
    And I should see Stuart's best and worst game scores
    And I should see score distribution for Stuart
    And the human player card should be visually highlighted

  Scenario: Error handling for invalid configurations
    Given I am on the Monte Carlo simulation page
    When I set the number of simulations to "0"
    And I click the "Run Monte Carlo Simulation" button
    Then I should see an error message
    And the simulation should not run

  Scenario: Error handling for missing opponent configurations
    Given I am on the Monte Carlo simulation page
    When I clear the name field for computer opponent 1
    And I click the "Run Monte Carlo Simulation" button
    Then I should see an error message
    And the simulation should not run

  Scenario: Large simulation performance test
    Given I have configured a valid simulation setup
    When I set the number of simulations to "100"
    And I click the "Run Monte Carlo Simulation" button
    Then the simulation should complete within "120" seconds
    And I should see results for 100 games

  Scenario: Handicap impact analysis
    Given I have configured Stuart with handicap "5"
    And I have configured three computer opponents with handicaps "15", "20", and "25"
    When I run a simulation with "50" games
    Then Stuart should have a win percentage greater than "40%"
    And Stuart's average score should be positive

  Scenario: Navigation and UI interaction
    Given I am on the Monte Carlo simulation page
    Then I should see the page title "Monte Carlo Simulation"
    And I should see the description explaining Monte Carlo functionality
    And I should see configuration sections for human player and computer opponents
    And I should see simulation parameters section
    When I navigate away and back to the Monte Carlo page
    Then the form should be reset to default values

  Scenario: Responsive design validation
    Given I am on the Monte Carlo simulation page
    When I resize the browser to mobile dimensions
    Then the layout should adapt to mobile view
    And all form elements should remain accessible
    And the results display should be mobile-friendly

  Scenario: Strategic recommendations validation
    Given I have completed a simulation where Stuart has low win percentage
    Then I should see recommendations about partnership selection
    And I should see advice about conservative play
    When I have completed a simulation where Stuart has high win percentage
    Then I should see congratulatory insights
    And I should see suggestions for more aggressive play

  Scenario: Simulation consistency test
    Given I have configured identical simulation parameters
    When I run the same simulation twice
    Then the results should be similar but not identical
    And both simulations should complete successfully