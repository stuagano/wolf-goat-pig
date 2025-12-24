import { renderHook, act } from '@testing-library/react';
import {
  useAardvarkState,
  aardvarkReducer,
  AARDVARK_ACTIONS,
  initialAardvarkState
} from '../useAardvarkState';

describe('useAardvarkState', () => {
  describe('initialAardvarkState', () => {
    it('has correct default values', () => {
      expect(initialAardvarkState()).toEqual({
        requestedTeam: null,
        tossed: false,
        solo: false,
        invisibleTossed: false,
      });
    });
  });

  describe('aardvarkReducer', () => {
    it('REQUEST_TEAM sets the requested team', () => {
      const state = initialAardvarkState();
      const result = aardvarkReducer(state, { type: AARDVARK_ACTIONS.REQUEST_TEAM, team: 'team1' });
      expect(result.requestedTeam).toBe('team1');
    });

    it('TOSS marks aardvark as tossed and clears request', () => {
      const state = { ...initialAardvarkState(), requestedTeam: 'team1' };
      const result = aardvarkReducer(state, { type: AARDVARK_ACTIONS.TOSS });
      expect(result.tossed).toBe(true);
      expect(result.requestedTeam).toBeNull();
    });

    it('GO_SOLO sets solo and tossed', () => {
      const state = { ...initialAardvarkState(), requestedTeam: 'team2' };
      const result = aardvarkReducer(state, { type: AARDVARK_ACTIONS.GO_SOLO });
      expect(result.solo).toBe(true);
      expect(result.tossed).toBe(true);
      expect(result.requestedTeam).toBeNull();
    });

    it('INVISIBLE_TOSS sets invisibleTossed', () => {
      const state = initialAardvarkState();
      const result = aardvarkReducer(state, { type: AARDVARK_ACTIONS.INVISIBLE_TOSS });
      expect(result.invisibleTossed).toBe(true);
    });

    it('ACCEPT clears tossed and request', () => {
      const state = { ...initialAardvarkState(), tossed: true };
      const result = aardvarkReducer(state, { type: AARDVARK_ACTIONS.ACCEPT });
      expect(result.tossed).toBe(false);
      expect(result.requestedTeam).toBeNull();
    });

    it('RESET returns to initial state', () => {
      const state = { requestedTeam: 'team1', tossed: true, solo: true, invisibleTossed: true };
      const result = aardvarkReducer(state, { type: AARDVARK_ACTIONS.RESET });
      expect(result).toEqual(initialAardvarkState());
    });

    it('handles unknown action', () => {
      const state = initialAardvarkState();
      const result = aardvarkReducer(state, { type: 'UNKNOWN' });
      expect(result).toEqual(state);
    });
  });

  describe('useAardvarkState hook', () => {
    it('returns state and actions', () => {
      const { result } = renderHook(() => useAardvarkState());
      expect(result.current.state).toEqual(initialAardvarkState());
      expect(typeof result.current.actions.requestTeam).toBe('function');
    });

    it('computes isAardvarkActive correctly', () => {
      const { result } = renderHook(() => useAardvarkState());
      expect(result.current.isAardvarkActive).toBe(false);

      act(() => result.current.actions.requestTeam('team1'));
      expect(result.current.isAardvarkActive).toBe(true);

      act(() => result.current.actions.toss());
      expect(result.current.isAardvarkActive).toBe(false);
    });
  });
});
