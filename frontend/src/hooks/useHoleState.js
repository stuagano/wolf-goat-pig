/**
 * useHoleState - Current hole state management
 *
 * Manages the state for the current hole being played:
 * - scores (gross scores per player)
 * - quarters (points per player)
 * - winner (hole winner)
 * - holeNotes (notes for current hole)
 * - playerDisplayOrder (order for entering quarters)
 *
 * Benefits:
 * - All hole-related state in one place
 * - Computed values for validation (allScoresEntered, quartersBalanced)
 * - Easy to reset between holes
 */

import { useReducer, useMemo } from 'react';

/**
 * Action types for hole state changes
 */
export const HOLE_ACTIONS = {
  SET_SCORE: 'SET_SCORE',
  SET_ALL_SCORES: 'SET_ALL_SCORES',
  SET_QUARTERS: 'SET_QUARTERS',
  SET_ALL_QUARTERS: 'SET_ALL_QUARTERS',
  SET_WINNER: 'SET_WINNER',
  SET_NOTES: 'SET_NOTES',
  SET_DISPLAY_ORDER: 'SET_DISPLAY_ORDER',
  RESTORE_FROM_HOLE: 'RESTORE_FROM_HOLE',
  RESET: 'RESET',
};

/**
 * Create initial hole state
 * @param {Array} players - Array of player objects with id
 * @returns {Object} Initial hole state
 */
export const initialHoleState = (players = []) => ({
  scores: {},
  quarters: {},
  winner: null,
  holeNotes: '',
  playerDisplayOrder: players.map(p => p.id),
  players,
});

/**
 * Hole state reducer - pure function for predictable state transitions
 *
 * @param {Object} state - Current hole state
 * @param {Object} action - Action to perform
 * @returns {Object} New hole state
 */
export function holeReducer(state, action) {
  switch (action.type) {
    case HOLE_ACTIONS.SET_SCORE:
      return {
        ...state,
        scores: {
          ...state.scores,
          [action.playerId]: action.score,
        },
      };

    case HOLE_ACTIONS.SET_ALL_SCORES:
      return {
        ...state,
        scores: action.scores,
      };

    case HOLE_ACTIONS.SET_QUARTERS:
      return {
        ...state,
        quarters: {
          ...state.quarters,
          [action.playerId]: action.quarters,
        },
      };

    case HOLE_ACTIONS.SET_ALL_QUARTERS:
      return {
        ...state,
        quarters: action.quarters,
      };

    case HOLE_ACTIONS.SET_WINNER:
      return {
        ...state,
        winner: action.winner,
      };

    case HOLE_ACTIONS.SET_NOTES:
      return {
        ...state,
        holeNotes: action.notes,
      };

    case HOLE_ACTIONS.SET_DISPLAY_ORDER:
      return {
        ...state,
        playerDisplayOrder: action.order,
      };

    case HOLE_ACTIONS.RESTORE_FROM_HOLE: {
      const { holeData } = action;
      return {
        ...state,
        scores: holeData.gross_scores || {},
        quarters: holeData.points_delta || {},
        winner: holeData.winner || null,
        holeNotes: holeData.notes || '',
      };
    }

    case HOLE_ACTIONS.RESET:
      return {
        ...state,
        scores: {},
        quarters: {},
        winner: null,
        holeNotes: '',
        // Keep playerDisplayOrder
      };

    default:
      return state;
  }
}

/**
 * Custom hook for hole state management
 *
 * @param {Array} players - Array of player objects
 * @returns {Object} { state, dispatch, actions, computed values }
 *
 * @example
 * const { state, actions, allScoresEntered, quartersBalanced } = useHoleState(players);
 * actions.setScore('p1', 5);
 * actions.setQuarters('p1', 2);
 */
export function useHoleState(players = []) {
  const [state, dispatch] = useReducer(
    holeReducer,
    players,
    initialHoleState
  );

  // Memoized action helpers
  const actions = useMemo(() => ({
    setScore: (playerId, score) => dispatch({
      type: HOLE_ACTIONS.SET_SCORE,
      playerId,
      score,
    }),

    setAllScores: (scores) => dispatch({
      type: HOLE_ACTIONS.SET_ALL_SCORES,
      scores,
    }),

    setQuarters: (playerId, quarters) => dispatch({
      type: HOLE_ACTIONS.SET_QUARTERS,
      playerId,
      quarters,
    }),

    setAllQuarters: (quarters) => dispatch({
      type: HOLE_ACTIONS.SET_ALL_QUARTERS,
      quarters,
    }),

    setWinner: (winner) => dispatch({
      type: HOLE_ACTIONS.SET_WINNER,
      winner,
    }),

    setNotes: (notes) => dispatch({
      type: HOLE_ACTIONS.SET_NOTES,
      notes,
    }),

    setDisplayOrder: (order) => dispatch({
      type: HOLE_ACTIONS.SET_DISPLAY_ORDER,
      order,
    }),

    restoreFromHole: (holeData) => dispatch({
      type: HOLE_ACTIONS.RESTORE_FROM_HOLE,
      holeData,
    }),

    reset: () => dispatch({ type: HOLE_ACTIONS.RESET }),
  }), []);

  // Computed values
  const allScoresEntered = useMemo(() => {
    if (state.players.length === 0) return false;
    return state.players.every(p =>
      state.scores[p.id] !== undefined && state.scores[p.id] !== null
    );
  }, [state.scores, state.players]);

  const allQuartersEntered = useMemo(() => {
    if (state.players.length === 0) return false;
    return state.players.every(p =>
      state.quarters[p.id] !== undefined && state.quarters[p.id] !== ''
    );
  }, [state.quarters, state.players]);

  const quartersSum = useMemo(() => {
    return Object.values(state.quarters).reduce((sum, q) => sum + (Number(q) || 0), 0);
  }, [state.quarters]);

  const quartersBalanced = useMemo(() => {
    return quartersSum === 0;
  }, [quartersSum]);

  return {
    state,
    dispatch,
    actions,
    allScoresEntered,
    allQuartersEntered,
    quartersSum,
    quartersBalanced,
  };
}

export default useHoleState;
