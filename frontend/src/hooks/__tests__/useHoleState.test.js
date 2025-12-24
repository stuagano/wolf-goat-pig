/**
 * useHoleState - Test Suite
 *
 * Tests for the hole state reducer that manages:
 * - scores (gross scores per player)
 * - quarters (points per player)
 * - winner (hole winner)
 * - holeNotes (notes for current hole)
 * - playerDisplayOrder (order for entering quarters)
 */

import { renderHook, act } from '@testing-library/react';
import {
  useHoleState,
  holeReducer,
  HOLE_ACTIONS,
  initialHoleState
} from '../useHoleState';

const mockPlayers = [
  { id: 'p1', name: 'Alice' },
  { id: 'p2', name: 'Bob' },
  { id: 'p3', name: 'Charlie' },
  { id: 'p4', name: 'Diana' },
];

describe('useHoleState', () => {
  describe('initialHoleState', () => {
    it('has correct default values', () => {
      const state = initialHoleState(mockPlayers);
      expect(state).toEqual({
        scores: {},
        quarters: {},
        winner: null,
        holeNotes: '',
        playerDisplayOrder: ['p1', 'p2', 'p3', 'p4'],
        players: mockPlayers,
      });
    });

    it('initializes playerDisplayOrder from players', () => {
      const players = [{ id: 'x1' }, { id: 'x2' }];
      const state = initialHoleState(players);
      expect(state.playerDisplayOrder).toEqual(['x1', 'x2']);
    });
  });

  describe('holeReducer - SET_SCORE action', () => {
    it('sets score for a player', () => {
      const state = initialHoleState(mockPlayers);
      const result = holeReducer(state, {
        type: HOLE_ACTIONS.SET_SCORE,
        playerId: 'p1',
        score: 5,
      });
      expect(result.scores).toEqual({ p1: 5 });
    });

    it('updates existing score', () => {
      const state = { ...initialHoleState(mockPlayers), scores: { p1: 4 } };
      const result = holeReducer(state, {
        type: HOLE_ACTIONS.SET_SCORE,
        playerId: 'p1',
        score: 6,
      });
      expect(result.scores).toEqual({ p1: 6 });
    });

    it('sets multiple scores independently', () => {
      let state = initialHoleState(mockPlayers);
      state = holeReducer(state, { type: HOLE_ACTIONS.SET_SCORE, playerId: 'p1', score: 4 });
      state = holeReducer(state, { type: HOLE_ACTIONS.SET_SCORE, playerId: 'p2', score: 5 });
      expect(state.scores).toEqual({ p1: 4, p2: 5 });
    });
  });

  describe('holeReducer - SET_ALL_SCORES action', () => {
    it('sets all scores at once', () => {
      const state = initialHoleState(mockPlayers);
      const scores = { p1: 4, p2: 5, p3: 4, p4: 6 };
      const result = holeReducer(state, {
        type: HOLE_ACTIONS.SET_ALL_SCORES,
        scores,
      });
      expect(result.scores).toEqual(scores);
    });
  });

  describe('holeReducer - SET_QUARTERS action', () => {
    it('sets quarters for a player', () => {
      const state = initialHoleState(mockPlayers);
      const result = holeReducer(state, {
        type: HOLE_ACTIONS.SET_QUARTERS,
        playerId: 'p1',
        quarters: 2,
      });
      expect(result.quarters).toEqual({ p1: 2 });
    });

    it('handles negative quarters', () => {
      const state = initialHoleState(mockPlayers);
      const result = holeReducer(state, {
        type: HOLE_ACTIONS.SET_QUARTERS,
        playerId: 'p2',
        quarters: -3,
      });
      expect(result.quarters).toEqual({ p2: -3 });
    });
  });

  describe('holeReducer - SET_ALL_QUARTERS action', () => {
    it('sets all quarters at once', () => {
      const state = initialHoleState(mockPlayers);
      const quarters = { p1: 2, p2: -1, p3: 1, p4: -2 };
      const result = holeReducer(state, {
        type: HOLE_ACTIONS.SET_ALL_QUARTERS,
        quarters,
      });
      expect(result.quarters).toEqual(quarters);
    });
  });

  describe('holeReducer - SET_WINNER action', () => {
    it('sets the winner', () => {
      const state = initialHoleState(mockPlayers);
      const result = holeReducer(state, {
        type: HOLE_ACTIONS.SET_WINNER,
        winner: 'team1',
      });
      expect(result.winner).toBe('team1');
    });

    it('clears winner when null', () => {
      const state = { ...initialHoleState(mockPlayers), winner: 'team1' };
      const result = holeReducer(state, {
        type: HOLE_ACTIONS.SET_WINNER,
        winner: null,
      });
      expect(result.winner).toBeNull();
    });
  });

  describe('holeReducer - SET_NOTES action', () => {
    it('sets hole notes', () => {
      const state = initialHoleState(mockPlayers);
      const result = holeReducer(state, {
        type: HOLE_ACTIONS.SET_NOTES,
        notes: 'Great eagle by Alice!',
      });
      expect(result.holeNotes).toBe('Great eagle by Alice!');
    });
  });

  describe('holeReducer - SET_DISPLAY_ORDER action', () => {
    it('sets player display order', () => {
      const state = initialHoleState(mockPlayers);
      const result = holeReducer(state, {
        type: HOLE_ACTIONS.SET_DISPLAY_ORDER,
        order: ['p4', 'p3', 'p2', 'p1'],
      });
      expect(result.playerDisplayOrder).toEqual(['p4', 'p3', 'p2', 'p1']);
    });
  });

  describe('holeReducer - RESTORE_FROM_HOLE action', () => {
    it('restores state from hole data', () => {
      const state = initialHoleState(mockPlayers);
      const holeData = {
        gross_scores: { p1: 4, p2: 5, p3: 4, p4: 6 },
        points_delta: { p1: 2, p2: -1, p3: 1, p4: -2 },
        winner: 'team1',
        notes: 'Exciting hole!',
      };
      const result = holeReducer(state, {
        type: HOLE_ACTIONS.RESTORE_FROM_HOLE,
        holeData,
      });
      expect(result.scores).toEqual(holeData.gross_scores);
      expect(result.quarters).toEqual(holeData.points_delta);
      expect(result.winner).toBe('team1');
      expect(result.holeNotes).toBe('Exciting hole!');
    });

    it('handles missing fields gracefully', () => {
      const state = initialHoleState(mockPlayers);
      const holeData = { gross_scores: { p1: 4 } };
      const result = holeReducer(state, {
        type: HOLE_ACTIONS.RESTORE_FROM_HOLE,
        holeData,
      });
      expect(result.scores).toEqual({ p1: 4 });
      expect(result.quarters).toEqual({});
      expect(result.winner).toBeNull();
      expect(result.holeNotes).toBe('');
    });
  });

  describe('holeReducer - RESET action', () => {
    it('resets to initial state', () => {
      const state = {
        ...initialHoleState(mockPlayers),
        scores: { p1: 4, p2: 5 },
        quarters: { p1: 2, p2: -2 },
        winner: 'team1',
        holeNotes: 'Some notes',
      };
      const result = holeReducer(state, { type: HOLE_ACTIONS.RESET });
      expect(result.scores).toEqual({});
      expect(result.quarters).toEqual({});
      expect(result.winner).toBeNull();
      expect(result.holeNotes).toBe('');
      // playerDisplayOrder preserved
      expect(result.playerDisplayOrder).toEqual(['p1', 'p2', 'p3', 'p4']);
    });
  });

  describe('useHoleState hook', () => {
    it('returns state and actions', () => {
      const { result } = renderHook(() => useHoleState(mockPlayers));
      expect(result.current.state.scores).toEqual({});
      expect(typeof result.current.actions.setScore).toBe('function');
      expect(typeof result.current.actions.setQuarters).toBe('function');
    });

    it('setScore action works', () => {
      const { result } = renderHook(() => useHoleState(mockPlayers));
      act(() => {
        result.current.actions.setScore('p1', 5);
      });
      expect(result.current.state.scores).toEqual({ p1: 5 });
    });

    it('computes allScoresEntered correctly', () => {
      const { result } = renderHook(() => useHoleState(mockPlayers));
      expect(result.current.allScoresEntered).toBe(false);

      act(() => {
        result.current.actions.setScore('p1', 4);
        result.current.actions.setScore('p2', 5);
        result.current.actions.setScore('p3', 4);
        result.current.actions.setScore('p4', 6);
      });
      expect(result.current.allScoresEntered).toBe(true);
    });

    it('computes allQuartersEntered correctly', () => {
      const { result } = renderHook(() => useHoleState(mockPlayers));
      expect(result.current.allQuartersEntered).toBe(false);

      act(() => {
        result.current.actions.setQuarters('p1', 2);
        result.current.actions.setQuarters('p2', -1);
        result.current.actions.setQuarters('p3', 1);
        result.current.actions.setQuarters('p4', -2);
      });
      expect(result.current.allQuartersEntered).toBe(true);
    });

    it('computes quartersSum correctly', () => {
      const { result } = renderHook(() => useHoleState(mockPlayers));

      act(() => {
        result.current.actions.setQuarters('p1', 2);
        result.current.actions.setQuarters('p2', -1);
        result.current.actions.setQuarters('p3', 1);
        result.current.actions.setQuarters('p4', -2);
      });
      expect(result.current.quartersSum).toBe(0);
    });

    it('computes quartersBalanced correctly', () => {
      const { result } = renderHook(() => useHoleState(mockPlayers));

      act(() => {
        result.current.actions.setQuarters('p1', 2);
        result.current.actions.setQuarters('p2', -2);
      });
      expect(result.current.quartersBalanced).toBe(true);

      act(() => {
        result.current.actions.setQuarters('p3', 1);
      });
      expect(result.current.quartersBalanced).toBe(false);
    });
  });

  describe('edge cases', () => {
    it('handles unknown action type gracefully', () => {
      const state = initialHoleState(mockPlayers);
      const result = holeReducer(state, { type: 'UNKNOWN_ACTION' });
      expect(result).toEqual(state);
    });

    it('handles empty players array', () => {
      const state = initialHoleState([]);
      expect(state.playerDisplayOrder).toEqual([]);
    });

    it('handles score of 0', () => {
      const { result } = renderHook(() => useHoleState(mockPlayers));
      // 0 is not a valid golf score, but reducer should accept it
      act(() => {
        result.current.actions.setScore('p1', 0);
      });
      expect(result.current.state.scores).toEqual({ p1: 0 });
    });
  });
});
