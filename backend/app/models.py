from sqlalchemy import Column, Integer, String, Float, Boolean
from .database import Base
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
import os

# Helper function to get correct UUID column type based on database
def get_uuid_column():
    """Return appropriate UUID column type for the current database."""
    database_url = os.getenv("DATABASE_URL", "")
    if 'postgresql' in database_url or 'postgres' in database_url:
        return UUID(as_uuid=True)
    else:
        # For SQLite, use String to store UUID as text
        return String

class Rule(Base):
    __tablename__ = "rules"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)

# Enhanced Course model for proper course management
class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, nullable=True)
    total_par = Column(Integer)
    total_yards = Column(Integer)
    course_rating = Column(Float, nullable=True)
    slope_rating = Column(Float, nullable=True)
    holes_data = Column(JSON)  # Store hole details as JSON
    created_at = Column(String)
    updated_at = Column(String)

class Hole(Base):
    __tablename__ = "holes"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, index=True)
    hole_number = Column(Integer)
    par = Column(Integer)
    yards = Column(Integer)
    handicap = Column(Integer)  # Stroke index (1-18)
    description = Column(String, nullable=True)
    tee_box = Column(String, default="regular")  # regular, championship, forward, etc.

# For MVP: store the entire game state as a JSON blob
# Updated to support multiple active games with unique game_id
class GameStateModel(Base):
    __tablename__ = "game_state"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(get_uuid_column(), unique=True, index=True)  # Unique identifier for each game
    join_code = Column(String, unique=True, index=True, nullable=True)  # 6-char code for joining
    creator_user_id = Column(String, nullable=True)  # Auth0 user ID of game creator
    game_status = Column(String, default="setup")  # setup, in_progress, completed
    state = Column(JSON)
    created_at = Column(String)
    updated_at = Column(String)

# Track authenticated players in games
class GamePlayer(Base):
    __tablename__ = "game_players"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(get_uuid_column(), index=True)  # References GameStateModel.game_id
    player_slot_id = Column(String)  # e.g., "p1", "p2", "p3", "p4"
    user_id = Column(String, nullable=True)  # Auth0 user ID
    player_profile_id = Column(Integer, nullable=True)  # References PlayerProfile.id
    player_name = Column(String)  # Display name
    handicap = Column(Float)
    join_status = Column(String, default="pending")  # pending, joined, ready
    joined_at = Column(String, nullable=True)
    created_at = Column(String)

# Store simulation results for analysis
class SimulationResult(Base):
    __tablename__ = "simulation_results"
    id = Column(Integer, primary_key=True, index=True)
    course_name = Column(String, nullable=True)
    player_count = Column(Integer)
    simulation_count = Column(Integer)
    results_data = Column(JSON)
    created_at = Column(String)

# Player Profile Management
class PlayerProfile(Base):
    __tablename__ = "player_profiles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    email = Column(String, nullable=True, unique=True, index=True)  # Email for notifications
    handicap = Column(Float, default=18.0)
    ghin_id = Column(String, nullable=True, unique=True, index=True)  # GHIN ID for handicap lookup
    ghin_last_updated = Column(String, nullable=True)  # When GHIN data was last synced
    avatar_url = Column(String, nullable=True)
    created_at = Column(String)
    updated_at = Column(String, nullable=True)
    last_played = Column(String, nullable=True)
    preferences = Column(JSON, default=lambda: {
        "ai_difficulty": "medium",
        "preferred_game_modes": ["wolf_goat_pig"],
        "preferred_player_count": 4,
        "betting_style": "conservative",
        "display_hints": True
    })
    is_active = Column(Integer, default=1)  # SQLite uses integers for booleans
    is_ai = Column(Integer, default=0)
    playing_style = Column(String, nullable=True)
    description = Column(String, nullable=True)
    personality_traits = Column(JSON, nullable=True)
    strengths = Column(JSON, nullable=True)
    weaknesses = Column(JSON, nullable=True)

class PlayerStatistics(Base):
    __tablename__ = "player_statistics"
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, index=True)  # References PlayerProfile.id
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    total_earnings = Column(Float, default=0.0)
    holes_played = Column(Integer, default=0)
    holes_won = Column(Integer, default=0)
    avg_earnings_per_hole = Column(Float, default=0.0)
    betting_success_rate = Column(Float, default=0.0)
    successful_bets = Column(Integer, default=0)
    total_bets = Column(Integer, default=0)
    partnership_success_rate = Column(Float, default=0.0)
    partnerships_formed = Column(Integer, default=0)
    partnerships_won = Column(Integer, default=0)
    solo_attempts = Column(Integer, default=0)
    solo_wins = Column(Integer, default=0)
    # Score performance tracking (eagles, birdies, pars, etc.)
    eagles = Column(Integer, default=0)  # 2 or more under par
    birdies = Column(Integer, default=0)  # 1 under par
    pars = Column(Integer, default=0)  # Equal to par
    bogeys = Column(Integer, default=0)  # 1 over par
    double_bogeys = Column(Integer, default=0)  # 2 over par
    worse_than_double = Column(Integer, default=0)  # 3+ over par
    favorite_game_mode = Column(String, default="wolf_goat_pig")
    preferred_player_count = Column(Integer, default=4)
    best_hole_performance = Column(JSON, default=list)  # Track best performing holes
    worst_hole_performance = Column(JSON, default=list)  # Track challenging holes
    performance_trends = Column(JSON, default=list)  # Historical performance data
    last_updated = Column(String)

