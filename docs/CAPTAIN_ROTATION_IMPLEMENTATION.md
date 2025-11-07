# Captain Rotation Implementation Analysis

## Executive Summary

The Wolf Goat Pig game uses a "toss tees order" determined at game start to establish captain rotation throughout the round. Currently, the implementation uses **simple rotation** without tracking the original toss order. The goal is to implement a **fixed "toss tees order"** stored at game initialization that determines captain rotation with this formula:

**Position N in toss order is captain on holes: N, N+4, N+8, N+12, N+16**

For a 4-player game with positions [P1, P2, P3, P4]:
- Hole 1: P1 is captain
- Hole 2: P2 is captain (position 2)
- Hole 3: P3 is captain (position 3)
- Hole 4: P4 is captain (position 4)
- Hole 5: P1 is captain again (position 1 = 1+4)
- Hole 9: P1 is captain (position 1 = 1+8)
- Hole 13: P1 is captain (position 1 = 1+12)
- Hole 17: P1 is captain (position 1 = 1+16, or shifts to Hoepfinger phase)

---

## Current Implementation

### 1. Backend: Captain Determination

**File: `/Users/stuartgano/Documents/wolf-goat-pig/backend/app/wolf_goat_pig_simulation.py`**

#### Game Initialization (Lines 728-750)
```python
def _initialize_hole(self, hole_number: int):
    """Initialize a new hole with proper state"""
    # Determine hitting order
    if hole_number == 1:
        hitting_order = self._random_hitting_order()  # Random shuffle for first hole
    else:
        hitting_order = self._rotate_hitting_order(hole_number)
    
    # ... rest of initialization ...
    
    # Create team formation - captain is first in hitting order
    teams = TeamFormation(type="pending", captain=hitting_order[0])
```

#### Random Hitting Order (Line 829-833)
```python
def _random_hitting_order(self) -> List[str]:
    """Determine random hitting order for first hole (tossing tees)"""
    player_ids = [p.id for p in self.players]
    random.shuffle(player_ids)
    return player_ids
```

#### Rotate Hitting Order (Lines 835-846)
```python
def _rotate_hitting_order(self, hole_number: int) -> List[str]:
    """Rotate hitting order for subsequent holes"""
    if hole_number == 1:
        return self._random_hitting_order()
    
    # Check if previous hole exists, if not use random order
    if hole_number - 1 not in self.hole_states:
        return self._random_hitting_order()
        
    previous_order = self.hole_states[hole_number - 1].hitting_order
    # Rotate: second becomes first, third becomes second, etc.
    return previous_order[1:] + [previous_order[0]]
```

**Key Issues:**
- Rotation is **hole-by-hole** (previous order shifts left)
- No storage of original "toss tees order"
- Captain position doesn't follow the 1, 5, 9, 13, 17... pattern
- Current logic: hole 2 captain = previous hole's 2nd player (not position 2 from toss)

### 2. Frontend: Captain Display

**File: `/Users/stuartgano/Documents/wolf-goat-pig/frontend/src/components/game/SimpleScorekeeper.jsx`**

- Captain is selected manually in UI (lines 107-115)
- No automatic captain assignment based on hole
- Caption manually managed with state: `const [captain, setCaptain] = useState(null);`

**File: `/Users/stuartgano/Documents/wolf-goat-pig/frontend/src/components/game/MobileScorecard.jsx`**

- Displays current teams but no captain rotation visualization
- Captain shown in team display but no indication of rotation rules

### 3. Database Schema

**File: `/Users/stuartgano/Documents/wolf-goat-pig/backend/app/models.py`**

#### GameStateModel (Lines 38-47)
```python
class GameStateModel(Base):
    __tablename__ = "game_state"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, unique=True, index=True)
    join_code = Column(String, unique=True, index=True, nullable=True)
    creator_user_id = Column(String, nullable=True)
    game_status = Column(String, default="setup")
    state = Column(JSON)  # Entire game state as JSON blob
    created_at = Column(String)
    updated_at = Column(String)
```

**Current State Storage:**
- Game state stored as JSON blob in `state` column
- No dedicated column for toss_tees_order
- Example initial state (lines 116-131 in GameLifecycleService):
```python
initial_state = {
    "game_status": "setup",
    "player_count": player_count,
    "players": [...],
    "course_name": course_name,
    "base_wager": base_wager or 1,
    "created_at": current_time
}
```

---

## Where Captain Rotation Should Be Tracked

### Option 1: Database Column (Recommended)
Add dedicated column to `GameStateModel`:
```sql
ALTER TABLE game_state ADD COLUMN toss_tees_order TEXT;
-- Store as JSON array: ["p1", "p2", "p3", "p4"]
```

