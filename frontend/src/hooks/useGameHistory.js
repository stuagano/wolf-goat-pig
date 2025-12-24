/**
 * useGameHistory - Game history state management
 *
 * Manages:
 * - holeHistory (array of completed holes)
 * - playerStandings (computed from history)
 * - bettingHistory (track of betting actions)
 */

import { useReducer, useMemo } from 'react';

export const HISTORY_ACTIONS = {
  ADD_HOLE: 'ADD_HOLE',
  UPDATE_HOLE: 'UPDATE_HOLE',
  SET_HISTORY: 'SET_HISTORY',
  ADD_BETTING_EVENT: 'ADD_BETTING_EVENT',
  CLEAR_BETTING_HISTORY: 'CLEAR_BETTING_HISTORY',
  RESET: 'RESET',
};

export const initialHistoryState = (initialHistory = []) => ({
  holeHistory: initialHistory,
  bettingHistory: [],
});

export function historyReducer(state, action) {
  switch (action.type) {
    case HISTORY_ACTIONS.ADD_HOLE:
      return {
        ...state,
        holeHistory: [...state.holeHistory, action.holeData],
      };

    case HISTORY_ACTIONS.UPDATE_HOLE: {
      const updated = state.holeHistory.map((hole, idx) =>
        idx === action.index ? { ...hole, ...action.holeData } : hole
      );
      return { ...state, holeHistory: updated };
    }

    case HISTORY_ACTIONS.SET_HISTORY:
      return { ...state, holeHistory: action.history };

    case HISTORY_ACTIONS.ADD_BETTING_EVENT:
      return {
        ...state,
        bettingHistory: [...state.bettingHistory, { ...action.event, timestamp: Date.now() }],
      };

    case HISTORY_ACTIONS.CLEAR_BETTING_HISTORY:
      return { ...state, bettingHistory: [] };

    case HISTORY_ACTIONS.RESET:
      return initialHistoryState();

    default:
      return state;
  }
}

export function useGameHistory(initialHistory = []) {
  const [state, dispatch] = useReducer(
    historyReducer,
    initialHistory,
    initialHistoryState
  );

  const actions = useMemo(() => ({
    addHole: (holeData) => dispatch({ type: HISTORY_ACTIONS.ADD_HOLE, holeData }),
    updateHole: (index, holeData) => dispatch({ type: HISTORY_ACTIONS.UPDATE_HOLE, index, holeData }),
    setHistory: (history) => dispatch({ type: HISTORY_ACTIONS.SET_HISTORY, history }),
    addBettingEvent: (event) => dispatch({ type: HISTORY_ACTIONS.ADD_BETTING_EVENT, event }),
    clearBettingHistory: () => dispatch({ type: HISTORY_ACTIONS.CLEAR_BETTING_HISTORY }),
    reset: () => dispatch({ type: HISTORY_ACTIONS.RESET }),
  }), []);

  // Compute player standings from hole history
  const playerStandings = useMemo(() => {
    const standings = {};
    state.holeHistory.forEach(hole => {
      if (hole.points_delta) {
        Object.entries(hole.points_delta).forEach(([playerId, points]) => {
          if (!standings[playerId]) {
            standings[playerId] = { quarters: 0, soloCount: 0 };
          }
          standings[playerId].quarters += points;
        });
      }
      if (hole.teams?.type === 'solo' && hole.teams?.captain) {
        if (!standings[hole.teams.captain]) {
          standings[hole.teams.captain] = { quarters: 0, soloCount: 0 };
        }
        standings[hole.teams.captain].soloCount += 1;
      }
    });
    return standings;
  }, [state.holeHistory]);

  const completedHoles = useMemo(() => state.holeHistory.length, [state.holeHistory]);

  return { state, dispatch, actions, playerStandings, completedHoles };
}

export default useGameHistory;
