/**
 * useUIToggles - UI visibility and toggle state management
 *
 * Manages:
 * - showUsageStats, showBettingHistory, showAdvancedBetting
 * - showTeamSelection, showGolfScores, showCommissioner, showNotes
 * - historyTab (selected tab in history view)
 * - isGameMarkedComplete
 * - localPlayers (for player management UI)
 */

import { useReducer, useMemo } from 'react';

export const UI_ACTIONS = {
  TOGGLE_USAGE_STATS: 'TOGGLE_USAGE_STATS',
  TOGGLE_BETTING_HISTORY: 'TOGGLE_BETTING_HISTORY',
  TOGGLE_ADVANCED_BETTING: 'TOGGLE_ADVANCED_BETTING',
  TOGGLE_TEAM_SELECTION: 'TOGGLE_TEAM_SELECTION',
  TOGGLE_GOLF_SCORES: 'TOGGLE_GOLF_SCORES',
  TOGGLE_COMMISSIONER: 'TOGGLE_COMMISSIONER',
  TOGGLE_NOTES: 'TOGGLE_NOTES',
  SET_HISTORY_TAB: 'SET_HISTORY_TAB',
  SET_GAME_COMPLETE: 'SET_GAME_COMPLETE',
  SET_LOCAL_PLAYERS: 'SET_LOCAL_PLAYERS',
  SHOW_PANEL: 'SHOW_PANEL',
  HIDE_PANEL: 'HIDE_PANEL',
  RESET: 'RESET',
};

export const initialUIState = () => ({
  showUsageStats: false,
  showBettingHistory: false,
  showAdvancedBetting: false,
  showTeamSelection: false,
  showGolfScores: true,
  showCommissioner: false,
  showNotes: false,
  historyTab: 'holes',
  isGameMarkedComplete: false,
  localPlayers: [],
});

export function uiReducer(state, action) {
  switch (action.type) {
    case UI_ACTIONS.TOGGLE_USAGE_STATS:
      return { ...state, showUsageStats: !state.showUsageStats };

    case UI_ACTIONS.TOGGLE_BETTING_HISTORY:
      return { ...state, showBettingHistory: !state.showBettingHistory };

    case UI_ACTIONS.TOGGLE_ADVANCED_BETTING:
      return { ...state, showAdvancedBetting: !state.showAdvancedBetting };

    case UI_ACTIONS.TOGGLE_TEAM_SELECTION:
      return { ...state, showTeamSelection: !state.showTeamSelection };

    case UI_ACTIONS.TOGGLE_GOLF_SCORES:
      return { ...state, showGolfScores: !state.showGolfScores };

    case UI_ACTIONS.TOGGLE_COMMISSIONER:
      return { ...state, showCommissioner: !state.showCommissioner };

    case UI_ACTIONS.TOGGLE_NOTES:
      return { ...state, showNotes: !state.showNotes };

    case UI_ACTIONS.SET_HISTORY_TAB:
      return { ...state, historyTab: action.tab };

    case UI_ACTIONS.SET_GAME_COMPLETE:
      return { ...state, isGameMarkedComplete: action.complete };

    case UI_ACTIONS.SET_LOCAL_PLAYERS:
      return { ...state, localPlayers: action.players };

    case UI_ACTIONS.SHOW_PANEL:
      if (state[action.panel] !== undefined) {
        return { ...state, [action.panel]: true };
      }
      return state;

    case UI_ACTIONS.HIDE_PANEL:
      if (state[action.panel] !== undefined) {
        return { ...state, [action.panel]: false };
      }
      return state;

    case UI_ACTIONS.RESET:
      return initialUIState();

    default:
      return state;
  }
}

export function useUIToggles(initialPlayers = []) {
  const [state, dispatch] = useReducer(uiReducer, null, () => ({
    ...initialUIState(),
    localPlayers: initialPlayers,
  }));

  const actions = useMemo(() => ({
    toggleUsageStats: () => dispatch({ type: UI_ACTIONS.TOGGLE_USAGE_STATS }),
    toggleBettingHistory: () => dispatch({ type: UI_ACTIONS.TOGGLE_BETTING_HISTORY }),
    toggleAdvancedBetting: () => dispatch({ type: UI_ACTIONS.TOGGLE_ADVANCED_BETTING }),
    toggleTeamSelection: () => dispatch({ type: UI_ACTIONS.TOGGLE_TEAM_SELECTION }),
    toggleGolfScores: () => dispatch({ type: UI_ACTIONS.TOGGLE_GOLF_SCORES }),
    toggleCommissioner: () => dispatch({ type: UI_ACTIONS.TOGGLE_COMMISSIONER }),
    toggleNotes: () => dispatch({ type: UI_ACTIONS.TOGGLE_NOTES }),
    setHistoryTab: (tab) => dispatch({ type: UI_ACTIONS.SET_HISTORY_TAB, tab }),
    setGameComplete: (complete) => dispatch({ type: UI_ACTIONS.SET_GAME_COMPLETE, complete }),
    setLocalPlayers: (players) => dispatch({ type: UI_ACTIONS.SET_LOCAL_PLAYERS, players }),
    showPanel: (panel) => dispatch({ type: UI_ACTIONS.SHOW_PANEL, panel }),
    hidePanel: (panel) => dispatch({ type: UI_ACTIONS.HIDE_PANEL, panel }),
    reset: () => dispatch({ type: UI_ACTIONS.RESET }),
  }), []);

  const anyPanelOpen = useMemo(() =>
    state.showUsageStats ||
    state.showBettingHistory ||
    state.showAdvancedBetting ||
    state.showTeamSelection ||
    state.showCommissioner ||
    state.showNotes,
  [state.showUsageStats, state.showBettingHistory, state.showAdvancedBetting,
   state.showTeamSelection, state.showCommissioner, state.showNotes]);

  const hasLocalPlayers = useMemo(() => state.localPlayers.length > 0, [state.localPlayers]);

  return { state, dispatch, actions, anyPanelOpen, hasLocalPlayers };
}

export default useUIToggles;