class GameRecord(Base):
    __tablename__ = "game_records"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(get_uuid_column(), unique=True, index=True)
    course_name = Column(String)
    game_mode = Column(String, default="wolf_goat_pig")
    player_count = Column(Integer)
    total_holes_played = Column(Integer, default=18)
    game_duration_minutes = Column(Integer, nullable=True)
    created_at = Column(String)
    completed_at = Column(String, nullable=True)
    game_settings = Column(JSON, default=dict)  # Store game configuration
    final_scores = Column(JSON, default=dict)  # Final leaderboard

class GamePlayerResult(Base):
    __tablename__ = "game_player_results"
    id = Column(Integer, primary_key=True, index=True)
    game_record_id = Column(Integer, index=True)  # References GameRecord.id
    player_profile_id = Column(Integer, index=True)  # References PlayerProfile.id
    player_name = Column(String)  # Denormalized for easier querying
    final_position = Column(Integer)  # 1st, 2nd, 3rd, etc.
    total_earnings = Column(Float, default=0.0)
    holes_won = Column(Integer, default=0)
    successful_bets = Column(Integer, default=0)
    total_bets = Column(Integer, default=0)
    partnerships_formed = Column(Integer, default=0)
    partnerships_won = Column(Integer, default=0)
    solo_attempts = Column(Integer, default=0)
    solo_wins = Column(Integer, default=0)
    hole_scores = Column(JSON, default=dict)  # Hole-by-hole scores
    betting_history = Column(JSON, default=list)  # Detailed betting decisions
    performance_metrics = Column(JSON, default=dict)  # Advanced metrics
    created_at = Column(String)

class PlayerAchievement(Base):
    __tablename__ = "player_achievements"
    id = Column(Integer, primary_key=True, index=True)
    player_profile_id = Column(Integer, index=True)
    achievement_type = Column(String)  # "first_win", "big_earner", "partnership_master", etc.
    achievement_name = Column(String)
    description = Column(String)
    earned_date = Column(String)
    game_record_id = Column(Integer, nullable=True)  # Game where achievement was earned
    achievement_data = Column(JSON, default=dict)  # Additional achievement details

# Daily Sign-up System Models
class DailySignup(Base):
    __tablename__ = "daily_signups"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True)  # YYYY-MM-DD format
    player_profile_id = Column(Integer, index=True)  # References PlayerProfile.id
    player_name = Column(String)  # Denormalized for easy querying
    signup_time = Column(String)  # ISO timestamp when they signed up
    preferred_start_time = Column(String, nullable=True)  # e.g., "4:30 PM", "morning", etc.
    notes = Column(String, nullable=True)  # Optional player notes
    status = Column(String, default="signed_up")  # signed_up, cancelled, played
    created_at = Column(String)
    updated_at = Column(String)

class PlayerAvailability(Base):
    __tablename__ = "player_availability"
    id = Column(Integer, primary_key=True, index=True)
    player_profile_id = Column(Integer, index=True)  # References PlayerProfile.id
    day_of_week = Column(Integer)  # 0=Monday, 1=Tuesday, ..., 6=Sunday
    available_from_time = Column(String, nullable=True)  # e.g., "4:30 PM"
    available_to_time = Column(String, nullable=True)  # e.g., "8:00 PM"
    is_available = Column(Integer, default=1)  # 1=available, 0=not available
    notes = Column(String, nullable=True)  # e.g., "Only after work"
    created_at = Column(String)
    updated_at = Column(String)

class EmailPreferences(Base):
    __tablename__ = "email_preferences"
    id = Column(Integer, primary_key=True, index=True)
    player_profile_id = Column(Integer, index=True)  # References PlayerProfile.id
    daily_signups_enabled = Column(Integer, default=1)  # Receive daily signup emails
    signup_confirmations_enabled = Column(Integer, default=1)  # When someone signs up
    signup_reminders_enabled = Column(Integer, default=1)  # Reminders to sign up
    game_invitations_enabled = Column(Integer, default=1)  # Direct game invitations
    weekly_summary_enabled = Column(Integer, default=1)  # Weekly activity summary
    email_frequency = Column(String, default="daily")  # daily, weekly, monthly, never
    preferred_notification_time = Column(String, default="8:00 AM")  # When to send dailies
    created_at = Column(String)
    updated_at = Column(String)

