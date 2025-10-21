Feature: Simulation partnership and team formation
  Wolf Goat Pig involves dynamic team formation with partnership requests, solo play, and captain decisions.
  These scenarios validate team-related helpers supported by the seeding DSL.

  Background:
    Given the simulation API is available
    And a simulation is set up with the following players
      | id   | name       | handicap | is_human |
      | p1   | Captain    | 10       | true     |
      | bot1 | Computer 1 | 12       | false    |
      | bot2 | Computer 2 | 14       | false    |
      | bot3 | Computer 3 | 8        | false    |

  Scenario: Partnership formation after tee shots
    Given the simulation is at hole 2
    And the ball positions are
      | player_id | distance_to_pin | lie_type | shot_count |
      | p1        | 175             | fairway  | 1          |
      | bot1      | 160             | fairway  | 1          |
      | bot2      | 195             | rough    | 1          |
      | bot3      | 150             | fairway  | 1          |
    And the team formation is
      | type    | partners         |
      | captain | p1               |
      | team1   | ["p1", "bot1"]   |
      | team2   | ["bot2", "bot3"] |
    When I refresh the simulation state
    Then team 1 contains players p1, bot1
    And team 2 contains players bot2, bot3

  Scenario: Captain goes solo
    Given the simulation is at hole 4
    And the team formation is
      | type        | solo                      |
      | solo_player | p1                        |
      | opponents   | ["bot1", "bot2", "bot3"] |
    When I refresh the simulation state
    And the simulation state contains
      | team_formation.type        | solo |
      | team_formation.solo_player | p1   |

  Scenario: Rotating captain order
    Given the simulation is at hole 5
    And the next player to hit is bot1
    And the team formation is
      | type    | pending |
      | captain | bot1    |
    When I refresh the simulation state
    Then the simulation state contains
      | team_formation.captain | bot1    |
      | team_formation.type    | pending |

  Scenario: Aardvark toss setup in 5-player game
    Given the simulation API is available
    And a simulation is set up with 5 players
    And the simulation is at hole 3
    And the team formation is
      | type    | partners          |
      | captain | p1                |
      | team1   | ["p1", "bot2"]    |
      | team2   | ["bot1", "bot3"]  |
    When I refresh the simulation state

  Scenario: Pending partnership request snapshot
    Given the simulation state is seeded with
      | current_hole               | 8       |
      | next_player_to_hit         | bot2    |
      | team_formation.type        | pending |
      | team_formation.captain     | bot2    |
      | wagering_closed            | false   |
    When I refresh the simulation state
    Then the simulation state contains
      | current_hole               | 8       |
      | team_formation.type        | pending |
      | team_formation.captain     | bot2    |

  Scenario: Team formation affects betting opportunities
    Given the simulation is at hole 6
    And the team formation is
      | type    | partners         |
      | captain | bot3             |
      | team1   | ["bot3", "p1"]   |
      | team2   | ["bot1", "bot2"] |
    And the betting state is
      | base_wager    | 2    |
      | current_wager | 2    |
      | doubled       | false |
    When I request the "GET" "/simulation/state" endpoint
    Then the response code is 200
    And the JSON response contains
      | hole_state.teams.type            | partners |
      | hole_state.betting.current_wager | 2        |

  Scenario: Pending partnership request acceptance
    Given the simulation is at hole 7
    And the ball positions are
      | player_id | distance_to_pin | lie_type | shot_count |
      | p1        | 155             | fairway  | 1          |
      | bot1      | 160             | fairway  | 1          |
      | bot2      | 150             | fairway  | 1          |
      | bot3      | 165             | rough    | 1          |
    And the team formation is
      | type            | pending                                                                |
      | captain         | p1                                                                     |
      | pending_request | {"captain": "p1", "requested": "bot2", "status": "pending"} |
    When I refresh the simulation state
    Then the simulation state contains
      | team_formation.type                       | pending |
      | team_formation.pending_request.status     | pending |
      | team_formation.pending_request.requested  | bot2    |
    When I seed the team formation with
      | type    | partners         |
      | captain | p1               |
      | team1   | ["p1", "bot2"]   |
      | team2   | ["bot1", "bot3"] |
    Then team 1 contains players p1, bot2
    And team 2 contains players bot1, bot3

  Scenario: Pending partnership request decline
    Given the simulation is at hole 9
    And the ball positions are
      | player_id | distance_to_pin | lie_type | shot_count |
      | p1        | 140             | fairway  | 1          |
      | bot1      | 145             | fairway  | 1          |
      | bot2      | 135             | fairway  | 1          |
      | bot3      | 150             | rough    | 1          |
    And the team formation is
      | type            | pending                                                                |
      | captain         | bot1                                                                   |
      | pending_request | {"captain": "bot1", "requested": "bot3", "status": "pending"} |
    When I seed the team formation with
      | type        | solo                      |
      | captain     | bot1                      |
      | solo_player | bot1                      |
      | opponents   | ["p1", "bot2", "bot3"]   |
    Then the simulation state contains
      | team_formation.type        | solo |
      | team_formation.solo_player | bot1 |

  Scenario: Solo captain doubles after wagering closed
    Given the simulation is at hole 11
    And the ball positions are
      | player_id | distance_to_pin | lie_type | shot_count |
      | p1        | 100             | fairway  | 2          |
      | bot1      | 95              | green    | 2          |
      | bot2      | 110             | fairway  | 2          |
      | bot3      | 105             | fairway  | 2          |
    And the team formation is
      | type        | solo                      |
      | captain     | bot2                      |
      | solo_player | bot2                      |
      | opponents   | ["p1", "bot1", "bot3"]   |
    And wagering is set to closed
    And the betting state is
      | current_wager | 2     |
      | doubled       | true  |
    When I refresh the simulation state
    Then the simulation state contains
      | team_formation.type         | solo |
      | team_formation.solo_player  | bot2 |
      | wagering_closed             | true |
      | betting_state.doubled       | true |
      | betting_state.current_wager | 2    |

  Scenario: Complex team transitions across holes
    Given the simulation is at hole 13
    And the team formation is
      | type    | partners         |
      | captain | p1               |
      | team1   | ["p1", "bot3"]   |
      | team2   | ["bot1", "bot2"] |
    When I refresh the simulation state
    Then the teams are formed as partners
    When the simulation is moved to hole 14
    And I seed the team formation with
      | type    | pending |
      | captain | bot1    |
    Then the simulation state contains
      | current_hole            | 14      |
      | team_formation.type     | pending |
      | team_formation.captain  | bot1    |
    When I seed the team formation with
      | type        | solo                      |
      | captain     | bot1                      |
      | solo_player | bot1                      |
      | opponents   | ["p1", "bot2", "bot3"]   |
    Then player "bot1" is going solo

  Scenario: Multiple captains in larger games
    Given the simulation API is available
    And a simulation is set up with 6 players
    And the simulation is at hole 15
    And the team formation is
      | type           | partners                                              |
      | captain        | p1                                                    |
      | second_captain | bot3                                                  |
      | team1          | ["p1", "bot1", "bot2"]                              |
      | team2          | ["bot3", "bot4", "bot5"]                            |
    When I refresh the simulation state
    Then the simulation state contains
      | team_formation.type           | partners |
      | team_formation.captain        | p1       |
      # NOTE: second captain is not currently surfaced by the API

  Scenario: Partnership request with invalid player
    Given the simulation is at hole 10
    When I seed the team formation with
      | type            | pending                                                             |
      | captain         | p1                                                                  |
      | pending_request | {"captain": "p1", "requested": "invalid_player", "status": "pending"} |
    Then the simulation state contains
      | team_formation.type                      | pending        |
      | team_formation.pending_request.requested | invalid_player |

  Scenario: Team formation reset between holes
    Given the simulation is at hole 16
    And the team formation is
      | type    | partners         |
      | captain | bot2             |
      | team1   | ["bot2", "p1"]   |
      | team2   | ["bot1", "bot3"] |
    When the simulation is moved to hole 17
    And I seed the team formation with
      | type    | pending |
      | captain | bot3    |
    Then the simulation state contains
      | current_hole           | 17      |
      | team_formation.type    | pending |
      | team_formation.captain | bot3    |

  Scenario: Captain rotation tracking
    Given the simulation is at hole 18
    And the next player to hit is bot3
    When I seed the team formation with
      | type    | pending |
      | captain | bot3    |
    Then the simulation state contains
      | next_player_to_hit     | bot3    |
      | team_formation.captain | bot3    |
      | team_formation.type    | pending |

  Scenario: Pending request clears when advancing the hole
    Given the simulation is at hole 8
    And the team formation is
      | type            | pending                                                                |
      | captain         | p1                                                                     |
      | pending_request | {"captain": "p1", "requested": "bot2", "status": "pending"} |
    When the simulation is moved to hole 9
    Then the simulation state contains
      | current_hole                  | 9   |
      | team_formation.pending_request | null |

  Scenario: Pending request records unknown player ids
    Given the simulation is at hole 5
    When I seed the team formation with
      | type            | pending                                                                       |
      | captain         | bot1                                                                          |
      | pending_request | {"captain": "bot1", "requested": "ghost_bot", "status": "pending"} |
    Then the simulation state contains
      | team_formation.pending_request.requested | ghost_bot |

  Scenario: Captain rotation preserves wagering state
    Given the simulation is at hole 12
    And the team formation is
      | type    | partners         |
      | captain | p1               |
      | team1   | ["p1", "bot1"]   |
      | team2   | ["bot2", "bot3"] |
    And wagering is set to closed
    When the simulation is moved to hole 13
    And wagering is set to closed
    And I seed the team formation with
      | type    | pending |
      | captain | bot2    |
    Then the simulation state contains
      | current_hole           | 13    |
      | team_formation.captain | bot2  |
      | wagering_closed        | true  |

  Scenario: Duplicate player assignment is reflected in team state
    Given the simulation is at hole 6
    When I seed the team formation with
      | type    | partners                   |
      | captain | p1                         |
      | team1   | ["p1", "bot1"]             |
      | team2   | ["p1", "bot2", "bot3"]     |
    Then the simulation state contains
      | team_formation.team1 | ["p1", "bot1"]         |
      | team_formation.team2 | ["p1", "bot2", "bot3"] |
