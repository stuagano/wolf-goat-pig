# Wolf Goat Pig - Complete Game Round Walkthrough

This document demonstrates a complete round of golf in the regular game mode, showing what the GameStateWidget displays at each step with the new `wgp_simulation` system.

## Step 1: Game Initialization

**API Call:**
```bash
POST /simulation/setup
{
  "players": [
    {"id": "p1", "name": "Bob", "handicap": 10.5},
    {"id": "p2", "name": "Scott", "handicap": 15},
    {"id": "p3", "name": "Vince", "handicap": 8},
    {"id": "p4", "name": "Mike", "handicap": 20.5}
  ],
  "course_name": "Wing Point Golf & Country Club"
}
```

**GameStateWidget Displays:**
```
┌─────────────────────────────────────────────┐
│ 🏌️ Hole 1                     Par 4         │
│ Regular Play               Stroke Index: 5   │
├─────────────────────────────────────────────┤
│ 🤝 Team Formation                            │
│ ⏳ Pending - Waiting for tee shots          │
│ Captain: Bob (p1)                            │
├─────────────────────────────────────────────┤
│ 💰 Betting State                             │
│ Current Wager: 1 quarter                     │
│ Base Wager: 1 quarter                        │
├─────────────────────────────────────────────┤
│ 🎯 Shot Progression                          │
│ Shot #1                                      │
│ Next to Hit: Bob                             │
│ Line of Scrimmage: Not set                   │
├─────────────────────────────────────────────┤
│ 👥 Player Status                             │
│ ┌─────────────────────────┐                 │
│ │ Bob                      │                 │
│ │ Handicap: 10.5 | Pts: 0  │                 │
│ │ ● +1 stroke              │                 │
│ │ Not yet hit              │                 │
│ └─────────────────────────┘                 │
│ [Scott, Vince, Mike - similar cards]        │
└─────────────────────────────────────────────┘
```

**hole_state data:**
```json
{
  "hole_number": 1,
  "hole_par": 4,
  "stroke_index": 5,
  "hitting_order": ["p1", "p2", "p3", "p4"],
  "current_shot_number": 1,
  "hole_complete": false,
  "wagering_closed": false,
  "ball_positions": {},
  "next_player_to_hit": "p1",
  "teams": {
    "type": "pending",
    "captain": "p1",
    "pending_request": null
  },
  "betting": {
    "base_wager": 1,
    "current_wager": 1,
    "doubled": false,
    "redoubled": false,
    "special_rules": {
      "float_invoked": false,
      "option_invoked": false
    }
  },
  "stroke_advantages": {
    "p1": {"strokes_received": 1, "handicap": 10.5},
    "p2": {"strokes_received": 1, "handicap": 15},
    "p3": {"strokes_received": 0, "handicap": 8},
    "p4": {"strokes_received": 2, "handicap": 20.5}
  }
}
```

---

## Step 2: Bob's Tee Shot

**API Call:**
```bash
POST /simulation/play-next-shot
```

**Shot Result:**
```json
{
  "player_id": "p1",
  "shot_quality": "good",
  "distance_to_pin": 150,
  "lie_type": "fairway",
  "shot_count": 1
}
```

**GameStateWidget Updates:**
```
┌─────────────────────────────────────────────┐
│ 🏌️ Hole 1                     Par 4         │
├─────────────────────────────────────────────┤
│ 🎯 Shot Progression                          │
│ Shot #2                                      │
│ Next to Hit: Scott                           │
│ Line of Scrimmage: Bob (150 yds)            │
├─────────────────────────────────────────────┤
│ 👥 Player Status                             │
│ ┌─────────────────────────┐                 │
│ │ Bob ⭐                   │                 │
│ │ Handicap: 10.5 | Pts: 0  │                 │
│ │ ● +1 stroke              │                 │
│ │ 150 yds • Shot #1        │  ← UPDATED!    │
│ └─────────────────────────┘                 │
└─────────────────────────────────────────────┘
```

---

## Step 3: Scott's Tee Shot

**API Call:**
```bash
POST /simulation/play-next-shot
```

