/**
 * useTeamManagement - Centralized team state management
 *
 * Consolidates team-related useState calls from SimpleScorekeeper:
 * - teamMode ('partners' or 'solo')
 * - team1, team2 (partner mode)
 * - captain, opponents (solo mode)
 * - rotationOrder, captainIndex
 *
 * Benefits:
 * - Team logic isolated and testable
 * - Auto-computes team2 from team1
 * - Auto-fills opponents when captain selected
 * - Rotation logic centralized
 */

import { useReducer, useMemo } from 'react';

/**
 * Action types for team state changes
 */
export const TEAM_ACTIONS = {
  SET_MODE: 'SET_MODE',
  TOGGLE_TEAM1: 'TOGGLE_TEAM1',
  SET_CAPTAIN: 'SET_CAPTAIN',
  SET_ROTATION: 'SET_ROTATION',
  SET_CAPTAIN_INDEX: 'SET_CAPTAIN_INDEX',
  ROTATE_CAPTAIN: 'ROTATE_CAPTAIN',
  RESTORE_FROM_HOLE: 'RESTORE_FROM_HOLE',
  RESET_FOR_HOLE: 'RESET_FOR_HOLE',
};

/**
 * Create initial team state
 * @param {Array} players - Array of player objects with id, name, tee_order
 * @returns {Object} Initial team state
 */
export const initialTeamState = (players = []) => {
  // Sort players by tee_order if available
  const sortedPlayers = [...players].sort((a, b) => {
    if (a.tee_order != null && b.tee_order != null) {
      return Number(a.tee_order) - Number(b.tee_order);
    }
    if (a.tee_order != null) return -1;
    if (b.tee_order != null) return 1;
    return 0;
  });

  return {
    teamMode: 'partners',
    team1: [],
    team2: [],
    captain: null,
    opponents: [],
    rotationOrder: sortedPlayers.map(p => p.id),
    captainIndex: 0,
    players,
  };
};

/**
 * Team state reducer - pure function for predictable state transitions
 *
 * @param {Object} state - Current team state
 * @param {Object} action - Action to perform
 * @returns {Object} New team state
 */
export function teamReducer(state, action) {
  switch (action.type) {
    case TEAM_ACTIONS.SET_MODE:
      if (action.mode === 'solo') {
        return {
          ...state,
          teamMode: 'solo',
          team1: [],
          team2: [],
        };
      }
      return {
        ...state,
        teamMode: 'partners',
        captain: null,
        opponents: [],
      };

    case TEAM_ACTIONS.TOGGLE_TEAM1: {
      const { playerId } = action;
      const isInTeam1 = state.team1.includes(playerId);

      let newTeam1;
      if (isInTeam1) {
        // Remove from team1
        newTeam1 = state.team1.filter(id => id !== playerId);
      } else {
        // Add to team1 (but don't allow all players)
        if (state.team1.length >= state.players.length - 1) {
          return state; // Can't add, would be all players
        }
        newTeam1 = [...state.team1, playerId];
      }

      // Auto-compute team2 as remaining players
      const newTeam2 = state.players
        .filter(p => !newTeam1.includes(p.id))
        .map(p => p.id);

      return {
        ...state,
        team1: newTeam1,
        team2: newTeam2,
      };
    }

    case TEAM_ACTIONS.SET_CAPTAIN: {
      const { playerId } = action;

      // Toggle off if same captain selected
      if (state.captain === playerId) {
        return {
          ...state,
          captain: null,
          opponents: [],
        };
      }

      // Set captain and auto-fill opponents
      const opponents = state.players
        .filter(p => p.id !== playerId)
        .map(p => p.id);

      return {
        ...state,
        captain: playerId,
        opponents,
      };
    }

    case TEAM_ACTIONS.SET_ROTATION:
      return {
        ...state,
        rotationOrder: action.rotationOrder,
      };

    case TEAM_ACTIONS.SET_CAPTAIN_INDEX: {
      const playerCount = state.rotationOrder.length;
      const index = playerCount > 0 ? action.index % playerCount : 0;
      return {
        ...state,
        captainIndex: index,
      };
    }

    case TEAM_ACTIONS.ROTATE_CAPTAIN: {
      const playerCount = state.rotationOrder.length;
      if (playerCount === 0) return state;
      return {
        ...state,
        captainIndex: (state.captainIndex + 1) % playerCount,
      };
    }

    case TEAM_ACTIONS.RESTORE_FROM_HOLE: {
      const { holeData } = action;
      if (!holeData?.teams) return state;

      const { teams } = holeData;

      if (teams.type === 'partners') {
        return {
          ...state,
          teamMode: 'partners',
          team1: teams.team1 || [],
          team2: teams.team2 || [],
          captain: null,
          opponents: [],
        };
      }

      if (teams.type === 'solo') {
        return {
          ...state,
          teamMode: 'solo',
          captain: teams.captain || null,
          opponents: teams.opponents || [],
          team1: [],
          team2: [],
        };
      }

      return state;
    }

    case TEAM_ACTIONS.RESET_FOR_HOLE:
      return {
        ...state,
        team1: [],
        team2: [],
        captain: null,
        opponents: [],
        // Keep rotation and captainIndex
      };

    default:
      return state;
  }
}

/**
 * Custom hook for team state management
 *
 * @param {Array} players - Array of player objects
 * @returns {Object} { state, dispatch, actions, currentCaptain, teamsFormed }
 *
 * @example
 * const { state, actions, currentCaptain, teamsFormed } = useTeamManagement(players);
 * actions.toggleTeam1('player-1');
 * actions.setMode('solo');
 * actions.setCaptain('player-2');
 */
export function useTeamManagement(players = []) {
  const [state, dispatch] = useReducer(
    teamReducer,
    players,
    initialTeamState
  );

  // Memoized action helpers
  const actions = useMemo(() => ({
    setMode: (mode) => dispatch({ type: TEAM_ACTIONS.SET_MODE, mode }),

    toggleTeam1: (playerId) => dispatch({
      type: TEAM_ACTIONS.TOGGLE_TEAM1,
      playerId,
    }),

    setCaptain: (playerId) => dispatch({
      type: TEAM_ACTIONS.SET_CAPTAIN,
      playerId,
    }),

    setRotation: (rotationOrder) => dispatch({
      type: TEAM_ACTIONS.SET_ROTATION,
      rotationOrder,
    }),

    setCaptainIndex: (index) => dispatch({
      type: TEAM_ACTIONS.SET_CAPTAIN_INDEX,
      index,
    }),

    rotateCaptain: () => dispatch({ type: TEAM_ACTIONS.ROTATE_CAPTAIN }),

    restoreFromHole: (holeData) => dispatch({
      type: TEAM_ACTIONS.RESTORE_FROM_HOLE,
      holeData,
    }),

    resetForHole: () => dispatch({ type: TEAM_ACTIONS.RESET_FOR_HOLE }),
  }), []);

  // Computed values
  const currentCaptain = useMemo(() => {
    if (state.rotationOrder.length === 0) return null;
    return state.rotationOrder[state.captainIndex];
  }, [state.rotationOrder, state.captainIndex]);

  const teamsFormed = useMemo(() => {
    if (state.teamMode === 'partners') {
      return state.team1.length > 0 && state.team1.length < state.players.length;
    }
    return state.captain !== null;
  }, [state.teamMode, state.team1, state.captain, state.players.length]);

  return {
    state,
    dispatch,
    actions,
    currentCaptain,
    teamsFormed,
  };
}

export default useTeamManagement;
