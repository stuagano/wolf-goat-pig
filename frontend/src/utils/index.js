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

