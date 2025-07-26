# 🏗️ Code Refactoring TODO List

## 🎯 **Goal: Improve Architecture & Reduce Primitive Dependencies**

### **Priority 1: Core Domain Objects**

#### ✅ **1. Create Player Class**
- [x] **File**: `backend/app/domain/player.py`
- [x] **Replace**: Player dictionaries throughout codebase
- [x] **Features**:
  - `id`, `name`, `handicap`, `points`, `strength`
  - Methods: `get_handicap_category()`, `get_strength_level()`
  - Validation: handicap range, name requirements
- [x] **Update**: All methods that currently use `player["id"]` syntax
- [x] **Files to update**: `game_state.py`, `simulation.py`, `main.py`

#### ✅ **2. Create ShotResult Class** ✅ **COMPLETED**
- [x] **File**: `backend/app/domain/shot_result.py`
- [x] **Replace**: Shot dictionaries throughout codebase
- [x] **Features**:
  - `player`, `drive`, `lie`, `remaining`, `quality`, `penalty`
  - Methods: `get_position_quality()`, `get_scoring_probability()`
  - Validation: distance ranges, lie types
- [x] **Update**: All methods that currently use `shot_result["drive"]` syntax
- [x] **Files to update**: `simulation.py` (most methods)

**Completed Implementation Details:**
- ✅ Created comprehensive ShotResult class with enums for quality and lie types
- ✅ Added validation in `__post_init__` for distance ranges and valid values
- ✅ Implemented strategic analysis methods: `get_position_quality()`, `get_scoring_probability()`, `get_partnership_value()`
- ✅ Added realistic shot descriptions with `get_shot_description()`
- ✅ Updated `_simulate_tee_shots()` to create ShotResult objects instead of dictionaries
- ✅ Updated all probability calculation methods to work with both ShotResult objects and dictionaries (backwards compatibility)
- ✅ Updated main.py API endpoint to handle ShotResult serialization properly
- ✅ Maintained defensive coding with proper null checks and fallbacks [[memory:4277323]]

#### ✅ **3. Create Hole Class**
- [ ] **File**: `backend/app/domain/hole.py`
- [ ] **Replace**: Hole dictionaries and primitive arrays
- [ ] **Features**:
  - `number`, `par`, `yards`, `stroke_index`, `description`
  - Methods: `get_difficulty_factor()`, `is_par_3()`, `is_par_5()`
- [ ] **Update**: Course data structures and hole-related logic
- [ ] **Files to update**: `game_state.py`, `simulation.py`

### **Priority 2: State Management**

#### ✅ **4. Extract BettingState from GameState**
- [ ] **File**: `backend/app/state/betting_state.py`
- [ ] **Extract from**: `GameState` class
- [ ] **Features**:
  - `teams`, `base_wager`, `doubled_status`, `game_phase`
  - Methods: `request_partner()`, `accept_partner()`, `offer_double()`
  - Team management logic
- [ ] **Update**: `GameState` to use `BettingState` composition
- [ ] **Files to update**: `game_state.py`, `simulation.py`

#### ✅ **5. Create ShotState Class** 
- [x] **File**: `backend/app/state/shot_state.py`
- [x] **Extract from**: `GameState.shot_sequence`
- [x] **Features**:
  - `phase`, `current_player_index`, `completed_shots`, `pending_decisions`
  - Methods: `next_shot()`, `add_completed_shot()`, `has_next_shot()`
- [x] **Update**: Event-driven simulation logic
- [x] **Files to update**: `simulation.py`
- [x] **Completed**: Extracted shot sequence management into dedicated ShotState class with proper serialization/deserialization and backward compatibility

#### ✅ **6. Create PlayerManager Class**
- [ ] **File**: `backend/app/state/player_manager.py`
- [ ] **Extract from**: `GameState` player management
- [ ] **Features**:
  - `players`, `hitting_order`, `captain_id`
  - Methods: `setup_players()`, `rotate_captain()`, `get_player_by_id()`
- [ ] **Update**: Player-related operations
- [ ] **Files to update**: `game_state.py`, `simulation.py`

### **Priority 3: Service Layer**

#### ✅ **7. Create ProbabilityCalculator Service**
- [x] **File**: `backend/app/services/probability_calculator.py`
- [x] **Extract from**: `SimulationEngine` probability methods
- [x] **Features**:
  - `calculate_tee_shot_probabilities()`
  - `calculate_post_shot_probabilities()`
  - `calculate_betting_probabilities()`
  - `calculate_scoring_probabilities()`
- [x] **Update**: All probability calculation logic
- [x] **Files to update**: `simulation.py`
- [x] **Completed**: Extracted all probability calculation methods into dedicated ProbabilityCalculator service with proper static methods and helper functions

#### ✅ **8. Create ShotSimulator Service**
- [x] **File**: `backend/app/services/shot_simulator.py`
- [x] **Extract from**: `SimulationEngine` shot simulation methods
- [x] **Features**:
  - `simulate_tee_shot()`, `simulate_approach_shot()`
  - `simulate_player_score()`, `simulate_individual_tee_shot()`
