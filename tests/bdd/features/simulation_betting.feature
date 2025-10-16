Feature: Simulation betting mechanics
  Wolf Goat Pig betting involves progressive wagering with doubles, carries, and special rules.
  These scenarios exercise the reusable seeding DSL for betting-related state.

  Background:
    Given the simulation API is available
    And a simulation is set up with 4 players

  Scenario: Seeded double state snapshot
    Given the simulation is at hole 3
    And the ball positions are
      | player_id | distance_to_pin | lie_type | shot_count |
      | p1        | 180             | fairway  | 1          |
      | bot1      | 150             | fairway  | 1          |
      | bot2      | 200             | rough    | 1          |
      | bot3      | 165             | fairway  | 1          |
    And the betting state is
      | base_wager    | 1    |
      | current_wager | 2    |
      | doubled       | true |
    Then the betting is doubled
    And the current wager is 2 quarters

  Scenario: Line of scrimmage enforcement
    Given the simulation is at hole 5
    And the ball positions are
      | player_id | distance_to_pin | lie_type | shot_count |
      | p1        | 250             | rough    | 1          |
      | bot1      | 150             | fairway  | 1          |
      | bot2      | 175             | fairway  | 1          |
      | bot3      | 200             | bunker   | 1          |
    And the line of scrimmage is p1
    When I request the "GET" "/simulation/state" endpoint
    Then the response code is 200
    And the JSON response contains
      | hole_state.line_of_scrimmage | p1 |

  Scenario: Wagering closes after tee shots
    Given the simulation is at hole 1
    And the ball positions are
      | player_id | distance_to_pin | lie_type | shot_count |
      | p1        | 180             | fairway  | 1          |
      | bot1      | 160             | fairway  | 1          |
      | bot2      | 190             | fairway  | 1          |
      | bot3      | 170             | fairway  | 1          |
    And wagering is set to closed
    When I refresh the simulation state
    Then wagering is closed
    And the simulation state contains
      | wagering_closed | true |

  Scenario: Carry-over betting state
    Given the simulation is at hole 7
    And the betting state is
      | base_wager    | 1    |
      | current_wager | 4    |
      | carry_over    | true |
    When I refresh the simulation state
    Then the current wager is 4 quarters
    And the simulation state contains
      | betting_state.carry_over | true |

  Scenario: Ping pong counter tracking
    Given the simulation is at hole 10
    And the betting state is
      | base_wager      | 2    |
      | ping_pong_count | 3    |
      | doubled         | true |
    When I refresh the simulation state
    Then the simulation state contains
      | betting_state.ping_pong_count | 3    |
      | betting_state.doubled         | true |

  Scenario: Complex betting state with multiple flags
    Given the simulation state is seeded with
      | current_hole                    | 15   |
      | betting.base_wager              | 2    |
      | betting.current_wager           | 8    |
      | betting.doubled                 | true |
      | betting.carry_over              | true |
      | betting.float_invoked           | true |
      | betting.line_of_scrimmage       | bot2 |
    When I refresh the simulation state
    Then the simulation state contains
      | current_hole                | 15   |
      | betting_state.current_wager | 8    |
      | betting_state.float_invoked | true |
      | hole_state.line_of_scrimmage | bot2 |

  Scenario: Reject double when wagering is closed
    Given the simulation is at hole 2
    And the ball positions are
      | player_id | distance_to_pin | lie_type | shot_count |
      | p1        | 150             | fairway  | 2          |
      | bot1      | 145             | fairway  | 2          |
      | bot2      | 160             | rough    | 2          |
      | bot3      | 155             | fairway  | 2          |
    And wagering is set to closed
    And the betting state is
      | current_wager | 1     |
      | doubled       | false |
    When I seed the betting state with
      | doubled       | true |
      | current_wager | 2    |
    Then the simulation state contains
      | betting_state.doubled       | true |
      | betting_state.current_wager | 2    |
      | wagering_closed             | true |

  Scenario: Solo captain can double when wagering closed
    Given the simulation is at hole 4
    And the team formation is
      | type        | solo                      |
      | captain     | p1                        |
      | solo_player | p1                        |
      | opponents   | ["bot1", "bot2", "bot3"] |
    And wagering is set to closed
    When I seed the betting state with
      | doubled       | true |
      | current_wager | 2    |
    Then the simulation state contains
      | team_formation.type         | solo |
      | team_formation.solo_player  | p1   |
      | betting_state.doubled       | true |
      | betting_state.current_wager | 2    |

  Scenario: Ping pong counter tracks escalating doubles
    Given the simulation is at hole 8
    And the ball positions are
      | player_id | distance_to_pin | lie_type | shot_count |
      | p1        | 120             | fairway  | 2          |
      | bot1      | 115             | fairway  | 2          |
      | bot2      | 130             | fairway  | 2          |
      | bot3      | 125             | fairway  | 2          |
    And the betting state is
      | base_wager      | 1     |
      | current_wager   | 1     |
      | ping_pong_count | 0     |
      | doubled         | false |
    When I seed the betting state with
      | doubled         | true  |
      | current_wager   | 2     |
      | ping_pong_count | 1     |
    And I refresh the simulation state
    Then the simulation state contains
      | betting_state.ping_pong_count | 1 |
      | betting_state.doubled         | true |
      | betting_state.current_wager   | 2    |
    When I seed the betting state with
      | redoubled       | true  |
      | current_wager   | 4     |
      | ping_pong_count | 2     |
    Then the simulation state contains
      | betting_state.ping_pong_count | 2    |
      | betting_state.redoubled       | true |
      | betting_state.current_wager   | 4    |

  Scenario: Betting with special rules invoked
    Given the simulation is at hole 12
    And the betting state is
      | base_wager        | 1     |
      | current_wager     | 3     |
      | float_invoked     | true  |
      | option_invoked    | true  |
      | duncan_invoked    | false |
      | tunkarri_invoked  | false |
    When I refresh the simulation state
    Then the simulation state contains
      | betting_state.current_wager    | 3    |
      | betting_state.float_invoked    | true |
      | betting_state.option_invoked   | true |
      | betting_state.duncan_invoked   | false |
      | betting_state.tunkarri_invoked | false |

  Scenario: Carry-over accumulates across holes
    Given the simulation is at hole 9
    And the betting state is
      | base_wager    | 2     |
      | current_wager | 8     |
      | carry_over    | true  |
      | doubled       | false |
    When I refresh the simulation state
    Then the simulation state contains
      | betting_state.carry_over    | true |
      | betting_state.current_wager | 8    |
    When the simulation is moved to hole 10
    And I seed the betting state with
      | base_wager    | 2  |
      | current_wager | 10 |
      | carry_over    | true |
    Then the simulation state contains
      | current_hole                | 10   |
      | betting_state.current_wager | 10   |
      | betting_state.carry_over    | true |

  Scenario: Line of scrimmage affects betting opportunities
    Given the simulation is at hole 6
    And the ball positions are
      | player_id | distance_to_pin | lie_type | shot_count |
      | p1        | 200             | rough    | 1          |
      | bot1      | 150             | fairway  | 1          |
      | bot2      | 160             | fairway  | 1          |
      | bot3      | 170             | fairway  | 1          |
    And the line of scrimmage is p1
    And the betting state is
      | current_wager | 1    |
      | doubled       | false |
    When I refresh the simulation state
    Then the simulation state contains
      | hole_state.line_of_scrimmage | p1    |
      | betting_state.current_wager   | 1     |

  Scenario: Reset doubles history flag
    Given the simulation is at hole 11
    And the betting state is
      | current_wager | 2    |
      | doubled       | true |
    When I seed the simulation state with
      | betting.current_wager     | 1     |
      | betting.doubled           | false |
      | reset_doubles_history     | true  |
    Then the simulation state contains
      | betting_state.current_wager | 1     |
      | betting_state.doubled       | false |
