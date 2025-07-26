# 🏗️ Wolf Goat Pig Golf Simulation - Application Architecture

## 📋 Table of Contents
1. [Overview](#overview)
2. [Architecture Layers](#architecture-layers)
3. [Domain Objects](#domain-objects)
4. [State Management](#state-management)
5. [Services](#services)
6. [API Layer](#api-layer)
7. [Database Models](#database-models)
8. [Frontend Components](#frontend-components)
9. [Testing Infrastructure](#testing-infrastructure)
10. [Data Flow](#data-flow)
11. [Conventions & Patterns](#conventions--patterns)

---

## 🎯 Overview

The Wolf Goat Pig golf simulation is a sophisticated web application that simulates the strategic golf betting game. The architecture follows a **Domain-Driven Design (DDD)** approach with clear separation of concerns across multiple layers.

### Core Architecture Principles
- **Domain-Driven Design**: Business logic encapsulated in domain objects
- **Single Responsibility**: Each class has one clear purpose
- **Composition over Inheritance**: Uses composition for complex behaviors
- **Defensive Programming**: Robust error handling and validation
- **Event-Driven Simulation**: Chronological, interactive game flow

---

## 🏛️ Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React.js)                      │
├─────────────────────────────────────────────────────────────┤
│                    API Layer (FastAPI)                      │
├─────────────────────────────────────────────────────────────┤
│                   Services Layer                            │
├─────────────────────────────────────────────────────────────┤
│                   State Management                          │
├─────────────────────────────────────────────────────────────┤
│                   Domain Objects                            │
├─────────────────────────────────────────────────────────────┤
│                   Database (SQLAlchemy)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎮 Domain Objects

### Core Domain Entities

#### `Player` (`backend/app/domain/player.py`)
**Purpose**: Represents a golfer in the simulation
```python
@dataclass
class Player:
    id: str
    name: str
    handicap: float
    points: int = 0
    strength: Optional[str] = None
    hole_scores: dict = field(default_factory=dict)
    float_used: bool = False
    last_points: int = 0
```

**Key Methods**:
- `get_handicap_category()` → `HandicapCategory`
- `get_strength_level()` → `StrengthLevel`
- `get_expected_drive_distance()` → `int`
- `get_shot_quality_weights()` → `list[float]`
- `add_points(points: int)` → `None`
- `use_float()` → `bool`
- `to_dict()` → `dict`
- `from_dict(data: dict)` → `Player`

**Enums**:
- `HandicapCategory`: SCRATCH, LOW, MID, HIGH, BEGINNER
- `StrengthLevel`: EXCELLENT, GOOD, AVERAGE, BELOW_AVERAGE, POOR

#### `ShotResult` (`backend/app/domain/shot_result.py`)
**Purpose**: Represents the result of a golf shot
```python
@dataclass
class ShotResult:
    player: Player
    drive: int
    lie: str
    remaining: int
    shot_quality: str
    penalty: int = 0
    hole_number: Optional[int] = None
    shot_number: Optional[int] = None
    wind_factor: Optional[float] = None
    pressure_factor: Optional[float] = None
```

**Key Methods**:
- `get_position_quality()` → `Dict[str, Any]`
- `get_scoring_probability()` → `Dict[str, Any]`
- `get_partnership_value()` → `Dict[str, Any]`
- `get_strategic_implications()` → `Dict[str, Any]`
- `get_shot_description()` → `str`

**Enums**:
- `ShotQuality`: EXCELLENT, GOOD, AVERAGE, POOR, TERRIBLE
- `LieType`: FAIRWAY, ROUGH, SAND, WATER, OUT_OF_BOUNDS

---

## 🗂️ State Management

### Game State Components

#### `GameState` (`backend/app/game_state.py`)
**Purpose**: Main orchestrator for game state and coordination
```python
class GameState:
    def __init__(self):
        self.player_manager: PlayerManager
        self.betting_state: BettingState
        self.course_manager: CourseManager
        self.shot_state: ShotState
        self.current_hole: int
        self.hole_scores: Dict[str, Optional[int]]
        self.game_status_message: str
```

**Key Methods**:
- `setup_players(players: list[dict], course_name: str)` → `None`
- `dispatch_action(action: str, payload: dict)` → `None`
- `next_hole()` → `None`
- `calculate_hole_points()` → `Dict[str, int]`
- `_serialize()` → `dict`
- `_deserialize(data: dict)` → `None`

#### `PlayerManager` (`backend/app/state/player_manager.py`)
**Purpose**: Manages players, hitting order, and captain rotation
```python
class PlayerManager:
    def __init__(self, players: Optional[List[Player]] = None):
        self.players: List[Player]
        self.hitting_order: List[str]
        self.captain_id: Optional[str]
```

**Key Methods**:
- `setup_players(players: List[Player])` → `None`
- `rotate_captain()` → `None`
- `get_player_by_id(player_id: str)` → `Optional[Player]`

#### `BettingState` (`backend/app/state/betting_state.py`)
**Purpose**: Manages betting logic, teams, and wagering
```python
@dataclass
class BettingState:
    teams: Dict[str, Any] = field(default_factory=dict)
    base_wager: int = 1
    doubled_status: bool = False
    game_phase: str = "Regular"
```

**Key Methods**:
- `request_partner(captain_id: str, partner_id: str)` → `Dict[str, Any]`
- `accept_partner(partner_id: str)` → `Dict[str, Any]`
- `go_solo(captain_id: str)` → `Dict[str, Any]`
- `offer_double(team_id: str)` → `Dict[str, Any]`
- `accept_double(team_id: str)` → `Dict[str, Any]`

#### `CourseManager` (`backend/app/state/course_manager.py`)
**Purpose**: Manages course data and hole information
```python
@dataclass
class CourseManager:
    selected_course: Optional[str] = None
    hole_stroke_indexes: List[int] = field(default_factory=list)
    hole_pars: List[int] = field(default_factory=list)
    hole_yards: List[int] = field(default_factory=list)
    course_data: Dict[str, Any] = field(default_factory=lambda: DEFAULT_COURSES.copy())
```

**Key Methods**:
- `load_course(course_name: str)` → `None`
- `get_hole_info(hole_number: int)` → `Dict[str, Any]`
- `get_current_hole_info()` → `Dict[str, Any]`
- `get_courses()` → `Dict[str, Any]`

#### `ShotState` (`backend/app/state/shot_state.py`)
**Purpose**: Manages shot-by-shot simulation state
```python
@dataclass
class ShotState:
    phase: str = "tee_shots"
    current_player_index: int = 0
    completed_shots: List[ShotResult] = field(default_factory=list)
    pending_decisions: List[Dict[str, Any]] = field(default_factory=list)
```

**Key Methods**:
- `reset_for_hole()` → `None`
- `add_completed_shot(shot: ShotResult)` → `None`
- `get_current_player_id()` → `Optional[str]`
- `to_dict()` → `Dict[str, Any]`
- `from_dict(data: Dict[str, Any])` → `None`

---

## ⚙️ Services

### Business Logic Services

#### `SimulationEngine` (`backend/app/simulation.py`)
**Purpose**: Orchestrates simulation logic and AI decision-making
```python
class SimulationEngine:
    def __init__(self):
        self.computer_players: List[ComputerPlayer] = []
```

**Key Methods**:
- `setup_simulation(human_player: Dict, computer_configs: List[Dict], course_name: str)` → `GameState`
- `simulate_hole(game_state: GameState, human_decisions: Dict)` → `Tuple[GameState, List[str], Optional[Dict]]`
- `run_monte_carlo_simulation(...)` → `MonteCarloResults`
- `get_next_shot_event(game_state: GameState)` → `Optional[Dict]`
- `execute_shot_event(game_state: GameState, shot_event: Dict)` → `Tuple[GameState, Dict, Dict]`

#### `ComputerPlayer` (`backend/app/simulation.py`)
**Purpose**: AI player with personality-driven decision making
```python
class ComputerPlayer:
    def __init__(self, player_id: str, name: str, handicap: float, personality: str = "balanced"):
        self.player_id: str
        self.name: str
        self.handicap: float
        self.personality: str
```

**Key Methods**:
- `should_accept_partnership(captain_handicap: float, game_state: GameState)` → `bool`
- `should_offer_double(game_state: GameState)` → `bool`
- `should_accept_double(game_state: GameState)` → `bool`
- `should_go_solo(game_state: GameState)` → `bool`

#### `ShotSimulator` (`backend/app/services/shot_simulator.py`)
**Purpose**: Simulates individual golf shots with realistic outcomes
```python
class ShotSimulator:
    @staticmethod
    def simulate_individual_tee_shot(player: Player, game_state: GameState) -> ShotResult
    @staticmethod
    def simulate_approach_shot(player: Player, distance: int, game_state: GameState) -> ShotResult
    @staticmethod
    def simulate_player_score(handicap: float, par: int, hole_number: int) -> int
```

#### `ProbabilityCalculator` (`backend/app/services/probability_calculator.py`)
**Purpose**: Calculates probabilities for shots, betting, and outcomes
```python
class ProbabilityCalculator:
    @staticmethod
    def calculate_tee_shot_probabilities(player: Player, game_state: GameState) -> Dict[str, Any]
    @staticmethod
    def calculate_betting_probabilities(game_state: GameState, decision: Dict[str, Any]) -> Dict[str, Any]
    @staticmethod
    def calculate_scoring_probabilities(shot_result: ShotResult) -> Dict[str, Any]
```

#### `BettingEngine` (`backend/app/services/betting_engine.py`)
**Purpose**: Handles betting decisions and team formation
```python
class BettingEngine:
    @staticmethod
    def check_betting_opportunity(game_state: GameState, shot_result: Dict[str, Any]) -> Optional[Dict[str, Any]]
    @staticmethod
    def execute_betting_decision(game_state: GameState, decision: Dict[str, Any], betting_probs: Dict[str, Any]) -> Tuple[GameState, Dict[str, Any]]
    @staticmethod
    def make_computer_partnership_decision(captain: ComputerPlayer, partner: ComputerPlayer, game_state: GameState) -> bool
```

---

## 🌐 API Layer

### FastAPI Application (`backend/app/main.py`)

#### Response Models
```python
class ShotEventResponse(BaseModel):
    status: str
    shot_event: Optional[dict]
    shot_result: Optional[dict]
    probabilities: Optional[dict]
    betting_opportunity: Optional[dict]
    game_state: dict
    next_shot_available: bool

class BettingDecisionResponse(BaseModel):
    status: str
    decision: dict
    decision_result: dict
    betting_probabilities: dict
    game_state: dict

class SimulationSetup(BaseModel):
    human_player: dict
    computer_players: List[ComputerPlayerConfig]
    course_name: Optional[str] = None
```

#### Key Endpoints
- `POST /simulation/setup` - Initialize simulation
- `POST /simulation/play-hole` - Play a complete hole
- `POST /simulation/next-shot` - Execute next shot event
- `POST /simulation/betting-decision` - Make betting decision
- `POST /simulation/monte-carlo` - Run Monte Carlo analysis
- `GET /game/state` - Get current game state
- `POST /game/action` - Execute game action
- `GET /courses` - List available courses

#### Custom Middleware
```python
class WildcardCORSMiddleware(BaseCORSMiddleware):
    """Handles dynamic Vercel/Render subdomains with regex patterns"""
```

---

## 🗄️ Database Models

### SQLAlchemy Models (`backend/app/models.py`)

#### `Rule` (Base)
```python
class Rule(Base):
    __tablename__ = "rules"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True)
    description = Column(String)
```

#### `Course` (Base)
```python
class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    total_par = Column(Integer)
    total_yards = Column(Integer)
    course_rating = Column(Float, nullable=True)
    slope_rating = Column(Float, nullable=True)
    holes_data = Column(JSON)
```

#### `GameStateModel` (Base)
```python
class GameStateModel(Base):
    __tablename__ = "game_states"
    id = Column(Integer, primary_key=True, index=True)
    game_data = Column(JSON)
    created_at = Column(String)
    updated_at = Column(String)
```

#### `SimulationResult` (Base)
```python
class SimulationResult(Base):
    __tablename__ = "simulation_results"
    id = Column(Integer, primary_key=True, index=True)
    simulation_type = Column(String)
    parameters = Column(JSON)
    results = Column(JSON)
    created_at = Column(String)
```

---

## 🎨 Frontend Components

### React Components (`frontend/src/`)

#### Core Components
- `App.js` - Main application component with routing
- `GameSetupForm.js` - Player and course setup interface
- `SimulationMode.js` - Interactive simulation interface
- `MonteCarloSimulation.js` - Monte Carlo analysis interface
- `CourseManager.js` - Course management interface

#### Key Features
- **Interactive Simulation**: Real-time shot-by-shot gameplay
- **Monte Carlo Analysis**: Statistical analysis with configurable parameters
- **Course Management**: Import, edit, and manage golf courses
- **Responsive Design**: Mobile-friendly interface
- **Real-time Updates**: Live game state synchronization

---

## 🧪 Testing Infrastructure

### Test Categories

#### Unit Tests
- `test_simulation.py` - Simulation engine tests
- `test_player_class.py` - Player domain object tests
- `test_betting_state.py` - Betting state tests

#### Integration Tests
- `test_monte_carlo_api.py` - API endpoint tests
- `test_simulation_courses.py` - Course integration tests

#### BDD Tests (`tests/`)
- `monte_carlo_simulation.feature` - Gherkin scenarios
- `course_management.feature` - Course management scenarios
- `monte_carlo_steps.py` - Step definitions

#### Test Utilities
- `conftest.py` - Pytest fixtures and test setup
- `BDDTestHelper` - Browser automation helper
- `TestServers` - Backend/frontend server management

---

## 🔄 Data Flow

### Simulation Flow
```
1. Setup → GameState.setup_players()
2. Hole Start → SimulationEngine.simulate_hole()
3. Tee Shots → ShotSimulator.simulate_individual_tee_shot()
4. Captain Decision → BettingEngine.check_betting_opportunity()
5. Partnership Response → BettingEngine.execute_betting_decision()
6. Approach Shots → ShotSimulator.simulate_approach_shot()
7. Scoring → GameState.calculate_hole_points()
8. Hole Complete → GameState.next_hole()
```

### API Request Flow
```
Frontend → FastAPI Endpoint → Service Layer → Domain Objects → State Management → Database
```

### State Persistence Flow
```
GameState → _serialize() → JSON → Database → _deserialize() → GameState
```

---

## 📏 Conventions & Patterns

### Naming Conventions
- **Classes**: PascalCase (`GameState`, `PlayerManager`)
- **Methods**: snake_case (`setup_players`, `calculate_hole_points`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_PLAYERS`, `DEFAULT_COURSES`)
- **Files**: snake_case (`game_state.py`, `player_manager.py`)

### Design Patterns
- **Composition**: `GameState` composes `PlayerManager`, `BettingState`, etc.
- **Factory**: `Player.from_dict()`, `ShotResult.from_dict()`
- **Strategy**: `ComputerPlayer` personalities for AI decision-making
- **Observer**: Event-driven simulation with state updates
- **Repository**: Database models with CRUD operations

### Error Handling
- **Defensive Programming**: All methods validate inputs
- **Graceful Degradation**: Fallback values for missing data
- **Comprehensive Logging**: Detailed error context
- **User-Friendly Messages**: Clear error descriptions

### Performance Patterns
- **Lazy Loading**: Database connections and heavy computations
- **Caching**: Course data and player configurations
- **Batch Operations**: Monte Carlo simulations
- **Async Operations**: API endpoints and database operations

---

## 🎯 Architecture Benefits

### Maintainability
- **Clear Separation**: Each layer has distinct responsibilities
- **Domain Focus**: Business logic isolated in domain objects
- **Testability**: Services and components easily unit tested

### Scalability
- **Modular Design**: Components can be enhanced independently
- **Service Layer**: Business logic can be distributed
- **Database Abstraction**: Easy to switch data stores

### Flexibility
- **Event-Driven**: Easy to add new simulation events
- **Plugin Architecture**: New AI personalities and shot types
- **Configuration-Driven**: Course data and game rules externalized

### Reliability
- **Defensive Coding**: Robust error handling throughout
- **State Management**: Consistent game state across operations
- **Validation**: Comprehensive input validation at all layers

---

This architecture provides a solid foundation for the Wolf Goat Pig golf simulation, enabling both current functionality and future enhancements while maintaining code quality and system reliability. 