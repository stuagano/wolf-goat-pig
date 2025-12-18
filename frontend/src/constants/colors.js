/**
 * Centralized Color Constants for Wolf Goat Pig
 *
 * This file consolidates all color definitions used across the application.
 * Colors are organized by category for easy maintenance and consistency.
 */

// ============================================================================
// UI Colors - General application colors
// ============================================================================
export const UI_COLORS = {
  // Primary brand colors
  primary: '#1976d2',      // Deep blue - main brand color
  primaryLight: '#64b5f6', // Light blue variant
  primaryDark: '#1565c0',  // Dark blue variant

  // Secondary/accent colors
  accent: '#00bcd4',       // Cyan - complementary accent
  accentLight: '#4dd0e1',  // Light cyan
  accentDark: '#0097a7',   // Dark cyan

  // Semantic colors
  success: '#388e3c',      // Green - success states
  successLight: '#66bb6a', // Light green
  successDark: '#1b5e20',  // Dark green

  warning: '#ff9800',      // Orange - warning states
  warningLight: '#ffa726', // Light orange
  warningDark: '#f57c00',  // Dark orange

  error: '#d32f2f',        // Red - error states
  errorLight: '#ef5350',   // Light red
  errorDark: '#b71c1c',    // Dark red

  // Neutral colors
  bg: '#f9fafe',           // App background
  card: '#fff',            // Card/paper background
  border: '#e0e0e0',       // Default border color
  borderMedium: '#bdbdbd', // Medium border color
  text: '#222',            // Primary text
  textSecondary: '#757575', // Secondary text
  muted: '#888',           // Muted/disabled text

  // Special game colors
  hoepfinger: '#9c27b0',   // Purple - Hoepfinger phase
  vinnie: '#795548',       // Brown - Vinnie variation
  gold: '#f1c40f',         // Gold - highlights
  purple: '#9b59b6',       // Alternative purple
};

// ============================================================================
// Golf-Specific Colors - Course terrain and features
// ============================================================================
export const GOLF_COLORS = {
  // Terrain types
  teeBox: '#8B4513',       // Brown tee box
  fairway: '#90EE90',      // Light green fairway
  fairwayBright: '#22C55E', // Bright fairway green
  rough: '#228B22',        // Dark green rough
  roughTan: '#D2B48C',     // Tan rough (alternative)
  bunker: '#F4A460',       // Sandy beige bunker
  sandTrap: '#D2B48C',     // Sand trap color
  green: '#006400',        // Dark green putting surface
  greenBright: '#00FF00',  // Bright green (visualization)
  water: '#4682B4',        // Steel blue water hazard
  waterLight: 'rgba(70, 130, 180, 0.6)', // Transparent water

  // Course element colors
  hole: '#000000',         // Black hole
  pin: '#FF0000',          // Red pin/flag
  lineOfScrimmage: '#d32f2f', // Red line of scrimmage marker

  // Player position colors
  humanPlayer: '#2196F3',  // Blue for human player
  computerPlayer1: '#F44336', // Red for AI player 1
  computerPlayer2: '#FFC107', // Yellow for AI player 2
  computerPlayer3: '#FF9800', // Orange for AI player 3
};

// ============================================================================
// Betting Colors - Betting odds and risk indicators
// ============================================================================
export const BETTING_COLORS = {
  // Win/Loss indicators
  favorable: '#4caf50',    // Green - favorable odds
  unfavorable: '#f44336',  // Red - unfavorable odds
  neutral: '#757575',      // Gray - neutral

  // Risk levels
  riskLow: '#388e3c',      // Green - low risk
  riskMedium: '#ff9800',   // Orange - medium risk
  riskHigh: '#d32f2f',     // Red - high risk

  // Risk icons (for reference, not actual colors)
  // Low: 🟢, Medium: 🟡, High: 🔴

  // Value indicators
  positiveValue: '#4caf50', // Green - positive expected value
  negativeValue: '#f44336', // Red - negative expected value
  neutralValue: '#757575',  // Gray - neutral value
};

// ============================================================================
// Shot Quality Colors - Shot result quality indicators
// ============================================================================
export const SHOT_QUALITY_COLORS = {
  excellent: '#388e3c',    // Green - excellent shot
  good: '#4caf50',         // Light green - good shot
  average: '#ff9800',      // Orange - average shot
  poor: '#ff5722',         // Deep orange - poor shot
  terrible: '#d32f2f',     // Red - terrible shot
  unknown: '#888',         // Gray - unknown quality
};

// ============================================================================
// Game Phase Colors - Different game phase indicators
// ============================================================================
export const GAME_PHASE_COLORS = {
  regular: '#1976d2',      // Blue - regular play
  vinnieVariation: '#795548', // Brown - Vinnie variation
  hoepfinger: '#9c27b0',   // Purple - Hoepfinger phase
  default: '#888',         // Gray - default/unknown
};

