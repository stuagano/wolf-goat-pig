# 🎮 Wolf-Goat-Pig Gameplay User Journey

## Overview
This document describes the expected user experience for playing Wolf-Goat-Pig, a golf betting simulation game. The game combines golf gameplay with strategic betting decisions.

## User Journey Flow

### 1. Game Setup Phase
**User Action:** Navigate to Simulation Mode
**Expected Experience:**
- User sees the game setup form
- Form displays:
  - Player name input field
  - Handicap selector (default: 18)
  - Computer opponents (3 pre-selected)
  - Course selection dropdown
  - Personality options for opponents

**User Action:** Configure game settings
- Enter their name
- Adjust handicap if desired
- Select/modify computer opponents
- Choose a golf course
- Click "Start Simulation"

**Expected Result:**
- Loading indicator appears briefly
- Transition to gameplay view
- Game state initialized with 4 players on hole 1

### 2. Main Gameplay Loop

#### 2a. Hole Start
**System Displays:**
- Current hole number (1-18)
- Par for the hole
- Player standings/scores
- "Play Next Shot" button

**User Action:** Click "Play Next Shot"
**Expected Result:**
- Backend simulates the tee shot
- Feedback shows who hit and result
- If user is captain, decision prompt appears
- Otherwise, continues to next shot

#### 2b. Captain Decision (if applicable)
**When:** User is randomly selected as captain for the hole
**System Displays:**
- "You are the Captain!" message
- Options:
  - Select a partner from other players
  - Go solo (double the wager)
  
**User Action:** Make captain decision
**Expected Result:**
- If partner requested: Wait for partner response
- If solo: Wager doubles, play continues
- Feedback shows decision outcome

#### 2c. Partnership Response (if requested as partner)
**System Displays:**
- "[Captain Name] wants you as their partner!"
- Accept/Decline buttons

**User Action:** Accept or Decline
**Expected Result:**
- Teams formed (or captain goes solo if declined)
- Play continues with teams established

#### 2d. Shot-by-Shot Play
**System Displays:**
- "Play Next Shot" button
- Current game state
- Player positions/scores

**User Action:** Click "Play Next Shot" repeatedly
**Expected Results:**
- Each click simulates one shot
- Feedback shows:
  - Player name who shot
  - Distance hit
  - Ball position (fairway, rough, green, etc.)
  - Special events (great shot, in the hole, etc.)
- Continue until hole complete

#### 2e. Hole Completion
**System Displays:**
- Hole results
- Points won/lost
- Updated standings
- Transition to next hole

### 3. Betting Decisions

#### 3a. Double Offer (periodic)
**When:** Teams may offer to double the wager
**System Displays:**
- "Your team wants to offer a double"
- Confirm/Cancel buttons

**User Action:** Decide on double
**Expected Result:**
- If confirmed: Other team must respond
- Wager potentially doubles

#### 3b. Double Response
**When:** Other team offers a double
**System Displays:**
- "They're offering to double!"
- Accept/Decline buttons

**User Action:** Respond to double
**Expected Result:**
- Accept: Wager doubles
- Decline: Continue with current wager

### 4. Game Progression

**Continuous Elements:**
- Hole counter (1-18)
- Running score/points
- Current teams/partnerships
- Base wager amount

**Hole Transitions:**
- After each hole completion
- Scores update
- New captain selected
- Reset to tee for next hole

### 5. Game Completion

**After Hole 18:**
- Final scores displayed
- Winner announced
- Points summary
- Option to start new game

## Key Interaction Points

### Primary Actions
1. **Play Next Shot** - Main gameplay driver
2. **Captain Decisions** - Strategic team formation
3. **Partnership Responses** - Accept/decline invitations
4. **Betting Decisions** - Double offers and responses

### Feedback Systems
- **Shot Results** - Distance, accuracy, position
- **Score Updates** - Points won/lost per hole
- **Educational Tips** - Strategy explanations
- **Game Status** - Current phase, waiting for, etc.

## Technical Flow

### API Calls Sequence
1. `POST /simulation/setup` - Initialize game
2. `POST /simulation/play-next-shot` - Each shot
3. `POST /simulation/play-hole` - Decisions
4. `POST /simulation/betting-decision` - Doubles

### State Management
- `gameState` - Core game data
- `hasNextShot` - Controls shot button visibility
- `interactionNeeded` - Triggers decision prompts
- `feedback` - Accumulates messages
- `shotState` - Current shot details
- `shotProbabilities` - Outcome predictions

## Current Issues to Fix

### ❌ Known Problems
1. **Play Next Shot button doesn't work** - Clicks don't trigger shot simulation
2. **gameState remains null** - Not properly set after setup
3. **No visual feedback** - User doesn't see what happens after clicking

### ✅ Working Features
- Game setup and configuration
- Data loading (personalities, opponents, courses)
- UI renders correctly
- Button appears when it should

## Expected Button Behavior

When user clicks "Play Next Shot":
1. Button should disable (prevent double-clicks)
2. Loading indicator appears
3. API call to `/simulation/play-next-shot`
4. Response updates:
   - Game state
   - Feedback messages
   - Shot results
   - Next shot availability
5. UI updates with results
6. Button re-enables if more shots available

## Success Criteria

The game is working correctly when:
- [ ] User can start a simulation
- [ ] Play Next Shot button triggers shot simulation
- [ ] Feedback appears after each shot
- [ ] Captain decisions work properly
- [ ] Partnership requests/responses function
- [ ] Betting doubles work
- [ ] Game progresses through 18 holes
- [ ] Final scores display correctly
- [ ] User can start a new game

## Testing Checklist

### Setup Phase
- [ ] Enter name and start game
- [ ] Game transitions to play mode
- [ ] Initial state is correct

### Gameplay Phase
- [ ] Play Next Shot works
- [ ] Shots simulate correctly
- [ ] Feedback displays
- [ ] Decisions appear when needed
- [ ] Teams form properly

### Completion Phase
- [ ] Holes complete properly
- [ ] Scores update
- [ ] Game ends after 18 holes

---

This journey represents the complete Wolf-Goat-Pig experience from setup through completion.