**Shot Result:**
```json
{
  "player_id": "p2",
  "shot_quality": "excellent",
  "distance_to_pin": 120,
  "lie_type": "fairway",
  "shot_count": 1
}
```

**GameStateWidget Updates:**
```
┌─────────────────────────────────────────────┐
│ 🎯 Shot Progression                          │
│ Shot #3                                      │
│ Next to Hit: Vince                           │
│ Line of Scrimmage: Scott (120 yds) ⭐       │
├─────────────────────────────────────────────┤
│ 👥 Player Status                             │
│ ┌─────────────────────────┐                 │
│ │ Bob                      │                 │
│ │ 150 yds • Shot #1        │                 │
│ └─────────────────────────┘                 │
│ ┌─────────────────────────┐                 │
│ │ Scott ⭐⭐               │                 │
│ │ Handicap: 15 | Pts: 0    │                 │
│ │ ● +1 stroke              │                 │
│ │ 120 yds • Shot #1        │  ← BEST SO FAR │
│ └─────────────────────────┘                 │
└─────────────────────────────────────────────┘
```

**Partnership Window Opens!** After 2 players have hit, Bob (captain) can now choose a partner.

---

## Step 4: Vince's Tee Shot

**API Call:**
```bash
POST /simulation/play-next-shot
```

**Shot Result:**
```json
{
  "player_id": "p3",
  "shot_quality": "poor",
  "distance_to_pin": 200,
  "lie_type": "rough",
  "shot_count": 1
}
```

**GameStateWidget Updates:**
```
┌─────────────────────────────────────────────┐
│ 👥 Player Status                             │
│ ┌─────────────────────────┐                 │
│ │ Scott ⭐⭐ (120 yds)     │                 │
│ │ Bob (150 yds)            │                 │
│ │ Vince (200 yds) ⚠️       │  ← POOR SHOT   │
│ │ Mike (not yet hit)       │                 │
│ └─────────────────────────┘                 │
└─────────────────────────────────────────────┘
```

**Available Actions:**
- **REQUEST_PARTNERSHIP** (Bob can pick Scott or Vince)
- **DECLARE_SOLO** (Bob goes alone)
- **PLAY_SHOT** (Let Mike hit before deciding)

---

## Step 5: Bob Requests Scott as Partner

**API Call:**
```bash
POST /game/action
{
  "action": "request_partner",
  "payload": {
    "captain_id": "p1",
    "partner_id": "p2"
  }
}
```

**GameStateWidget Updates:**
```
┌─────────────────────────────────────────────┐
│ 🤝 Team Formation                            │
│ ⏳ PENDING RESPONSE                          │
│ Bob requests Scott as partner               │
│ Awaiting Scott's decision...                │
├─────────────────────────────────────────────┤
│ Available Actions (for Scott):              │
│ ✓ Accept Partnership                        │
│ ✗ Decline Partnership                       │
└─────────────────────────────────────────────┘
```

**hole_state.teams:**
```json
{
  "type": "pending",
  "captain": "p1",
  "pending_request": {
    "requested": "p2",
    "timestamp": "2025-11-02T..."
  }
}
```

---

## Step 6: Scott Accepts Partnership

**API Call:**
```bash
POST /game/action
{
  "action": "accept_partner",
  "payload": {
    "partner_id": "p2",
    "accepted": true
  }
}
```

**GameStateWidget Updates:**
```
┌─────────────────────────────────────────────┐
│ 🤝 Team Formation                            │
│ ✓ PARTNERS FORMED                           │
│ ┌────────────────────────────┐              │
│ │ Team 1: Bob & Scott         │              │
│ │ Team 2: Vince & Mike        │              │
│ └────────────────────────────┘              │
├─────────────────────────────────────────────┤
│ 💰 Betting State                             │
│ Current Wager: 1 quarter                     │
│ Base Wager: 1 quarter                        │
│ Wagering Open - Doubles Available           │
└─────────────────────────────────────────────┘
```

