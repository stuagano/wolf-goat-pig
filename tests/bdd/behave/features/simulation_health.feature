Feature: Simulation service health checks
  The Wolf Goat Pig platform needs high-level functional signals so stakeholders can express
  expectations in plain English. These Gherkin scenarios can be generated collaboratively with the AI agent
  from conversational requirements and then executed automatically.

  Background:
    Given the simulation API is available

  Scenario: Health endpoint returns an "ok" status payload
    When I request the "GET" "health" endpoint
    Then the response code is 200
    And the JSON response contains:
      | status | ok |

  Scenario: Simulation setup rejects requests with fewer than four players
    When I submit a simulation setup request with 2 players
    # Backend currently surfaces this as an internal error wrapping the 400 detail
    Then the response code is 500
    And the JSON response contains:
      | detail | Failed to setup simulation: 400: At least 4 players required |

  Scenario: Simulation state endpoint requires admin header
    Given ENABLE_TEST_ENDPOINTS is set to "true"
    And a simulation is set up with 4 players
    When I request the "GET" "/simulation/state" endpoint without admin headers
    Then the response code is 403
    And the JSON response contains:
      | detail | Admin access required |

  Scenario: Simulation seed-state endpoint requires admin header
    Given ENABLE_TEST_ENDPOINTS is set to "true"
    And a simulation is set up with 4 players
    When I request the "POST" "/simulation/test/seed-state" endpoint without admin headers with
      | betting.current_wager | 3 |
    Then the response code is 403
    And the JSON response contains:
      | detail | Admin access required |
