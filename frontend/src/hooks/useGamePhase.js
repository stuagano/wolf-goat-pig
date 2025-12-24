/**
 * useGamePhase - Game phase state machine
 *
 * Manages game phase transitions based on hole number:
 * - Holes 1-12: normal
 * - Holes 13-16: vinnies (Vinnie's Variation)
 * - Holes 17-18: hoepfinger (final phase)
 * - After 18: complete
 *
 * Consolidates:
 * - phase, isHoepfinger, goatId, vinniesVariation
 *
 * Benefits:
 * - Automatic phase transitions based on hole
 * - Impossible invalid states (can't be hoepfinger on hole 5)
 * - Computed values for UI (holesUntilHoepfinger, isLastChance)
 */

import { useReducer, useMemo } from 'react';

/**
 * Action types for phase state changes
 */
export const PHASE_ACTIONS = {
  SET_HOLE: 'SET_HOLE',
  SET_GOAT: 'SET_GOAT',
  ENTER_HOEPFINGER: 'ENTER_HOEPFINGER',
  EXIT_HOEPFINGER: 'EXIT_HOEPFINGER',
  SET_VINNIES: 'SET_VINNIES',
  COMPLETE_GAME: 'COMPLETE_GAME',
  RESET: 'RESET',
};

/**
 * Determine the phase for a given hole number
 * @param {number} hole - Current hole number
 * @returns {string} Phase name
 */
export function getPhaseForHole(hole) {
  if (hole < 1) return 'normal';
  if (hole <= 12) return 'normal';
  if (hole <= 16) return 'vinnies';
  if (hole <= 18) return 'hoepfinger';
  return 'complete';
}

/**
 * Create initial phase state
 * @param {number} hole - Initial hole number (default: 1)
 * @returns {Object} Initial phase state
 */
export const initialPhaseState = (hole = 1) => {
  const phase = getPhaseForHole(hole);
  return {
    phase,
    isHoepfinger: phase === 'hoepfinger',
    goatId: null,
    vinniesVariation: phase === 'vinnies',
    currentHole: hole,
  };
};

/**
 * Phase state reducer - pure function for predictable state transitions
 *
 * @param {Object} state - Current phase state
 * @param {Object} action - Action to perform
 * @returns {Object} New phase state
 */
export function phaseReducer(state, action) {
  switch (action.type) {
    case PHASE_ACTIONS.SET_HOLE: {
      const { hole } = action;
      const newPhase = getPhaseForHole(hole);
      return {
        ...state,
        currentHole: hole,
        phase: newPhase,
        isHoepfinger: newPhase === 'hoepfinger',
        vinniesVariation: newPhase === 'vinnies',
        // Clear goat when leaving hoepfinger
        goatId: newPhase === 'hoepfinger' ? state.goatId : null,
      };
    }

    case PHASE_ACTIONS.SET_GOAT:
      return {
        ...state,
        goatId: action.goatId,
      };

    case PHASE_ACTIONS.ENTER_HOEPFINGER:
      return {
        ...state,
        phase: 'hoepfinger',
        isHoepfinger: true,
        goatId: action.goatId || null,
      };

    case PHASE_ACTIONS.EXIT_HOEPFINGER:
      return {
        ...state,
        isHoepfinger: false,
        goatId: null,
        // Phase still determined by hole number
        phase: getPhaseForHole(state.currentHole),
      };

    case PHASE_ACTIONS.SET_VINNIES:
      return {
        ...state,
        vinniesVariation: action.active,
      };

    case PHASE_ACTIONS.COMPLETE_GAME:
      return {
        ...state,
        phase: 'complete',
      };

    case PHASE_ACTIONS.RESET:
      return initialPhaseState(1);

    default:
      return state;
  }
}

/**
 * Custom hook for game phase state management
 *
 * @param {number} initialHole - Starting hole number
 * @returns {Object} { state, dispatch, actions, computed values }
 *
 * @example
 * const { state, actions, holesUntilHoepfinger, isLastChance } = useGamePhase(1);
 * actions.advanceHole();
 * actions.setGoat('player-3');
 */
export function useGamePhase(initialHole = 1) {
  const [state, dispatch] = useReducer(
    phaseReducer,
    initialHole,
    initialPhaseState
  );

  // Memoized action helpers
  const actions = useMemo(() => ({
    setHole: (hole) => dispatch({ type: PHASE_ACTIONS.SET_HOLE, hole }),

    advanceHole: () => dispatch({
      type: PHASE_ACTIONS.SET_HOLE,
      hole: state.currentHole + 1,
    }),

    setGoat: (goatId) => dispatch({ type: PHASE_ACTIONS.SET_GOAT, goatId }),

    enterHoepfinger: (goatId) => dispatch({
      type: PHASE_ACTIONS.ENTER_HOEPFINGER,
      goatId,
    }),

    exitHoepfinger: () => dispatch({ type: PHASE_ACTIONS.EXIT_HOEPFINGER }),

    setVinnies: (active) => dispatch({
      type: PHASE_ACTIONS.SET_VINNIES,
      active,
    }),

    completeGame: () => dispatch({ type: PHASE_ACTIONS.COMPLETE_GAME }),

    reset: () => dispatch({ type: PHASE_ACTIONS.RESET }),
  }), [state.currentHole]);

  // Computed values
  const holesUntilHoepfinger = useMemo(() => {
    if (state.currentHole >= 17) return 0;
    return 17 - state.currentHole;
  }, [state.currentHole]);

  const isLastChance = useMemo(() => {
    return state.currentHole === 16;
  }, [state.currentHole]);

  const isGameComplete = useMemo(() => {
    return state.phase === 'complete';
  }, [state.phase]);

  return {
    state,
    dispatch,
    actions,
    holesUntilHoepfinger,
    isLastChance,
    isGameComplete,
  };
}

export default useGamePhase;
