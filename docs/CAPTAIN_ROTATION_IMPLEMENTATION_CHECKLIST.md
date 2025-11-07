# Implementation Checklist - Captain Rotation with Toss Tees Order

## Files to Modify (with exact line numbers)

### 1. Backend Game Engine

#### File: `backend/app/wolf_goat_pig_simulation.py`

**Section A: Class Initialization**
- **Location**: Lines ~250-280 (in `__init__` method)
- **Current Code**: Initialize all game state fields
- **Change**: Add `self.toss_tees_order: List[str] = []`
- **Impact**: Minimal - just adds one list field

**Section B: Hole Initialization**
- **Location**: Lines 728-810 (`_initialize_hole` method)
- **Current Logic**:
  ```python
  if hole_number == 1:
      hitting_order = self._random_hitting_order()
  else:
      hitting_order = self._rotate_hitting_order(hole_number)
  ```
- **New Logic**:
  ```python
  if hole_number == 1:
      hitting_order = self._random_hitting_order()
      self.toss_tees_order = hitting_order  # Store original order
  else:
      captain_id = self._get_captain_for_hole(hole_number)
      hitting_order = [captain_id] + [p for p in self.toss_tees_order if p != captain_id]
  ```

**Section C: Add New Method**
- **Location**: After `_get_hoepfinger_start_hole` (around line 727)
- **New Method**:
```python
def _get_captain_for_hole(self, hole_number: int) -> str:
    """
    Determine captain based on original toss tees order.
    Position index N (0-based) in toss order captains holes: N+1, N+5, N+9, N+13, N+17
    """
    if not self.toss_tees_order:
        # Fallback for legacy games
        return self._rotate_hitting_order(hole_number)[0]
    
    # Use modulo to cycle through positions
    position_index = (hole_number - 1) % len(self.toss_tees_order)
    captain_id = self.toss_tees_order[position_index]
    
    logger.debug(f"Hole {hole_number}: Captain = {captain_id} (position {position_index} in toss order)")
    return captain_id
```

**Section D: Keep Existing Methods (for now)**
- `_random_hitting_order()` - Lines 829-833 (unchanged)
- `_rotate_hitting_order()` - Lines 835-846 (can be deprecated later, keep for reference)

---

### 2. Game Lifecycle Service

#### File: `backend/app/services/game_lifecycle_service.py`

**Location**: After game creation and first hole initialization
- **Change**: Ensure toss_tees_order is persisted after first hole
- **Implementation**: 

```python
# In the method that handles hole completion/progression:
def update_game_state_after_hole(self, game_id: str, db: Session):
    """Update persisted game state to include toss_tees_order after first hole"""
    game = self._active_games.get(game_id)
    if game and game.toss_tees_order:
        game_record = db.query(GameStateModel).filter(
            GameStateModel.game_id == game_id
        ).first()
        if game_record:
            if not game_record.state:
                game_record.state = {}
            game_record.state['toss_tees_order'] = game.toss_tees_order
            game_record.updated_at = datetime.utcnow().isoformat()
            db.commit()
```

---

### 3. Database Schema (Optional)

#### File: `backend/app/models.py`

**Location**: Lines 38-47 (GameStateModel class)
- **Optional Change**: Add explicit column for toss_tees_order
```python
class GameStateModel(Base):
    __tablename__ = "game_state"
    # ... existing columns ...
    toss_tees_order = Column(JSON, nullable=True)  # NEW: Store original order
    # ... other columns ...
```

**Alternative**: Keep storing in `state` JSON blob (no change needed)

---

#### File: `backend/migrations/add_toss_tees_order.sql` (NEW FILE)

**Location**: `backend/migrations/add_toss_tees_order.sql`
```sql
-- Migration: Add toss_tees_order column to track original order at game start
-- Date: 2025-XX-XX
-- Purpose: Explicit tracking of captain rotation order

-- Add column (optional - can use state JSON instead)
ALTER TABLE game_state ADD COLUMN IF NOT EXISTS toss_tees_order TEXT;

-- Create index if needed for querying
CREATE INDEX IF NOT EXISTS idx_game_state_toss_order ON game_state(game_id);
```

---

### 4. Frontend Components

#### File: `frontend/src/components/game/SimpleScorekeeper.jsx`

