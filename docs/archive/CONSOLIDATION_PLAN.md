# Wolf Goat Pig - Class Consolidation Plan

## Executive Decision: WolfGoatPigSimulation is the Single Source of Truth

**Target Architecture**: One unified game engine (`WolfGoatPigSimulation`) with:
- ✅ Full game rules (already has this)
- ✅ Database persistence (adding from GameState)
- ✅ Consolidated classes (merging duplicates)

## Phase 1: Add Persistence to WolfGoatPigSimulation

### 1.1 Add Persistence Mixin
Create `backend/app/mixins/persistence_mixin.py`:
```python
class PersistenceMixin:
    def _save_to_db(self): ...
    def _load_from_db(self): ...
    def _serialize(self): ...
    def _deserialize(self, data): ...
```

### 1.2 Make WolfGoatPigSimulation inherit PersistenceMixin
```python
class WolfGoatPigSimulation(PersistenceMixin):
    def __init__(self, game_id=None, player_count=4, players=None):
        self.game_id = game_id or str(uuid.uuid4())
        self._db_session = SessionLocal()
        self._load_from_db()  # Load existing or start fresh
        # ... rest of initialization
```

## Phase 2: Consolidate Duplicate Classes

### 2.1 BettingState Consolidation

**Keep**: `backend/app/domain/betting_state.py` (simple 13-field version)
**Deprecate**: `backend/app/models/odds_calculator.py:BettingState` (4-field version)

**Action**: Update OddsCalculator to use domain.betting_state.BettingState

### 2.2 HoleState Consolidation

**Keep**: `backend/app/wolf_goat_pig_simulation.py:WGPHoleState` (rich game simulation)
**Rename to**: `HoleState` (drop WGP prefix)
**Deprecate**: `backend/app/models/odds_calculator.py:HoleState`

**Action**: Update OddsCalculator to use WGPHoleState

### 2.3 PlayerState Consolidation

**Keep**: `backend/app/wolf_goat_pig_simulation.py:WGPPlayer` (full player model)
**Rename to**: `Player` (drop WGP prefix)
**Deprecate**:
- `backend/app/models/odds_calculator.py:PlayerState`
- `backend/app/domain/player.py:Player` (merge useful bits into WGPPlayer)

**Action**: WGPPlayer becomes the canonical Player class

## Phase 3: Update Main.py to Use Unified System

### 3.1 Replace Global Instances
```python
# OLD (main.py lines 50-58)
game_state = GameState()
wgp_simulation = WolfGoatPigSimulation(player_count=4)

# NEW
game_engine = None  # Will be WolfGoatPigSimulation instance per game
games: Dict[str, WolfGoatPigSimulation] = {}
```

### 3.2 Update All Handlers
Every handler that currently uses either `game_state` or `wgp_simulation` will use `game_engine`:

```python
@app.post("/games/create")
async def create_game(...):
    game_engine = WolfGoatPigSimulation(
        player_count=player_count,
        players=wgp_players
    )
    games[game_engine.game_id] = game_engine
    return {"game_id": game_engine.game_id, ...}

@app.post("/games/{game_id}/action")
async def unified_action(game_id: str, action: ActionRequest):
    game_engine = games.get(game_id)
    if not game_engine:
        # Try loading from DB
        game_engine = WolfGoatPigSimulation(game_id=game_id)
        games[game_id] = game_engine

    # All actions go through game_engine
    return await handle_action(game_engine, action)
```

## Phase 4: Deprecate GameState

### 4.1 Mark as Deprecated
Add to `game_state.py`:
```python
import warnings

warnings.warn(
    "GameState is deprecated. Use WolfGoatPigSimulation instead.",
    DeprecationWarning,
    stacklevel=2
)
```

### 4.2 Create Migration Path
```python
# In wolf_goat_pig_simulation.py
@classmethod
def from_game_state(cls, old_game_state: GameState):
    """Migrate from old GameState to new unified system"""
    return cls(
        game_id=old_game_state.game_id,
        player_count=len(old_game_state.player_manager.players),
        players=old_game_state.player_manager.players
    )
```

## Phase 5: Clean Up Duplicate Logic

### 5.1 Stroke Calculation
**Keep**: `WGPHoleState._calculate_strokes_received()` (most complete)
**Remove**:
- `GameState.get_player_strokes()`
- `OddsCalculator.calculate_strokes_received()`

### 5.2 Shot Tracking
**Decision needed**: Which system to keep?
- Option A: Keep `ball_positions` (physical) + add phase tracking
- Option B: Keep `ShotState` (phases) + add position tracking
- Option C: Merge both into unified ShotTracker

**Recommendation**: Option A - Physical positions are more fundamental

### 5.3 Points Distribution
**Keep**: `WolfGoatPigSimulation.distribute_hole_points()` (has Karl Marx rule)
**Remove**: Duplicate logic in GameState

## Execution Order (Critical!)

1. ✅ Create PersistenceMixin
2. ✅ Add persistence to WolfGoatPigSimulation
3. ✅ Test: Create game, save, load, verify state preserved
4. ✅ Consolidate BettingState (update imports in OddsCalculator)
5. ✅ Consolidate HoleState (rename WGPHoleState → HoleState)
6. ✅ Consolidate PlayerState (rename WGPPlayer → Player)
7. ✅ Update main.py handlers one by one
8. ✅ Test each handler after update
9. ✅ Mark GameState as deprecated
10. ✅ Remove duplicate stroke/shot/points logic

## Success Criteria

- [ ] Can create game using only WolfGoatPigSimulation
- [ ] Game state persists across server restart
- [ ] All betting actions work (Float, Double, Option, Flush)
- [ ] All handlers use single game engine
- [ ] No more duplicate class definitions
- [ ] Tests pass
- [ ] Old games can be migrated

## Rollback Plan

If something breaks:
1. Git checkout previous commit
2. Fix issue in new branch
3. Test thoroughly before merging

Keep GameState.py file for 2 release cycles before deleting (deprecation period).
