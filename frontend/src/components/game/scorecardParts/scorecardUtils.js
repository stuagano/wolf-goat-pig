// frontend/src/components/game/scorecardParts/scorecardUtils.js
// Pure helpers and shared cell styles for the Scorecard component.

export const HOLES = Array.from({ length: 18 }, (_, i) => i + 1);
export const FRONT_NINE = HOLES.slice(0, 9);
export const BACK_NINE = HOLES.slice(9, 18);

const EMPTY_HOLE_DATA = { quarters: null, strokes: null, quartersBreakdown: {}, bettingNarrative: null };

// Get course hole info (par, handicap, yards)
export const getCourseHoleInfo = (courseHoles, holeNumber) => {
  if (!Array.isArray(courseHoles) || courseHoles.length === 0) return null;
  if (typeof holeNumber !== 'number' || holeNumber < 1 || holeNumber > 18) return null;
  const holeInfo = courseHoles.find(h => h && typeof h.hole === 'number' && h.hole === holeNumber);
  return holeInfo || null;
};

// Returns a warning message when stroke allocation data is missing or incomplete, else null
export const getStrokeAllocationWarning = (strokeAllocation, players) => {
  if (!strokeAllocation || typeof strokeAllocation !== 'object' || Object.keys(strokeAllocation).length === 0) {
    return 'Stroke allocation data not available';
  }

  // Check if all players have stroke data
  const missingPlayers = players.filter(p => !strokeAllocation[p.id]);
  if (missingPlayers.length > 0) {
    return `Missing stroke data for: ${missingPlayers.map(p => p.name).join(', ')}`;
  }

  return null;
};

// Get stroke allocation for a player on a hole
// Returns null if data is genuinely missing (vs 0 which means no strokes on that hole)
export const getStrokesReceived = (strokeAllocation, playerId, holeNumber) => {
  if (!strokeAllocation || typeof strokeAllocation !== 'object') {
    // Data not available - return null to indicate missing, not 0
    return null;
  }
  if (!playerId || typeof holeNumber !== 'number') {
    return null;
  }
  const playerAllocation = strokeAllocation[playerId];
  if (!playerAllocation || typeof playerAllocation !== 'object') {
    // Player not in allocation - could be lowest handicap (0 strokes everywhere)
    // or missing data. Check if ANY player has allocation.
    const hasAnyAllocation = Object.keys(strokeAllocation).length > 0;
    if (hasAnyAllocation) {
      // Other players have data, this player genuinely has no strokes
      return 0;
    }
    return null; // No data at all
  }
  // Handle both string and number keys (JSON serialization converts int keys to strings)
  const strokes = playerAllocation[holeNumber] ?? playerAllocation[String(holeNumber)];
  return typeof strokes === 'number' ? strokes : 0;
};

// Check if a value is approximately equal to 0.5 (for half strokes)
export const isHalfStroke = (value) => {
  const fractional = value % 1;
  return Math.abs(fractional - 0.5) < 0.01;
};

// Get full strokes (integer part)
export const getFullStrokes = (value) => Math.floor(value);

// Check if value has a half-stroke component
export const hasHalfStroke = (value) => isHalfStroke(value);

// Get golf score indicator based on score relative to par
export const getScoreIndicator = (strokes, par) => {
  if (!strokes || !par) return null;

  const diff = strokes - par;

  if (diff <= -2) return { symbol: '⊚', color: '#4CAF50', label: 'Eagle or better', shape: 'circle' }; // Double circle
  if (diff === -1) return { symbol: '○', color: '#4CAF50', label: 'Birdie', shape: 'circle' }; // Circle
  if (diff === 0) return { symbol: null, color: '#000', label: 'Par', shape: 'none' }; // Plain number
  if (diff === 1) return { symbol: '□', color: '#f44336', label: 'Bogey', shape: 'square' }; // Square
  if (diff === 2) return { symbol: '⊡', color: '#f44336', label: 'Double Bogey', shape: 'square' }; // Double square
  if (diff >= 3) return { symbol: '△', color: '#f44336', label: 'Triple Bogey+', shape: 'triangle' }; // Triangle

  return null;
};