class DailyMessage(Base):
    __tablename__ = "daily_messages"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True)  # YYYY-MM-DD format
    player_profile_id = Column(Integer, index=True)  # References PlayerProfile.id
    player_name = Column(String)  # Denormalized for easy querying
    message = Column(String)  # The actual message content
    message_time = Column(String)  # ISO timestamp when message was posted
    is_active = Column(Integer, default=1)  # 1=active, 0=deleted/hidden
    created_at = Column(String)
    updated_at = Column(String)

# GHIN Integration Models
class GHINScore(Base):
    __tablename__ = "ghin_scores"
    id = Column(Integer, primary_key=True, index=True)
    player_profile_id = Column(Integer, index=True)  # References PlayerProfile.id
    ghin_id = Column(String, index=True)  # GHIN ID
    score_date = Column(String, index=True)  # Date the round was played (YYYY-MM-DD)
    course_name = Column(String)  # Name of the golf course
    tees = Column(String, nullable=True)  # Tee box played (e.g., "Blue", "Championship")
    score = Column(Integer)  # Total score for the round
    course_rating = Column(Float, nullable=True)  # Course rating for the tees played
    slope_rating = Column(Integer, nullable=True)  # Slope rating for the tees played
    differential = Column(Float, nullable=True)  # Score differential for handicap calculation
    posted = Column(Integer, default=1)  # Whether this score counts for handicap (1=yes, 0=no)
    handicap_index_at_time = Column(Float, nullable=True)  # Player's handicap when this score was posted
    synced_at = Column(String)  # When this score was synced from GHIN
    created_at = Column(String)
    updated_at = Column(String)

class GHINHandicapHistory(Base):
    __tablename__ = "ghin_handicap_history"
    id = Column(Integer, primary_key=True, index=True)
    player_profile_id = Column(Integer, index=True)  # References PlayerProfile.id
    ghin_id = Column(String, index=True)  # GHIN ID
    effective_date = Column(String, index=True)  # Date this handicap became effective (YYYY-MM-DD)
    handicap_index = Column(Float)  # The handicap index value
    revision_reason = Column(String, nullable=True)  # Why the handicap changed
    scores_used_count = Column(Integer, nullable=True)  # Number of scores used in calculation
    synced_at = Column(String)  # When this record was synced from GHIN
    created_at = Column(String)

# Matchmaking Models
class MatchSuggestion(Base):
    __tablename__ = "match_suggestions"
    id = Column(Integer, primary_key=True, index=True)
    day_of_week = Column(Integer)  # 0=Monday, 6=Sunday
    suggested_date = Column(String, nullable=True)  # Specific date if scheduled
    overlap_start = Column(String)  # Start time of availability overlap
    overlap_end = Column(String)  # End time of availability overlap
    suggested_tee_time = Column(String)  # Recommended tee time
    match_quality_score = Column(Float)  # Quality score of the match
    status = Column(String, default="pending")  # pending, accepted, declined, expired
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(String, nullable=True)
    created_at = Column(String)
    expires_at = Column(String)  # When this suggestion expires
    
class MatchPlayer(Base):
    __tablename__ = "match_players"
    id = Column(Integer, primary_key=True, index=True)
    match_suggestion_id = Column(Integer, index=True)  # References MatchSuggestion.id
    player_profile_id = Column(Integer, index=True)  # References PlayerProfile.id
    player_name = Column(String)
    player_email = Column(String)
    response = Column(String, nullable=True)  # accepted, declined, no_response
    responded_at = Column(String, nullable=True)
    created_at = Column(String)
    updated_at = Column(String, nullable=True)

# Achievement Badge System Models
class Badge(Base):
    __tablename__ = "badges"
    id = Column(Integer, primary_key=True, index=True)
    badge_id = Column(Integer, unique=True, index=True)  # Unique badge identifier
    name = Column(String, index=True)
    description = Column(String)
    category = Column(String, index=True)  # achievement, progression, seasonal, rare_event, collectible_series
    rarity = Column(String, index=True)  # common, rare, epic, legendary, mythic
    image_url = Column(String, nullable=True)  # Badge image path or URL
    trigger_condition = Column(JSON)  # Logic for earning badge
    trigger_type = Column(String)  # one_time, career_milestone, series_completion, seasonal
    max_supply = Column(Integer, nullable=True)  # NULL = unlimited (for limited edition badges)
    current_supply = Column(Integer, default=0)  # How many players have earned this
    points_value = Column(Integer, default=0)  # Point value for gamification
    is_active = Column(Boolean, default=True)
    series_id = Column(Integer, nullable=True, index=True)  # References BadgeSeries.id
    tier = Column(Integer, nullable=True)  # For progression badges (0=Bronze, 1=Silver, etc.)
    created_at = Column(String)
    updated_at = Column(String, nullable=True)

