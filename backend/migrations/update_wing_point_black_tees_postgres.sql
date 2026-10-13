-- Wing Point plays off the Black tees (men): 71.1 rating / 130 slope, par 71,
-- 6,093 yards. Course handicaps are computed from these (11.8 index -> 14).
-- The row previously held placeholder values (73.2 / 135 / par 72 / 7,050 yd),
-- and par 72 disagreed with its own holes, which add up to 71.
-- Idempotent: re-running sets the same values.
UPDATE courses
SET course_rating = 71.1,
    slope_rating = 130,
    total_par = 71,
    total_yards = 6093
WHERE name = 'Wing Point Golf & Country Club';