**hole_state.teams:**
```json
{
  "type": "partners",
  "captain": "p1",
  "team1": ["p1", "p2"],
  "team2": ["p3", "p4"],
  "pending_request": null
}
```

---

## Step 7: Mike's Tee Shot

**API Call:**
```bash
POST /simulation/play-next-shot
```

**Shot Result:**
```json
{
  "player_id": "p4",
  "shot_quality": "average",
  "distance_to_pin": 180,
  "lie_type": "fairway",
  "shot_count": 1
}
```

**GameStateWidget Updates:**
```
┌─────────────────────────────────────────────┐
│ 🎯 Shot Progression                          │
│ Shot #5                                      │
│ Next to Hit: Scott (120 yds - closest)      │
│ Line of Scrimmage: Scott                     │
├─────────────────────────────────────────────┤
│ 👥 Player Status                             │
│ All players have hit tee shots:              │
│ 1. Scott (Team 1) - 120 yds ⭐              │
│ 2. Bob (Team 1) - 150 yds                   │
│ 3. Mike (Team 2) - 180 yds                  │
│ 4. Vince (Team 2) - 200 yds ⚠️              │
└─────────────────────────────────────────────┘
```

**Available Betting Actions:**
- **OFFER_DOUBLE** (Team 2 can double the wager)

---

## Step 8: Team 2 Offers Double

**API Call:**
```bash
POST /game/action
{
  "action": "offer_double",
  "payload": {
    "player_id": "p3"
  }
}
```

**GameStateWidget Updates:**
```
┌─────────────────────────────────────────────┐
│ 💰 Betting State                             │
│ ⚡ DOUBLE OFFERED!                           │
│ Vince offers to double from 1 to 2 quarters │
│                                              │
│ Available Actions (for Team 1):             │
│ ✓ Accept Double                             │
│ ✗ Decline Double (forfeit hole)            │
└─────────────────────────────────────────────┘
```

---

## Step 9: Team 1 Accepts Double

**API Call:**
```bash
POST /game/action
{
  "action": "accept_double",
  "payload": {
    "team_id": "team1",
    "accepted": true
  }
}
```

**GameStateWidget Updates:**
```
┌─────────────────────────────────────────────┐
│ 💰 Betting State                             │
│ ⚡ Doubled!                                   │
│ Current Wager: 2 quarters                    │
│ Base Wager: 1 quarter                        │
│ Wagering Closed - No more doubles           │
├─────────────────────────────────────────────┤
│ ⚡ Special Rules Active                      │
│ Double accepted on Hole 1                   │
└─────────────────────────────────────────────┘
```

**hole_state.betting:**
```json
{
  "base_wager": 1,
  "current_wager": 2,
  "doubled": true,
  "redoubled": false,
  "wagering_closed": false
}
```

---

## Step 10: Continue Playing - Scott's Approach Shot

**API Call:**
```bash
POST /simulation/play-next-shot
```

**Shot Result:**
```json
{
  "player_id": "p2",
  "shot_quality": "excellent",
  "distance_to_pin": 5,
  "lie_type": "green",
  "shot_count": 2
}
```

**GameStateWidget Updates:**
```
┌─────────────────────────────────────────────┐
│ 🎯 Shot Progression                          │
│ Shot #6                                      │
│ Next to Hit: Bob (150 yds)                  │
│                                              │
│ 👥 Player Status                             │
│ ┌─────────────────────────┐                 │
│ │ Scott (Team 1) ⭐⭐⭐    │                 │
│ │ 5 yds • Shot #2          │  ← ON GREEN!   │
│ │ (Excellent approach!)    │                 │
│ └─────────────────────────┘                 │
└─────────────────────────────────────────────┘
```

---

## Step 11-15: Continue Until All Balls Holed

Players continue hitting until all balls are holed or conceded...

**After all players finish:**

```
┌─────────────────────────────────────────────┐
│ 🎯 Shot Progression                          │
│ ✅ HOLE COMPLETE!                            │
│                                              │
│ Final Positions:                             │
│ Scott (Team 1) - Holed in 3                 │
│ Bob (Team 1) - Holed in 4                   │
│ Mike (Team 2) - Holed in 4                  │
│ Vince (Team 2) - Holed in 5                 │
└─────────────────────────────────────────────┘
```

