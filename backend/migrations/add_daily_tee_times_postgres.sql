-- The club's posted tee times for one day (free text), shown on the signup page.
CREATE TABLE IF NOT EXISTS daily_tee_times (
    date VARCHAR PRIMARY KEY,
    tee_times TEXT NOT NULL DEFAULT '',
    updated_by_profile_id INTEGER REFERENCES player_profiles(id),
    updated_at VARCHAR NOT NULL
);
