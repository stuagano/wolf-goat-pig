Feature: Core Wolf Goat Pig Game Rules
  As a Wolf Goat Pig player
  I want the game to correctly apply all scoring and betting rules
  So that the game is fair and matches Wing Point Golf & Country Club rules

  Background:
    Given a standard 4-player game is set up
    And players have the following handicaps:
      | player   | handicap |
      | Player 1 | 10       |
      | Player 2 | 15       |
      | Player 3 | 8        |
      | Player 4 | 12       |

  # ============================================================================
  # SCORING SCENARIOS
  # ============================================================================

  Scenario: Best-ball scoring with 2v2 teams
    Given we are on hole 5 (Par 4, Stroke Index 10)
    And Player 1 is the captain
    And Player 1 chooses Player 2 as partner
    And teams are formed as Player1+Player2 vs Player3+Player4
    And the base wager is 1 quarter
    When the hole is completed with gross scores:
      | player   | gross |
      | Player 1 | 5     |
      | Player 2 | 4     |
      | Player 3 | 6     |
      | Player 4 | 5     |
    Then Player 2 net score should be 4
    And Player 1 net score should be 5
    And Player 3 net score should be 5
    And Player 4 net score should be 5
    And Team1 best ball is 4
    And Team2 best ball is 5
    And Team1 wins the hole
    And Player 1 earns 1 quarter
    And Player 2 earns 1 quarter
    And Player 3 loses 1 quarter
    And Player 4 loses 1 quarter

  Scenario: Solo player wins - double payout
    Given we are on hole 8 (Par 4, Stroke Index 5)
    And Player 3 is the captain
    And Player 3 chooses to go solo
    And Player 3 is playing alone against Player1+Player2+Player4
    And the base wager is 1 quarter
    When the hole is completed with net scores:
      | player   | net |
      | Player 1 | 5   |
      | Player 2 | 6   |
      | Player 3 | 4   |
      | Player 4 | 5   |
    Then Player 3 wins the hole
    And Player 3 earns 6 quarters total
    And Player 1 loses 2 quarters
    And Player 2 loses 2 quarters
    And Player 4 loses 2 quarters
    And the solo player won with double payout

  Scenario: Solo player loses - double penalty
    Given we are on hole 12 (Par 5, Stroke Index 1)
    And Player 1 is the captain
    And Player 1 chooses to go solo
    And Player 1 is playing alone against Player2+Player3+Player4
    And the base wager is 1 quarter
    When the hole is completed with net scores:
      | player   | net |
      | Player 1 | 6   |
      | Player 2 | 4   |
      | Player 3 | 5   |
      | Player 4 | 5   |
    Then the opponents team wins the hole
    And Player 1 loses 6 quarters total
    And Player 2 wins 2 quarters
    And Player 3 wins 2 quarters
    And Player 4 wins 2 quarters
    And the solo player lost with double penalty

  Scenario: Partnership vs partnership - tie hole
    Given we are on hole 7 (Par 3, Stroke Index 15)
    And Player 2 is the captain
    And Player 2 chooses Player 4 as partner
    And teams are formed as Player2+Player4 vs Player1+Player3
    And the base wager is 1 quarter
    When the hole is completed with net scores:
      | player   | net |
      | Player 1 | 3   |
      | Player 2 | 4   |
      | Player 3 | 4   |
      | Player 4 | 3   |
    Then Team1 best ball is 3
    And Team2 best ball is 3
    And the hole is halved (tied)
    And no points are awarded
    And no player earnings change

  # ============================================================================
  # HANDICAP APPLICATION
  # ============================================================================

  Scenario: Handicap strokes applied correctly to net scores
    Given we are on hole 1 (Par 4, Stroke Index 1)
    And Player 2 has handicap 15 and receives 1 stroke
    And Player 3 has handicap 8 and receives 1 stroke
    And Player 4 has handicap 12 and receives 1 stroke
    And Player 1 has handicap 10 and receives 1 stroke
    When the hole is completed with gross scores:
      | player   | gross |
      | Player 1 | 5     |
      | Player 2 | 6     |
      | Player 3 | 4     |
      | Player 4 | 5     |
    Then net scores should be:
      | player   | net |
      | Player 1 | 4   |
      | Player 2 | 5   |
      | Player 3 | 3   |
      | Player 4 | 4   |

  Scenario: No handicap strokes on easier holes
    Given we are on hole 12 (Par 3, Stroke Index 18)
    And Player 1 has handicap 10 and receives 0 strokes
    And Player 2 has handicap 15 and receives 0 strokes
    And Player 3 has handicap 8 and receives 0 strokes
    And Player 4 has handicap 12 and receives 0 strokes
    When the hole is completed with gross scores:
      | player   | gross |
      | Player 1 | 4     |
      | Player 2 | 5     |
      | Player 3 | 3     |
      | Player 4 | 4     |
    Then net scores should equal gross scores:
      | player   | net |
      | Player 1 | 4   |
      | Player 2 | 5   |
      | Player 3 | 3   |
      | Player 4 | 4   |

  # ============================================================================
  # CARRY-OVER (TIE HANDLING)
  # ============================================================================

  Scenario: Halved hole carries wager to next hole
    Given we are on hole 9 (Par 4, Stroke Index 7)
    And Player 4 is the captain
    And Player 4 chooses Player 1 as partner
    And teams are formed as Player4+Player1 vs Player2+Player3
    And the base wager is 1 quarter
    And the current wager is 1 quarter
    When the hole is completed with both teams scoring net 4
    Then the hole is halved
    And the carry_over flag is set to true
    And no points are awarded this hole
    And the next hole wager should be 2 quarters

  Scenario: Multiple consecutive ties accumulate wager
    Given we are on hole 10 (Par 5, Stroke Index 3)
    And the previous hole was halved with carry_over active
    And the current wager is 2 quarters (base 1 + carry 1)
    And teams are Player1+Player2 vs Player3+Player4
    When the hole is completed with both teams scoring net 5
    Then the hole is halved again
    And the carry_over flag remains true
    And the next hole wager should be 3 quarters

  Scenario: Carry-over resolves when hole is won
    Given we are on hole 11 (Par 4, Stroke Index 9)
    And the previous 2 holes were halved
    And the current wager is 3 quarters (base 1 + carry 2)
    And teams are Player1+Player3 vs Player2+Player4
    When the hole is completed with Team1 scoring net 4 and Team2 scoring net 5
    Then Team1 wins the hole
    And Player 1 earns 3 quarters
    And Player 3 earns 3 quarters
    And Player 2 loses 3 quarters
    And Player 4 loses 3 quarters
    And the carry_over flag is cleared
    And the next hole wager returns to 1 quarter

  # ============================================================================
  # KARL MARX RULE (5+ PLAYER GAMES)
  # ============================================================================

  Scenario: Karl Marx Rule with 5 players - unequal teams
    Given a 5-player game is set up
    And players are Player1, Player2, Player3, Player4, and Aardvark
    And we are on hole 6 (Par 4, Stroke Index 6)
    And Player 1 is the captain
    And Player 1 chooses Player 2 as partner
    And Aardvark joins Team1
    And teams are Team1(Player1+Player2+Aardvark) vs Team2(Player3+Player4)
    And the base wager is 1 quarter
    When the hole is completed with Team1 winning
    Then each Team1 player earns 0.67 quarters (2 quarters / 3 players)
    And each Team2 player loses 1 quarter
    And total quarters balance to zero

  Scenario: Karl Marx Rule ensures fair point distribution
    Given a 5-player game is set up
    And we are on hole 10 (Par 5, Stroke Index 2)
    And teams are Team1(Captain+Partner) vs Team2(Opp1+Opp2+Aardvark)
    And Team2 has 3 players and Team1 has 2 players
    And the base wager is 1 quarter
    When the hole is completed with Team2 winning
    Then each Team2 player earns 0.67 quarters
    And each Team1 player loses 1.5 quarters
    And the Karl Marx Rule was applied for unequal teams

  # ============================================================================
  # WOLF FORMAT - PARTNERSHIP DECISIONS
  # ============================================================================

  Scenario: Wolf format - Captain chooses after seeing all tee shots
    Given we are on hole 3 (Par 4, Stroke Index 12)
    And Player 2 is the captain
    And the game format is Wolf
    When Player 2 tees off - 200 yards in fairway
    And Player 3 tees off - 240 yards in fairway
    And Player 4 tees off - 180 yards in rough
    And Player 1 tees off - 160 yards in rough
    And Player 2 reviews all tee shot results
    And Player 2 chooses Player 3 as partner
    Then teams are formed as Player2+Player3 vs Player1+Player4
    And the base wager is 1 quarter
    And the partnership was formed after seeing all shots

  Scenario: Wolf format - Captain goes solo after poor opponent shots
    Given we are on hole 14 (Par 4, Stroke Index 4)
    And Player 3 is the captain
    And the game format is Wolf
    When Player 3 tees off - 230 yards in fairway
    And Player 4 tees off - 150 yards in rough
    And Player 1 tees off - 140 yards in bunker
    And Player 2 tees off - 160 yards in rough
    And Player 3 reviews all tee shot results
    And Player 3 decides to go solo
    Then Player 3 is playing alone against Player1+Player2+Player4
    And the wager is doubled to 2 quarters
    And Player 3 will earn triple if winning

  # ============================================================================
  # SPECIAL BETTING RULES
  # ============================================================================

  Scenario: The Float - Captain doubles base wager once per round
    Given we are on hole 5 (Par 4, Stroke Index 8)
    And Player 1 is the captain
    And Player 1 has not used The Float this round
    And the base wager is 1 quarter
    When Player 1 invokes The Float
    Then the current wager becomes 2 quarters for this hole only
    And the float_invoked flag is set to true
    And Player 1 cannot invoke The Float again this round

  Scenario: The Float - Cannot be invoked twice in same round
    Given we are on hole 15 (Par 5, Stroke Index 11)
    And Player 2 is the captain
    And Player 2 already used The Float on hole 7
    And the float_invoked flag is true for Player 2
    And the base wager is 1 quarter
    When Player 2 attempts to invoke The Float
    Then the Float invocation is rejected
    And an error message says "Float already used this round"
    And the wager remains 1 quarter

  Scenario: The Option - Auto-triggers when captain is Goat (furthest down)
    Given we are on hole 16 (Par 3, Stroke Index 17)
    And Player 4 is the captain
    And cumulative scores show:
      | player   | points |
      | Player 1 | +4     |
      | Player 2 | +2     |
      | Player 3 | +1     |
      | Player 4 | -7     |
    And Player 4 is the Goat (furthest down in points)
    When Player 4 forms a partnership
    Then The Option is automatically triggered
    And the wager doubles to 2 quarters
    And the option_invoked flag is set to true

  # ============================================================================
  # WAGERING RESTRICTIONS
  # ============================================================================

  Scenario: Wagering closes after tee shots - team cannot double
    Given we are on hole 8 (Par 4, Stroke Index 13)
    And teams are Player1+Player2 vs Player3+Player4
    And all players have completed their tee shots
    And the wagering_closed flag is true
    When Team1 attempts to offer a double
    Then the double offer is rejected
    And an error message says "Wagering is closed after tee shots"
    And the wager remains unchanged

  Scenario: Solo player can double even after wagering closed
    Given we are on hole 13 (Par 5, Stroke Index 5)
    And Player 2 is playing solo against Player1+Player3+Player4
    And all players have completed their tee shots
    And the wagering_closed flag is true for teams
    When Player 2 offers to double the wager
    Then the double offer is accepted
    And the wager doubles to 2 quarters
    And solo players have special doubling privileges

  Scenario: Line of scrimmage restricts trailing player betting
    Given we are on hole 10 (Par 5, Stroke Index 2)
    And teams are Player1+Player2 vs Player3+Player4
    And Player 1 is trailing in position (furthest from hole)
    And the line_of_scrimmage rule is active
    When Player 1 attempts to double the wager
    Then the double is not allowed
    And an error message says "Must be at or beyond line of scrimmage to double"
    And Player 1 must reach a better position first
