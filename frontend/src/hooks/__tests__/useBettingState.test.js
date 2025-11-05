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
});
