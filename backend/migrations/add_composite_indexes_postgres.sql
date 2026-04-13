-- Migration: add composite indexes for common query patterns

-- DailySignup: dedup checks by (date, player_profile_id)
CREATE INDEX IF NOT EXISTS ix_daily_signups_date_player
    ON daily_signups (date, player_profile_id);

-- LegacyRound: dedup checks by (date, group, member)
CREATE INDEX IF NOT EXISTS ix_legacy_rounds_date_group_member
    ON legacy_rounds (date, "group", member);

-- GamePlayer: lookups by (game_id, player_slot_id)
CREATE INDEX IF NOT EXISTS ix_game_players_game_slot
    ON game_players (game_id, player_slot_id);

-- GamePlayer: lookups by (game_id, user_id)
CREATE INDEX IF NOT EXISTS ix_game_players_game_user
    ON game_players (game_id, user_id);

-- GHINScore: lookups by (player_profile_id, score_date)
CREATE INDEX IF NOT EXISTS ix_ghin_scores_player_date
    ON ghin_scores (player_profile_id, score_date);
