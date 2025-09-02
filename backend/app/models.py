from sqlalchemy import Column, Integer, String, Float
from .database import Base
from sqlalchemy.types import JSON

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
class GameStateModel(Base):
    __tablename__ = "game_state"
    id = Column(Integer, primary_key=True, index=True)
    state = Column(JSON)

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
    favorite_game_mode = Column(String, default="wolf_goat_pig")
    preferred_player_count = Column(Integer, default=4)
    best_hole_performance = Column(JSON, default=list)  # Track best performing holes
    worst_hole_performance = Column(JSON, default=list)  # Track challenging holes
    performance_trends = Column(JSON, default=list)  # Historical performance data
    last_updated = Column(String)

class GameRecord(Base):
    __tablename__ = "game_records"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, unique=True, index=True)
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