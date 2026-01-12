/**
 * Betting Helpers
 *
 * Shared utility functions for betting-related UI components.
 * Includes action icons, betting-specific formatting, and EV calculations.
 *
 * Note: Color constants and risk helpers are in constants/colors.js
 */

import { BETTING_COLORS, getRiskColor, getRiskIcon } from '../constants/colors';

// Re-export for backwards compatibility
export { BETTING_COLORS, getRiskColor, getRiskIcon };

/**
 * Get emoji icon for betting action
 * @param {string} action - Betting action type
 * @returns {string} Emoji icon
 */
export const getActionIcon = (action) => {
  const actionIcons = {
    'offer_double': '💰',
    'accept_double': '✅',
    'decline_double': '❌',
    'go_solo': '👤',
    'accept_partnership': '🤝',
    'decline_partnership': '🚫',
    'pass': '⏭️',
    'offer': '💰',
    'accept': '✅',
    'decline': '❌'
  };

  return actionIcons[action] || '🎯';
};

/**
 * Get human-readable description for betting action
 * @param {string} action - Betting action type
 * @returns {string} Action description
 */
export const getActionDescription = (action) => {
  const descriptions = {
    'offer_double': 'Double the stakes - higher risk, higher reward',
    'accept_double': 'Accept the double - stakes are now doubled',
    'decline_double': 'Decline double - concede the hole',
    'go_solo': 'Play alone against everyone - double stakes',
    'accept_partnership': 'Form a partnership with captain',
    'decline_partnership': 'Decline partnership - captain goes solo',
    'pass': 'Skip this betting opportunity'
  };

  return descriptions[action] || 'Make your betting decision';
};

/**
 * Format probability as percentage
 * @param {number} prob - Probability value (0-1)
 * @returns {string} Formatted percentage string
 */
export const formatProbability = (prob) => {
  if (prob === null || prob === undefined) return 'N/A';
  return `${(prob * 100).toFixed(1)}%`;
};

/**
 * Format value with + or - sign
 * @param {number} value - Numeric value
 * @returns {string} Formatted value with sign
 */
export const formatValue = (value) => {
  if (value === null || value === undefined) return 'N/A';
  return value >= 0 ? `+${value.toFixed(2)}` : value.toFixed(2);
};

/**
 * Calculate expected value for a betting action
 * @param {string} action - Betting action type
 * @param {Object} analysis - Probability analysis object
 * @param {Object} gameState - Current game state
 * @returns {number|null} Expected value or null if calculation not possible
 */
export const calculateExpectedValue = (action, analysis, gameState) => {
  if (!analysis) return null;

  const baseWager = gameState?.base_wager || 1;
  const currentWager = gameState?.holeState?.betting?.current_wager || baseWager;

  // Simplified EV calculation based on win probability
  const winProb = analysis.win_probability || 0.5;
  const loseProb = 1 - winProb;

  switch (action) {
    case 'offer_double':
    case 'accept_double':
      return (winProb * currentWager * 2) - (loseProb * currentWager * 2);
    case 'go_solo':
      return (winProb * currentWager * 3) - (loseProb * currentWager * 2);
    default:
      return (winProb * currentWager) - (loseProb * currentWager);
  }
};

/**
 * Get color based on probability value
 * @param {number} probability - Probability value (0-1)
 * @returns {string} Hex color code
 */
export const getProbabilityColor = (probability) => {
  if (probability === null || probability === undefined) {
    return BETTING_COLORS.neutral;
  }

  if (probability > 0.6) {
    return BETTING_COLORS.favorable;
  } else if (probability > 0.4) {
    return BETTING_COLORS.neutral;
  } else {
    return BETTING_COLORS.unfavorable;
  }
};

/**
 * Format action text for display
 * @param {string} action - Action string in snake_case
 * @returns {string} Formatted action text in Title Case
 */
export const formatActionText = (action) => {
  if (!action) return '';
  return action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};
