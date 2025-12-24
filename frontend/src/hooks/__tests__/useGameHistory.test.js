import { renderHook, act } from '@testing-library/react';
import {
  useGameHistory,
  historyReducer,
  HISTORY_ACTIONS,
  initialHistoryState
} from '../useGameHistory';

describe('useGameHistory', () => {
  const mockHole = {
    hole: 1,
    gross_scores: { p1: 4, p2: 5 },
    points_delta: { p1: 2, p2: -2 },
    teams: { type: 'partners', team1: ['p1'], team2: ['p2'] },
  };

  describe('initialHistoryState', () => {
    it('has correct default values', () => {
      expect(initialHistoryState()).toEqual({
        holeHistory: [],
        bettingHistory: [],
      });
    });

    it('accepts initial history', () => {
      const history = [mockHole];
      expect(initialHistoryState(history)).toEqual({
        holeHistory: history,
        bettingHistory: [],
      });
    });
  });

  describe('historyReducer', () => {
    it('ADD_HOLE appends to history', () => {
      const state = initialHistoryState();
      const result = historyReducer(state, { type: HISTORY_ACTIONS.ADD_HOLE, holeData: mockHole });
      expect(result.holeHistory).toHaveLength(1);
      expect(result.holeHistory[0]).toEqual(mockHole);
    });

    it('UPDATE_HOLE updates specific hole', () => {
      const state = { ...initialHistoryState([mockHole, { hole: 2 }]) };
      const result = historyReducer(state, {
        type: HISTORY_ACTIONS.UPDATE_HOLE,
        index: 0,
        holeData: { notes: 'Updated' },
      });
      expect(result.holeHistory[0].notes).toBe('Updated');
      expect(result.holeHistory[1].hole).toBe(2);
    });

    it('SET_HISTORY replaces entire history', () => {
      const state = initialHistoryState([mockHole]);
      const newHistory = [{ hole: 5 }, { hole: 6 }];
      const result = historyReducer(state, { type: HISTORY_ACTIONS.SET_HISTORY, history: newHistory });
      expect(result.holeHistory).toEqual(newHistory);
    });

    it('ADD_BETTING_EVENT adds with timestamp', () => {
      const state = initialHistoryState();
      const event = { type: 'DOUBLE', playerId: 'p1' };
      const result = historyReducer(state, { type: HISTORY_ACTIONS.ADD_BETTING_EVENT, event });
      expect(result.bettingHistory).toHaveLength(1);
      expect(result.bettingHistory[0].type).toBe('DOUBLE');
      expect(result.bettingHistory[0].timestamp).toBeDefined();
    });

    it('CLEAR_BETTING_HISTORY empties betting history', () => {
      const state = { ...initialHistoryState(), bettingHistory: [{ type: 'DOUBLE' }] };
      const result = historyReducer(state, { type: HISTORY_ACTIONS.CLEAR_BETTING_HISTORY });
      expect(result.bettingHistory).toEqual([]);
    });

    it('RESET returns to initial', () => {
      const state = { holeHistory: [mockHole], bettingHistory: [{ type: 'FLOAT' }] };
      const result = historyReducer(state, { type: HISTORY_ACTIONS.RESET });
      expect(result).toEqual(initialHistoryState());
    });

    it('handles unknown action', () => {
      const state = initialHistoryState();
      expect(historyReducer(state, { type: 'UNKNOWN' })).toEqual(state);
    });
  });

  describe('useGameHistory hook', () => {
    it('returns state and actions', () => {
      const { result } = renderHook(() => useGameHistory());
      expect(result.current.state.holeHistory).toEqual([]);
      expect(typeof result.current.actions.addHole).toBe('function');
    });

    it('computes playerStandings from history', () => {
      const { result } = renderHook(() => useGameHistory([mockHole]));
      expect(result.current.playerStandings.p1.quarters).toBe(2);
      expect(result.current.playerStandings.p2.quarters).toBe(-2);
    });

    it('tracks solo count in standings', () => {
      const soloHole = {
        hole: 1,
        points_delta: { p1: 3 },
        teams: { type: 'solo', captain: 'p1', opponents: ['p2'] },
      };
      const { result } = renderHook(() => useGameHistory([soloHole]));
      expect(result.current.playerStandings.p1.soloCount).toBe(1);
    });

    it('computes completedHoles', () => {
      const { result } = renderHook(() => useGameHistory([mockHole, mockHole]));
      expect(result.current.completedHoles).toBe(2);
    });
  });
});