**Location**: Lines 77-115 (toggleCaptain function)
- **Current**: User manually selects captain
- **Change**: Auto-calculate captain from hole number
```javascript
// Add helper function
const getCaptainForHole = (hole, tossTeeOrder) => {
  if (!tossTeeOrder || tossTeeOrder.length === 0) return null;
  const index = (hole - 1) % tossTeeOrder.length;
  return tossTeeOrder[index];
};

// In handleHoleLoad or similar, auto-set captain:
const autoSetCaptain = (holeNumber) => {
  const captainId = getCaptainForHole(holeNumber, tossTeeOrder);
  if (captainId) {
    setCaptain(captainId);
    setOpponents(players.filter(p => p.id !== captainId).map(p => p.id));
  }
};
```

**Optional**: Allow manual override with warning
- Check if user tries to override captain
- Show tooltip: "Auto-determined captain based on toss order"

---

#### File: `frontend/src/components/game/MobileScorecard.jsx`

**Location**: Around line 60-100 (teams display section)
- **Add**: Captain rotation indicator
```javascript
// Add new section for captain info
{currentHole <= 16 && tossTeeOrder && (
  <div style={{
    background: theme.colors.paper,
    padding: '16px',
    marginBottom: '16px',
    borderLeft: '4px solid ' + theme.colors.primary
  }}>
    <div style={{ fontSize: '14px', color: theme.colors.textSecondary }}>
      Current Captain (Hole {currentHole})
    </div>
    <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
      {players?.find(p => p.id === currentCaptain)?.name}
    </div>
  </div>
)}
```

---

#### File: `frontend/src/pages/GamePage.js`

**Location**: Component initialization section
- **Add**: Pass toss_tees_order to child components
```javascript
const GamePage = ({ gameId }) => {
  const [gameState, setGameState] = useState(null);
  const tossTeeOrder = gameState?.toss_tees_order || gameState?.state?.toss_tees_order;
  
  // Pass to children:
  return (
    <>
      <SimpleScorekeeper 
        gameId={gameId} 
        tossTeeOrder={tossTeeOrder}
        {...otherProps}
      />
    </>
  );
};
```

---

## Verification Checklist

### Unit Tests to Add

**File: `backend/tests/test_captain_rotation.py` (NEW)**

```python
import pytest
from backend.app.wolf_goat_pig_simulation import WolfGoatPigSimulation, Player

class TestCaptainRotation:
    
    def test_toss_tees_order_stored_on_hole_1(self):
        """Verify toss order is stored on first hole"""
        players = [Player(id=f"p{i}", name=f"Player{i}", handicap=18.0) for i in range(1, 5)]
        game = WolfGoatPigSimulation(player_count=4, players=players)
        game.start_hole(1)
        
        assert game.toss_tees_order is not None
        assert len(game.toss_tees_order) == 4
        assert all(p.id in game.toss_tees_order for p in players)
    
    def test_captain_rotation_4_player(self):
        """Verify captain rotation formula for 4-player game"""
        players = [Player(id=f"p{i}", name=f"Player{i}", handicap=18.0) for i in range(1, 5)]
        game = WolfGoatPigSimulation(player_count=4, players=players)
        game.start_hole(1)
        
        # Verify formula: position index = (hole - 1) % player_count
        toss_order = game.toss_tees_order
        
        # Test holes 1-4
        for hole in range(1, 5):
            captain = game._get_captain_for_hole(hole)
            expected_index = (hole - 1) % 4
            assert captain == toss_order[expected_index]
        
        # Test cycling back
        assert game._get_captain_for_hole(5) == toss_order[0]
        assert game._get_captain_for_hole(9) == toss_order[0]
        assert game._get_captain_for_hole(13) == toss_order[0]
    
    def test_captain_rotation_5_player(self):
        """Verify captain rotation formula for 5-player game"""
        players = [Player(id=f"p{i}", name=f"Player{i}", handicap=18.0) for i in range(1, 6)]
        game = WolfGoatPigSimulation(player_count=5, players=players)
        game.start_hole(1)
        
        toss_order = game.toss_tees_order
        
        # Test cycle through all 5 positions
        for hole in range(1, 6):
            captain = game._get_captain_for_hole(hole)
            expected_index = (hole - 1) % 5
            assert captain == toss_order[expected_index]
        
        # Test cycling
        assert game._get_captain_for_hole(6) == toss_order[0]
        assert game._get_captain_for_hole(16) == toss_order[0]  # 6+10
    
    def test_hitting_order_has_captain_first(self):
        """Verify hitting order has captain in first position"""
        players = [Player(id=f"p{i}", name=f"Player{i}", handicap=18.0) for i in range(1, 5)]
        game = WolfGoatPigSimulation(player_count=4, players=players)
        
        for hole in [1, 2, 3, 5, 9]:
            game.start_hole(hole)
            captain_id = game._get_captain_for_hole(hole)
            assert game.hole_states[hole].hitting_order[0] == captain_id
```