**Advantages:**
- Explicit, queryable data
- Easy to audit and debug
- Separates critical game config from JSON blob

### Option 2: JSON Blob (Current Pattern)
Store in `state` JSON:
```json
{
  "toss_tees_order": ["p1", "p2", "p3", "p4"],
  "game_status": "setup",
  "players": [...],
  ...
}
```

**Advantages:**
- Consistent with current schema
- No migration needed
- All game config in one place

### Option 3: HoleState (Per-Hole)
Store in each hole's hitting_order:
```python
hole_state.hitting_order = ["p2", "p3", "p4", "p1"]  # Rotated from toss order
hole_state.toss_tees_order_position = 2  # Captain's position in original toss (1-indexed)
```

**Advantages:**
- Audit trail per hole
- Easy to verify rotation accuracy

---

## HoleState Data Structure

**File: `/Users/stuartgano/Documents/wolf-goat-pig/backend/app/wolf_goat_pig_simulation.py` (Lines 122-156)**

```python
@dataclass
class HoleState:
    hole_number: int
    hitting_order: List[str]  # Current hitting order for hole
    teams: TeamFormation      # Team formation including captain
    betting: BettingState
    # ... other fields ...
    
@dataclass
class TeamFormation:
    type: str                 # "partners", "solo", "pending"
    captain: Optional[str]    # Captain player ID
    opponents: List[str]      # Opponents in solo mode
    # ... other fields ...
```

---

## Implementation Plan

### 1. Backend Changes

#### A. Add Toss Tees Order to WolfGoatPigSimulation

**File: `wolf_goat_pig_simulation.py`**

```python
class WolfGoatPigSimulation:
    def __init__(self, player_count: int, players: List[Player]):
        self.players = players
        self.player_count = player_count
        self.toss_tees_order: List[str] = []  # NEW: Store original toss order
        # ... other init ...
    
    def _initialize_hole(self, hole_number: int):
        # On first hole, establish and store toss tees order
        if hole_number == 1:
            hitting_order = self._random_hitting_order()
            self.toss_tees_order = hitting_order  # NEW: Save original order
        else:
            hitting_order = self._get_captain_for_hole(hole_number)
        
        # ... rest of initialization ...
```

#### B. Calculate Captain by Position

```python
def _get_captain_for_hole(self, hole_number: int) -> str:
    """
    Get captain for hole based on toss tees order.
    Position N in toss order captains holes: N, N+4, N+8, N+12, N+16
    """
    if not self.toss_tees_order:
        # Fallback for legacy games
        return self._rotate_hitting_order(hole_number)
    
    # 1-indexed position in toss order
    position = ((hole_number - 1) % len(self.toss_tees_order)) + 1
    return self.toss_tees_order[position - 1]
```

Wait, let me recalculate the formula:
- Hole 1: captain = toss_order[0] (position 1, index 0)
- Hole 2: captain = toss_order[1] (position 2, index 1)
- Hole 3: captain = toss_order[2] (position 3, index 2)
- Hole 4: captain = toss_order[3] (position 4, index 3)
- Hole 5: captain = toss_order[0] (position 1, index 0, cycle back)

Formula:
```python
def _get_captain_for_hole(self, hole_number: int) -> str:
    position_index = (hole_number - 1) % len(self.toss_tees_order)
    return self.toss_tees_order[position_index]
```

#### C. Update Hole Initialization

```python
def _initialize_hole(self, hole_number: int):
    if hole_number == 1:
        hitting_order = self._random_hitting_order()
        self.toss_tees_order = hitting_order  # Store original toss order
    else:
        captain_id = self._get_captain_for_hole(hole_number)
        # Build hitting order with captain first, others after
        hitting_order = [captain_id] + [p for p in self.toss_tees_order if p != captain_id]
    
    # ... rest stays same ...
    teams = TeamFormation(type="pending", captain=hitting_order[0])
```

### 2. Database Migration

**New file: `/backend/migrations/add_toss_tees_order.sql`**

```sql
-- Add toss_tees_order to track original order at game start
ALTER TABLE game_state ADD COLUMN toss_tees_order TEXT;
-- OR if using JSON column type:
ALTER TABLE game_state ADD COLUMN toss_tees_order JSON;

-- Create index for potential queries
CREATE INDEX idx_game_state_toss_order ON game_state(game_id);
```

### 3. Persistence Update

**File: `game_lifecycle_service.py` (Lines 115-131)**

Update initial_state to include toss_tees_order after first hole:

```python
def _initialize_hole(self, hole_number: int):
    if hole_number == 1:
        hitting_order = self._random_hitting_order()
        self.toss_tees_order = hitting_order
        # Persist to database - update game state JSON
        self.persist_game_state()
```

