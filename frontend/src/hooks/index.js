/**
 * Hooks Index
 *
 * Central export point for all custom hooks.
 * Import from here instead of individual files:
 *
 * import { useScoreValidation, useScoreInput, useCourseData } from '../hooks';
 */

// Score-related hooks
export { default as useScoreValidation, SCORE_CONSTRAINTS } from './useScoreValidation';
export { default as useScoreInput } from './useScoreInput';
export { default as useCourseData } from './useCourseData';
export { default as useZeroSumValidation } from './useZeroSumValidation';

// Game API hooks
export { default as useGamePersistence } from './useGamePersistence';
export { default as useSimulationApi } from './useSimulationApi';

// Analytics hooks
export { default as useOddsCalculation } from './useOddsCalculation';
export { default as usePostHoleAnalytics } from './usePostHoleAnalytics';

// Player and auth hooks
export { default as useAuth } from './useAuth';
export { default as usePlayerProfile } from './usePlayerProfile';

// Utility hooks
export { default as useFetchAsync } from './useFetchAsync';
export { default as useTutorialProgress } from './useTutorialProgress';