---

### Integration Tests

**Add to: `backend/tests/test_integration_scenarios.py`**

```python
def test_captain_rotation_full_game():
    """Test captain rotation through entire 18-hole game"""
    players = [
        Player(id="alice", name="Alice", handicap=10),
        Player(id="bob", name="Bob", handicap=12),
        Player(id="charlie", name="Charlie", handicap=14),
        Player(id="dave", name="Dave", handicap=16)
    ]
    game = WolfGoatPigSimulation(player_count=4, players=players)
    game.start_hole(1)
    
    toss_order = game.toss_tees_order
    
    # Play through all 18 holes
    for hole in range(1, 19):
        game.start_hole(hole)
        
        # Verify captain
        expected_captain_index = (hole - 1) % 4
        expected_captain = toss_order[expected_captain_index]
        actual_captain = game.hole_states[hole].teams.captain
        
        assert actual_captain == expected_captain, \
            f"Hole {hole}: Expected {expected_captain}, got {actual_captain}"
```

---

### Frontend Tests

**File: `frontend/src/components/game/__tests__/SimpleScorekeeper.test.js`**

```javascript
import { getCaptainForHole } from '../SimpleScorekeeper';

describe('Captain Rotation', () => {
  test('getCaptainForHole calculates correct captain', () => {
    const tossOrder = ['p1', 'p2', 'p3', 'p4'];
    
    expect(getCaptainForHole(1, tossOrder)).toBe('p1');
    expect(getCaptainForHole(2, tossOrder)).toBe('p2');
    expect(getCaptainForHole(3, tossOrder)).toBe('p3');
    expect(getCaptainForHole(4, tossOrder)).toBe('p4');
    expect(getCaptainForHole(5, tossOrder)).toBe('p1');  // Cycles back
    expect(getCaptainForHole(9, tossOrder)).toBe('p1');
  });
  
  test('getCaptainForHole works with 5 players', () => {
    const tossOrder = ['p1', 'p2', 'p3', 'p4', 'p5'];
    
    expect(getCaptainForHole(1, tossOrder)).toBe('p1');
    expect(getCaptainForHole(6, tossOrder)).toBe('p1');  // Cycles at 5+1
    expect(getCaptainForHole(16, tossOrder)).toBe('p1'); // 15%5=0
  });
});
```

---

## Deployment Steps

1. **Add field to WolfGoatPigSimulation**
   - Edit `wolf_goat_pig_simulation.py`
   - Add `toss_tees_order` field to `__init__`
   - No database or frontend changes needed yet

2. **Add captain calculation method**
   - Add `_get_captain_for_hole()` method
   - Update `_initialize_hole()` to use new logic
   - Test with existing unit tests

3. **Update persistence** (optional)
   - Add migration for `toss_tees_order` column
   - Or rely on JSON state blob

4. **Update frontend components**
   - Modify SimpleScorekeeper to auto-populate captain
   - Add captain rotation display to MobileScorecard
   - Pass toss_tees_order through GamePage

5. **Add comprehensive tests**
   - Unit tests for captain calculation
   - Integration tests for full game
   - Frontend tests for component behavior

6. **Deploy and monitor**
   - Roll out changes
   - Monitor for any regression in captain assignment
   - Verify rotation matches rules throughout 18 holes

---

## Edge Cases to Handle

1. **Legacy games without toss_tees_order**
   - Fallback to old rotation logic
   - Log warning in debug mode

2. **Game pause/resume**
   - Ensure toss_tees_order persists in database
   - Verify captain recalculated correctly on resume

3. **Hoepfinger phase** (holes 17-18 in 4-man)
   - Goat chooses position, overrides normal rotation
   - Normal captain rotation applies before Goat choice
   - May need special handling

4. **Incomplete games**
   - If game stopped at hole 7, toss_tees_order still valid
   - Can resume and captain will be correct

---

## Rollback Plan

If issues discovered:
1. Revert changes to `_initialize_hole()` in `wolf_goat_pig_simulation.py`
2. Comment out use of `_get_captain_for_hole()`
3. Fall back to `_rotate_hitting_order()` for holes 2+
4. toss_tees_order can remain in database without causing issues
5. No frontend changes necessary to rollback

---
