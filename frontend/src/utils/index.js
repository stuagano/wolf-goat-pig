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
