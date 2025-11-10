# Wolf-Goat-Pig PostgreSQL Database Schema

This document describes the complete database schema for the Wolf-Goat-Pig application.

## Table of Contents
- [Core Game Tables](#core-game-tables)
- [Player Management](#player-management)
- [Statistics & Records](#statistics--records)
- [Daily Sign-up System](#daily-sign-up-system)
- [GHIN Integration](#ghin-integration)
- [Matchmaking System](#matchmaking-system)
- [Achievement & Badge System](#achievement--badge-system)
- [Notifications](#notifications)
- [Relationships Diagram](#relationships-diagram)

---

## Core Game Tables

### `game_state`
Stores the current state of active games. Each game gets a unique ID and optional join code.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| game_id | UUID/VARCHAR | UNIQUE, INDEXED | Unique identifier for each game |
| join_code | VARCHAR | UNIQUE, INDEXED, NULLABLE | 6-character code for joining games |
| creator_user_id | VARCHAR | NULLABLE | Auth0 user ID of game creator |
| game_status | VARCHAR | DEFAULT 'setup' | Game state: setup, in_progress, completed |
| state | JSON | NOT NULL | Complete game state as JSON blob |
| created_at | VARCHAR | NOT NULL | ISO timestamp |
| updated_at | VARCHAR | NOT NULL | ISO timestamp |

**Indexes:**
- `game_id` (unique)
- `join_code` (unique)

---

### `game_players`
Tracks authenticated players participating in specific games.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| game_id | UUID/VARCHAR | INDEXED | References `game_state.game_id` |
| player_slot_id | VARCHAR | NOT NULL | Player slot (p1, p2, p3, p4) |
| user_id | VARCHAR | NULLABLE | Auth0 user ID |
| player_profile_id | INTEGER | NULLABLE | References `player_profiles.id` |
| player_name | VARCHAR | NOT NULL | Display name |
| handicap | FLOAT | NOT NULL | Player handicap |
| join_status | VARCHAR | DEFAULT 'pending' | Status: pending, joined, ready |
| joined_at | VARCHAR | NULLABLE | ISO timestamp when joined |
| created_at | VARCHAR | NOT NULL | ISO timestamp |

**Indexes:**
- `game_id`

**Foreign Keys:**
- `player_profile_id` → `player_profiles.id`
- `game_id` → `game_state.game_id`

---

### `courses`
Golf course definitions with hole data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| name | VARCHAR | UNIQUE, INDEXED | Course name |
| description | VARCHAR | NULLABLE | Course description |
| total_par | INTEGER | NOT NULL | Total par for 18 holes |
| total_yards | INTEGER | NOT NULL | Total yardage |
| course_rating | FLOAT | NULLABLE | USGA course rating |
| slope_rating | FLOAT | NULLABLE | USGA slope rating |
| holes_data | JSON | NOT NULL | Array of hole definitions |
| created_at | VARCHAR | NOT NULL | ISO timestamp |
| updated_at | VARCHAR | NOT NULL | ISO timestamp |

**Indexes:**
- `name` (unique)

**holes_data JSON Structure:**
```json
[
  {
    "hole_number": 1,
    "par": 4,
    "yards": 420,
    "stroke_index": 5,
    "description": "Dogleg right with water hazard",
    "tee_box": "regular"
  }
]
```

---

### `holes`
Alternative hole storage (legacy, holes_data in courses is preferred).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| course_id | INTEGER | INDEXED | References `courses.id` |
| hole_number | INTEGER | NOT NULL | Hole number (1-18) |
| par | INTEGER | NOT NULL | Par for this hole |
| yards | INTEGER | NOT NULL | Hole yardage |
| handicap | INTEGER | NOT NULL | Stroke index (1-18) |
| description | VARCHAR | NULLABLE | Hole description |
| tee_box | VARCHAR | DEFAULT 'regular' | Tee box name |

**Indexes:**
- `course_id`

**Foreign Keys:**
- `course_id` → `courses.id`

---

### `rules`
Game rules and documentation.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| title | VARCHAR | INDEXED | Rule title |
| description | VARCHAR | NOT NULL | Rule description |

**Indexes:**
- `title`

---

### `game_banners`
System-wide banners for announcements.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| title | VARCHAR | NULLABLE | Banner title |
| message | VARCHAR | NOT NULL | Banner message |
| banner_type | VARCHAR | DEFAULT 'info' | Type: info, warning, announcement, rules |
| is_active | BOOLEAN | DEFAULT TRUE | Whether banner is shown |
| background_color | VARCHAR | DEFAULT '#3B82F6' | Hex color code |
| text_color | VARCHAR | DEFAULT '#FFFFFF' | Hex color code |
| show_icon | BOOLEAN | DEFAULT TRUE | Show type icon |
| dismissible | BOOLEAN | DEFAULT FALSE | Can be dismissed |
| created_at | VARCHAR | NOT NULL | ISO timestamp |
| updated_at | VARCHAR | NULLABLE | ISO timestamp |

---

## Player Management

### `player_profiles`
Core player profile data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| name | VARCHAR | UNIQUE, INDEXED | Player name |
| email | VARCHAR | UNIQUE, INDEXED, NULLABLE | Email for notifications |
| handicap | FLOAT | DEFAULT 18.0 | Current handicap |
| ghin_id | VARCHAR | UNIQUE, INDEXED, NULLABLE | GHIN ID for handicap sync |
| ghin_last_updated | VARCHAR | NULLABLE | Last GHIN sync timestamp |
| avatar_url | VARCHAR | NULLABLE | Avatar image URL |
| created_at | VARCHAR | NOT NULL | ISO timestamp |
| updated_at | VARCHAR | NULLABLE | ISO timestamp |
| last_played | VARCHAR | NULLABLE | Last game timestamp |
| preferences | JSON | DEFAULT {} | Player preferences object |
| is_active | INTEGER | DEFAULT 1 | Active status (0/1) |
| is_ai | INTEGER | DEFAULT 0 | AI player flag (0/1) |
| playing_style | VARCHAR | NULLABLE | Playing style (aggressive, steady, etc.) |
| description | VARCHAR | NULLABLE | Player description |
| personality_traits | JSON | NULLABLE | AI personality traits |
| strengths | JSON | NULLABLE | Array of strengths |
| weaknesses | JSON | NULLABLE | Array of weaknesses |

**Indexes:**
- `name` (unique)
- `email` (unique)
- `ghin_id` (unique)

**preferences JSON Structure:**
```json
{
  "ai_difficulty": "medium",
  "preferred_game_modes": ["wolf_goat_pig"],
  "preferred_player_count": 4,
  "betting_style": "conservative",
  "display_hints": true
}
```

---

### `email_preferences`
Email notification preferences per player.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| player_profile_id | INTEGER | INDEXED | References `player_profiles.id` |
| daily_signups_enabled | INTEGER | DEFAULT 1 | Daily signup emails (0/1) |
| signup_confirmations_enabled | INTEGER | DEFAULT 1 | Signup confirmation emails (0/1) |
| signup_reminders_enabled | INTEGER | DEFAULT 1 | Reminder emails (0/1) |
| game_invitations_enabled | INTEGER | DEFAULT 1 | Game invitation emails (0/1) |
| weekly_summary_enabled | INTEGER | DEFAULT 1 | Weekly summary emails (0/1) |
| email_frequency | VARCHAR | DEFAULT 'daily' | Frequency: daily, weekly, monthly, never |
| preferred_notification_time | VARCHAR | DEFAULT '8:00 AM' | Preferred send time |
| created_at | VARCHAR | NOT NULL | ISO timestamp |
| updated_at | VARCHAR | NOT NULL | ISO timestamp |

**Indexes:**
- `player_profile_id`

**Foreign Keys:**
- `player_profile_id` → `player_profiles.id`

---

## Statistics & Records

### `player_statistics`
Aggregated player performance statistics.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| player_id | INTEGER | INDEXED | References `player_profiles.id` |
| games_played | INTEGER | DEFAULT 0 | Total games played |
| games_won | INTEGER | DEFAULT 0 | Total games won |
| total_earnings | FLOAT | DEFAULT 0.0 | Total earnings |
| holes_played | INTEGER | DEFAULT 0 | Total holes played |
| holes_won | INTEGER | DEFAULT 0 | Total holes won |
| avg_earnings_per_hole | FLOAT | DEFAULT 0.0 | Average earnings per hole |
| betting_success_rate | FLOAT | DEFAULT 0.0 | Success rate (0.0-1.0) |
| successful_bets | INTEGER | DEFAULT 0 | Number of successful bets |
| total_bets | INTEGER | DEFAULT 0 | Total bets placed |
| partnership_success_rate | FLOAT | DEFAULT 0.0 | Partnership success (0.0-1.0) |
| partnerships_formed | INTEGER | DEFAULT 0 | Total partnerships |
| partnerships_won | INTEGER | DEFAULT 0 | Partnerships won |
| solo_attempts | INTEGER | DEFAULT 0 | Solo attempts |
| solo_wins | INTEGER | DEFAULT 0 | Solo wins |
| eagles | INTEGER | DEFAULT 0 | Eagles scored |
| birdies | INTEGER | DEFAULT 0 | Birdies scored |
| pars | INTEGER | DEFAULT 0 | Pars scored |
| bogeys | INTEGER | DEFAULT 0 | Bogeys scored |
| double_bogeys | INTEGER | DEFAULT 0 | Double bogeys |
| worse_than_double | INTEGER | DEFAULT 0 | Worse than double bogey |
| favorite_game_mode | VARCHAR | DEFAULT 'wolf_goat_pig' | Preferred game mode |
| preferred_player_count | INTEGER | DEFAULT 4 | Preferred player count |
| best_hole_performance | JSON | DEFAULT [] | Best performing holes |
| worst_hole_performance | JSON | DEFAULT [] | Worst performing holes |
| performance_trends | JSON | DEFAULT [] | Historical trends |
| last_updated | VARCHAR | NOT NULL | ISO timestamp |

**Indexes:**
- `player_id`

**Foreign Keys:**
- `player_id` → `player_profiles.id`

---

### `game_records`
Completed game records.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| game_id | UUID/VARCHAR | UNIQUE, INDEXED | Unique game identifier |
| course_name | VARCHAR | NOT NULL | Course played |
| game_mode | VARCHAR | DEFAULT 'wolf_goat_pig' | Game mode |
| player_count | INTEGER | NOT NULL | Number of players |
| total_holes_played | INTEGER | DEFAULT 18 | Holes completed |
| game_duration_minutes | INTEGER | NULLABLE | Game duration |
| created_at | VARCHAR | NOT NULL | Game start time |
| completed_at | VARCHAR | NULLABLE | Game end time |
| game_settings | JSON | DEFAULT {} | Game configuration |
| final_scores | JSON | DEFAULT {} | Final leaderboard |

**Indexes:**
- `game_id` (unique)

---

### `game_player_results`
Individual player results for completed games.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| game_record_id | INTEGER | INDEXED | References `game_records.id` |
| player_profile_id | INTEGER | INDEXED | References `player_profiles.id` |
| player_name | VARCHAR | NOT NULL | Player name (denormalized) |
| final_position | INTEGER | NOT NULL | Final rank (1st, 2nd, etc.) |
| total_earnings | FLOAT | DEFAULT 0.0 | Total earnings |
| holes_won | INTEGER | DEFAULT 0 | Holes won |
| successful_bets | INTEGER | DEFAULT 0 | Successful bets |
| total_bets | INTEGER | DEFAULT 0 | Total bets |
| partnerships_formed | INTEGER | DEFAULT 0 | Partnerships formed |
| partnerships_won | INTEGER | DEFAULT 0 | Partnerships won |
| solo_attempts | INTEGER | DEFAULT 0 | Solo attempts |
| solo_wins | INTEGER | DEFAULT 0 | Solo wins |
| hole_scores | JSON | DEFAULT {} | Hole-by-hole scores |
| betting_history | JSON | DEFAULT [] | Betting decisions |
| performance_metrics | JSON | DEFAULT {} | Advanced metrics |
| created_at | VARCHAR | NOT NULL | ISO timestamp |

**Indexes:**
- `game_record_id`
- `player_profile_id`

**Foreign Keys:**
- `game_record_id` → `game_records.id`
- `player_profile_id` → `player_profiles.id`

---

### `simulation_results`
Monte Carlo simulation results for analysis.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| course_name | VARCHAR | NULLABLE | Course simulated |
| player_count | INTEGER | NOT NULL | Number of players |
| simulation_count | INTEGER | NOT NULL | Iterations run |
| results_data | JSON | NOT NULL | Simulation results |
| created_at | VARCHAR | NOT NULL | ISO timestamp |

---

## Daily Sign-up System

### `daily_signups`
Daily player sign-ups for tee times.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| date | VARCHAR | INDEXED | Date (YYYY-MM-DD) |
| player_profile_id | INTEGER | INDEXED | References `player_profiles.id` |
| player_name | VARCHAR | NOT NULL | Player name (denormalized) |
| signup_time | VARCHAR | NOT NULL | ISO timestamp |
| preferred_start_time | VARCHAR | NULLABLE | Preferred tee time |
| notes | VARCHAR | NULLABLE | Player notes |
| status | VARCHAR | DEFAULT 'signed_up' | Status: signed_up, cancelled, played |
| created_at | VARCHAR | NOT NULL | ISO timestamp |
| updated_at | VARCHAR | NOT NULL | ISO timestamp |

**Indexes:**
- `date`
- `player_profile_id`

**Foreign Keys:**
- `player_profile_id` → `player_profiles.id`

---

### `daily_messages`
Daily message board posts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| date | VARCHAR | INDEXED | Date (YYYY-MM-DD) |
| player_profile_id | INTEGER | INDEXED | References `player_profiles.id` |
| player_name | VARCHAR | NOT NULL | Player name (denormalized) |
| message | VARCHAR | NOT NULL | Message content |
| message_time | VARCHAR | NOT NULL | ISO timestamp |
| is_active | INTEGER | DEFAULT 1 | Active/deleted (0/1) |
| created_at | VARCHAR | NOT NULL | ISO timestamp |
| updated_at | VARCHAR | NOT NULL | ISO timestamp |

**Indexes:**
- `date`
- `player_profile_id`

**Foreign Keys:**
- `player_profile_id` → `player_profiles.id`

---

### `player_availability`
Regular weekly availability for players.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| player_profile_id | INTEGER | INDEXED | References `player_profiles.id` |
| day_of_week | INTEGER | NOT NULL | Day (0=Mon, 6=Sun) |
| available_from_time | VARCHAR | NULLABLE | Start time (e.g., "4:30 PM") |
| available_to_time | VARCHAR | NULLABLE | End time (e.g., "8:00 PM") |
| is_available | INTEGER | DEFAULT 1 | Available flag (0/1) |
| notes | VARCHAR | NULLABLE | Availability notes |
| created_at | VARCHAR | NOT NULL | ISO timestamp |
| updated_at | VARCHAR | NOT NULL | ISO timestamp |

**Indexes:**
- `player_profile_id`

**Foreign Keys:**
- `player_profile_id` → `player_profiles.id`

---

## GHIN Integration

### `ghin_scores`
GHIN score history for players.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| player_profile_id | INTEGER | INDEXED | References `player_profiles.id` |
| ghin_id | VARCHAR | INDEXED | GHIN ID |
| score_date | VARCHAR | INDEXED | Round date (YYYY-MM-DD) |
| course_name | VARCHAR | NOT NULL | Course name |
| tees | VARCHAR | NULLABLE | Tee box (Blue, White, etc.) |
| score | INTEGER | NOT NULL | Total score |
| course_rating | FLOAT | NULLABLE | Course rating |
| slope_rating | INTEGER | NULLABLE | Slope rating |
| differential | FLOAT | NULLABLE | Score differential |
| posted | INTEGER | DEFAULT 1 | Counts for handicap (0/1) |
| handicap_index_at_time | FLOAT | NULLABLE | Handicap when posted |
| synced_at | VARCHAR | NOT NULL | Sync timestamp |
| created_at | VARCHAR | NOT NULL | ISO timestamp |
| updated_at | VARCHAR | NOT NULL | ISO timestamp |

**Indexes:**
- `player_profile_id`
- `ghin_id`
- `score_date`

**Foreign Keys:**
- `player_profile_id` → `player_profiles.id`

---

### `ghin_handicap_history`
Historical handicap index changes.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| player_profile_id | INTEGER | INDEXED | References `player_profiles.id` |
| ghin_id | VARCHAR | INDEXED | GHIN ID |
| effective_date | VARCHAR | INDEXED | Effective date (YYYY-MM-DD) |
| handicap_index | FLOAT | NOT NULL | Handicap index value |
| revision_reason | VARCHAR | NULLABLE | Why it changed |
| scores_used_count | INTEGER | NULLABLE | Scores in calculation |
| synced_at | VARCHAR | NOT NULL | Sync timestamp |
| created_at | VARCHAR | NOT NULL | ISO timestamp |

**Indexes:**
- `player_profile_id`
- `ghin_id`
- `effective_date`

**Foreign Keys:**
- `player_profile_id` → `player_profiles.id`

---

## Matchmaking System

### `match_suggestions`
Suggested player matches based on availability.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| day_of_week | INTEGER | NOT NULL | Day (0=Mon, 6=Sun) |
| suggested_date | VARCHAR | NULLABLE | Specific date if scheduled |
| overlap_start | VARCHAR | NOT NULL | Overlap start time |
| overlap_end | VARCHAR | NOT NULL | Overlap end time |
| suggested_tee_time | VARCHAR | NOT NULL | Recommended tee time |
| match_quality_score | FLOAT | NOT NULL | Quality score |
| status | VARCHAR | DEFAULT 'pending' | Status: pending, accepted, declined, expired |
| notification_sent | BOOLEAN | DEFAULT FALSE | Notification sent flag |
| notification_sent_at | VARCHAR | NULLABLE | Notification timestamp |
| created_at | VARCHAR | NOT NULL | ISO timestamp |
| expires_at | VARCHAR | NOT NULL | Expiration timestamp |

---

### `match_players`
Players in a match suggestion.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| match_suggestion_id | INTEGER | INDEXED | References `match_suggestions.id` |
| player_profile_id | INTEGER | INDEXED | References `player_profiles.id` |
| player_name | VARCHAR | NOT NULL | Player name |
| player_email | VARCHAR | NOT NULL | Player email |
| response | VARCHAR | NULLABLE | Response: accepted, declined, no_response |
| responded_at | VARCHAR | NULLABLE | Response timestamp |
| created_at | VARCHAR | NOT NULL | ISO timestamp |
| updated_at | VARCHAR | NULLABLE | ISO timestamp |

**Indexes:**
- `match_suggestion_id`
- `player_profile_id`

**Foreign Keys:**
- `match_suggestion_id` → `match_suggestions.id`
- `player_profile_id` → `player_profiles.id`

---

## Achievement & Badge System

### `player_achievements`
Player achievements (simpler system than badges).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| player_profile_id | INTEGER | INDEXED | References `player_profiles.id` |
| achievement_type | VARCHAR | NOT NULL | Type: first_win, big_earner, etc. |
| achievement_name | VARCHAR | NOT NULL | Achievement name |
| description | VARCHAR | NOT NULL | Achievement description |
| earned_date | VARCHAR | NOT NULL | Date earned |
| game_record_id | INTEGER | NULLABLE | Game where earned |
| achievement_data | JSON | DEFAULT {} | Additional details |

**Indexes:**
- `player_profile_id`

**Foreign Keys:**
- `player_profile_id` → `player_profiles.id`

---

### `badges`
Badge definitions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| badge_id | INTEGER | UNIQUE, INDEXED | Unique badge ID |
| name | VARCHAR | INDEXED | Badge name |
| description | VARCHAR | NOT NULL | Badge description |
| category | VARCHAR | INDEXED | Category: achievement, progression, seasonal, etc. |
| rarity | VARCHAR | INDEXED | Rarity: common, rare, epic, legendary, mythic |
| image_url | VARCHAR | NULLABLE | Badge image path |
| trigger_condition | JSON | NOT NULL | Earning logic |
| trigger_type | VARCHAR | NOT NULL | Type: one_time, career_milestone, etc. |
| max_supply | INTEGER | NULLABLE | Max earners (NULL = unlimited) |
| current_supply | INTEGER | DEFAULT 0 | Current earners |
| points_value | INTEGER | DEFAULT 0 | Point value |
| is_active | BOOLEAN | DEFAULT TRUE | Active flag |
| series_id | INTEGER | NULLABLE, INDEXED | References `badge_series.id` |
| tier | INTEGER | NULLABLE | Progression tier |
| created_at | VARCHAR | NOT NULL | ISO timestamp |
| updated_at | VARCHAR | NULLABLE | ISO timestamp |

**Indexes:**
- `badge_id` (unique)
- `name`
- `category`
- `rarity`
- `series_id`

**Foreign Keys:**
- `series_id` → `badge_series.id`

---

### `player_badges_earned`
Badges earned by players.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| player_profile_id | INTEGER | INDEXED | References `player_profiles.id` |
| badge_id | INTEGER | INDEXED | References `badges.id` |
| earned_at | VARCHAR | INDEXED | Earned timestamp |
| game_record_id | INTEGER | NULLABLE, INDEXED | Game where earned |
| serial_number | INTEGER | NOT NULL | Order earned (e.g., #47) |
| showcase_position | INTEGER | NULLABLE | Showcase position (1-6) |
| is_favorited | BOOLEAN | DEFAULT FALSE | Favorited flag |
| created_at | VARCHAR | NOT NULL | ISO timestamp |
| updated_at | VARCHAR | NULLABLE | ISO timestamp |

**Indexes:**
- `player_profile_id`
- `badge_id`
- `earned_at`
- `game_record_id`

**Foreign Keys:**
- `player_profile_id` → `player_profiles.id`
- `badge_id` → `badges.id`

---

### `badge_progress`
Track progress toward earning badges.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| player_profile_id | INTEGER | INDEXED | References `player_profiles.id` |
| badge_id | INTEGER | INDEXED | References `badges.id` |
| current_progress | INTEGER | DEFAULT 0 | Current progress (e.g., 7) |
| target_progress | INTEGER | NOT NULL | Target (e.g., 10) |
| progress_percentage | FLOAT | DEFAULT 0.0 | Progress percentage |
| last_progress_date | VARCHAR | NULLABLE | Last update timestamp |
| progress_data | JSON | DEFAULT {} | Additional tracking data |
| created_at | VARCHAR | NOT NULL | ISO timestamp |
| updated_at | VARCHAR | NOT NULL | ISO timestamp |

**Indexes:**
- `player_profile_id`
- `badge_id`

**Foreign Keys:**
- `player_profile_id` → `player_profiles.id`
- `badge_id` → `badges.id`

---

### `badge_series`
Badge collection series.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| name | VARCHAR | UNIQUE, INDEXED | Series name |
| description | VARCHAR | NOT NULL | Series description |
| category | VARCHAR | NOT NULL | Category: collectible, progression |
| badge_count | INTEGER | NOT NULL | Badges in series |
| completion_badge_id | INTEGER | NULLABLE | Badge when complete |
| image_url | VARCHAR | NULLABLE | Series artwork |
| is_active | BOOLEAN | DEFAULT TRUE | Active flag |
| created_at | VARCHAR | NOT NULL | ISO timestamp |

**Indexes:**
- `name` (unique)

---

### `player_series_progress`
Player progress on badge series.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| player_profile_id | INTEGER | INDEXED | References `player_profiles.id` |
| series_id | INTEGER | INDEXED | References `badge_series.id` |
| badges_earned | INTEGER | DEFAULT 0 | Badges collected |
| badges_needed | INTEGER | NOT NULL | Total in series |
| is_completed | BOOLEAN | DEFAULT FALSE | Completion flag |
| completed_at | VARCHAR | NULLABLE | Completion timestamp |
| progress_data | JSON | DEFAULT {} | Which badges earned |
| created_at | VARCHAR | NOT NULL | ISO timestamp |
| updated_at | VARCHAR | NOT NULL | ISO timestamp |

**Indexes:**
- `player_profile_id`
- `series_id`

**Foreign Keys:**
- `player_profile_id` → `player_profiles.id`
- `series_id` → `badge_series.id`

---

### `seasonal_badges`
Time-limited seasonal badges.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| badge_id | INTEGER | INDEXED | References `badges.id` |
| season_name | VARCHAR | INDEXED | Season name |
| start_date | VARCHAR | INDEXED | Start date (YYYY-MM-DD) |
| end_date | VARCHAR | INDEXED | End date (YYYY-MM-DD) |
| is_active | BOOLEAN | DEFAULT TRUE | Active flag |
| max_earners | INTEGER | NULLABLE | Max players who can earn |
| current_earners | INTEGER | DEFAULT 0 | Current earners |
| created_at | VARCHAR | NOT NULL | ISO timestamp |

**Indexes:**
- `badge_id`
- `season_name`
- `start_date`
- `end_date`

**Foreign Keys:**
- `badge_id` → `badges.id`

---

## Notifications

### `notifications`
Player notifications.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing ID |
| player_profile_id | INTEGER | INDEXED | References `player_profiles.id` |
| notification_type | VARCHAR | INDEXED | Type: game_start, turn_notification, etc. |
| message | VARCHAR | NOT NULL | Notification message |
| data | JSON | NULLABLE | Additional data |
| is_read | BOOLEAN | DEFAULT FALSE, INDEXED | Read status |
| created_at | VARCHAR | INDEXED | ISO timestamp |

**Indexes:**
- `player_profile_id`
- `notification_type`
- `is_read`
- `created_at`

**Foreign Keys:**
- `player_profile_id` → `player_profiles.id`

---

## Relationships Diagram

```
player_profiles (id)
    ├─── player_statistics (player_id)
    ├─── game_players (player_profile_id)
    ├─── game_player_results (player_profile_id)
    ├─── player_achievements (player_profile_id)
    ├─── player_badges_earned (player_profile_id)
    ├─── badge_progress (player_profile_id)
    ├─── player_series_progress (player_profile_id)
    ├─── daily_signups (player_profile_id)
    ├─── daily_messages (player_profile_id)
    ├─── player_availability (player_profile_id)
    ├─── match_players (player_profile_id)
    ├─── email_preferences (player_profile_id)
    ├─── ghin_scores (player_profile_id)
    ├─── ghin_handicap_history (player_profile_id)
    └─── notifications (player_profile_id)

game_state (game_id)
    └─── game_players (game_id)

game_records (id)
    └─── game_player_results (game_record_id)

courses (id)
    └─── holes (course_id)

badge_series (id)
    ├─── badges (series_id)
    └─── player_series_progress (series_id)

badges (id)
    ├─── player_badges_earned (badge_id)
    ├─── badge_progress (badge_id)
    └─── seasonal_badges (badge_id)

match_suggestions (id)
    └─── match_players (match_suggestion_id)
```

---

## Notes

### Data Type Conventions
- **VARCHAR**: All string fields use VARCHAR without explicit length
- **INTEGER**: Standard integers, used for boolean flags (0/1) for SQLite compatibility
- **FLOAT**: Decimal numbers (handicaps, earnings, rates)
- **JSON**: Complex objects and arrays
- **BOOLEAN**: True boolean type (converted to INTEGER for SQLite)
- **UUID**: UUID type for PostgreSQL, VARCHAR for SQLite

### Timestamp Format
All timestamps use ISO 8601 format strings (e.g., `2025-01-15T14:30:00Z`) stored as VARCHAR.

### Boolean Conventions
- SQLite-compatible tables use INTEGER (0/1)
- PostgreSQL-specific features use BOOLEAN

### JSON Field Patterns
Many tables use JSON for flexible data storage:
- `preferences` - Player settings
- `state` - Complete game state
- `holes_data` - Hole definitions
- `achievement_data` - Achievement metadata
- `trigger_condition` - Badge earning logic
- `progress_data` - Progress tracking

### Migration Strategy
Database supports both SQLite (local dev) and PostgreSQL (production). The schema accommodates both using helper functions for UUID fields.

---

## Common Queries

### Get Player with Statistics
```sql
SELECT p.*, s.*
FROM player_profiles p
LEFT JOIN player_statistics s ON p.id = s.player_id
WHERE p.id = ?
```

### Get Active Games
```sql
SELECT *
FROM game_state
WHERE game_status IN ('setup', 'in_progress')
ORDER BY created_at DESC
```

### Get Player Game History
```sql
SELECT gr.*, gpr.*
FROM game_records gr
JOIN game_player_results gpr ON gr.id = gpr.game_record_id
WHERE gpr.player_profile_id = ?
ORDER BY gr.completed_at DESC
```

### Get Leaderboard
```sql
SELECT
    p.name,
    s.games_played,
    s.games_won,
    s.total_earnings,
    CASE WHEN s.games_played > 0
         THEN CAST(s.games_won AS FLOAT) / s.games_played
         ELSE 0 END as win_rate
FROM player_profiles p
JOIN player_statistics s ON p.id = s.player_id
WHERE p.is_active = 1 AND p.is_ai = 0
ORDER BY s.total_earnings DESC
LIMIT 10
```

### Get Daily Signups
```sql
SELECT ds.*, p.email
FROM daily_signups ds
JOIN player_profiles p ON ds.player_profile_id = p.id
WHERE ds.date = ?
AND ds.status = 'signed_up'
ORDER BY ds.signup_time ASC
```
