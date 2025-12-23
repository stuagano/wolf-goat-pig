/**
 * Game Components Index
 *
 * Central export point for all game-related components.
 * Import from here instead of individual files:
 *
 * import { ScoreInputField, EditHoleModal } from '../components/game';
 */

// Core game components
export { default as CourseManager } from './CourseManager';
export { default as CourseImport } from './CourseImport';
export { default as SimpleScorekeeper } from './SimpleScorekeeper';
export { default as GameCompletionView } from './GameCompletionView';
export { default as Scorecard } from './Scorecard';

// Extracted/reusable components for score entry
export { default as ScoreInputField } from './ScoreInputField';
export { default as EditHoleModal } from './EditHoleModal';

// New modular scorekeeper components (TypeScript)
export {
  // Main container (feature-complete)
  LiveScorekeeperContainer,
  // Core UI components
  LiveScorekeeper,
  HoleHeader,
  TeamSelector,
  PlayerCard,
  BettingActionsPanel,
  StandingsSidebar,
  NotesPanel,
  SubmitButton,
  // New UI components
  QuartersPresets,
  HoleNavigation,
  AardvarkPanel,
} from './scorekeeper';
