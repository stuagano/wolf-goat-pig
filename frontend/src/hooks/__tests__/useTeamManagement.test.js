/**
 * useTeamManagement - Test Suite
 *
 * Tests for the team state reducer that consolidates:
 * - teamMode ('partners' or 'solo')
 * - team1, team2 (partner mode)
 * - captain, opponents (solo mode)
 * - rotationOrder, captainIndex
 */

import { renderHook, act } from '@testing-library/react';
import {
  useTeamManagement,
  teamReducer,
  TEAM_ACTIONS,
  initialTeamState
} from '../useTeamManagement';

const mockPlayers = [
  { id: 'p1', name: 'Alice', tee_order: 1 },
  { id: 'p2', name: 'Bob', tee_order: 2 },
  { id: 'p3', name: 'Charlie', tee_order: 3 },
  { id: 'p4', name: 'Diana', tee_order: 4 },
];

describe('useTeamManagement', () => {
  describe('initialTeamState', () => {
    it('has correct default values', () => {
      const state = initialTeamState(mockPlayers);
      expect(state).toEqual({
        teamMode: 'partners',
        team1: [],
        team2: [],
        captain: null,
        opponents: [],
        rotationOrder: ['p1', 'p2', 'p3', 'p4'],
        captainIndex: 0,
        players: mockPlayers,
      });
    });

    it('sorts players by tee_order for rotation', () => {
      const unsortedPlayers = [
        { id: 'p3', name: 'Charlie', tee_order: 3 },
        { id: 'p1', name: 'Alice', tee_order: 1 },
        { id: 'p4', name: 'Diana', tee_order: 4 },
        { id: 'p2', name: 'Bob', tee_order: 2 },
      ];
      const state = initialTeamState(unsortedPlayers);
      expect(state.rotationOrder).toEqual(['p1', 'p2', 'p3', 'p4']);
    });

    it('handles players without tee_order', () => {
      const playersNoOrder = [
        { id: 'p1', name: 'Alice' },
        { id: 'p2', name: 'Bob' },
      ];
      const state = initialTeamState(playersNoOrder);
      expect(state.rotationOrder).toEqual(['p1', 'p2']);
    });
  });

  describe('teamReducer - SET_MODE action', () => {
    it('switches to solo mode and clears partner state', () => {
      const state = {
        ...initialTeamState(mockPlayers),
        team1: ['p1', 'p2'],
        team2: ['p3', 'p4'],
      };
      const result = teamReducer(state, { type: TEAM_ACTIONS.SET_MODE, mode: 'solo' });
      expect(result.teamMode).toBe('solo');
      expect(result.team1).toEqual([]);
      expect(result.team2).toEqual([]);
    });

    it('switches to partners mode and clears solo state', () => {
      const state = {
        ...initialTeamState(mockPlayers),
        teamMode: 'solo',
        captain: 'p1',
        opponents: ['p2', 'p3', 'p4'],
      };
      const result = teamReducer(state, { type: TEAM_ACTIONS.SET_MODE, mode: 'partners' });
      expect(result.teamMode).toBe('partners');
      expect(result.captain).toBeNull();
      expect(result.opponents).toEqual([]);
    });
  });

  describe('teamReducer - TOGGLE_TEAM1 action', () => {
    it('adds player to team1', () => {
      const state = initialTeamState(mockPlayers);
      const result = teamReducer(state, { type: TEAM_ACTIONS.TOGGLE_TEAM1, playerId: 'p1' });
      expect(result.team1).toEqual(['p1']);
    });

    it('removes player from team1 if already in', () => {
      const state = { ...initialTeamState(mockPlayers), team1: ['p1', 'p2'] };
      const result = teamReducer(state, { type: TEAM_ACTIONS.TOGGLE_TEAM1, playerId: 'p1' });
      expect(result.team1).toEqual(['p2']);
    });

    it('auto-computes team2 as remaining players', () => {
      const state = initialTeamState(mockPlayers);
      let result = teamReducer(state, { type: TEAM_ACTIONS.TOGGLE_TEAM1, playerId: 'p1' });
      result = teamReducer(result, { type: TEAM_ACTIONS.TOGGLE_TEAM1, playerId: 'p2' });
      expect(result.team1).toEqual(['p1', 'p2']);
      expect(result.team2).toEqual(['p3', 'p4']);
    });
  });

  describe('teamReducer - SET_CAPTAIN action', () => {
    it('sets captain and auto-fills opponents', () => {
      const state = { ...initialTeamState(mockPlayers), teamMode: 'solo' };
      const result = teamReducer(state, { type: TEAM_ACTIONS.SET_CAPTAIN, playerId: 'p1' });
      expect(result.captain).toBe('p1');
      expect(result.opponents).toEqual(['p2', 'p3', 'p4']);
    });

    it('toggles captain off if same player selected', () => {
      const state = {
        ...initialTeamState(mockPlayers),
        teamMode: 'solo',
        captain: 'p1',
        opponents: ['p2', 'p3', 'p4'],
      };
      const result = teamReducer(state, { type: TEAM_ACTIONS.SET_CAPTAIN, playerId: 'p1' });
      expect(result.captain).toBeNull();
      expect(result.opponents).toEqual([]);
    });
  });

  describe('teamReducer - SET_ROTATION action', () => {
    it('sets rotation order', () => {
      const state = initialTeamState(mockPlayers);
      const result = teamReducer(state, {
        type: TEAM_ACTIONS.SET_ROTATION,
        rotationOrder: ['p4', 'p3', 'p2', 'p1'],
      });
      expect(result.rotationOrder).toEqual(['p4', 'p3', 'p2', 'p1']);
    });
  });

  describe('teamReducer - SET_CAPTAIN_INDEX action', () => {
    it('sets captain index', () => {
      const state = initialTeamState(mockPlayers);
      const result = teamReducer(state, { type: TEAM_ACTIONS.SET_CAPTAIN_INDEX, index: 2 });
      expect(result.captainIndex).toBe(2);
    });

    it('wraps around when exceeding player count', () => {
      const state = initialTeamState(mockPlayers);
      const result = teamReducer(state, { type: TEAM_ACTIONS.SET_CAPTAIN_INDEX, index: 5 });
      expect(result.captainIndex).toBe(1); // 5 % 4 = 1
    });
  });

  describe('teamReducer - ROTATE_CAPTAIN action', () => {
    it('advances captain index by 1', () => {
      const state = { ...initialTeamState(mockPlayers), captainIndex: 0 };
      const result = teamReducer(state, { type: TEAM_ACTIONS.ROTATE_CAPTAIN });
      expect(result.captainIndex).toBe(1);
    });

    it('wraps around to 0', () => {
      const state = { ...initialTeamState(mockPlayers), captainIndex: 3 };
      const result = teamReducer(state, { type: TEAM_ACTIONS.ROTATE_CAPTAIN });
      expect(result.captainIndex).toBe(0);
    });
  });

  describe('teamReducer - RESTORE_FROM_HOLE action', () => {
    it('restores partners mode from hole data', () => {
      const state = initialTeamState(mockPlayers);
      const holeData = {
        teams: {
          type: 'partners',
          team1: ['p1', 'p2'],
          team2: ['p3', 'p4'],
        }
      };
      const result = teamReducer(state, { type: TEAM_ACTIONS.RESTORE_FROM_HOLE, holeData });
      expect(result.teamMode).toBe('partners');
      expect(result.team1).toEqual(['p1', 'p2']);
      expect(result.team2).toEqual(['p3', 'p4']);
      expect(result.captain).toBeNull();
    });

    it('restores solo mode from hole data', () => {
      const state = initialTeamState(mockPlayers);
      const holeData = {
        teams: {
          type: 'solo',
          captain: 'p1',
          opponents: ['p2', 'p3', 'p4'],
        }
      };
      const result = teamReducer(state, { type: TEAM_ACTIONS.RESTORE_FROM_HOLE, holeData });
      expect(result.teamMode).toBe('solo');
      expect(result.captain).toBe('p1');
      expect(result.opponents).toEqual(['p2', 'p3', 'p4']);
      expect(result.team1).toEqual([]);
    });
  });

  describe('teamReducer - RESET_FOR_HOLE action', () => {
    it('clears team selections but keeps rotation', () => {
      const state = {
        ...initialTeamState(mockPlayers),
        team1: ['p1', 'p2'],
        team2: ['p3', 'p4'],
        captain: 'p1',
        captainIndex: 2,
      };
      const result = teamReducer(state, { type: TEAM_ACTIONS.RESET_FOR_HOLE });
      expect(result.team1).toEqual([]);
      expect(result.team2).toEqual([]);
      expect(result.captain).toBeNull();
      expect(result.opponents).toEqual([]);
      expect(result.captainIndex).toBe(2); // Preserved
      expect(result.rotationOrder).toEqual(['p1', 'p2', 'p3', 'p4']); // Preserved
    });
  });

  describe('useTeamManagement hook', () => {
    it('returns state and actions', () => {
      const { result } = renderHook(() => useTeamManagement(mockPlayers));
      expect(result.current.state.teamMode).toBe('partners');
      expect(typeof result.current.actions.setMode).toBe('function');
      expect(typeof result.current.actions.toggleTeam1).toBe('function');
      expect(typeof result.current.actions.setCaptain).toBe('function');
    });

    it('computes currentCaptain from rotation', () => {
      const { result } = renderHook(() => useTeamManagement(mockPlayers));
      expect(result.current.currentCaptain).toBe('p1'); // First in rotation

      act(() => {
        result.current.actions.rotateCaptain();
      });
      expect(result.current.currentCaptain).toBe('p2');
    });

    it('computes teamsFormed correctly for partners', () => {
      const { result } = renderHook(() => useTeamManagement(mockPlayers));
      expect(result.current.teamsFormed).toBe(false);

      act(() => {
        result.current.actions.toggleTeam1('p1');
        result.current.actions.toggleTeam1('p2');
      });
      expect(result.current.teamsFormed).toBe(true);
    });

    it('computes teamsFormed correctly for solo', () => {
      const { result } = renderHook(() => useTeamManagement(mockPlayers));

      act(() => {
        result.current.actions.setMode('solo');
      });
      expect(result.current.teamsFormed).toBe(false);

      act(() => {
        result.current.actions.setCaptain('p1');
      });
      expect(result.current.teamsFormed).toBe(true);
    });
  });

  describe('edge cases', () => {
    it('handles unknown action type gracefully', () => {
      const state = initialTeamState(mockPlayers);
      const result = teamReducer(state, { type: 'UNKNOWN_ACTION' });
      expect(result).toEqual(state);
    });

    it('handles empty players array', () => {
      const state = initialTeamState([]);
      expect(state.rotationOrder).toEqual([]);
      expect(state.captainIndex).toBe(0);
    });

    it('prevents selecting all players as team1', () => {
      const { result } = renderHook(() => useTeamManagement(mockPlayers));

      act(() => {
        result.current.actions.toggleTeam1('p1');
        result.current.actions.toggleTeam1('p2');
        result.current.actions.toggleTeam1('p3');
        result.current.actions.toggleTeam1('p4'); // Should not add 4th
      });

      // Can't have all players on team1
      expect(result.current.state.team1.length).toBeLessThan(4);
    });
  });
});
