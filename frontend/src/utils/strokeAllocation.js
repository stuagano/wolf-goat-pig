/**
 * Stroke Allocation Utility
 *
 * Calculates stroke allocation for golf match play using the Creecher Feature rules.
 * The Creecher Feature modifies stroke distribution for high handicap players.
 *
 * This utility consolidates the stroke allocation logic that was previously
 * duplicated across SimpleScorekeeper.jsx and Scorecard.jsx.
 */

/**
 * Calculate strokes received for a given hole based on net handicap and stroke index
 *
 * @param {number} netHandicap - Player's handicap relative to lowest handicap player
 * @param {number} strokeIndex - Hole difficulty (1 = hardest, 18 = easiest)
 * @returns {number} - Strokes received (0, 0.5, 1, or more)
 */
export const getStrokesForHole = (netHandicap, strokeIndex) => {
  if (!netHandicap || netHandicap <= 0 || !strokeIndex) return 0;

  const fullHandicap = Math.floor(netHandicap);
  const hasFractional = (netHandicap % 1) >= 0.5;

  // Creecher Feature implementation
  if (netHandicap <= 6) {
    // All allocated holes get 0.5
    return strokeIndex <= fullHandicap ? 0.5 : 0;
  } else if (netHandicap <= 18) {
    // Easiest 6 of allocated holes get 0.5, rest get 1.0
    if (strokeIndex <= fullHandicap) {
      const easiestSix = Array.from({ length: fullHandicap }, (_, idx) => fullHandicap - idx);
      return easiestSix.slice(0, 6).includes(strokeIndex) ? 0.5 : 1.0;
    }
    // Fractional: add 0.5 to next hole
    if (hasFractional && strokeIndex === fullHandicap + 1) {
      return 0.5;
    }
    return 0;
  } else {
    // Handicap > 18
    // Base 18: holes 13-18 get 0.5, holes 1-12 get 1.0
    const extraStrokes = fullHandicap - 18;
    const extraHalfStrokes = extraStrokes * 2;

    if (strokeIndex >= 13 && strokeIndex <= 18) {
      // Easiest 6 holes get base 0.5
      const halfsNeeded = extraHalfStrokes;
      const holesGettingExtra = Math.min(halfsNeeded, 12);
      if (strokeIndex <= holesGettingExtra) {
        return 1.0; // 0.5 base + 0.5 extra
      }
      return 0.5;
    } else {
      // Hardest 12 holes get base 1.0
      const halfsNeeded = extraHalfStrokes;
      const holesGettingExtra = Math.min(halfsNeeded, 12);
      if (strokeIndex <= holesGettingExtra) {
        return 1.5; // 1.0 base + 0.5 extra
      }
      return 1.0;
    }
  }
};

/**
 * Calculate net handicaps for all players relative to the lowest handicap player
 *
 * @param {Array} players - Array of player objects with handicap property
 * @returns {Object} - Map of playerId to net handicap
 */
export const calculateNetHandicaps = (players) => {
  if (!Array.isArray(players) || players.length === 0) return {};

  const playerHandicaps = players.reduce((acc, player) => {
    acc[player.id] = player.handicap || 0;
    return acc;
  }, {});

  const lowestHandicap = Math.min(...Object.values(playerHandicaps));

  const netHandicaps = {};
  Object.entries(playerHandicaps).forEach(([playerId, handicap]) => {
    netHandicaps[playerId] = Math.max(0, handicap - lowestHandicap);
  });

  return netHandicaps;
};

/**
 * Calculate complete stroke allocation for all players across all 18 holes
 *
 * @param {Array} players - Array of player objects with id and handicap
 * @param {Array} courseHoles - Array of hole objects with hole_number and handicap (stroke index)
 * @returns {Object} - Nested object: { playerId: { holeNumber: strokes } }
 */
export const calculateStrokeAllocation = (players, courseHoles) => {
  if (!Array.isArray(players) || players.length === 0) return {};
  if (!Array.isArray(courseHoles) || courseHoles.length === 0) return {};

  const netHandicaps = calculateNetHandicaps(players);
  const allocation = {};

  players.forEach(player => {
    allocation[player.id] = {};
    const netHandicap = netHandicaps[player.id];

    for (let holeNum = 1; holeNum <= 18; holeNum++) {
      const holeData = courseHoles.find(h => h.hole_number === holeNum);
      if (holeData?.handicap) {
        allocation[player.id][holeNum] = getStrokesForHole(netHandicap, holeData.handicap);
      } else {
        allocation[player.id][holeNum] = 0;
      }
    }
  });

  return allocation;
};

/**
 * Get players who receive strokes on a specific hole
 *
 * @param {Array} players - Array of player objects
 * @param {number} holeNumber - Current hole number (1-18)
 * @param {Array} courseHoles - Course hole data with handicap (stroke index)
 * @returns {Array} - Array of { player, strokes } for players getting strokes
 */
export const getPlayersWithStrokesOnHole = (players, holeNumber, courseHoles) => {
  if (!Array.isArray(players) || !Array.isArray(courseHoles)) return [];

  const holeData = courseHoles.find(h => h.hole_number === holeNumber);
  if (!holeData?.handicap) return [];

  const strokeIndex = holeData.handicap;
  const netHandicaps = calculateNetHandicaps(players);

  return players
    .map(player => ({
      ...player,
      strokes: getStrokesForHole(netHandicaps[player.id], strokeIndex)
    }))
    .filter(p => p.strokes > 0);
};

/**
 * Format strokes for display (e.g., 0.5 -> "1/2 STROKE", 1 -> "1 STROKE")
 *
 * @param {number} strokes - Number of strokes
 * @returns {string} - Formatted string for display
 */
export const formatStrokesDisplay = (strokes) => {
  if (strokes === 0.5) return '1/2 STROKE';
  if (strokes === 1) return '1 STROKE';
  if (strokes === 1.5) return '1 1/2 STROKES';
  return `${strokes} STROKES`;
};

export default {
  getStrokesForHole,
  calculateNetHandicaps,
  calculateStrokeAllocation,
  getPlayersWithStrokesOnHole,
  formatStrokesDisplay
};