---

## Step 16: Enter Scores

**API Call:**
```bash
POST /game/action
{
  "action": "record_net_score",
  "payload": {
    "player_id": "p1",
    "score": 3
  }
}
```

(Repeat for each player with their net scores after handicap strokes)

**Final Net Scores:**
- Scott: 3 (gross 3 - 1 stroke = 2 net) ⭐
- Bob: 4 (gross 4 - 1 stroke = 3 net)
- Mike: 4 (gross 4 - 2 strokes = 2 net) ⭐
- Vince: 5 (gross 5 - 0 strokes = 5 net)

---

## Step 17: Calculate Points

**API Call:**
```bash
POST /game/action
{
  "action": "calculate_hole_points"
}
```

**GameStateWidget Updates:**
```
┌─────────────────────────────────────────────┐
│ 🏆 Hole 1 Complete!                          │
│                                              │
│ Result: TIE (both teams had best ball of 2) │
│                                              │
│ Points Awarded:                              │
│ Team 1 (Bob & Scott): 0 points              │
│ Team 2 (Vince & Mike): 0 points             │
│                                              │
│ Wager carried over to Hole 2! (2 quarters)  │
└─────────────────────────────────────────────┘
```

**Updated Player Points:**
```json
{
  "p1": {"points": 0},
  "p2": {"points": 0},
  "p3": {"points": 0},
  "p4": {"points": 0}
}
```

---

## Step 18: Advance to Hole 2

**API Call:**
```bash
POST /game/action
{
  "action": "next_hole"
}
```

**GameStateWidget Resets for Hole 2:**
```
┌─────────────────────────────────────────────┐
│ 🏌️ Hole 2                     Par 5         │
│ Regular Play               Stroke Index: 3   │
├─────────────────────────────────────────────┤
│ 🤝 Team Formation                            │
│ ⏳ Pending - New captain: Scott             │
│ Hitting Order: Scott, Vince, Mike, Bob      │
├─────────────────────────────────────────────┤
│ 💰 Betting State                             │
│ Base Wager: 2 quarters (CARRY OVER!)        │
│ Current Wager: 2 quarters                    │
├─────────────────────────────────────────────┤
│ 🎯 Shot Progression                          │
│ Shot #1                                      │
│ Next to Hit: Scott                           │
└─────────────────────────────────────────────┘
```

**hole_state for Hole 2:**
```json
{
  "hole_number": 2,
  "hole_par": 5,
  "hitting_order": ["p2", "p3", "p4", "p1"],
  "current_shot_number": 1,
  "ball_positions": {},
  "teams": {
    "type": "pending",
    "captain": "p2"
  },
  "betting": {
    "base_wager": 2,
    "current_wager": 2,
    "carry_over": true
  }
}
```

---

## Summary

This walkthrough shows how the **GameStateWidget** provides real-time tracking throughout a complete hole:

### What You See at Each Step:

1. **Before shots**: Captain, hitting order, handicap strokes
2. **During tee shots**: Live ball positions, distances, shot quality
3. **Partnership decision**: Available partners with their tee shot results
4. **Betting opportunities**: Double offers with current positions
5. **Shot progression**: Next player to hit, line of scrimmage
6. **Hole completion**: Final scores, net scores with handicap strokes
7. **Points calculation**: Who won, points awarded, carry-over status
8. **Next hole**: Captain rotation, carry-over wagers

### Key Features Working:

✅ Real-time `hole_state` updates from `wgp_simulation`
✅ Team formation tracking (pending → partners)
✅ Betting state with doubles/redoubles
✅ Shot progression with ball positions
✅ Handicap stroke advantages (Creecher feature)
✅ Special rules indicators
✅ Captain rotation between holes
✅ Carry-over wagers

The modern `wgp_simulation` system provides all this data automatically through the `hole_state` object, making the "toss the tees let's track what's going on" vision fully realized!
