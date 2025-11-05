// frontend/src/hooks/__tests__/useBettingState.test.js
import { renderHook, act } from '@testing-library/react';
import useBettingState from '../useBettingState';
import { BettingEventTypes } from '../../constants/bettingEvents';

describe('useBettingState', () => {
  test('should initialize with default state', () => {
    const { result } = renderHook(() => useBettingState('game-123', 1));

    expect(result.current.state.currentMultiplier).toBe(1);
    expect(result.current.state.baseAmount).toBe(1.00);
    expect(result.current.state.currentBet).toBe(1.00);
    expect(result.current.state.pendingAction).toBeNull();
    expect(result.current.eventHistory.currentHole).toEqual([]);
  });

  test('should handle DOUBLE_OFFERED event', () => {
    const { result } = renderHook(() => useBettingState('game-123', 1));

    act(() => {
      result.current.actions.offerDouble('Player1', 2);
    });

    expect(result.current.state.pendingAction).toEqual({
      type: 'DOUBLE_OFFERED',
      by: 'Player1',
      proposedMultiplier: 2
    });
    expect(result.current.eventHistory.currentHole.length).toBe(1);
    expect(result.current.eventHistory.currentHole[0].eventType).toBe(BettingEventTypes.DOUBLE_OFFERED);
  });

  test('should handle DOUBLE_ACCEPTED event', () => {
    const { result } = renderHook(() => useBettingState('game-123', 1));

    act(() => {
      result.current.actions.offerDouble('Player1', 2);
    });

    act(() => {
      result.current.actions.acceptDouble('Player2');
    });

    expect(result.current.state.currentMultiplier).toBe(2);
    expect(result.current.state.currentBet).toBe(2.00);
    expect(result.current.state.pendingAction).toBeNull();
  });

  test('should handle DOUBLE_DECLINED event', () => {
    const { result } = renderHook(() => useBettingState('game-123', 1));

    act(() => {
      result.current.actions.offerDouble('Player1', 2);
    });

    act(() => {
      result.current.actions.declineDouble('Player2');
    });

    expect(result.current.state.currentMultiplier).toBe(1);
    expect(result.current.state.pendingAction).toBeNull();
  });

  describe('Input validation', () => {
    test('offerDouble should throw error for null playerId', () => {
      const { result } = renderHook(() => useBettingState('game-123', 1));

      expect(() => {
        act(() => {
          result.current.actions.offerDouble(null, 2);
        });
      }).toThrow('playerId must be a non-empty string');
    });

    test('offerDouble should throw error for empty playerId', () => {
      const { result } = renderHook(() => useBettingState('game-123', 1));

      expect(() => {
        act(() => {
          result.current.actions.offerDouble('', 2);
        });
      }).toThrow('playerId must be a non-empty string');
    });

    test('offerDouble should throw error for negative multiplier', () => {
      const { result } = renderHook(() => useBettingState('game-123', 1));

      expect(() => {
        act(() => {
          result.current.actions.offerDouble('Player1', -1);
        });
      }).toThrow('proposedMultiplier must be a positive number');
    });

    test('offerDouble should throw error for zero multiplier', () => {
      const { result } = renderHook(() => useBettingState('game-123', 1));

      expect(() => {
        act(() => {
          result.current.actions.offerDouble('Player1', 0);
        });
      }).toThrow('proposedMultiplier must be a positive number');
    });

    test('offerDouble should throw error for non-numeric multiplier', () => {
      const { result } = renderHook(() => useBettingState('game-123', 1));

      expect(() => {
        act(() => {
          result.current.actions.offerDouble('Player1', 'two');
        });
      }).toThrow('proposedMultiplier must be a positive number');
    });

    test('acceptDouble should throw error for null playerId', () => {
      const { result } = renderHook(() => useBettingState('game-123', 1));

      act(() => {
        result.current.actions.offerDouble('Player1', 2);
      });

      expect(() => {
        act(() => {
          result.current.actions.acceptDouble(null);
        });
      }).toThrow('playerId must be a non-empty string');
    });

    test('declineDouble should throw error for null playerId', () => {
      const { result } = renderHook(() => useBettingState('game-123', 1));

      act(() => {
        result.current.actions.offerDouble('Player1', 2);
      });

      expect(() => {
        act(() => {
          result.current.actions.declineDouble(null);
        });
      }).toThrow('playerId must be a non-empty string');
    });
  });

  describe('Edge cases', () => {
    test('acceptDouble should be no-op when no pending action', () => {
      const { result } = renderHook(() => useBettingState('game-123', 1));

      const beforeState = result.current.state;
      const beforeEvents = result.current.eventHistory.currentHole.length;

      act(() => {
        result.current.actions.acceptDouble('Player1');
      });

      expect(result.current.state).toEqual(beforeState);
      expect(result.current.eventHistory.currentHole.length).toBe(beforeEvents);
    });

    test('declineDouble should be no-op when no pending action', () => {
      const { result } = renderHook(() => useBettingState('game-123', 1));

      const beforeState = result.current.state;
      const beforeEvents = result.current.eventHistory.currentHole.length;

      act(() => {
        result.current.actions.declineDouble('Player1');
      });

      expect(result.current.state).toEqual(beforeState);
      expect(result.current.eventHistory.currentHole.length).toBe(beforeEvents);
    });

    test('should handle multiple sequential double offers', () => {
      const { result } = renderHook(() => useBettingState('game-123', 1));

      // First double offer
      act(() => {
        result.current.actions.offerDouble('Player1', 2);
      });

      expect(result.current.state.pendingAction.proposedMultiplier).toBe(2);

      // Second double offer (should replace first)
      act(() => {
        result.current.actions.offerDouble('Player2', 4);
      });

      expect(result.current.state.pendingAction.proposedMultiplier).toBe(4);
      expect(result.current.state.pendingAction.by).toBe('Player2');
      expect(result.current.eventHistory.currentHole.length).toBe(2);
    });

    test('should handle sequential accept and new offer', () => {
      const { result } = renderHook(() => useBettingState('game-123', 1));

      // First double offer and accept
      act(() => {
        result.current.actions.offerDouble('Player1', 2);
      });

      act(() => {
        result.current.actions.acceptDouble('Player2');
      });

      expect(result.current.state.currentMultiplier).toBe(2);
      expect(result.current.state.pendingAction).toBeNull();

      // Second double offer from new multiplier
      act(() => {
        result.current.actions.offerDouble('Player1', 4);
      });

      expect(result.current.state.pendingAction.proposedMultiplier).toBe(4);
      // After first offer (index 0) and first accept (index 1), second offer is at index 2
      expect(result.current.eventHistory.currentHole[2].data.currentMultiplier).toBe(2);

      // Accept second offer
      act(() => {
        result.current.actions.acceptDouble('Player2');
      });

      expect(result.current.state.currentMultiplier).toBe(4);
      expect(result.current.state.currentBet).toBe(4.00);
    });

    test('should handle decline followed by new offer', () => {
      const { result } = renderHook(() => useBettingState('game-123', 1));

      // First double offer and decline
      act(() => {
        result.current.actions.offerDouble('Player1', 2);
      });

      act(() => {
        result.current.actions.declineDouble('Player2');
      });

      expect(result.current.state.currentMultiplier).toBe(1);
      expect(result.current.state.pendingAction).toBeNull();

      // New offer after decline
      act(() => {
        result.current.actions.offerDouble('Player1', 2);
      });

      expect(result.current.state.pendingAction).not.toBeNull();
      expect(result.current.state.pendingAction.proposedMultiplier).toBe(2);
    });

    test('should record correct event data for sequential actions', () => {
      const { result } = renderHook(() => useBettingState('game-123', 1));

      // Offer double
      act(() => {
        result.current.actions.offerDouble('Player1', 2);
      });

      const offerEvent = result.current.eventHistory.currentHole[0];
      expect(offerEvent.data.currentMultiplier).toBe(1);
      expect(offerEvent.data.proposedMultiplier).toBe(2);

      // Accept double
      act(() => {
        result.current.actions.acceptDouble('Player2');
      });

      const acceptEvent = result.current.eventHistory.currentHole[1];
      expect(acceptEvent.data.previousMultiplier).toBe(1);
      expect(acceptEvent.data.newMultiplier).toBe(2);

      // Verify game history matches
      expect(result.current.eventHistory.gameHistory.length).toBe(2);
      expect(result.current.eventHistory.gameHistory[0]).toEqual(offerEvent);
      expect(result.current.eventHistory.gameHistory[1]).toEqual(acceptEvent);
    });
  });
});
