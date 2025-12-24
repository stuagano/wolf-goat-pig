/**
 * useBettingReducer - Centralized betting state management
 *
 * Consolidates 11 useState calls from SimpleScorekeeper into a single reducer:
 * - currentWager, nextHoleWager, joesSpecialWager
 * - floatInvokedBy, optionInvokedBy
 * - carryOver, carryOverApplied
 * - vinniesVariation
 * - optionActive, optionTurnedOff
 * - duncanInvoked
 *
 * Benefits:
 * - Impossible invalid states (e.g., can't float twice)
 * - All betting logic in one place
 * - Easy to test (pure reducer function)
 * - Clear action contracts
 */

import { useReducer, useCallback, useMemo } from 'react';

/**
 * Action types for betting state changes
 */
export const BETTING_ACTIONS = {
  DOUBLE: 'DOUBLE',
  FLOAT: 'FLOAT',
  OPTION: 'OPTION',
  OPTION_OFF: 'OPTION_OFF',
  DUNCAN: 'DUNCAN',
  CARRY_OVER: 'CARRY_OVER',
  APPLY_CARRY_OVER: 'APPLY_CARRY_OVER',
  VINNIES_VARIATION: 'VINNIES_VARIATION',
  JOES_SPECIAL: 'JOES_SPECIAL',
  SET_NEXT_HOLE_WAGER: 'SET_NEXT_HOLE_WAGER',
  RESET_FOR_HOLE: 'RESET_FOR_HOLE',
  RESET_ALL: 'RESET_ALL',
};

/**
 * Create initial betting state
 * @param {number} baseWager - The base wager amount (default: 1)
 * @returns {Object} Initial betting state
 */
export const initialBettingState = (baseWager = 1) => ({
  baseWager,
  currentWager: baseWager,
  nextHoleWager: baseWager,
  joesSpecialWager: null,
  floatInvokedBy: null,
  optionInvokedBy: null,
  carryOver: false,
  carryOverApplied: false,
  vinniesVariation: false,
  optionActive: false,
  optionTurnedOff: false,
  duncanInvoked: false,
});

/**
 * Betting state reducer - pure function for predictable state transitions
 *
 * @param {Object} state - Current betting state
 * @param {Object} action - Action to perform
 * @returns {Object} New betting state
 */
export function bettingReducer(state, action) {
  switch (action.type) {
    case BETTING_ACTIONS.DOUBLE:
      return {
        ...state,
        currentWager: state.currentWager * 2,
      };

    case BETTING_ACTIONS.FLOAT:
      // Prevent double float - idempotent
      if (state.floatInvokedBy) {
        return state;
      }
      return {
        ...state,
        currentWager: state.currentWager * 2,
        floatInvokedBy: action.playerId,
      };

    case BETTING_ACTIONS.OPTION:
      // Cannot activate if already turned off this hole
      if (state.optionTurnedOff) {
        return state;
      }
      return {
        ...state,
        optionActive: true,
        optionInvokedBy: action.playerId,
      };

    case BETTING_ACTIONS.OPTION_OFF:
      return {
        ...state,
        optionActive: false,
        optionTurnedOff: true,
      };

    case BETTING_ACTIONS.DUNCAN:
      // Prevent double duncan
      if (state.duncanInvoked) {
        return state;
      }
      return {
        ...state,
        duncanInvoked: true,
        currentWager: state.currentWager * 2,
      };

    case BETTING_ACTIONS.CARRY_OVER:
      return {
        ...state,
        carryOver: true,
      };

    case BETTING_ACTIONS.APPLY_CARRY_OVER:
      if (!state.carryOver) {
        return state;
      }
      return {
        ...state,
        currentWager: state.currentWager * 2,
        carryOver: false,
        carryOverApplied: true,
      };

    case BETTING_ACTIONS.VINNIES_VARIATION:
      return {
        ...state,
        vinniesVariation: action.active,
      };

    case BETTING_ACTIONS.JOES_SPECIAL:
      return {
        ...state,
        joesSpecialWager: action.wager,
      };

    case BETTING_ACTIONS.SET_NEXT_HOLE_WAGER:
      return {
        ...state,
        nextHoleWager: action.wager,
      };

    case BETTING_ACTIONS.RESET_FOR_HOLE:
      // Reset per-hole state, use nextHoleWager as new current
      return {
        ...state,
        currentWager: state.nextHoleWager,
        nextHoleWager: state.baseWager,
        floatInvokedBy: null,
        optionInvokedBy: null,
        optionActive: false,
        optionTurnedOff: false,
        duncanInvoked: false,
        carryOverApplied: false,
      };

    case BETTING_ACTIONS.RESET_ALL:
      return initialBettingState(state.baseWager);

    default:
      return state;
  }
}

/**
 * Custom hook for betting state management
 *
 * @param {number} baseWager - Initial base wager amount
 * @returns {Object} { state, dispatch, actions }
 *
 * @example
 * const { state, actions } = useBettingReducer(1);
 * actions.double();
 * actions.float('player-1');
 * console.log(state.currentWager); // 4
 */
export function useBettingReducer(baseWager = 1) {
  const [state, dispatch] = useReducer(
    bettingReducer,
    baseWager,
    initialBettingState
  );

  // Memoized action helpers for cleaner component code
  const actions = useMemo(() => ({
    double: () => dispatch({ type: BETTING_ACTIONS.DOUBLE }),

    float: (playerId) => dispatch({
      type: BETTING_ACTIONS.FLOAT,
      playerId,
    }),

    option: (playerId) => dispatch({
      type: BETTING_ACTIONS.OPTION,
      playerId,
    }),

    optionOff: () => dispatch({ type: BETTING_ACTIONS.OPTION_OFF }),

    duncan: () => dispatch({ type: BETTING_ACTIONS.DUNCAN }),

    setCarryOver: () => dispatch({ type: BETTING_ACTIONS.CARRY_OVER }),

    applyCarryOver: () => dispatch({ type: BETTING_ACTIONS.APPLY_CARRY_OVER }),

    setVinniesVariation: (active) => dispatch({
      type: BETTING_ACTIONS.VINNIES_VARIATION,
      active,
    }),

    setJoesSpecial: (wager) => dispatch({
      type: BETTING_ACTIONS.JOES_SPECIAL,
      wager,
    }),

    setNextHoleWager: (wager) => dispatch({
      type: BETTING_ACTIONS.SET_NEXT_HOLE_WAGER,
      wager,
    }),

    resetForHole: () => dispatch({ type: BETTING_ACTIONS.RESET_FOR_HOLE }),

    resetAll: () => dispatch({ type: BETTING_ACTIONS.RESET_ALL }),
  }), []);

  return { state, dispatch, actions };
}

export default useBettingReducer;
