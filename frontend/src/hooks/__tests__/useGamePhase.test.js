/**
 * useGamePhase - Test Suite
 *
 * Tests for the game phase state machine that manages:
 * - phase ('normal', 'vinnies', 'hoepfinger', 'complete')
 * - isHoepfinger flag
 * - goatId (player who is the goat in hoepfinger)
 * - vinniesVariation flag
 *
 * Phase transitions:
 * - Holes 1-12: normal
 * - Holes 13-16: vinnies (Vinnie's Variation)
 * - Holes 17-18: hoepfinger
 * - After 18: complete
 */

import { renderHook, act } from '@testing-library/react';
import {
  useGamePhase,
  phaseReducer,
  PHASE_ACTIONS,
  initialPhaseState,
  getPhaseForHole,
} from '../useGamePhase';

describe('useGamePhase', () => {
  describe('getPhaseForHole utility', () => {
    it('returns normal for holes 1-12', () => {
      for (let hole = 1; hole <= 12; hole++) {
        expect(getPhaseForHole(hole)).toBe('normal');
      }
    });

    it('returns vinnies for holes 13-16', () => {
      for (let hole = 13; hole <= 16; hole++) {
        expect(getPhaseForHole(hole)).toBe('vinnies');
      }
    });

    it('returns hoepfinger for holes 17-18', () => {
      expect(getPhaseForHole(17)).toBe('hoepfinger');
      expect(getPhaseForHole(18)).toBe('hoepfinger');
    });

    it('returns complete for holes > 18', () => {
      expect(getPhaseForHole(19)).toBe('complete');
      expect(getPhaseForHole(20)).toBe('complete');
    });

    it('returns normal for invalid holes', () => {
      expect(getPhaseForHole(0)).toBe('normal');
      expect(getPhaseForHole(-1)).toBe('normal');
    });
  });

  describe('initialPhaseState', () => {
    it('has correct default values', () => {
      expect(initialPhaseState()).toEqual({
        phase: 'normal',
        isHoepfinger: false,
        goatId: null,
        vinniesVariation: false,
        currentHole: 1,
      });
    });

    it('respects initial hole number', () => {
      const state = initialPhaseState(15);
      expect(state.currentHole).toBe(15);
      expect(state.phase).toBe('vinnies');
      expect(state.vinniesVariation).toBe(true);
    });

    it('initializes hoepfinger phase correctly', () => {
      const state = initialPhaseState(17);
      expect(state.phase).toBe('hoepfinger');
      expect(state.isHoepfinger).toBe(true);
    });
  });

  describe('phaseReducer - SET_HOLE action', () => {
    it('transitions to vinnies at hole 13', () => {
      const state = initialPhaseState(12);
      const result = phaseReducer(state, { type: PHASE_ACTIONS.SET_HOLE, hole: 13 });
      expect(result.phase).toBe('vinnies');
      expect(result.vinniesVariation).toBe(true);
      expect(result.currentHole).toBe(13);
    });

    it('transitions to hoepfinger at hole 17', () => {
      const state = initialPhaseState(16);
      const result = phaseReducer(state, { type: PHASE_ACTIONS.SET_HOLE, hole: 17 });
      expect(result.phase).toBe('hoepfinger');
      expect(result.isHoepfinger).toBe(true);
    });

    it('transitions to complete after hole 18', () => {
      const state = initialPhaseState(18);
      const result = phaseReducer(state, { type: PHASE_ACTIONS.SET_HOLE, hole: 19 });
      expect(result.phase).toBe('complete');
    });

    it('goes back to normal when returning to hole 12', () => {
      const state = { ...initialPhaseState(14), phase: 'vinnies', vinniesVariation: true };
      const result = phaseReducer(state, { type: PHASE_ACTIONS.SET_HOLE, hole: 12 });
      expect(result.phase).toBe('normal');
      expect(result.vinniesVariation).toBe(false);
    });
  });

  describe('phaseReducer - SET_GOAT action', () => {
    it('sets the goat player', () => {
      const state = initialPhaseState(17);
      const result = phaseReducer(state, { type: PHASE_ACTIONS.SET_GOAT, goatId: 'player-3' });
      expect(result.goatId).toBe('player-3');
    });

    it('clears goat when null passed', () => {
      const state = { ...initialPhaseState(17), goatId: 'player-3' };
      const result = phaseReducer(state, { type: PHASE_ACTIONS.SET_GOAT, goatId: null });
      expect(result.goatId).toBeNull();
    });
  });

  describe('phaseReducer - ENTER_HOEPFINGER action', () => {
    it('enters hoepfinger phase with goat', () => {
      const state = initialPhaseState(16);
      const result = phaseReducer(state, {
        type: PHASE_ACTIONS.ENTER_HOEPFINGER,
        goatId: 'player-2',
      });
      expect(result.phase).toBe('hoepfinger');
      expect(result.isHoepfinger).toBe(true);
      expect(result.goatId).toBe('player-2');
    });
  });

  describe('phaseReducer - EXIT_HOEPFINGER action', () => {
    it('exits hoepfinger phase', () => {
      const state = {
        ...initialPhaseState(17),
        phase: 'hoepfinger',
        isHoepfinger: true,
        goatId: 'player-2',
      };
      const result = phaseReducer(state, { type: PHASE_ACTIONS.EXIT_HOEPFINGER });
      expect(result.isHoepfinger).toBe(false);
      expect(result.goatId).toBeNull();
      // Phase determined by hole number
      expect(result.phase).toBe('hoepfinger'); // Still on 17
    });
  });

  describe('phaseReducer - SET_VINNIES action', () => {
    it('enables vinnies variation', () => {
      const state = initialPhaseState(13);
      const result = phaseReducer(state, { type: PHASE_ACTIONS.SET_VINNIES, active: true });
      expect(result.vinniesVariation).toBe(true);
    });

    it('disables vinnies variation', () => {
      const state = { ...initialPhaseState(13), vinniesVariation: true };
      const result = phaseReducer(state, { type: PHASE_ACTIONS.SET_VINNIES, active: false });
      expect(result.vinniesVariation).toBe(false);
    });
  });

  describe('phaseReducer - COMPLETE_GAME action', () => {
    it('sets phase to complete', () => {
      const state = initialPhaseState(18);
      const result = phaseReducer(state, { type: PHASE_ACTIONS.COMPLETE_GAME });
      expect(result.phase).toBe('complete');
    });
  });

  describe('phaseReducer - RESET action', () => {
    it('resets to initial state', () => {
      const state = {
        phase: 'hoepfinger',
        isHoepfinger: true,
        goatId: 'player-1',
        vinniesVariation: true,
        currentHole: 17,
      };
      const result = phaseReducer(state, { type: PHASE_ACTIONS.RESET });
      expect(result).toEqual(initialPhaseState(1));
    });
  });

  describe('useGamePhase hook', () => {
    it('returns state and actions', () => {
      const { result } = renderHook(() => useGamePhase(1));
      expect(result.current.state.phase).toBe('normal');
      expect(typeof result.current.actions.setHole).toBe('function');
      expect(typeof result.current.actions.setGoat).toBe('function');
    });

    it('advances hole correctly', () => {
      const { result } = renderHook(() => useGamePhase(12));

      act(() => {
        result.current.actions.advanceHole();
      });

      expect(result.current.state.currentHole).toBe(13);
      expect(result.current.state.phase).toBe('vinnies');
    });

    it('provides computed holesUntilHoepfinger', () => {
      const { result } = renderHook(() => useGamePhase(12));
      expect(result.current.holesUntilHoepfinger).toBe(5); // 17 - 12 = 5
    });

    it('provides isLastChance flag', () => {
      const { result: result16 } = renderHook(() => useGamePhase(16));
      expect(result16.current.isLastChance).toBe(true);

      const { result: result15 } = renderHook(() => useGamePhase(15));
      expect(result15.current.isLastChance).toBe(false);
    });

    it('provides isGameComplete flag', () => {
      const { result } = renderHook(() => useGamePhase(18));
      expect(result.current.isGameComplete).toBe(false);

      act(() => {
        result.current.actions.completeGame();
      });

      expect(result.current.isGameComplete).toBe(true);
    });
  });

  describe('edge cases', () => {
    it('handles unknown action type gracefully', () => {
      const state = initialPhaseState(1);
      const result = phaseReducer(state, { type: 'UNKNOWN_ACTION' });
      expect(result).toEqual(state);
    });

    it('handles rapid hole changes', () => {
      const { result } = renderHook(() => useGamePhase(1));

      act(() => {
        result.current.actions.setHole(5);
        result.current.actions.setHole(13);
        result.current.actions.setHole(17);
      });

      expect(result.current.state.currentHole).toBe(17);
      expect(result.current.state.phase).toBe('hoepfinger');
    });

    it('correctly handles editing past holes', () => {
      const { result } = renderHook(() => useGamePhase(17));

      // Go back to edit hole 5
      act(() => {
        result.current.actions.setHole(5);
      });

      expect(result.current.state.phase).toBe('normal');
      expect(result.current.state.isHoepfinger).toBe(false);
    });
  });
});