// Get hole data for a player
export const getHoleData = (holeHistory, holeNumber, playerId) => {
  if (!Array.isArray(holeHistory)) return { ...EMPTY_HOLE_DATA };
  if (typeof holeNumber !== 'number' || !playerId) return { ...EMPTY_HOLE_DATA };

  const holeData = holeHistory.find(h => h && typeof h.hole === 'number' && h.hole === holeNumber);
  if (!holeData) return { ...EMPTY_HOLE_DATA };

  const pointsDelta = (holeData.points_delta && typeof holeData.points_delta === 'object')
    ? holeData.points_delta
    : {};
  const grossScores = (holeData.gross_scores && typeof holeData.gross_scores === 'object')
    ? holeData.gross_scores
    : {};
  const quartersBreakdown = (holeData.quarters_breakdown && typeof holeData.quarters_breakdown === 'object')
    ? holeData.quarters_breakdown[playerId] || {}
    : {};
  const bettingNarrative = holeData.betting_narrative || null;

  const quarters = pointsDelta[playerId];
  const strokes = grossScores[playerId];

  return {
    quarters: typeof quarters === 'number' ? quarters : null,
    strokes: typeof strokes === 'number' ? strokes : null,
    quartersBreakdown: quartersBreakdown,
    bettingNarrative: bettingNarrative
  };
};

// Get hole-level data (not player-specific)
export const getHoleInfo = (holeHistory, holeNumber) => {
  if (!Array.isArray(holeHistory)) return null;
  if (typeof holeNumber !== 'number') return null;
  const holeData = holeHistory.find(h => h && typeof h.hole === 'number' && h.hole === holeNumber);
  return holeData || null;
};

// Whether a hole has been played (before the current hole, or present in history).
// Returns a truthy/falsy value (may be the hole record itself), matching original semantics.
export const isHoleCompleted = (hole, currentHole, holeHistory) =>
  hole < currentHole || (Array.isArray(holeHistory) && holeHistory.find(h => h && h.hole === hole));

const sumNine = (holeHistory, playerId, nine, field) =>
  nine.reduce((sum, hole) => {
    const value = getHoleData(holeHistory, hole, playerId)[field];
    return sum + (typeof value === 'number' ? value : 0);
  }, 0);

// Calculate front 9, back 9, and total quarters
export const calculateTotals = (holeHistory, playerId) => {
  if (!playerId) return { front9: 0, back9: 0, total: 0 };
  const front9 = sumNine(holeHistory, playerId, FRONT_NINE, 'quarters');
  const back9 = sumNine(holeHistory, playerId, BACK_NINE, 'quarters');
  return { front9, back9, total: front9 + back9 };
};

// Calculate golf score (strokes) totals
export const calculateStrokeTotals = (holeHistory, playerId) => {
  if (!playerId) return { front9: 0, back9: 0, total: 0 };
  const front9 = sumNine(holeHistory, playerId, FRONT_NINE, 'strokes');
  const back9 = sumNine(holeHistory, playerId, BACK_NINE, 'strokes');
  return { front9, back9, total: front9 + back9 };
};

// Sum par for a slice of course holes
export const sumPar = (courseHoles, start, end) =>
  Array.isArray(courseHoles)
    ? courseHoles.slice(start, end).reduce((sum, h) => sum + (h && typeof h.par === 'number' ? h.par : 0), 0)
    : 0;

// Abbreviated betting text for the BETS row: wager and any special actions
export const abbreviateBetting = (narrative, wager) => (
  narrative
    ? narrative.split(' → ').map(part => {
        // Abbreviate common terms
        if (part.includes('doubles')) return '2×';
        if (part.includes('floats')) return 'F';
        if (part.includes('Duncan')) return 'D';
        if (part.includes('Option')) return 'O';
        if (part === 'accepted') return '✓';
        if (part === 'declined') return '✗';
        return '';
      }).filter(Boolean).join('')
    : (wager && wager > 2 ? `${wager}Q` : '')
);

// Signed display for a quarters value: "+3", "-2", or the fallback for zero
export const formatSignedQuarters = (value, zeroLabel = '-') =>
  value !== 0 ? (value > 0 ? `+${value}` : value) : zeroLabel;

// Color for a quarters total: green if positive, red if negative, else fallback
export const quartersColor = (value, neutral = 'inherit') =>
  value > 0 ? '#4CAF50' : value < 0 ? '#f44336' : neutral;

export const isHumanPlayer = (player) => player.is_human || player.id === 'human';

export const displayName = (player) => (typeof player.name === 'string' ? player.name : 'Unknown');

export const headerCellStyle = {
  padding: '8px 4px',
  textAlign: 'center',
  borderBottom: '2px solid rgba(0, 0, 0, 0.1)',
  fontSize: '11px',
  fontWeight: 'bold'
};

export const cellStyle = {
  padding: '6px 4px',
  textAlign: 'center',
  borderBottom: '1px solid rgba(0, 0, 0, 0.05)',
  fontSize: '12px'
};

export const totalCellStyle = {
  ...cellStyle,
  borderLeft: '2px solid rgba(0, 0, 0, 0.1)',
  backgroundColor: 'rgba(0, 0, 0, 0.03)'
};
