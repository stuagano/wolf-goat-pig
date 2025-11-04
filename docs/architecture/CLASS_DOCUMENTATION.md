# Wolf Goat Pig - Class Documentation

Comprehensive documentation of all classes in the Wolf Goat Pig codebase, organized by category.

---

## Table of Contents

1. [Core Game Engine](#core-game-engine)
2. [State Management](#state-management)
3. [Domain Models](#domain-models)
4. [Validators](#validators)
5. [Data Models (SQLAlchemy)](#data-models-sqlalchemy)
6. [API Schemas (Pydantic)](#api-schemas-pydantic)
7. [Services](#services)
8. [Mixins/Utilities](#mixinsutilities)
9. [Enums](#enums)
10. [Analytics & Insights](#analytics--insights)
11. [Badge System](#badge-system)
12. [Gaps & Recommendations](#gaps--recommendations)
13. [DRY Opportunities](#dry-opportunities)

---

## Core Game Engine

### WolfGoatPigSimulation
**Location**: `/backend/app/wolf_goat_pig_simulation.py`

**Purpose**: Main game engine for Wolf Goat Pig, managing complete game lifecycle from setup through completion.

**Key Responsibilities**:
- Initialize games with player configurations
- Manage hole-by-hole gameplay progression
- Execute shots using Monte Carlo simulation
- Handle partnership formations and betting
- Track game state and timeline events
- Persist game state to database via PersistenceMixin

**Dependencies**:
- PersistenceMixin
- Player (domain model)
- HoleState, TeamFormation, BettingState
- CourseManager
- Database models (GameStateModel, GameRecord)

**Usage**:
- Created per-game instance in main.py
- Managed in `active_games` dictionary
- Loaded from database when game resumes

---

### MonteCarloEngine
**Location**: `/backend/app/services/monte_carlo.py`

**Purpose**: Simulates golf shots using Monte Carlo methods to generate realistic shot outcomes.

**Key Responsibilities**:
- Run statistical simulations for shot outcomes
- Calculate probabilities for different shot results
- Generate realistic score distributions
- Provide odds calculations for partnerships

**Dependencies**:
- SimulationParams (dataclass)
- Player handicap calculations

**Usage**:
- Used by WolfGoatPigSimulation for shot execution
- Standalone service for "What-If" analysis
- Odds calculator service

---

## State Management

### CourseManager
**Location**: `/backend/app/state/course_manager.py`

**Purpose**: Manages golf course data including hole information, difficulty factors, and course selection.

**Key Responsibilities**:
- Load and store course data (holes, pars, yardages)
- Calculate hole difficulty factors
- Provide course statistics
- CRUD operations for courses
- Maintain default courses

**Dependencies**:
- Wing Point course data
- DEFAULT_COURSES dictionary

**Usage**:
- Global instance in main.py
- Shared across all games for course information

---

### PlayerManager
**Location**: `/backend/app/state/player_manager.py`

**Purpose**: Manages player roster, hitting order rotation, and captain selection.

**Key Responsibilities**:
- Store player list and state
- Rotate hitting order between holes
- Track captain for each hole
- Retrieve players by ID

**Dependencies**:
- Player (domain model)

**Usage**:
- Component of WolfGoatPigSimulation
- Handles player-related state

---

### ShotState
**Location**: `/backend/app/state/shot_state.py`

**Purpose**: Tracks chronological shot sequence during hole play with phase management.

**Key Responsibilities**:
- Track current shot phase (tee shots, approach shots)
- Maintain completed shot history
- Manage pending decisions
- Advance through shot sequences

**Dependencies**:
- ShotStateEntry (dataclass)

**Usage**:
- Component of HoleState
- Tracks shot-by-shot progression

---

### HoleState
**Location**: `/backend/app/wolf_goat_pig_simulation.py`

**Purpose**: Complete state for a single hole including shots, betting, teams, and progression.

**Key Responsibilities**:
- Track ball positions for all players
- Manage betting state and wagers
- Store team formations
- Calculate stroke advantages based on handicaps
- Track hole completion and scores
- Manage partnership deadlines and invitation windows

**Dependencies**:
- TeamFormation, BettingState, BallPosition
- StrokeAdvantage, Player

**Usage**:
- Created per-hole within WolfGoatPigSimulation
- Stored in game timeline

---

## Domain Models

### Player
**Location**: `/backend/app/domain/player.py`

**Purpose**: Represents a golfer with handicap, scoring attributes, and game state.

**Key Responsibilities**:
- Store player ID, name, handicap
- Track points/quarters
- Manage float usage
- Record hole scores
- Calculate strength levels and shot quality weights
- Convert to/from dictionary for serialization

**Dependencies**:
- HandicapCategory, StrengthLevel (enums)

**Usage**:
- Core entity throughout game engine
- Used in simulations, state management, and scoring

---

### ShotResult
**Location**: `/backend/app/domain/shot_result.py`

**Purpose**: Represents the result of a golf shot with distance, accuracy, and strategic implications.

**Key Responsibilities**:
- Store shot outcome (drive, lie, remaining distance)
- Calculate position quality scores
- Determine scoring probabilities
- Analyze partnership value
- Generate shot descriptions
- Provide strategic implications

**Dependencies**:
- Player, ShotQuality, LieType (enums)
- ShotRangeAnalyzer

**Usage**:
- Created after each shot in simulation
- Used for partnership decisions
- Displayed in UI for shot results

---

### ShotRange
**Location**: `/backend/app/domain/shot_range_analysis.py`

**Purpose**: Represents a possible shot option with poker-style risk/reward metrics.

**Key Responsibilities**:
- Store shot type and probabilities
- Calculate expected value (EV)
- Track fold equity and bluff frequency
- Compute pot odds requirements

**Dependencies**:
- ShotType, RiskProfile (enums)

**Usage**:
- Generated by ShotRangeAnalyzer
- Used for strategic shot selection advice

---

### ShotRangeMatrix
**Location**: `/backend/app/domain/shot_range_analysis.py`

**Purpose**: Matrix of all available shot ranges for a given situation with GTO and exploitative recommendations.

**Key Responsibilities**:
- Calculate all possible shot ranges
- Determine game theory optimal (GTO) play
- Provide exploitative adjustments
- Generate 3-bet ranges
- Calculate range distributions

**Dependencies**:
- ShotRange, ShotType, RiskProfile

**Usage**:
- Created by ShotRangeAnalyzer
- Provides comprehensive shot analysis

---

### ShotRangeAnalyzer
**Location**: `/backend/app/domain/shot_range_analysis.py`

**Purpose**: Analyzes shot selection using poker-style range analysis.

**Key Responsibilities**:
- Generate complete shot analysis
- Determine optimal player style
- Provide strategic advice
- Generate comparisons and recommendations

**Dependencies**:
- ShotRangeMatrix, ShotRange, RiskProfile

**Usage**:
- Standalone analysis service
- Called from ShotResult for next shot planning

---

### CourseImportData
**Location**: `/backend/app/course_import.py`

**Purpose**: Data structure for imported course information from external sources.

**Key Responsibilities**:
- Store course metadata (name, rating, slope)
- Hold hole-by-hole data
- Track import source and timestamps

**Dependencies**: None (dataclass)

**Usage**:
- Return type from CourseImporter methods
- Passed to database save operations

---

### CourseImporter
**Location**: `/backend/app/course_import.py`

**Purpose**: Imports golf course data from external APIs (USGA, GHIN, GolfNow, TheGrint).

**Key Responsibilities**:
- Search multiple course databases
- Parse different API formats
- Import from JSON files
- Save course data to database
- Handle API keys and authentication

**Dependencies**:
- CourseImportData
- Course (SQLAlchemy model)
- httpx for HTTP requests

**Usage**:
- Manual course import operations
- Seeding course database
- Future automated course sync

---

## Validators

### ValidationError (Base Exception)
**Location**: `/backend/app/validators/exceptions.py`

**Purpose**: Base exception class for all validation errors with structured error information.

**Key Responsibilities**:
- Store error message, field name, and additional details
- Convert exceptions to API-friendly dictionaries
- Provide consistent error format across validators

**Subclasses**:
- GameStateValidationError
- BettingValidationError
- HandicapValidationError
- PartnershipValidationError

**Usage**:
- Raised by all validator classes
- Caught in try/except blocks in game engine
- Converted to HTTP responses in API endpoints

**Example**:
```python
try:
    HandicapValidator.validate_handicap(player.handicap)
except HandicapValidationError as e:
    return {"error": e.message, "field": e.field, "details": e.details}
```

---

### HandicapValidator
**Location**: `/backend/app/validators/handicap_validator.py`

**Purpose**: Validates handicap calculations and ensures USGA compliance for all handicap-related operations.

**Key Responsibilities**:
- Validate handicaps within USGA range (0-54)
- Calculate strokes received using USGA stroke allocation rules
- Validate stroke indexes (1-18)
- Calculate net scores from gross scores
- Validate course ratings and slope ratings
- Calculate course handicaps from handicap index
- Validate stroke allocation across all holes
- Categorize handicaps into skill levels
- Validate team handicap balance

**Key Methods**:
- `validate_handicap(handicap, field_name)` - Validate handicap range
- `validate_stroke_index(stroke_index, field_name)` - Validate stroke index
- `calculate_strokes_received(course_handicap, stroke_index)` - USGA stroke allocation
- `calculate_net_score(gross_score, strokes_received)` - Net score calculation
- `validate_course_rating(course_rating, slope_rating)` - Course rating validation
- `calculate_course_handicap(handicap_index, slope, course_rating, par)` - Full USGA formula
- `validate_stroke_allocation(players_handicaps, hole_stroke_indexes)` - Full validation
- `get_handicap_category(handicap)` - Categorize skill level
- `validate_team_handicaps(team1, team2, max_difference)` - Team balance

**Constants**:
- MIN_HANDICAP = 0.0
- MAX_HANDICAP = 54.0
- MIN_STROKE_INDEX = 1
- MAX_STROKE_INDEX = 18

**Dependencies**: None (pure validation logic)

**Usage**:
- Used in WolfGoatPigSimulation at 7 integration points
- Validates player handicaps on game initialization
- Calculates strokes received during shot execution
- Ensures USGA compliance throughout game

**Integration Points** (wolf_goat_pig_simulation.py):
- Line 664-671: Player handicap validation in `__init__`
- Line 212-249: Stroke calculation in shot execution
- Line 255-277: Net score calculation

**Example**:
```python
# Validate handicap
HandicapValidator.validate_handicap(15.2, "player_handicap")

# Calculate strokes using USGA rules
strokes = HandicapValidator.calculate_strokes_received(
    course_handicap=15.2,
    stroke_index=5,
    validate=True
)

# Calculate net score
net = HandicapValidator.calculate_net_score(
    gross_score=6,
    strokes_received=1
)
```

---

### BettingValidator
**Location**: `/backend/app/validators/betting_validator.py`

**Purpose**: Validates Wolf Goat Pig betting rules including doubles, redoubles, and special betting actions.

**Key Responsibilities**:
- Validate base wager amounts
- Enforce double/redouble rules
- Validate "The Duncan" special rule
- Validate carry-over rules
- Calculate total wager multipliers
- Ensure betting actions occur at proper times

**Key Methods**:
- `validate_base_wager(wager, min_wager, max_wager)` - Wager range validation
- `validate_double(already_doubled, wagering_closed, partnership_formed)` - Double rules
- `validate_redouble(already_doubled, already_redoubled, wagering_closed)` - Redouble rules
- `validate_duncan(is_captain, partnership_formed, tee_shots_complete)` - Duncan validation
- `validate_carry_over(holes_remaining, current_carry_over)` - Carry-over rules
- `calculate_wager_multiplier(doubled, redoubled, duncan, other_rules)` - Total multiplier

**Constants**:
- DEFAULT_MIN_WAGER = 0.25
- DEFAULT_MAX_WAGER = 10.0
- DOUBLE_MULTIPLIER = 2.0
- REDOUBLE_MULTIPLIER = 2.0

**Dependencies**: None (pure validation logic)

**Usage**:
- Used in WolfGoatPigSimulation for betting actions
- Validates doubles/redoubles before applying
- Ensures Duncan can only be used by captain
- Prevents betting after wagering closes

**Integration Points** (wolf_goat_pig_simulation.py):
- Line 1146-1156: Double validation
- Line 1006-1018: Duncan validation

**Example**:
```python
# Validate double
BettingValidator.validate_double(
    already_doubled=False,
    wagering_closed=False,
    partnership_formed=True
)

# Validate Duncan
BettingValidator.validate_duncan(
    is_captain=True,
    partnership_formed=False,
    tee_shots_complete=False
)

# Calculate multiplier
multiplier = BettingValidator.calculate_wager_multiplier(
    doubled=True,
    redoubled=True,
    duncan_invoked=True
)  # Returns 8.0
```

---

### GameStateValidator
**Location**: `/backend/app/validators/game_state_validator.py`

**Purpose**: Validates game state transitions, player actions, and ensures game rules are followed correctly.

**Key Responsibilities**:
- Validate game phases and transitions
- Validate player counts (2-6 players)
- Validate hole numbers (1-18)
- Validate partnership formations
- Validate shot execution timing
- Validate player turn order
- Validate game completion conditions
- Ensure actions occur in correct game phase

**Key Methods**:
- `validate_game_phase(current_phase, required_phase, action)` - Phase validation
- `validate_player_count(count, game_mode)` - Player count validation
- `validate_hole_number(hole_number, field_name)` - Hole number validation
- `validate_partnership_formation(captain_id, partner_id, tee_shots_complete)` - Partnership rules
- `validate_shot_execution(active_hole, player_id, ball_positions)` - Shot timing validation
- `validate_player_turn(current_player, expected_player, action)` - Turn order validation
- `validate_game_completion(holes_played, min_holes)` - Completion validation
- `validate_action_timing(action_type, game_phase, hole_phase)` - Action timing validation

**Constants**:
- MIN_PLAYERS = 2
- MAX_PLAYERS = 6
- MIN_HOLE_NUMBER = 1
- MAX_HOLE_NUMBER = 18

**Dependencies**: None (pure validation logic)

**Usage**:
- Used in WolfGoatPigSimulation to validate state transitions
- Ensures partnerships formed at correct time
- Validates shots executed in proper order
- Prevents invalid game state changes

**Integration Points** (wolf_goat_pig_simulation.py):
- Line 729-734: Hole number validation
- Line 927-938: Partnership formation validation

**Example**:
```python
# Validate game phase
GameStateValidator.validate_game_phase(
    current_phase="PLAYING",
    required_phase="PLAYING",
    action="execute_shot"
)

# Validate player count
GameStateValidator.validate_player_count(4, "wolf_goat_pig")

# Validate partnership formation
GameStateValidator.validate_partnership_formation(
    captain_id="p1",
    partner_id="p2",
    tee_shots_complete=True
)
```

---

## Data Models (SQLAlchemy)

### Course
**Location**: `/backend/app/models.py`

**Purpose**: Database model for golf course with hole details and ratings.

**Columns**: id, name, description, total_par, total_yards, course_rating, slope_rating, holes_data (JSON), created_at, updated_at

**Usage**: Stores course information permanently

---

### Hole
**Location**: `/backend/app/models.py`

**Purpose**: Database model for individual hole information.

**Columns**: id, course_id, hole_number, par, yards, handicap (stroke index), description, tee_box

**Usage**: Detailed hole data (currently holes stored in Course.holes_data JSON)

---

### GameStateModel
**Location**: `/backend/app/models.py`

**Purpose**: Stores serialized game state for multi-game management and persistence.

**Columns**: id, game_id (unique), join_code, creator_user_id, game_status, state (JSON), created_at, updated_at

**Usage**:
- Persists in-progress games
- Enables game resumption
- Supports multiplayer join codes

---

### GamePlayer
**Location**: `/backend/app/models.py`

**Purpose**: Tracks authenticated players in multiplayer games.

**Columns**: id, game_id, player_slot_id (p1-p4), user_id (Auth0), player_profile_id, player_name, handicap, join_status, joined_at, created_at

**Usage**: Links Auth0 users to game slots for multiplayer

---

### SimulationResult
**Location**: `/backend/app/models.py`

**Purpose**: Stores Monte Carlo simulation results for analysis.

**Columns**: id, course_name, player_count, simulation_count, results_data (JSON), created_at

**Usage**: Historical simulation data and statistics

---

### PlayerProfile
**Location**: `/backend/app/models.py`

**Purpose**: Player account with preferences and GHIN integration.

**Columns**: id, name, email, handicap, ghin_id, ghin_last_updated, avatar_url, created_at, updated_at, last_played, preferences (JSON), is_active, is_ai, playing_style, description, personality_traits (JSON), strengths (JSON), weaknesses (JSON)

**Usage**:
- User profile management
- GHIN handicap sync
- AI player definitions

---

### PlayerStatistics
**Location**: `/backend/app/models.py`

**Purpose**: Comprehensive player statistics and performance metrics.

**Columns**: id, player_id, games_played, games_won, total_earnings, holes_played, holes_won, avg_earnings_per_hole, betting_success_rate, successful_bets, total_bets, partnership_success_rate, partnerships_formed, partnerships_won, solo_attempts, solo_wins, eagles, birdies, pars, bogeys, double_bogeys, worse_than_double, favorite_game_mode, preferred_player_count, best_hole_performance (JSON), worst_hole_performance (JSON), performance_trends (JSON), last_updated

**Usage**:
- Player analytics and dashboards
- Performance tracking
- Badge eligibility calculations

---

### GameRecord
**Location**: `/backend/app/models.py`

**Purpose**: Permanent record of completed games.

**Columns**: id, game_id, course_name, game_mode, player_count, total_holes_played, game_duration_minutes, created_at, completed_at, game_settings (JSON), final_scores (JSON)

**Usage**:
- Game history
- Statistics aggregation
- Leaderboards

---

### GamePlayerResult
**Location**: `/backend/app/models.py`

**Purpose**: Individual player performance in a completed game.

**Columns**: id, game_record_id, player_profile_id, player_name, final_position, total_earnings, holes_won, successful_bets, total_bets, partnerships_formed, partnerships_won, solo_attempts, solo_wins, hole_scores (JSON), betting_history (JSON), performance_metrics (JSON), created_at

**Usage**:
- Per-game player statistics
- Badge achievement detection
- Performance analysis

---

### PlayerAchievement
**Location**: `/backend/app/models.py`

**Purpose**: Achievement/milestone tracking for players (legacy, being replaced by Badge system).

**Columns**: id, player_profile_id, achievement_type, achievement_name, description, earned_date, game_record_id, achievement_data (JSON)

**Usage**: Simple achievement tracking

---

### DailySignup
**Location**: `/backend/app/models.py`

**Purpose**: Daily tee time sign-up system for regular player groups.

**Columns**: id, date, player_profile_id, player_name, signup_time, preferred_start_time, notes, status, created_at, updated_at

**Usage**:
- Coordinate daily games
- Email notifications
- Player availability

---

### PlayerAvailability
**Location**: `/backend/app/models.py`

**Purpose**: Recurring weekly availability patterns for players.

**Columns**: id, player_profile_id, day_of_week (0-6), available_from_time, available_to_time, is_available, notes, created_at, updated_at

**Usage**:
- Matchmaking service
- Suggest optimal tee times

---

### EmailPreferences
**Location**: `/backend/app/models.py`

**Purpose**: Player email notification preferences.

**Columns**: id, player_profile_id, daily_signups_enabled, signup_confirmations_enabled, signup_reminders_enabled, game_invitations_enabled, weekly_summary_enabled, email_frequency, preferred_notification_time, created_at, updated_at

**Usage**: Email service filtering

---

### DailyMessage
**Location**: `/backend/app/models.py`

**Purpose**: Player messages in daily sign-up board.

**Columns**: id, date, player_profile_id, player_name, message, message_time, is_active, created_at, updated_at

**Usage**: Communication on sign-up board

---

### GHINScore
**Location**: `/backend/app/models.py`

**Purpose**: Individual score records synced from GHIN.

**Columns**: id, player_profile_id, ghin_id, score_date, course_name, tees, score, course_rating, slope_rating, differential, posted, handicap_index_at_time, synced_at, created_at, updated_at

**Usage**:
- Handicap verification
- Score history
- Performance tracking

---

### GHINHandicapHistory
**Location**: `/backend/app/models.py`

**Purpose**: Historical handicap index changes from GHIN.

**Columns**: id, player_profile_id, ghin_id, effective_date, handicap_index, revision_reason, scores_used_count, synced_at, created_at

**Usage**:
- Handicap trend analysis
- Verification of handicap changes

---

### MatchSuggestion
**Location**: `/backend/app/models.py`

**Purpose**: AI-generated match suggestions based on availability.

**Columns**: id, day_of_week, suggested_date, overlap_start, overlap_end, suggested_tee_time, match_quality_score, status, notification_sent, notification_sent_at, created_at, expires_at

**Usage**: Matchmaking service suggestions

---

### MatchPlayer
**Location**: `/backend/app/models.py`

**Purpose**: Players in a match suggestion.

**Columns**: id, match_suggestion_id, player_profile_id, player_name, player_email, response, responded_at, created_at, updated_at

**Usage**: Track match responses

---

### Badge
**Location**: `/backend/app/models.py`

**Purpose**: Defines available achievement badges with trigger conditions.

**Columns**: id, badge_id, name, description, category, rarity, image_url, trigger_condition (JSON), trigger_type, max_supply, current_supply, points_value, is_active, series_id, tier, created_at, updated_at

**Usage**:
- Badge catalog
- Achievement definitions
- NFT metadata

---

### PlayerBadgeEarned
**Location**: `/backend/app/models.py`

**Purpose**: Tracks badges earned by players.

**Columns**: id, player_profile_id, badge_id, earned_at, game_record_id, serial_number, showcase_position, is_favorited, created_at, updated_at

**Usage**:
- Player badge collection
- Badge showcases
- Leaderboards

---

### BadgeProgress
**Location**: `/backend/app/models.py`

**Purpose**: Tracks progress toward career milestone badges.

**Columns**: id, player_profile_id, badge_id, current_progress, target_progress, progress_percentage, last_progress_date, progress_data (JSON), created_at, updated_at

**Usage**:
- Show progress bars
- Badge eligibility checking

---

### BadgeSeries
**Location**: `/backend/app/models.py`

**Purpose**: Defines badge series (e.g., "Four Horsemen").

**Columns**: id, name, description, category, badge_count, completion_badge_id, image_url, is_active, created_at

**Usage**:
- Series collections
- Completion tracking

---

### PlayerSeriesProgress
**Location**: `/backend/app/models.py`

**Purpose**: Tracks player progress through badge series.

**Columns**: id, player_profile_id, series_id, badges_earned, badges_needed, is_completed, completed_at, progress_data (JSON), created_at, updated_at

**Usage**: Series progress tracking

---

### SeasonalBadge
**Location**: `/backend/app/models.py`

**Purpose**: Time-limited seasonal badge availability.

**Columns**: id, badge_id, season_name, start_date, end_date, is_active, max_earners, current_earners, created_at

**Usage**: Seasonal events and limited badges

---

### GameBanner
**Location**: `/backend/app/models.py`

**Purpose**: In-app announcements and rule explanations.

**Columns**: id, title, message, banner_type, is_active, background_color, text_color, show_icon, dismissible, created_at, updated_at

**Usage**: UI notifications and announcements

---

## API Schemas (Pydantic)

### ActionRequest
**Location**: `/backend/app/main.py`

**Purpose**: Unified request schema for all game actions.

**Fields**: action_type (str), payload (Dict, optional)

**Usage**: Standard API request format for game interactions

---

### ActionResponse
**Location**: `/backend/app/main.py`

**Purpose**: Standard response structure for all game actions.

**Fields**: game_state (Dict), log_message (str), available_actions (List), timeline_event (Dict, optional)

**Usage**: Standard API response format

---

### CourseCreate
**Location**: `/backend/app/schemas.py`

**Purpose**: Schema for creating new golf courses with validation.

**Fields**: name (str), description (str, optional), holes (List[HoleInfo])

**Validations**:
- 18 holes required
- Unique handicaps 1-18
- Unique hole numbers 1-18
- Total par 70-74

**Usage**: POST /courses endpoint

---

### CourseUpdate
**Location**: `/backend/app/schemas.py`

**Purpose**: Schema for updating course information.

**Fields**: name (str, optional), description (str, optional), holes (List[HoleInfo], optional)

**Usage**: PATCH /courses/{id} endpoint

---

### CourseResponse
**Location**: `/backend/app/schemas.py`

**Purpose**: Course data with computed statistics for API responses.

**Fields**: id, name, description, total_par, total_yards, course_rating, slope_rating, holes, created_at, updated_at

**Usage**: GET /courses responses

---

### CourseList
**Location**: `/backend/app/schemas.py`

**Purpose**: List of multiple courses.

**Fields**: courses (List[CourseResponse])

**Usage**: GET /courses endpoint

---

### CourseStats
**Location**: `/backend/app/schemas.py`

**Purpose**: Computed statistics for a course.

**Fields**: total_par, total_yards, par_3_count, par_4_count, par_5_count, average_yards_per_hole, longest_hole, shortest_hole, difficulty_rating

**Usage**: Course comparison and analysis

---

### CourseComparison
**Location**: `/backend/app/schemas.py`

**Purpose**: Side-by-side course comparison data.

**Fields**: course1, course2, stats1, stats2, difficulty_difference, yard_difference

**Usage**: Course selection UI

---

### PlayerProfileCreate
**Location**: `/backend/app/schemas.py`

**Purpose**: Create new player profile with validation.

**Fields**: name (str), handicap (float), avatar_url (str, optional), preferences (Dict, optional)

**Validations**:
- Name 2-50 characters
- Handicap 0-54

**Usage**: POST /players endpoint

---

### PlayerProfileUpdate
**Location**: `/backend/app/schemas.py`

**Purpose**: Update player profile fields.

**Fields**: name, handicap, avatar_url, preferences, last_played (all optional)

**Usage**: PATCH /players/{id} endpoint

---

### PlayerProfileResponse
**Location**: `/backend/app/schemas.py`

**Purpose**: Complete player profile for API responses.

**Fields**: id, name, email, handicap, avatar_url, created_at, updated_at, last_played, is_active, is_ai, playing_style, description, preferences

**Usage**: GET /players responses

---

### PlayerStatisticsResponse
**Location**: `/backend/app/schemas.py`

**Purpose**: Complete player statistics for API responses.

**Fields**: All PlayerStatistics columns

**Usage**: GET /players/{id}/statistics endpoint

---

### GameRecordCreate
**Location**: `/backend/app/schemas.py`

**Purpose**: Create game record when game completes.

**Fields**: game_id, course_name, game_mode, player_count, game_settings

**Usage**: Internal - called by PersistenceMixin.complete_game()

---

### GamePlayerResultCreate
**Location**: `/backend/app/schemas.py`

**Purpose**: Create player result record for completed game.

**Fields**: game_record_id, player_profile_id, player_name, final_position, all performance metrics

**Usage**: Internal - called by PersistenceMixin.complete_game()

---

### BadgeResponse
**Location**: `/backend/app/badge_routes.py`

**Purpose**: Badge information for API responses.

**Fields**: Badge model fields formatted for display

**Usage**: GET /badges endpoints

---

### BadgeLeaderboardEntry
**Location**: `/backend/app/badge_routes.py`

**Purpose**: Player entry in badge leaderboard.

**Fields**: Player info with badge counts and rankings

**Usage**: GET /badges/leaderboard endpoint

---

## Services

### BadgeEngine
**Location**: `/backend/app/badge_engine.py`

**Purpose**: Detects when players earn badges and manages badge awarding logic.

**Key Responsibilities**:
- Check post-game achievements
- Check real-time achievements (hole-in-one)
- Award badges and update supply
- Track badge progress
- Check series completion
- Update progression badges

**Dependencies**:
- Badge, PlayerBadgeEarned, BadgeProgress (models)
- PlayerStatistics, GamePlayerResult

**Usage**:
- Called after game completion
- Called after significant in-game events

---

### AuthService
**Location**: `/backend/app/services/auth_service.py`

**Purpose**: Auth0 integration for user authentication and profile management.

**Key Responsibilities**:
- Verify JWT tokens
- Get user profiles from Auth0
- Link user_id to PlayerProfile
- Manage authentication flow

**Dependencies**: Auth0 SDK, environment variables

**Usage**: FastAPI Depends for protected endpoints

---

### EmailScheduler
**Location**: `/backend/app/services/email_scheduler.py`

**Purpose**: Schedules and sends recurring email notifications.

**Key Responsibilities**:
- Schedule daily signup reminders
- Schedule weekly summaries
- Manage email job queue
- Handle email delivery timing

**Dependencies**: EmailService, APScheduler

**Usage**: Background service started on app initialization

---

### EmailService
**Location**: `/backend/app/services/email_service.py`

**Purpose**: Sends transactional and notification emails.

**Key Responsibilities**:
- Send signup confirmations
- Send game invitations
- Send daily/weekly summaries
- Template rendering
- Email delivery via SMTP

**Dependencies**: SMTP configuration, email templates

**Usage**:
- Called by EmailScheduler
- Direct calls for transactional emails

---

### GHINService
**Location**: `/backend/app/services/ghin_service.py`

**Purpose**: Syncs player handicaps and scores from GHIN API.

**Key Responsibilities**:
- Authenticate with GHIN API
- Fetch player handicap index
- Fetch score history
- Update PlayerProfile and GHINScore models
- Handle API rate limits and errors

**Dependencies**: GHIN API credentials, httpx

**Usage**:
- Manual handicap sync
- Scheduled daily sync (future)

---

### LegacySignupSyncService
**Location**: `/backend/app/services/legacy_signup_service.py`

**Purpose**: Syncs with external/legacy signup system (Google Sheets).

**Key Responsibilities**:
- Import signups from Google Sheets
- Export signups to Google Sheets
- Bi-directional sync
- Handle date formatting

**Dependencies**: SheetIntegrationService, Google Sheets API

**Usage**: Migration tool for existing groups

---

### MatchmakingService
**Location**: `/backend/app/services/matchmaking_service.py`

**Purpose**: AI-powered player matchmaking based on availability.

**Key Responsibilities**:
- Find availability overlaps
- Calculate match quality scores
- Generate match suggestions
- Send match notifications
- Track match responses

**Dependencies**: PlayerAvailability, EmailService

**Usage**:
- Scheduled daily/weekly
- On-demand match suggestions

---

### OAuth2EmailService
**Location**: `/backend/app/services/oauth2_email_service.py`

**Purpose**: Send emails via Gmail OAuth2 (alternative to SMTP).

**Key Responsibilities**:
- OAuth2 authentication with Gmail
- Send emails via Gmail API
- Refresh access tokens
- Handle API errors

**Dependencies**: Google OAuth2 SDK, credentials

**Usage**: Alternative email backend

---

### OddsCalculator
**Location**: `/backend/app/services/odds_calculator.py`

**Purpose**: Calculates real-time winning odds for different scenarios.

**Key Responsibilities**:
- Calculate solo vs partnership odds
- Evaluate betting scenarios
- Provide EV calculations
- Recommend optimal decisions

**Dependencies**: MonteCarloEngine, Player stats

**Usage**:
- Real-time odds display in UI
- AI decision making

---

### PlayerService
**Location**: `/backend/app/services/player_service.py`

**Purpose**: CRUD operations and business logic for player profiles.

**Key Responsibilities**:
- Create/update/delete player profiles
- Link Auth0 users to profiles
- Manage player statistics
- Calculate performance metrics
- Handle AI player templates

**Dependencies**:
- PlayerProfile, PlayerStatistics (models)
- Database session

**Usage**:
- Player management endpoints
- User registration flow

---

### SheetIntegrationService
**Location**: `/backend/app/services/sheet_integration_service.py`

**Purpose**: Google Sheets integration for legacy data import/export.

**Key Responsibilities**:
- Authenticate with Google Sheets API
- Read sheet data
- Write sheet data
- Map columns to data models

**Dependencies**: Google Sheets API, credentials

**Usage**: LegacySignupSyncService

---

### StatisticsService
**Location**: `/backend/app/services/statistics_service.py`

**Purpose**: Advanced analytics and performance insights.

**Key Responsibilities**:
- Calculate performance trends
- Generate insights and recommendations
- Compare player performances
- Identify strengths and weaknesses
- Create performance charts

**Dependencies**: PlayerStatistics, GamePlayerResult

**Usage**:
- Player dashboard analytics
- Performance comparison features

---

### TeamFormationService
**Location**: `/backend/app/services/team_formation_service.py`

**Purpose**: Generates balanced teams based on handicaps and preferences.

**Key Responsibilities**:
- Balance teams by handicap
- Apply player preferences
- Calculate team equity
- Generate optimal pairings

**Dependencies**: PlayerProfile, handicap calculations

**Usage**: Sunday game pairing generation

---

## Mixins/Utilities

### PersistenceMixin
**Location**: `/backend/app/mixins/persistence_mixin.py`

**Purpose**: Adds database persistence to any game engine class.

**Key Responsibilities**:
- Save game state to database
- Load game state from database
- Handle serialization/deserialization
- Mark games as completed
- Create permanent game records

**Dependencies**:
- GameStateModel, GameRecord (models)
- Database session

**Usage**:
- Mixed into WolfGoatPigSimulation
- Provides _save_to_db(), _load_from_db(), complete_game()

**Required Implementations**:
- Subclass must implement _serialize() and _deserialize()

---

### SimulationTimelineManager
**Location**: `/backend/app/simulation_timeline_enhancements.py`

**Purpose**: Enhances simulations with poker-style betting visualizations.

**Key Responsibilities**:
- Format betting state for display
- Create betting options UI
- Generate timeline enhancements

**Dependencies**: HoleState, BettingState

**Usage**:
- Called after shot execution
- Formats data for frontend display

---

## Enums

### GamePhase
**Location**: `/backend/app/wolf_goat_pig_simulation.py`

**Values**: REGULAR, VINNIE_VARIATION, HOEPFINGER

**Purpose**: Track special game phases in Wolf Goat Pig rules

---

### PlayerRole
**Location**: `/backend/app/wolf_goat_pig_simulation.py`

**Values**: CAPTAIN, SECOND_CAPTAIN, AARDVARK, INVISIBLE_AARDVARK, GOAT

**Purpose**: Define player roles in different game variations

---

### HandicapCategory
**Location**: `/backend/app/domain/player.py`

**Values**: SCRATCH, LOW, MID, HIGH, BEGINNER

**Purpose**: Classify players by handicap range

---

### StrengthLevel
**Location**: `/backend/app/domain/player.py`

**Values**: EXCELLENT, GOOD, AVERAGE, BELOW_AVERAGE, POOR

**Purpose**: Rate player skill level

---

### ShotQuality
**Location**: `/backend/app/domain/shot_result.py`

**Values**: EXCELLENT, GOOD, AVERAGE, POOR, TERRIBLE

**Purpose**: Rate individual shot outcomes

---

### LieType
**Location**: `/backend/app/domain/shot_result.py`

**Values**: FAIRWAY, FIRST_CUT, ROUGH, BUNKER, TREES, HAZARD, DEEP_ROUGH

**Purpose**: Define ball lie positions

---

### ShotType
**Location**: `/backend/app/domain/shot_range_analysis.py`

**Values**: LAY_UP, SAFE_APPROACH, STANDARD_APPROACH, FAIRWAY_FINDER, PIN_SEEKER, RISK_REWARD, HERO_SHOT, RECOVERY_GAMBLE

**Purpose**: Categorize shot strategies

---

### RiskProfile
**Location**: `/backend/app/domain/shot_range_analysis.py`

**Values**: NIT, TAG, LAG, MANIAC

**Purpose**: Poker-style player risk profiles

---

### DecisionQuality
**Location**: `/backend/app/post_hole_analytics.py`

**Values**: EXCELLENT, GOOD, NEUTRAL, POOR, TERRIBLE

**Purpose**: Rate decision quality in analytics

---

### InsightCategory
**Location**: `/backend/app/post_hole_analytics.py`

**Values**: PARTNERSHIP, BETTING, TIMING, RISK_MANAGEMENT, SHOT_SELECTION, STRATEGY

**Purpose**: Categorize analytical insights

---

## Analytics & Insights

### PostHoleAnalyzer
**Location**: `/backend/app/post_hole_analytics.py`

**Purpose**: Analyzes completed holes and generates learning insights.

**Key Responsibilities**:
- Analyze decision points
- Rate partnership choices
- Evaluate betting decisions
- Assess shot quality
- Identify key moments
- Compare to AI recommendations
- Generate improvement tips

**Dependencies**:
- HoleState, timeline events
- DecisionPoint, PartnershipAnalysis, etc. (dataclasses)

**Usage**: Practice mode post-hole analysis

---

### PostHoleAnalytics
**Location**: `/backend/app/post_hole_analytics.py`

**Purpose**: Complete analytics package for a hole.

**Key Responsibilities**:
- Store all analytical data
- Provide decision breakdowns
- Rate performance
- Offer recommendations

**Dependencies**:
- DecisionPoint, PartnershipAnalysis, BettingAnalysis, ShotAnalysis, KeyMoment (dataclasses)

**Usage**: Returned by PostHoleAnalyzer.analyze_hole()

---

### DecisionPoint
**Location**: `/backend/app/post_hole_analytics.py`

**Purpose**: Represents a key decision during the hole.

**Fields**: decision_type, player_id, timestamp, options_available, decision_made, outcome, quarters_impact, quality, explanation

**Usage**: Component of PostHoleAnalytics

---

### PartnershipAnalysis
**Location**: `/backend/app/post_hole_analytics.py`

**Purpose**: Analysis of partnership formation decisions.

**Fields**: partnership_formed, captain_id, partner_id, timing, success, chemistry_rating, alternative_partners, optimal_choice, explanation

**Usage**: Component of PostHoleAnalytics

---

### BettingAnalysis
**Location**: `/backend/app/post_hole_analytics.py`

**Purpose**: Analysis of all betting decisions.

**Fields**: doubles_offered, doubles_accepted, doubles_declined, duncan_used, timing_quality, aggressive_rating, missed_opportunities, costly_mistakes, net_quarter_impact

**Usage**: Component of PostHoleAnalytics

---

### ShotAnalysis
**Location**: `/backend/app/post_hole_analytics.py`

**Purpose**: Analysis of shot execution.

**Fields**: total_shots, shot_quality_distribution, clutch_shots, worst_shot, best_shot, pressure_performance

**Usage**: Component of PostHoleAnalytics

---

### KeyMoment
**Location**: `/backend/app/post_hole_analytics.py`

**Purpose**: Represents a pivotal game moment.

**Fields**: description, impact, quarters_swing, player_involved, timestamp

**Usage**: Component of PostHoleAnalytics

---

## Badge System

### TimelineEvent
**Location**: `/backend/app/wolf_goat_pig_simulation.py`

**Purpose**: Chronological event in game timeline.

**Fields**: id, timestamp, type, description, details, player_id, player_name

**Usage**:
- Timeline visualization
- Event replay
- Analytics

---

### TeamFormation
**Location**: `/backend/app/wolf_goat_pig_simulation.py`

**Purpose**: Represents team configurations for a hole.

**Fields**: type, captain, second_captain, team1, team2, team3, solo_player, opponents, pending_request

**Usage**:
- Partnership tracking
- Scoring calculations

---

### BettingState
**Location**: `/backend/app/wolf_goat_pig_simulation.py`

**Purpose**: Complete betting state for Wolf Goat Pig rules.

**Fields**: base_wager, current_wager, doubled, redoubled, carry_over, float_invoked, option_invoked, duncan_invoked, tunkarri_invoked, big_dick_invoked, joes_special_value, ackerley_gambit, line_of_scrimmage, doubles_history, tossed_aardvarks, ping_pong_count

**Usage**:
- Betting logic
- Wager calculations
- Rule enforcement

---

### BallPosition
**Location**: `/backend/app/wolf_goat_pig_simulation.py`

**Purpose**: Tracks ball location and status during hole.

**Fields**: player_id, distance_to_pin, lie_type, shot_count, holed, conceded, penalty_strokes

**Usage**:
- Order of play determination
- Shot execution
- Scoring

---

### StrokeAdvantage
**Location**: `/backend/app/wolf_goat_pig_simulation.py`

**Purpose**: Handicap strokes for a player on specific hole.

**Fields**: player_id, handicap, strokes_received, net_score, stroke_index

**Usage**:
- Net score calculation
- Fair play enforcement

---

### WGPShotResult
**Location**: `/backend/app/wolf_goat_pig_simulation.py`

**Purpose**: Wolf Goat Pig specific shot result.

**Usage**: Simulation-specific shot data

---

### WGPBettingOpportunity
**Location**: `/backend/app/wolf_goat_pig_simulation.py`

**Purpose**: Betting opportunity during hole.

**Usage**: UI display of betting options

---

### WGPHoleProgression
**Location**: `/backend/app/wolf_goat_pig_simulation.py`

**Purpose**: Tracks hole progression state.

**Usage**: Hole advancement logic

---

## Gaps & Recommendations

### ✅ Implemented Validation Classes

All three core validator classes have been successfully implemented and integrated:

1. **HandicapValidator** ✅
   - **Status**: IMPLEMENTED - `/backend/app/validators/handicap_validator.py` (326 lines)
   - **Integration**: Integrated at 3 points in WolfGoatPigSimulation
   - **Test Coverage**: 52 unit tests, 100% pass rate
   - **Features**: USGA-compliant handicap validation, stroke allocation, net score calculation

2. **BettingValidator** ✅
   - **Status**: IMPLEMENTED - `/backend/app/validators/betting_validator.py` (145 lines)
   - **Integration**: Integrated at 2 points in WolfGoatPigSimulation
   - **Test Coverage**: 23 unit tests, 100% pass rate
   - **Features**: Double/redouble validation, Duncan validation, wager multiplier calculation

3. **GameStateValidator** ✅
   - **Status**: IMPLEMENTED - `/backend/app/validators/game_state_validator.py` (210 lines)
   - **Integration**: Integrated at 2 points in WolfGoatPigSimulation
   - **Test Coverage**: 23 unit tests, 100% pass rate
   - **Features**: Game phase validation, partnership rules, shot execution timing

**Total Test Coverage**: 109 tests, 100% pass rate, 0.05s execution time

**Documentation**:
- Complete usage guide: `VALIDATOR_USAGE_GUIDE.md` (2,466 lines)
- Implementation summary: `VALIDATOR_IMPLEMENTATION_SUMMARY.md`

See [Validators](#validators) section above for detailed class documentation.

### Missing Service Classes

1. **GameLifecycleService**
   - **Purpose**: Manage complete game lifecycle (create, start, pause, resume, complete)
   - **Why Needed**: Game management logic currently in main.py and WolfGoatPigSimulation
   - **Responsibilities**: Game creation, player invitations, game state management
   - **Location**: Should be in `/backend/app/services/game_lifecycle_service.py`

2. **NotificationService**
   - **Purpose**: Unified notification system (email, in-app, push)
   - **Why Needed**: Currently only EmailService, need broader notification support
   - **Responsibilities**: Multi-channel notifications, notification preferences, delivery tracking
   - **Location**: Should be in `/backend/app/services/notification_service.py`

3. **AchievementService**
   - **Purpose**: Unified achievement and badge management
   - **Why Needed**: BadgeEngine handles badges, but PlayerAchievement is separate
   - **Responsibilities**: Unify badge and achievement systems, progress tracking
   - **Location**: Should be in `/backend/app/services/achievement_service.py`

4. **LeaderboardService**
   - **Purpose**: Generate various leaderboards and rankings
   - **Why Needed**: Leaderboard logic scattered across endpoints
   - **Responsibilities**: Global leaderboards, course leaderboards, badge leaderboards
   - **Location**: Should be in `/backend/app/services/leaderboard_service.py`

### Missing Manager Classes

1. **RuleManager**
   - **Purpose**: Centralize Wolf Goat Pig rule enforcement
   - **Why Needed**: Rules logic embedded in WolfGoatPigSimulation
   - **Responsibilities**: Enforce partnership rules, betting rules, special variations
   - **Location**: Should be in `/backend/app/state/rule_manager.py`

2. **ScoringManager**
   - **Purpose**: Handle all scoring calculations
   - **Why Needed**: Scoring spread across multiple classes
   - **Responsibilities**: Calculate net scores, team scores, quarterly earnings
   - **Location**: Should be in `/backend/app/state/scoring_manager.py`

### Duplicate Functionality

1. **Player vs WGPPlayer**
   - **Issue**: Two Player classes (domain.player.Player and wolf_goat_pig_simulation.Player)
   - **Recommendation**: Consolidate into single Player domain model
   - **Action**: Use domain.player.Player everywhere, remove WGPPlayer alias

2. **Achievement vs Badge System**
   - **Issue**: PlayerAchievement and Badge/PlayerBadgeEarned serve similar purposes
   - **Recommendation**: Fully migrate to Badge system, deprecate PlayerAchievement
   - **Action**: Create AchievementService to unify both systems during migration

3. **Course Storage**
   - **Issue**: Course data in CourseManager.DEFAULT_COURSES AND Course database model
   - **Recommendation**: Use database as source of truth, CourseManager as cache
   - **Action**: Load DEFAULT_COURSES into database on first run

### Classes That Should Exist

1. **AIPlayerStrategy**
   - **Purpose**: AI decision-making strategies for different player types
   - **Why Needed**: AI logic currently in simulation code
   - **Responsibilities**: Partnership decisions, betting aggression, shot selection
   - **Location**: `/backend/app/ai/player_strategy.py`

2. **TournamentManager**
   - **Purpose**: Manage multi-round tournaments
   - **Why Needed**: Foundation for future tournament feature
   - **Responsibilities**: Bracket management, scoring across rounds
   - **Location**: `/backend/app/services/tournament_manager.py`

3. **ReplayService**
   - **Purpose**: Replay completed games from timeline
   - **Why Needed**: Learning and review feature
   - **Responsibilities**: Load game timeline, step through events, annotate
   - **Location**: `/backend/app/services/replay_service.py`

4. **HandicapCalculator**
   - **Purpose**: Calculate course handicaps from handicap index
   - **Why Needed**: Complex USGA formula not currently implemented
   - **Responsibilities**: Apply slope/rating to handicap index
   - **Location**: `/backend/app/services/handicap_calculator.py`

---

## DRY Opportunities

### Repeated Code Patterns

1. **Database Session Management**
   - **Pattern**: try/except/rollback/close repeated in many services
   - **Recommendation**: Create context manager decorator
   - **Example**:
   ```python
   @database_session
   def some_service_method(self, db: Session):
       # Auto-handles commit/rollback/close
   ```

2. **Date/Time Handling**
   - **Pattern**: `datetime.utcnow().isoformat()` appears everywhere
   - **Recommendation**: Create utility functions
   - **Example**:
   ```python
   # utils/datetime_utils.py
   def utc_now_iso() -> str:
       return datetime.utcnow().isoformat()
   ```

3. **API Error Responses**
   - **Pattern**: HTTPException with detail string repeated
   - **Recommendation**: Create exception classes
   - **Example**:
   ```python
   class GameNotFoundException(HTTPException):
       def __init__(self, game_id: str):
           super().__init__(status_code=404, detail=f"Game {game_id} not found")
   ```

4. **JSON Serialization**
   - **Pattern**: to_dict() and from_dict() methods in many classes
   - **Recommendation**: Create base serializable class or use dataclasses with asdict
   - **Example**:
   ```python
   from dataclasses import dataclass, asdict

   @dataclass
   class SerializableBase:
       def to_dict(self):
           return asdict(self)
   ```

### Similar Classes That Could Be Consolidated

1. **ShotQuality and DecisionQuality Enums**
   - **Issue**: Both have same values (EXCELLENT, GOOD, etc.)
   - **Recommendation**: Create single Quality enum
   - **Action**: Replace both with shared enum

2. **Course-related Schemas**
   - **Issue**: CourseCreate, CourseUpdate, CourseResponse have overlapping fields
   - **Recommendation**: Use Pydantic inheritance
   - **Example**:
   ```python
   class CourseBase(BaseModel):
       name: str
       description: Optional[str]

   class CourseCreate(CourseBase):
       holes: List[HoleInfo]

   class CourseResponse(CourseBase):
       id: int
       # ...
   ```

3. **Player Profile Schemas**
   - **Issue**: PlayerProfileBase, Create, Update, Response have duplication
   - **Recommendation**: Use Pydantic inheritance hierarchy
   - **Action**: Refactor to shared base with specific extensions

### Shared Behavior That Could Be Mixins

1. **TimestampMixin**
   - **Purpose**: Add created_at/updated_at to models
   - **Usage**: Most database models
   - **Implementation**:
   ```python
   class TimestampMixin:
       created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
       updated_at = Column(String, onupdate=lambda: datetime.utcnow().isoformat())
   ```

2. **PlayerAssociationMixin**
   - **Purpose**: Add player_profile_id foreign key
   - **Usage**: Many models (statistics, badges, achievements)
   - **Implementation**:
   ```python
   class PlayerAssociationMixin:
       player_profile_id = Column(Integer, ForeignKey('player_profiles.id'), index=True)
   ```

3. **JSONSerializableMixin**
   - **Purpose**: Add to_dict/from_dict methods
   - **Usage**: All state management classes
   - **Implementation**:
   ```python
   class JSONSerializableMixin:
       def to_dict(self) -> Dict[str, Any]:
           # Generic implementation

       @classmethod
       def from_dict(cls, data: Dict[str, Any]):
           # Generic implementation
   ```

4. **StatisticsTrackingMixin**
   - **Purpose**: Add common statistics fields
   - **Usage**: PlayerStatistics, GamePlayerResult
   - **Implementation**:
   ```python
   class StatisticsTrackingMixin:
       holes_played = Column(Integer, default=0)
       holes_won = Column(Integer, default=0)
       total_earnings = Column(Float, default=0.0)
       # ... other common fields
   ```

### Extracted Utilities

1. **HandicapUtils**
   - **Extract From**: Player, StrokeAdvantage, various services
   - **Purpose**: Centralize handicap calculations
   - **Functions**:
     - `calculate_strokes_received(handicap, stroke_index)`
     - `calculate_net_score(gross_score, strokes_received)`
     - `get_handicap_category(handicap)`
     - `get_strength_level(handicap)`

2. **BettingUtils**
   - **Extract From**: BettingState, WolfGoatPigSimulation
   - **Purpose**: Centralize betting calculations
   - **Functions**:
     - `calculate_wager(base, doubles, rules_applied)`
     - `validate_betting_action(action, state)`
     - `apply_betting_rule(rule_name, state)`

3. **ScoringUtils**
   - **Extract From**: Scattered across simulation and analytics
   - **Purpose**: Centralize scoring calculations
   - **Functions**:
     - `calculate_hole_winner(scores, teams)`
     - `distribute_quarters(winner, losers, wager)`
     - `calculate_game_totals(hole_results)`

4. **ValidationUtils**
   - **Extract From**: Pydantic validators, service validations
   - **Purpose**: Shared validation logic
   - **Functions**:
     - `validate_player_count(count, game_mode)`
     - `validate_handicap(handicap)`
     - `validate_date_format(date_str)`

---

## Implementation Priority

### High Priority (Immediate Need)

1. **Consolidate Player Classes** - Eliminate WGPPlayer confusion
2. **Create GameLifecycleService** - Centralize game management
3. **Extract HandicapUtils** - Consistency in handicap handling
4. **Add TimestampMixin** - Reduce model duplication

### Medium Priority (Next Sprint)

1. **Create Validator Classes** - GameStateValidator, BettingValidator
2. **Consolidate Achievement Systems** - Migrate to Badge system
3. **Create NotificationService** - Expand beyond email
4. **Extract BettingUtils and ScoringUtils**

### Low Priority (Future Enhancement)

1. **Add Tournament Support** - TournamentManager
2. **Add Replay Feature** - ReplayService
3. **Create AI Strategy System** - AIPlayerStrategy
4. **Add Leaderboard Service** - Centralize rankings

---

## Architecture Principles

### Current Strengths

1. **Clear Separation of Concerns**: Domain models, state management, services well separated
2. **Persistence Layer**: PersistenceMixin provides clean abstraction
3. **API Design**: Unified ActionRequest/ActionResponse pattern
4. **Extensibility**: Enum-based design allows easy additions

### Areas for Improvement

1. **Validation**: Needs centralized validation layer
2. **Error Handling**: Inconsistent exception patterns
3. **Testing**: Need more test coverage (fixtures, mocks)
4. **Documentation**: Need class-level docstrings consistently

### Recommended Patterns

1. **Repository Pattern**: For complex database queries
2. **Factory Pattern**: For creating game instances with different configurations
3. **Strategy Pattern**: For AI player decision making
4. **Observer Pattern**: For event-driven badge detection
5. **Decorator Pattern**: For cross-cutting concerns (logging, validation)

---

## Conclusion

The Wolf Goat Pig codebase has a solid foundation with clear separation between domain logic, state management, and services. The main opportunities for improvement are:

1. **Consolidation**: Merge duplicate functionality (Player classes, achievement systems)
2. **Extraction**: Pull out common utilities and mixins
3. **Centralization**: Create service classes for scattered logic
4. **Validation**: Add dedicated validation layer

By addressing these areas, the codebase will become more maintainable, testable, and extensible for future features like tournaments, AI improvements, and advanced analytics.
