import { renderHook, act } from '@testing-library/react';
import {
  useBettingOffers,
  offerReducer,
  OFFER_ACTIONS,
  OFFER_TYPES,
  initialOfferState
} from '../useBettingOffers';

describe('useBettingOffers', () => {
  describe('initialOfferState', () => {
    it('has correct default values', () => {
      expect(initialOfferState()).toEqual({
        pendingOffer: null,
        currentHoleBettingEvents: [],
      });
    });
  });

  describe('offerReducer', () => {
    it('CREATE_OFFER creates a pending offer', () => {
      const state = initialOfferState();
      const result = offerReducer(state, {
        type: OFFER_ACTIONS.CREATE_OFFER,
        offerType: OFFER_TYPES.DOUBLE,
        from: 'p1',
        to: 'p2',
        wagerMultiplier: 2,
      });
      expect(result.pendingOffer).not.toBeNull();
      expect(result.pendingOffer.type).toBe(OFFER_TYPES.DOUBLE);
      expect(result.pendingOffer.from).toBe('p1');
      expect(result.pendingOffer.to).toBe('p2');
      expect(result.pendingOffer.wagerMultiplier).toBe(2);
      expect(result.pendingOffer.timestamp).toBeDefined();
    });

    it('CREATE_OFFER defaults wagerMultiplier to 1', () => {
      const state = initialOfferState();
      const result = offerReducer(state, {
        type: OFFER_ACTIONS.CREATE_OFFER,
        offerType: OFFER_TYPES.FLOAT,
        from: 'p1',
        to: 'p2',
      });
      expect(result.pendingOffer.wagerMultiplier).toBe(1);
    });

    it('ACCEPT_OFFER moves offer to events with accepted status', () => {
      const state = {
        pendingOffer: {
          type: OFFER_TYPES.DOUBLE,
          from: 'p1',
          to: 'p2',
          wagerMultiplier: 2,
          timestamp: 1000,
        },
        currentHoleBettingEvents: [],
      };
      const result = offerReducer(state, { type: OFFER_ACTIONS.ACCEPT_OFFER });
      expect(result.pendingOffer).toBeNull();
      expect(result.currentHoleBettingEvents).toHaveLength(1);
      expect(result.currentHoleBettingEvents[0].status).toBe('accepted');
      expect(result.currentHoleBettingEvents[0].acceptedAt).toBeDefined();
    });

    it('ACCEPT_OFFER does nothing if no pending offer', () => {
      const state = initialOfferState();
      const result = offerReducer(state, { type: OFFER_ACTIONS.ACCEPT_OFFER });
      expect(result).toEqual(state);
    });

    it('REJECT_OFFER moves offer to events with rejected status', () => {
      const state = {
        pendingOffer: {
          type: OFFER_TYPES.OPTION,
          from: 'p1',
          to: 'p2',
          wagerMultiplier: 1,
          timestamp: 1000,
        },
        currentHoleBettingEvents: [],
      };
      const result = offerReducer(state, { type: OFFER_ACTIONS.REJECT_OFFER });
      expect(result.pendingOffer).toBeNull();
      expect(result.currentHoleBettingEvents).toHaveLength(1);
      expect(result.currentHoleBettingEvents[0].status).toBe('rejected');
      expect(result.currentHoleBettingEvents[0].rejectedAt).toBeDefined();
    });

    it('REJECT_OFFER does nothing if no pending offer', () => {
      const state = initialOfferState();
      const result = offerReducer(state, { type: OFFER_ACTIONS.REJECT_OFFER });
      expect(result).toEqual(state);
    });

    it('CANCEL_OFFER clears pending offer without adding to events', () => {
      const state = {
        pendingOffer: { type: OFFER_TYPES.PRESS, from: 'p1', to: 'p2' },
        currentHoleBettingEvents: [],
      };
      const result = offerReducer(state, { type: OFFER_ACTIONS.CANCEL_OFFER });
      expect(result.pendingOffer).toBeNull();
      expect(result.currentHoleBettingEvents).toHaveLength(0);
    });

    it('ADD_BETTING_EVENT adds event with timestamp', () => {
      const state = initialOfferState();
      const event = { type: 'MANUAL', description: 'Test event' };
      const result = offerReducer(state, { type: OFFER_ACTIONS.ADD_BETTING_EVENT, event });
      expect(result.currentHoleBettingEvents).toHaveLength(1);
      expect(result.currentHoleBettingEvents[0].type).toBe('MANUAL');
      expect(result.currentHoleBettingEvents[0].timestamp).toBeDefined();
    });

    it('CLEAR_HOLE_EVENTS empties current hole events', () => {
      const state = {
        pendingOffer: null,
        currentHoleBettingEvents: [{ type: 'DOUBLE' }, { type: 'FLOAT' }],
      };
      const result = offerReducer(state, { type: OFFER_ACTIONS.CLEAR_HOLE_EVENTS });
      expect(result.currentHoleBettingEvents).toEqual([]);
    });

    it('RESET returns to initial state', () => {
      const state = {
        pendingOffer: { type: OFFER_TYPES.DOUBLE },
        currentHoleBettingEvents: [{ type: 'FLOAT' }],
      };
      const result = offerReducer(state, { type: OFFER_ACTIONS.RESET });
      expect(result).toEqual(initialOfferState());
    });

    it('handles unknown action', () => {
      const state = initialOfferState();
      expect(offerReducer(state, { type: 'UNKNOWN' })).toEqual(state);
    });
  });

  describe('useBettingOffers hook', () => {
    it('returns state and actions', () => {
      const { result } = renderHook(() => useBettingOffers());
      expect(result.current.state.pendingOffer).toBeNull();
      expect(typeof result.current.actions.createOffer).toBe('function');
    });

    it('computes hasPendingOffer correctly', () => {
      const { result } = renderHook(() => useBettingOffers());
      expect(result.current.hasPendingOffer).toBe(false);

      act(() => result.current.actions.createOffer(OFFER_TYPES.DOUBLE, 'p1', 'p2', 2));
      expect(result.current.hasPendingOffer).toBe(true);

      act(() => result.current.actions.cancelOffer());
      expect(result.current.hasPendingOffer).toBe(false);
    });

    it('computes holeEventCount correctly', () => {
      const { result } = renderHook(() => useBettingOffers());
      expect(result.current.holeEventCount).toBe(0);

      act(() => result.current.actions.addBettingEvent({ type: 'TEST' }));
      expect(result.current.holeEventCount).toBe(1);

      act(() => result.current.actions.addBettingEvent({ type: 'TEST2' }));
      expect(result.current.holeEventCount).toBe(2);
    });

    it('computes acceptedEvents correctly', () => {
      const { result } = renderHook(() => useBettingOffers());

      act(() => result.current.actions.createOffer(OFFER_TYPES.DOUBLE, 'p1', 'p2'));
      act(() => result.current.actions.acceptOffer());

      act(() => result.current.actions.createOffer(OFFER_TYPES.FLOAT, 'p2', 'p1'));
      act(() => result.current.actions.rejectOffer());

      expect(result.current.acceptedEvents).toHaveLength(1);
      expect(result.current.acceptedEvents[0].type).toBe(OFFER_TYPES.DOUBLE);
    });

    it('full offer workflow works', () => {
      const { result } = renderHook(() => useBettingOffers());

      // Create offer
      act(() => result.current.actions.createOffer(OFFER_TYPES.DOUBLE, 'p1', 'p2', 2));
      expect(result.current.hasPendingOffer).toBe(true);
      expect(result.current.state.pendingOffer.from).toBe('p1');

      // Accept it
      act(() => result.current.actions.acceptOffer());
      expect(result.current.hasPendingOffer).toBe(false);
      expect(result.current.holeEventCount).toBe(1);

      // Clear for next hole
      act(() => result.current.actions.clearHoleEvents());
      expect(result.current.holeEventCount).toBe(0);
    });

    it('reset clears everything', () => {
      const { result } = renderHook(() => useBettingOffers());

      act(() => result.current.actions.createOffer(OFFER_TYPES.OPTION, 'p1', 'p2'));
      act(() => result.current.actions.addBettingEvent({ type: 'TEST' }));
      act(() => result.current.actions.reset());

      expect(result.current.hasPendingOffer).toBe(false);
      expect(result.current.holeEventCount).toBe(0);
    });
  });
});
