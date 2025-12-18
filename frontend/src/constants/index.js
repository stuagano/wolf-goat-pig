/**
 * Constants Module - Exports all application constants
 */

// Export all color constants and utilities
export {
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
} from './colors';

// Re-export the default colors object
export { default as colors } from './colors';
