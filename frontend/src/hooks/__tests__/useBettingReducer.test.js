/**
 * useBettingReducer - Test Suite
 *
 * Tests for the betting state reducer that consolidates:
 * - currentWager, nextHoleWager, joesSpecialWager
 * - floatInvokedBy, optionInvokedBy
 * - carryOver, carryOverApplied
 * - vinniesVariation
 * - optionActive, optionTurnedOff
 * - duncanInvoked
 */

import { renderHook, act } from '@testing-library/react';
import { useBettingReducer, bettingReducer, BETTING_ACTIONS, initialBettingState } from '../useBettingReducer';

describe('useBettingReducer', () => {
  describe('initialBettingState', () => {
    it('has correct default values', () => {
      expect(initialBettingState(1)).toEqual({
        baseWager: 1,
        currentWager: 1,
        nextHoleWager: 1,
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
    });

    it('respects custom base wager', () => {
      const state = initialBettingState(5);
      expect(state.baseWager).toBe(5);
      expect(state.currentWager).toBe(5);
      expect(state.nextHoleWager).toBe(5);
    });
  });

  describe('bettingReducer - DOUBLE action', () => {
    it('doubles the current wager', () => {
      const state = { ...initialBettingState(1), currentWager: 2 };
      const result = bettingReducer(state, { type: BETTING_ACTIONS.DOUBLE });
      expect(result.currentWager).toBe(4);
    });

    it('tracks who invoked double via playerId', () => {
      const state = initialBettingState(1);
      const result = bettingReducer(state, {
        type: BETTING_ACTIONS.DOUBLE,
        playerId: 'player-1'
      });
      expect(result.currentWager).toBe(2);
    });
  });

  describe('bettingReducer - FLOAT action', () => {
    it('doubles the wager when float is invoked', () => {
      const state = initialBettingState(1);
      const result = bettingReducer(state, {
        type: BETTING_ACTIONS.FLOAT,
        playerId: 'player-1'
      });
      expect(result.currentWager).toBe(2);
      expect(result.floatInvokedBy).toBe('player-1');
    });

    it('prevents double float (idempotent)', () => {
      const state = {
        ...initialBettingState(1),
        currentWager: 2,
        floatInvokedBy: 'player-1'
      };
      const result = bettingReducer(state, {
        type: BETTING_ACTIONS.FLOAT,
        playerId: 'player-2'
      });
      // Should not change - already floated
      expect(result.currentWager).toBe(2);
      expect(result.floatInvokedBy).toBe('player-1');
    });
  });

  describe('bettingReducer - OPTION action', () => {
    it('activates option and tracks invoker', () => {
      const state = initialBettingState(1);
      const result = bettingReducer(state, {
        type: BETTING_ACTIONS.OPTION,
        playerId: 'captain-1'
      });
      expect(result.optionActive).toBe(true);
      expect(result.optionInvokedBy).toBe('captain-1');
    });

    it('does not activate if option was turned off', () => {
      const state = { ...initialBettingState(1), optionTurnedOff: true };
      const result = bettingReducer(state, {
        type: BETTING_ACTIONS.OPTION,
        playerId: 'captain-1'
      });
      expect(result.optionActive).toBe(false);
    });
  });

  describe('bettingReducer - OPTION_OFF action', () => {
    it('deactivates option permanently for the hole', () => {
      const state = { ...initialBettingState(1), optionActive: true };
      const result = bettingReducer(state, { type: BETTING_ACTIONS.OPTION_OFF });
      expect(result.optionActive).toBe(false);
      expect(result.optionTurnedOff).toBe(true);
    });
  });

  describe('bettingReducer - DUNCAN action', () => {
    it('invokes duncan (doubles wager)', () => {
      const state = initialBettingState(1);
      const result = bettingReducer(state, { type: BETTING_ACTIONS.DUNCAN });
      expect(result.duncanInvoked).toBe(true);
      expect(result.currentWager).toBe(2);
    });

    it('prevents double duncan', () => {
      const state = { ...initialBettingState(1), duncanInvoked: true, currentWager: 2 };
      const result = bettingReducer(state, { type: BETTING_ACTIONS.DUNCAN });
      expect(result.currentWager).toBe(2); // No change
    });
  });

  describe('bettingReducer - CARRY_OVER action', () => {
    it('sets carry over flag', () => {
      const state = initialBettingState(1);
      const result = bettingReducer(state, { type: BETTING_ACTIONS.CARRY_OVER });
      expect(result.carryOver).toBe(true);
    });
  });

  describe('bettingReducer - APPLY_CARRY_OVER action', () => {
    it('doubles wager and marks as applied', () => {
      const state = { ...initialBettingState(1), carryOver: true };
      const result = bettingReducer(state, { type: BETTING_ACTIONS.APPLY_CARRY_OVER });
      expect(result.currentWager).toBe(2);
      expect(result.carryOverApplied).toBe(true);
      expect(result.carryOver).toBe(false);
    });

    it('does nothing if no carry over', () => {
      const state = initialBettingState(1);
      const result = bettingReducer(state, { type: BETTING_ACTIONS.APPLY_CARRY_OVER });
      expect(result.currentWager).toBe(1);
      expect(result.carryOverApplied).toBe(false);
    });
  });

  describe('bettingReducer - VINNIES_VARIATION action', () => {
    it('activates vinnies variation', () => {
      const state = initialBettingState(1);
      const result = bettingReducer(state, {
        type: BETTING_ACTIONS.VINNIES_VARIATION,
        active: true
      });
      expect(result.vinniesVariation).toBe(true);
    });

    it('deactivates vinnies variation', () => {
      const state = { ...initialBettingState(1), vinniesVariation: true };
      const result = bettingReducer(state, {
        type: BETTING_ACTIONS.VINNIES_VARIATION,
        active: false
      });
      expect(result.vinniesVariation).toBe(false);
    });
  });

  describe('bettingReducer - JOES_SPECIAL action', () => {
    it('sets joes special wager', () => {
      const state = initialBettingState(1);
      const result = bettingReducer(state, {
        type: BETTING_ACTIONS.JOES_SPECIAL,
        wager: 8
      });
      expect(result.joesSpecialWager).toBe(8);
    });
  });

  describe('bettingReducer - SET_NEXT_HOLE_WAGER action', () => {
    it('sets the wager for next hole', () => {
      const state = initialBettingState(1);
      const result = bettingReducer(state, {
        type: BETTING_ACTIONS.SET_NEXT_HOLE_WAGER,
        wager: 4
      });
      expect(result.nextHoleWager).toBe(4);
    });
  });

  describe('bettingReducer - RESET_FOR_HOLE action', () => {
    it('resets per-hole state but keeps persistent state', () => {
      const state = {
        ...initialBettingState(1),
        currentWager: 8,
        floatInvokedBy: 'player-1',
        optionInvokedBy: 'captain-1',
        optionActive: true,
        optionTurnedOff: true,
        duncanInvoked: true,
        carryOverApplied: true,
        nextHoleWager: 4,
      };
      const result = bettingReducer(state, { type: BETTING_ACTIONS.RESET_FOR_HOLE });

      // Should reset to nextHoleWager
      expect(result.currentWager).toBe(4);
      // Should clear per-hole flags
      expect(result.floatInvokedBy).toBeNull();
      expect(result.optionInvokedBy).toBeNull();
      expect(result.optionActive).toBe(false);
      expect(result.optionTurnedOff).toBe(false);
      expect(result.duncanInvoked).toBe(false);
      expect(result.carryOverApplied).toBe(false);
      // Should reset nextHoleWager to base
      expect(result.nextHoleWager).toBe(1);
    });
  });

  describe('bettingReducer - RESET_ALL action', () => {
    it('resets everything to initial state', () => {
      const state = {
        ...initialBettingState(2),
        currentWager: 16,
        floatInvokedBy: 'player-1',
        carryOver: true,
        vinniesVariation: true,
      };
      const result = bettingReducer(state, { type: BETTING_ACTIONS.RESET_ALL });
      expect(result).toEqual(initialBettingState(2));
    });
  });

  describe('useBettingReducer hook', () => {
    it('returns state and dispatch', () => {
      const { result } = renderHook(() => useBettingReducer(1));
      expect(result.current.state).toEqual(initialBettingState(1));
      expect(typeof result.current.dispatch).toBe('function');
    });

    it('provides action helper functions', () => {
      const { result } = renderHook(() => useBettingReducer(1));
      expect(typeof result.current.actions.double).toBe('function');
      expect(typeof result.current.actions.float).toBe('function');
      expect(typeof result.current.actions.option).toBe('function');
      expect(typeof result.current.actions.duncan).toBe('function');
      expect(typeof result.current.actions.resetForHole).toBe('function');
    });

    it('double action works through helper', () => {
      const { result } = renderHook(() => useBettingReducer(1));
      act(() => {
        result.current.actions.double();
      });
      expect(result.current.state.currentWager).toBe(2);
    });

    it('float action works through helper', () => {
      const { result } = renderHook(() => useBettingReducer(1));
      act(() => {
        result.current.actions.float('player-1');
      });
      expect(result.current.state.currentWager).toBe(2);
      expect(result.current.state.floatInvokedBy).toBe('player-1');
    });
  });

  describe('edge cases', () => {
    it('handles unknown action type gracefully', () => {
      const state = initialBettingState(1);
      const result = bettingReducer(state, { type: 'UNKNOWN_ACTION' });
      expect(result).toEqual(state);
    });

    it('handles rapid successive doubles', () => {
      let state = initialBettingState(1);
      state = bettingReducer(state, { type: BETTING_ACTIONS.DOUBLE });
      state = bettingReducer(state, { type: BETTING_ACTIONS.DOUBLE });
      state = bettingReducer(state, { type: BETTING_ACTIONS.DOUBLE });
      expect(state.currentWager).toBe(8);
    });

    it('handles combined float + double + duncan', () => {
      let state = initialBettingState(1);
      state = bettingReducer(state, { type: BETTING_ACTIONS.FLOAT, playerId: 'p1' }); // 1 -> 2
      state = bettingReducer(state, { type: BETTING_ACTIONS.DOUBLE }); // 2 -> 4
      state = bettingReducer(state, { type: BETTING_ACTIONS.DUNCAN }); // 4 -> 8
      expect(state.currentWager).toBe(8);
      expect(state.floatInvokedBy).toBe('p1');
      expect(state.duncanInvoked).toBe(true);
    });
  });
});