class PlayerBadgeEarned(Base):
    __tablename__ = "player_badges_earned"
    id = Column(Integer, primary_key=True, index=True)
    player_profile_id = Column(Integer, index=True)  # References PlayerProfile.id
    badge_id = Column(Integer, index=True)  # References Badge.id
    earned_at = Column(String, index=True)
    game_record_id = Column(Integer, nullable=True, index=True)  # Game where badge was earned
    serial_number = Column(Integer)  # Order earned (e.g., #47 of all players who earned this)
    showcase_position = Column(Integer, nullable=True)  # Position in player's badge showcase (1-6)
    is_favorited = Column(Boolean, default=False)
    created_at = Column(String)
    updated_at = Column(String, nullable=True)

class BadgeProgress(Base):
    __tablename__ = "badge_progress"
    id = Column(Integer, primary_key=True, index=True)
    player_profile_id = Column(Integer, index=True)  # References PlayerProfile.id
    badge_id = Column(Integer, index=True)  # References Badge.id
    current_progress = Column(Integer, default=0)  # e.g., 7/10 solo wins
    target_progress = Column(Integer)  # 10
    progress_percentage = Column(Float, default=0.0)  # 70.0
    last_progress_date = Column(String, nullable=True)  # When progress was last updated
    progress_data = Column(JSON, default=dict)  # Additional tracking data (streaks, specific achievements)
    created_at = Column(String)
    updated_at = Column(String)

class BadgeSeries(Base):
    __tablename__ = "badge_series"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # "Four Horsemen", "Course Conquerer"
    description = Column(String)
    category = Column(String)  # collectible, progression
    badge_count = Column(Integer)  # How many badges in series
    completion_badge_id = Column(Integer, nullable=True)  # Badge earned when series complete
    image_url = Column(String, nullable=True)  # Series artwork
    is_active = Column(Boolean, default=True)
    created_at = Column(String)

class PlayerSeriesProgress(Base):
    __tablename__ = "player_series_progress"
    id = Column(Integer, primary_key=True, index=True)
    player_profile_id = Column(Integer, index=True)  # References PlayerProfile.id
    series_id = Column(Integer, index=True)  # References BadgeSeries.id
    badges_earned = Column(Integer, default=0)  # How many badges collected
    badges_needed = Column(Integer)  # Total badges in series
    is_completed = Column(Boolean, default=False)
    completed_at = Column(String, nullable=True)
    progress_data = Column(JSON, default=dict)  # Which badges are earned
    created_at = Column(String)
    updated_at = Column(String)

class SeasonalBadge(Base):
    __tablename__ = "seasonal_badges"
    id = Column(Integer, primary_key=True, index=True)
    badge_id = Column(Integer, index=True)  # References Badge.id
    season_name = Column(String, index=True)  # "January 2026", "Spring 2026"
    start_date = Column(String, index=True)  # YYYY-MM-DD
    end_date = Column(String, index=True)  # YYYY-MM-DD
    is_active = Column(Boolean, default=True)
    max_earners = Column(Integer, nullable=True)  # Limited number of players who can earn
    current_earners = Column(Integer, default=0)
    created_at = Column(String)

# Game Banner System
class GameBanner(Base):
    __tablename__ = "game_banners"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)  # Optional banner title
    message = Column(String)  # Banner message content
    banner_type = Column(String, default="info")  # info, warning, announcement, rules
    is_active = Column(Boolean, default=True)  # Whether banner is currently displayed
    background_color = Column(String, default="#3B82F6")  # Hex color code
    text_color = Column(String, default="#FFFFFF")  # Hex color code
    show_icon = Column(Boolean, default=True)  # Show icon based on type
    dismissible = Column(Boolean, default=False)  # Can users dismiss it
    created_at = Column(String)
    updated_at = Column(String, nullable=True)

# Notification System
class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    player_profile_id = Column(Integer, index=True)  # References PlayerProfile.id
    notification_type = Column(String, index=True)  # game_start, game_end, turn_notification, etc.
    message = Column(String)  # Notification message content
    data = Column(JSON, nullable=True)  # Optional additional data as JSON
    is_read = Column(Boolean, default=False, index=True)  # Read status
    created_at = Column(String, index=True)  # ISO timestamp when notification was created 