### 4. Frontend Display

**Create component to show captain rotation:**

```javascript
// frontend/src/components/game/CaptainRotationIndicator.jsx
const CaptainRotationIndicator = ({ tossTeeOrder, currentHole, players }) => {
  const getCaptainForHole = (hole) => {
    if (!tossTeeOrder || tossTeeOrder.length === 0) return null;
    const index = (hole - 1) % tossTeeOrder.length;
    return players.find(p => p.id === tossTeeOrder[index])?.name;
  };
  
  return (
    <div>
      <h3>Captain Rotation (Toss Tees Order: {tossTeeOrder.join(', ')})</h3>
      <p>Hole {currentHole} Captain: {getCaptainForHole(currentHole)}</p>
      <div>
        {tossTeeOrder.map((playerId, i) => {
          const holes = [i+1, i+5, i+9, i+13, i+17].filter(h => h <= 18);
          return (
            <div key={playerId}>
              Position {i+1}: Holes {holes.join(', ')}
            </div>
          );
        })}
      </div>
    </div>
  );
};
```

---

## Key Files Summary

### Backend
| File | Location | Purpose | Change Needed |
|------|----------|---------|---------------|
| WolfGoatPigSimulation | `backend/app/wolf_goat_pig_simulation.py` | Game engine | Add `toss_tees_order` field and logic |
| GameLifecycleService | `backend/app/services/game_lifecycle_service.py` | Game lifecycle | Persist toss order to DB |
| GameStateModel | `backend/app/models.py` | Database model | Add `toss_tees_order` column (optional) |
| Database Migration | `backend/migrations/add_toss_tees_order.sql` | Schema | NEW: Add column for explicit tracking |

### Frontend
| File | Location | Purpose | Change Needed |
|------|----------|---------|---------------|
| SimpleScorekeeper | `frontend/src/components/game/SimpleScorekeeper.jsx` | Score entry | Auto-populate captain by hole |
| MobileScorecard | `frontend/src/components/game/MobileScorecard.jsx` | Game display | Show captain rotation |
| GamePage | `frontend/src/pages/GamePage.js` | Game orchestration | Pass toss order to components |

### Data Model
| Field | Location | Current | Needed |
|-------|----------|---------|--------|
| game_state.state (JSON) | GameStateModel | Has players list | Add `toss_tees_order` array |
| HoleState.hitting_order | WolfGoatPigSimulation | Rotated each hole | Derive from toss order |
| HoleState.teams.captain | WolfGoatPigSimulation | hitting_order[0] | Determined by position formula |

---

## Testing Considerations

### Unit Tests Needed
```python
def test_toss_tees_order_stored():
    """Verify toss order stored on hole 1"""
    
def test_captain_rotation_formula():
    """Verify position N captains holes N, N+4, N+8, N+12, N+16"""
    # Test 4-player game
    toss_order = ["p1", "p2", "p3", "p4"]
    assert get_captain_for_hole(1, toss_order) == "p1"
    assert get_captain_for_hole(2, toss_order) == "p2"
    assert get_captain_for_hole(5, toss_order) == "p1"
    assert get_captain_for_hole(9, toss_order) == "p1"
    
def test_captain_rotation_5_player():
    """Verify rotation works with 5 players"""
    toss_order = ["p1", "p2", "p3", "p4", "p5"]
    # Holes 1,6,11,16 = p1, Holes 2,7,12,17 = p2, etc.
    
def test_captain_rotation_6_player():
    """Verify rotation works with 6 players"""
    pass
```

### Integration Tests Needed
- Game initialization through hole 18
- Captain correctly determined each hole
- Hoepfinger phase behavior (goat chooses position)
- Database persistence and retrieval

---

## Migration Path

1. **Add field to WolfGoatPigSimulation** - No breaking changes
2. **Update _initialize_hole logic** - Works alongside existing code
3. **Add database migration** - Optional, can store in JSON
4. **Update frontend** - Use auto-determined captain or allow override
5. **Test extensively** - Verify 4, 5, 6 player games

---

## Rules Reference

From `/Users/stuartgano/Documents/wolf-goat-pig/docs/rules.txt`:

> "The Tossing of the Tees: Before the start of play, a designee tosses tees, one by one, to determine the order of play from the tee throughout the round, up and until the Hoepfinger phase. The order of play rotates from tee box to tee box."

> "At the second hole, the order of play shall rotate so that the player who hit second on the first tee shall hit first on the second. The third becomes second, the fourth becomes third and the Captain from the prior tee moves to the fourth position."

**Note:** The rules state simple rotation (2→1, 3→2, 4→3, 1→4), but your implementation goal requires storing the original toss order and using position-based captain assignment.