- [x] **Update**: Shot execution logic
- [x] **Files to update**: `simulation.py`
- [x] **Completed**: Extracted all shot simulation methods into dedicated ShotSimulator service with proper static methods and helper functions

#### ✅ **9. Create BettingEngine Service**
- [x] **File**: `backend/app/services/betting_engine.py`
- [x] **Extract from**: `SimulationEngine` betting methods
- [x] **Features**:
  - `check_betting_opportunity()`, `execute_betting_decision()`
  - `make_computer_partnership_decision()`
- [x] **Update**: Betting decision logic
- [x] **Files to update**: `simulation.py`
- [x] **Completed**: Extracted all betting-related methods into dedicated BettingEngine service with proper static methods and helper functions

### **Priority 4: Data Structures**

#### ✅ **10. Use Dataclasses for Simple Structures**
- [x] **Files**: `backend/app/state/betting_state.py`, `backend/app/state/shot_state.py`, and all relevant simple state containers
- [x] **Refactor**: All simple state containers (BettingState, ShotState, and their fields) now use @dataclass with proper field defaults
- [x] **Update**: Serialization/deserialization logic and all methods remain compatible
- [x] **Completed**: All simple state containers are dataclasses, with logic and serialization preserved

#### ✅ **11. Create CourseManager Class**
- [x] **File**: `backend/app/state/course_manager.py`
- [x] **Extract from**: `GameState` course management
- [x] **Features**:
  - Course CRUD operations
  - Hole management
  - Course statistics
- [x] **Update**: Course-related operations
- [x] **Files to update**: `game_state.py`, `simulation.py`, `main.py`
- [x] **Completed**: Extracted all course-related state and logic into dedicated CourseManager class with proper dataclass structure and serialization

### **Priority 5: Integration & Testing**

#### ✅ **12. Update SimulationEngine**
- [ ] **Refactor**: Use new domain objects and services
- [ ] **Simplify**: Remove primitive dictionary handling
- [ ] **Update**: Method signatures to use proper types
- [ ] **Files to update**: `simulation.py`

#### ✅ **13. Update GameState**
- [ ] **Compose**: Use new state classes
- [ ] **Simplify**: Remove duplicated logic
- [ ] **Update**: Serialization/deserialization
- [ ] **Files to update**: `game_state.py`

#### ✅ **14. Update API Endpoints**
- [ ] **Refactor**: Use new domain objects in responses
- [ ] **Update**: Pydantic models for new structures
- [ ] **Test**: Ensure API compatibility
- [ ] **Files to update**: `main.py`

#### ✅ **15. Add Type Hints**
- [ ] **Add**: Comprehensive type hints throughout
- [ ] **Use**: New domain classes in type annotations
- [ ] **Validate**: Type safety with mypy
- [ ] **Files to update**: All Python files

### **Priority 6: Testing & Validation**

#### ✅ **16. Create Unit Tests**
- [ ] **Test**: New domain classes
- [ ] **Test**: Service layer methods
- [ ] **Test**: State management
- [ ] **Files to create**: `tests/test_domain/`, `tests/test_services/`

#### ✅ **17. Integration Tests**
- [ ] **Test**: End-to-end simulation flow
- [ ] **Test**: API endpoint functionality
- [ ] **Test**: State persistence
- [ ] **Files to create**: `tests/test_integration/`

#### ✅ **18. Performance Testing**
- [ ] **Benchmark**: New vs old architecture
- [ ] **Profile**: Memory usage improvements
- [ ] **Validate**: No regression in performance
- [ ] **Files to create**: `tests/test_performance/`

## 🎯 **Implementation Order**

1. **Start with Domain Objects** (1-3) - Foundation
2. **Extract State Management** (4-6) - Clean separation
3. **Create Service Layer** (7-9) - Business logic
4. **Add Data Structures** (10-11) - Type safety
5. **Integrate Everything** (12-14) - Connect the pieces
6. **Add Type Hints** (15) - Code quality
7. **Test Thoroughly** (16-18) - Validation

## 🎯 **Success Criteria**

- [ ] **No more `KeyError` exceptions** from dictionary access
- [ ] **Type safety** throughout the codebase
- [ ] **Reduced coupling** between components
- [ ] **Improved testability** of individual components
- [ ] **Better maintainability** and readability
- [ ] **No performance regression**

## 🎯 **Files to Create**

```
backend/app/
├── domain/
│   ├── __init__.py
│   ├── player.py
│   ├── shot_result.py
│   ├── hole.py
│   └── data_structures.py
├── state/
│   ├── __init__.py
│   ├── betting_state.py
│   ├── shot_state.py
│   └── player_manager.py
├── services/
│   ├── __init__.py
│   ├── probability_calculator.py
│   ├── shot_simulator.py
│   └── betting_engine.py
└── domain/
    └── course_manager.py
```

## 🎯 **Migration Strategy**

1. **Create new classes** alongside existing code
2. **Gradually migrate** methods one at a time
3. **Update tests** to use new structures
4. **Remove old code** once migration is complete
5. **Validate** no functionality is lost

---

**Estimated Time**: 2-3 days for complete refactoring
**Risk Level**: Medium (significant changes but well-contained)
**Benefits**: Much more maintainable and robust codebase 