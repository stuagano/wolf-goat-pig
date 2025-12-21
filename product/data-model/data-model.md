# Data Model

## Entities

### Player
A person participating in a game. Includes their name and handicap for scoring adjustments.

### Course
A golf course with its 18 holes and their respective pars. Provides the layout and scoring baseline for games.

### Game
A single round of Wolf Goat Pig played on a course with a group of 4-6 players. Contains the betting configuration and tracks overall game state.

### Hole
One hole within a game. Tracks the captain for that hole, any partnerships formed, and the betting outcome (who won the hole and how many quarters).

### Score
A player's stroke count on a specific hole. Used to determine hole winners and net scores with handicap adjustments.

### Bet
A betting action that occurred during a hole. Includes actions like The Float, The Option, doubles offered/accepted, and special bets.

## Relationships

- Course has many Games
- Game belongs to a Course
- Game has many Players (4-6)
- Game has 18 Holes
- Hole has many Scores (one per player)
- Hole has many Bets
- Hole has one Captain (a Player)
- Bet belongs to a Player