// ============================================================================
// Helper Functions - Utility functions for color selection
// ============================================================================

/**
 * Get risk level color based on risk string
 * @param {string} risk - Risk level ('low', 'medium', 'high')
 * @returns {string} Hex color code
 */
export const getRiskColor = (risk) => {
  switch (risk?.toLowerCase()) {
    case 'low':
      return BETTING_COLORS.riskLow;
    case 'medium':
      return BETTING_COLORS.riskMedium;
    case 'high':
      return BETTING_COLORS.riskHigh;
    default:
      return UI_COLORS.muted;
  }
};

/**
 * Get risk level icon emoji
 * @param {string} risk - Risk level ('low', 'medium', 'high')
 * @returns {string} Emoji icon
 */
export const getRiskIcon = (risk) => {
  switch (risk?.toLowerCase()) {
    case 'low':
      return '🟢';
    case 'medium':
      return '🟡';
    case 'high':
      return '🔴';
    default:
      return '⚪';
  }
};

/**
 * Get shot quality color based on quality string
 * @param {string} quality - Shot quality ('excellent', 'good', 'average', 'poor', 'terrible')
 * @returns {string} Hex color code
 */
export const getShotQualityColor = (quality) => {
  switch (quality?.toLowerCase()) {
    case 'excellent':
      return SHOT_QUALITY_COLORS.excellent;
    case 'good':
      return SHOT_QUALITY_COLORS.good;
    case 'average':
      return SHOT_QUALITY_COLORS.average;
    case 'poor':
      return SHOT_QUALITY_COLORS.poor;
    case 'terrible':
      return SHOT_QUALITY_COLORS.terrible;
    default:
      return SHOT_QUALITY_COLORS.unknown;
  }
};

/**
 * Get shot quality icon emoji
 * @param {string} quality - Shot quality ('excellent', 'good', 'average', 'poor', 'terrible')
 * @returns {string} Emoji icon
 */
export const getShotQualityIcon = (quality) => {
  switch (quality?.toLowerCase()) {
    case 'excellent':
      return '🏆';
    case 'good':
      return '👍';
    case 'average':
      return '👌';
    case 'poor':
      return '👎';
    case 'terrible':
      return '💥';
    default:
      return '⚪';
  }
};

/**
 * Get game phase color based on phase string
 * @param {string} phase - Game phase ('regular', 'vinnie_variation', 'hoepfinger')
 * @returns {string} Hex color code
 */
export const getPhaseColor = (phase) => {
  switch (phase?.toLowerCase()) {
    case 'regular':
      return GAME_PHASE_COLORS.regular;
    case 'vinnie_variation':
      return GAME_PHASE_COLORS.vinnieVariation;
    case 'hoepfinger':
      return GAME_PHASE_COLORS.hoepfinger;
    default:
      return GAME_PHASE_COLORS.default;
  }
};

/**
 * Get game phase icon emoji
 * @param {string} phase - Game phase ('regular', 'vinnie_variation', 'hoepfinger')
 * @returns {string} Emoji icon
 */
export const getPhaseIcon = (phase) => {
  switch (phase?.toLowerCase()) {
    case 'regular':
      return '⛳';
    case 'vinnie_variation':
      return '🐺';
    case 'hoepfinger':
      return '🎯';
    default:
      return '🏌️';
  }
};

/**
 * Get lie type color based on terrain
 * @param {string} lieType - Lie type ('tee', 'fairway', 'rough', 'bunker', 'green', 'in_hole')
 * @returns {string} Hex color code
 */
export const getLieColor = (lieType) => {
  switch (lieType?.toLowerCase()) {
    case 'tee':
      return GOLF_COLORS.teeBox;
    case 'fairway':
      return GOLF_COLORS.fairway;
    case 'rough':
      return GOLF_COLORS.rough;
    case 'bunker':
      return GOLF_COLORS.bunker;
    case 'green':
      return GOLF_COLORS.green;
    case 'in_hole':
      return GOLF_COLORS.hole;
    default:
      return '#808080'; // Gray default
  }
};

/**
 * Get player color by index (for visualization)
 * @param {number} index - Player index
 * @returns {string} Hex color code
 */
export const getPlayerColor = (index) => {
  const colors = [
    UI_COLORS.accent,
    UI_COLORS.success,
    UI_COLORS.warning,
    UI_COLORS.purple,
    UI_COLORS.error,
    UI_COLORS.gold
  ];
  return colors[index % colors.length];
};

// Export all color groups as a single object for convenience
export default {
  UI_COLORS,
  GOLF_COLORS,
  BETTING_COLORS,
  SHOT_QUALITY_COLORS,
  GAME_PHASE_COLORS,
  getRiskColor,
  getRiskIcon,
  getShotQualityColor,
  getShotQualityIcon,
  getPhaseColor,
  getPhaseIcon,
  getLieColor,
  getPlayerColor,
};
