// =============================================================================
// Scorekeeper Hooks - Barrel Export
// =============================================================================

export { useGameState, default as useGameStateDefault } from './useGameState';
export { useStrokeAllocation, strokeCalculations } from './useStrokeAllocation';
export { useRotationWager, rotationUtils } from './useRotationWager';
export { useBettingActions, bettingUtils } from './useBettingActions';
export { useHoleSubmission, submissionUtils } from './useHoleSubmission';
export { useAardvark, aardvarkUtils } from './useAardvark';

// Re-export hook return types from types.ts for convenience
export type {
  UseGameStateReturn,
  UseRotationWagerReturn,
  UseBettingActionsReturn,
  UseStrokeAllocationReturn,
  UseHoleSubmissionReturn,
  UseAardvarkReturn,
} from '../types';
