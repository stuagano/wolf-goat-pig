/**
 * Utils Index
 *
 * Central export point for all utility functions.
 * Import from here instead of individual files:
 *
 * import { calculateStrokeAllocation, getStrokesForHole } from '../utils';
 */

// API utilities
export * from './api';

// Stroke allocation utilities (Creecher Feature)
export {
  getStrokesForHole,
  calculateNetHandicaps,
  calculateStrokeAllocation,
  getPlayersWithStrokesOnHole,
  formatStrokesDisplay
} from './strokeAllocation';

// Storage utilities
export {
  storage,
  createNamespacedStorage,
  get as storageGet,
  set as storageSet,
  remove as storageRemove,
  clear as storageClear,
  has as storageHas,
  getKeys as storageGetKeys
} from './storage';

// Betting helpers
export {
  BETTING_COLORS,
  getRiskColor,
  getRiskIcon,
  getActionIcon,
  getActionDescription,
  formatProbability,
  formatValue,
  calculateExpectedValue,
  getProbabilityColor,
  formatActionText
} from './bettingHelpers';

// ============================================================================
// General Formatting Utilities
// ============================================================================

/**
 * Format a percentage value
 * @param {number} value - The value to format (0-1 or 0-100)
 * @param {boolean} isDecimal - Whether the value is in decimal form (0-1) vs percentage form (0-100)
 * @returns {string} Formatted percentage string (e.g., "45.0%")
 */
export const formatPercentage = (value, isDecimal = true) => {
  const percentage = isDecimal ? value * 100 : value;
  return `${percentage.toFixed(1)}%`;
};

/**
 * Format currency value with sign
 * @param {number} amount - The amount to format
 * @returns {string} Formatted currency string (e.g., "+$10.00" or "-$5.50")
 */
export const formatCurrency = (amount) => {
  return amount >= 0 ? `+$${amount.toFixed(2)}` : `-$${Math.abs(amount).toFixed(2)}`;
};

/**
 * Get performance color class based on value and thresholds
 * @param {number} value - The value to evaluate
 * @param {Object} thresholds - Threshold object with 'good' and 'average' properties
 * @param {number} thresholds.good - Threshold for good performance (default: 0.6)
 * @param {number} thresholds.average - Threshold for average performance (default: 0.4)
 * @returns {string} Tailwind CSS color class (e.g., 'text-green-600')
 */
export const getPerformanceColor = (value, thresholds = { good: 0.6, average: 0.4 }) => {
  if (value >= thresholds.good) return 'text-green-600';
  if (value >= thresholds.average) return 'text-yellow-600';
  return 'text-red-600';
};
