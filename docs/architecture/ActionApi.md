Of course. Here is a fully fleshed-out design for the unified action API, centralizing game logic on the server and simplifying the client.


Core Data Models


These are the key data structures the API will use to represent the game's state.
* Player: Represents a single golfer.
   * name: string (e.g., "Scott Stover")
   * handicap: number
   * round_score: number (Quarters won/lost)
* Ball: Tracks each player's ball on the current hole.
   * player_name: string
   * shot_count: number
   * distance_to_hole: number (in yards)
   * status: string ("tee", "fairway", "rough", "green", "holed_out", "conceded")
* BettingState: Manages the wager for the current hole.
   * base_wager: number (Initial quarters at stake)
   * current_wager: number (Wager after doubles)
   * doubling_team: string[] (Names of players on the team that last offered a double)
* GameState: The comprehensive state object returned after every action.
   * game_id: string
   * hole_number: number
   * whos_turn: string (Name of the player who needs to act next)
   * order_of_play: string[] (Teeing order for the current hole)
   * teams: object[] (e.g., [{ "members": ["Scott", "Bob"], "best_ball": 0 }])
   * balls: Ball[]
   * betting_state: BettingState
   * players: Player[]
________________


The Unified API Endpoint


All game interactions are handled through a single endpoint. This ensures the server is the sole authority on game rules and state transitions.
POST /wgp/{game_id}/action
The request body contains the action the user wants to take. The server validates if the action is legal, updates the game state, and returns the new state along with the next possible actions.
________________


Action Payloads & Server Logic


Here are the various action_type values and the server logic they trigger.
Action Type
	Payload
	Server Logic
	INITIALIZE_GAME
	{ "players": Player[] }
	Creates a new game, sets the random tee order for hole 1, and returns the initial state.
	PLAY_SHOT
	null
	Simulates a shot for whos_turn. Updates the corresponding Ball object. Determines the next player to hit (farthest from the hole).
	REQUEST_PARTNERSHIP
	{ "target_player_name": string }
	Records the Captain's request. Sets whos_turn to the target player.
	RESPOND_PARTNERSHIP
	{ "accepted": boolean }
	If true, forms the team. If false, the rejecting player plays solo against the other three.
	DECLARE_SOLO
	null
	The Captain decides to play alone. Finalizes teams as 1 vs. 3.
	AARDVARK_JOIN_REQUEST
	{ "target_team_index": number }
	The Aardvark asks to join a team. Sets whos_turn to the members of that team.
	AARDVARK_TOSS
	{ "accepted": boolean }
	A team accepts or rejects ("tosses") an Aardvark. Doubles the wager if tossed.
	OFFER_DOUBLE
	null
	Records the double offer. Sets whos_turn to the opposing team members.
	ACCEPT_DOUBLE
	{ "accepted": boolean }
	If true, doubles current_wager. If false, the hole ends, and the offering team wins the current wager.
	CONCEDE_PUTT
	{ "target_player_name": string }
	Sets a player's Ball.status to "conceded," allowing betting to continue as per "good but not in."
	________________


Standard API Response Structure


Every successful POST request to the action endpoint receives this structured response, which contains everything the client needs to update the UI.


JSON




{
 "game_state": { ... },
 "log_message": "Scott's drive lands in the fairway, 245 yards out. It is now Bob's turn to tee off.",
 "available_actions": [
   {
     "action_type": "PLAY_SHOT",
     "prompt": "Tee off",
     "player_turn": "Bob"
   }
 ]
}

________________


Example Flow: Hole 2 (4-Man Game)


Let's assume the tee order is Scott (Captain), Bob, Vince, Mike.
1. Scott Tees Off
   * Client Request: POST /wgp/123/action with payload { "action_type": "PLAY_SHOT" }
   * Server Response:
JSON
{
 "game_state": { "whos_turn": "Bob", "balls": [{ "player_name": "Scott", ... }] },
 "log_message": "Scott tees off. It is Bob's turn.",
 "available_actions": [{ "action_type": "PLAY_SHOT", "player_turn": "Bob" }]
}

   2. Bob Tees Off, Scott Requests Partnership
   * Client sends PLAY_SHOT for Bob. Server responds with available_actions for Scott.
   * Client Request: POST /wgp/123/action with payload { "action_type": "REQUEST_PARTNERSHIP", "payload": { "target_player_name": "Bob" } }
   * Server Response:
JSON
{
 "game_state": { "whos_turn": "Bob" },
 "log_message": "Scott asks Bob to be his partner.",
 "available_actions": [{ "action_type": "RESPOND_PARTNERSHIP", "player_turn": "Bob" }]
}

      3. Bob Accepts
      * Client Request: POST /wgp/123/action with payload { "action_type": "RESPOND_PARTNERSHIP", "payload": { "accepted": true } }
      * Server Response: The server finalizes the teams ([Scott, Bob] vs. [Vince, Mike]) and sets the turn to the next player in the original tee order.
JSON
{
 "game_state": { "whos_turn": "Vince", "teams": [...] },
 "log_message": "Bob accepts! The teams are Scott/Bob vs. Vince/Mike. Vince's turn to tee off.",
 "available_actions": [{ "action_type": "PLAY_SHOT", "player_turn": "Vince" }]
}

         4. Mid-Hole Double Offer
         * After a few shots, Scott and Bob are in a good position. The server determines it's their turn to act.
         * Server Response (after a shot from Vince/Mike's team):
JSON
{
 "game_state": { "whos_turn": "Scott" },
 "log_message": "Vince's ball is on the green. It is Scott's turn to hit.",
 "available_actions": [
   { "action_type": "PLAY_SHOT", "player_turn": "Scott" },
   { "action_type": "OFFER_DOUBLE", "player_turn": "Scott" }
 ]
}

         * The client UI can now show both a "Hit Shot" and an "Offer Double" button for Scott. This flow continues until the hole is complete, with the server always providing the legal next moves.