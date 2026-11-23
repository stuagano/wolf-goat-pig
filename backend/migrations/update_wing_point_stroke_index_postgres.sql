-- Official Wing Point men's stroke index from the club scorecard
-- (https://www.wingpointgolf.com/public/golf/scorecard-490.html, also GolfPass).
-- The previous BlueGolf card had men's holes 5/6 and 14/15 swapped.
-- holes.handicap is the men's stroke index. There is no women's handicap column.
-- Idempotent: re-running sets the same values and leaves other courses alone.
UPDATE holes
SET handicap = CASE hole_number
    WHEN 1 THEN 5
    WHEN 2 THEN 15
    WHEN 3 THEN 1
    WHEN 4 THEN 17
    WHEN 5 THEN 9
    WHEN 6 THEN 7
    WHEN 7 THEN 13
    WHEN 8 THEN 11
    WHEN 9 THEN 3
    WHEN 10 THEN 16
    WHEN 11 THEN 2
    WHEN 12 THEN 14
    WHEN 13 THEN 18
    WHEN 14 THEN 10
    WHEN 15 THEN 8
    WHEN 16 THEN 4
    WHEN 17 THEN 12
    WHEN 18 THEN 6
    ELSE handicap
END
WHERE course_id IN (
    SELECT id FROM courses WHERE name = 'Wing Point Golf & Country Club'
);
