import { renderHook, act } from '@testing-library/react';
import { useBettingState } from '../useBettingState';

describe('useBettingState', () => {
  const mockPlayers = [
    { id: 'p1', name: 'Alice' },
    { id: 'p2', name: 'Bob' },
    { id: 'p3', name: 'Charlie' },
    { id: 'p4', name: 'Diana' },
  ];

  const defaultOptions = {
    currentHole: 1,
    currentWager: 1,
    setCurrentWager: jest.fn(),
    players: mockPlayers,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('initial state', () => {
    test('should initialize with empty betting history', () => {
      const { result } = renderHook(() => useBettingState(defaultOptions));
      
      expect(result.current.bettingHistory).toEqual([]);
      expect(result.current.currentHoleBettingEvents).toEqual([]);
      expect(result.current.pendingOffer).toBeNull();
    });

    test('should initialize UI state correctly', () => {
      const { result } = renderHook(() => useBettingState(defaultOptions));
      
      expect(result.current.showBettingHistory).toBe(false);
      expect(result.current.historyTab).toBe('current');
    });
  });

  describe('getPlayerName', () => {
    test('should return player name for valid ID', () => {
      const { result } = renderHook(() => useBettingState(defaultOptions));
      
      expect(result.current.getPlayerName('p1')).toBe('Alice');
      expect(result.current.getPlayerName('p2')).toBe('Bob');
    });

    test('should return Unknown for invalid ID', () => {
      const { result } = renderHook(() => useBettingState(defaultOptions));
      
      expect(result.current.getPlayerName('invalid')).toBe('Unknown');
    });
  });

  describe('createOffer', () => {
    test('should create a pending offer', () => {
      const { result } = renderHook(() => useBettingState(defaultOptions));
      
      let offer;
      act(() => {
        offer = result.current.createOffer('double', 'p1');
      });
      
      expect(offer).toBeDefined();
      expect(offer.offer_type).toBe('double');
      expect(offer.offered_by).toBe('p1');
      expect(offer.wager_before).toBe(1);
      expect(offer.wager_after).toBe(2);
      expect(offer.status).toBe('pending');
      expect(result.current.pendingOffer).toEqual(offer);
    });

    test('should not create offer if one is pending', () => {
      const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
      const { result } = renderHook(() => useBettingState(defaultOptions));
      
      act(() => {
        result.current.createOffer('double', 'p1');
      });
      
      let secondOffer;
      act(() => {
        secondOffer = result.current.createOffer('float', 'p2');
      });
      
      expect(secondOffer).toBeNull();
      expect(warnSpy).toHaveBeenCalledWith('Cannot create offer while another is pending');
      warnSpy.mockRestore();
    });

    test('should add betting event for offer', () => {
      const { result } = renderHook(() => useBettingState(defaultOptions));
      
      act(() => {
        result.current.createOffer('double', 'p1');
      });
      
      expect(result.current.currentHoleBettingEvents.length).toBe(1);
      expect(result.current.currentHoleBettingEvents[0].eventType).toBe('DOUBLE_OFFERED');
    });
  });

  describe('respondToOffer', () => {
    test('should accept pending offer and update wager', () => {
      const setCurrentWager = jest.fn();
      const { result } = renderHook(() => useBettingState({
        ...defaultOptions,
        setCurrentWager,
      }));
      
      act(() => {
        result.current.createOffer('double', 'p1');
      });
      
      act(() => {
        result.current.respondToOffer('accept', 'p2');
      });
      
      expect(setCurrentWager).toHaveBeenCalledWith(2);
      expect(result.current.pendingOffer).toBeNull();
      expect(result.current.currentHoleBettingEvents.some(
        e => e.eventType === 'DOUBLE_ACCEPTED'
      )).toBe(true);
    });

    test('should decline pending offer without updating wager', () => {
      const setCurrentWager = jest.fn();
      const { result } = renderHook(() => useBettingState({
        ...defaultOptions,
        setCurrentWager,
      }));
      
      act(() => {
        result.current.createOffer('double', 'p1');
      });
      
      act(() => {
        result.current.respondToOffer('decline', 'p2');
      });
      
      expect(setCurrentWager).not.toHaveBeenCalled();
      expect(result.current.pendingOffer).toBeNull();
      expect(result.current.currentHoleBettingEvents.some(
        e => e.eventType === 'DOUBLE_DECLINED'
      )).toBe(true);
    });

    test('should warn if no pending offer', () => {
      const warnSpy = jest.spyOn(console, 'warn').mockImplementation(() => {});
      const { result } = renderHook(() => useBettingState(defaultOptions));
      
      act(() => {
        result.current.respondToOffer('accept', 'p2');
      });
      
      expect(warnSpy).toHaveBeenCalledWith('No pending offer to respond to');
      warnSpy.mockRestore();
    });
  });

  describe('cancelOffer', () => {
    test('should cancel pending offer', () => {
      const { result } = renderHook(() => useBettingState(defaultOptions));
      
      act(() => {
        result.current.createOffer('double', 'p1');
      });
      
      expect(result.current.pendingOffer).not.toBeNull();
      
      act(() => {
        result.current.cancelOffer();
      });
      
      expect(result.current.pendingOffer).toBeNull();
      expect(result.current.currentHoleBettingEvents.some(
        e => e.eventType === 'DOUBLE_CANCELLED'
      )).toBe(true);
    });

    test('should do nothing if no pending offer', () => {
      const { result } = renderHook(() => useBettingState(defaultOptions));
      const initialEventsLength = result.current.currentHoleBettingEvents.length;
      
      act(() => {
        result.current.cancelOffer();
      });
      
      expect(result.current.currentHoleBettingEvents.length).toBe(initialEventsLength);
    });
  });

  describe('resetForNewHole', () => {
    test('should clear pending offer and current hole events', () => {
      const { result } = renderHook(() => useBettingState(defaultOptions));
      
      act(() => {
        result.current.createOffer('double', 'p1');
      });
      
      expect(result.current.pendingOffer).not.toBeNull();
      expect(result.current.currentHoleBettingEvents.length).toBeGreaterThan(0);
      
      act(() => {
        result.current.resetForNewHole();
      });
      
      expect(result.current.pendingOffer).toBeNull();
      expect(result.current.currentHoleBettingEvents).toEqual([]);
    });
  });

  describe('loadEventsForEdit', () => {
    test('should load events and clear pending offer', () => {
      const { result } = renderHook(() => useBettingState(defaultOptions));
      const mockEvents = [
        { eventType: 'DOUBLE_OFFERED', hole: 1 },
        { eventType: 'DOUBLE_ACCEPTED', hole: 1 },
      ];
      
      act(() => {
        result.current.createOffer('double', 'p1');
      });
      
      act(() => {
        result.current.loadEventsForEdit(mockEvents);
      });
      
      expect(result.current.currentHoleBettingEvents).toEqual(mockEvents);
      expect(result.current.pendingOffer).toBeNull();
    });

    test('should handle null events', () => {
      const { result } = renderHook(() => useBettingState(defaultOptions));
      
      act(() => {
        result.current.loadEventsForEdit(null);
      });
      
      expect(result.current.currentHoleBettingEvents).toEqual([]);
    });
  });

  describe('getEventsForHole', () => {
    test('should return events for specific hole', () => {
      const { result } = renderHook(() => useBettingState(defaultOptions));
      
      // Create events on hole 1
      act(() => {
        result.current.createOffer('double', 'p1');
      });
      
      const hole1Events = result.current.getEventsForHole(1);
      expect(hole1Events.length).toBeGreaterThan(0);
      expect(hole1Events.every(e => e.hole === 1)).toBe(true);
      
      const hole2Events = result.current.getEventsForHole(2);
      expect(hole2Events.length).toBe(0);
    });
  });

  describe('getLastHoleEvents', () => {
    test('should return empty array on hole 1', () => {
      const { result } = renderHook(() => useBettingState({
        ...defaultOptions,
        currentHole: 1,
      }));
      
      expect(result.current.getLastHoleEvents()).toEqual([]);
    });
  });

  describe('UI state setters', () => {
    test('should toggle showBettingHistory', () => {
      const { result } = renderHook(() => useBettingState(defaultOptions));
      
      act(() => {
        result.current.setShowBettingHistory(true);
      });
      
      expect(result.current.showBettingHistory).toBe(true);
    });

    test('should change historyTab', () => {
      const { result } = renderHook(() => useBettingState(defaultOptions));
      
      act(() => {
        result.current.setHistoryTab('game');
      });
      
      expect(result.current.historyTab).toBe('game');
    });
  });

  describe('logBettingAction', () => {
    test('should log action to betting history', () => {
      const { result } = renderHook(() => useBettingState(defaultOptions));
      
      act(() => {
        result.current.logBettingAction('MANUAL_ACTION', { detail: 'test' });
      });
      
      expect(result.current.bettingHistory.length).toBe(1);
      expect(result.current.bettingHistory[0].eventType).toBe('MANUAL_ACTION');
      expect(result.current.bettingHistory[0].hole).toBe(1);
    });

    test('should resolve player name from playerId', () => {
      const { result } = renderHook(() => useBettingState(defaultOptions));
      
      act(() => {
        result.current.logBettingAction('TEST_ACTION', { playerId: 'p1' });
      });
      
      expect(result.current.bettingHistory[0].actor).toBe('Alice');
    });
  });

  describe('addBettingEvent', () => {
    test('should add event to current hole events', () => {
      const { result } = renderHook(() => useBettingState(defaultOptions));
      
      act(() => {
        result.current.addBettingEvent({
          eventType: 'CUSTOM_EVENT',
          actor: 'Test Actor',
        });
      });
      
      expect(result.current.currentHoleBettingEvents.length).toBe(1);
      expect(result.current.currentHoleBettingEvents[0].eventType).toBe('CUSTOM_EVENT');
      expect(result.current.currentHoleBettingEvents[0].hole).toBe(1);
    });
  });
});
