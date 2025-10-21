Feature: Simulation integration flows
  Full round scenarios ensure the backend, betting, and partnership helpers stay in sync across holes.

  Background:
    Given the simulation API is available
    And a simulation is set up with 4 players

  Scenario: Full round progression retains betting and captain state
    When I progress through the following holes
      | hole | team_type | captain | current_wager | wagering_closed |
      | 1    | partners  | p1      | 1             | false           |
      | 2    | partners  | bot1    | 1             | false           |
      | 3    | partners  | bot2    | 2             | false           |
      | 4    | solo      | bot3    | 2             | true            |
      | 5    | partners  | p1      | 3             | false           |
      | 6    | partners  | bot1    | 3             | false           |
      | 7    | partners  | bot2    | 3             | false           |
      | 8    | partners  | bot3    | 4             | false           |
      | 9    | partners  | p1      | 4             | true            |
      | 10   | partners  | bot1    | 1             | false           |
      | 11   | partners  | bot2    | 1             | false           |
      | 12   | partners  | bot3    | 2             | false           |
      | 13   | partners  | p1      | 2             | false           |
      | 14   | partners  | bot1    | 2             | false           |
      | 15   | partners  | bot2    | 3             | false           |
      | 16   | partners  | bot3    | 3             | false           |
      | 17   | partners  | p1      | 3             | false           |
      | 18   | solo      | p1      | 4             | true            |
    Then the hole progression is
      | hole |
      | 1    |
      | 2    |
      | 3    |
      | 4    |
      | 5    |
      | 6    |
      | 7    |
      | 8    |
      | 9    |
      | 10   |
      | 11   |
      | 12   |
      | 13   |
      | 14   |
      | 15   |
      | 16   |
      | 17   |
      | 18   |
    And the simulation state contains
      | current_hole                | 18   |
      | team_formation.captain      | p1   |
      | team_formation.type         | solo |
      | betting_state.current_wager | 4    |
      | wagering_closed             | true |
