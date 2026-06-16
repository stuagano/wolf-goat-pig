// Pure helpers for the scorekeeper's hole-history list.
//
// holeHistory is an array of hole-result objects, each with a numeric `.hole`
// (1-18). Two correctness rules, mirrored on the backend (games_holes.py):
//   1. A given hole appears at most once. Offline replay / re-submitting a
//      played hole must REPLACE, never append — duplicates inflate standings
//      (money) and corrupt the completion count.
//   2. A round is complete only when every hole 1..N actually has data, not
//      when the list happens to be N long.

const STANDARD_ROUND_HOLES = 18;

/**
 * Insert or replace a hole result, keyed by `.hole`. Last write wins.
 * Returns a new array (does not mutate the input).
 */
export function upsertHole(holeHistory, holeResult) {
  const exists = holeHistory.some((h) => h.hole === holeResult.hole);
  if (exists) {
    return holeHistory.map((h) =>
      h.hole === holeResult.hole ? holeResult : h,
    );
  }
  return [...holeHistory, holeResult];
}

/**
 * True when holes 1..totalHoles are ALL present in holeHistory (distinct),
 * regardless of how many entries the list has.
 */
export function allHolesPlayed(holeHistory, totalHoles = STANDARD_ROUND_HOLES) {
  const played = new Set(holeHistory.map((h) => h.hole));
  for (let n = 1; n <= totalHoles; n += 1) {
    if (!played.has(n)) return false;
  }
  return true;
}
