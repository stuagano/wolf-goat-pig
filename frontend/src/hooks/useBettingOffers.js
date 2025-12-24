/**
 * useBettingOffers - Betting offer state management
 *
 * Manages:
 * - pendingOffer (current offer awaiting response)
 * - currentHoleBettingEvents (betting events for current hole)
 */

import { useReducer, useMemo } from 'react';

export const OFFER_ACTIONS = {
  CREATE_OFFER: 'CREATE_OFFER',
  ACCEPT_OFFER: 'ACCEPT_OFFER',
  REJECT_OFFER: 'REJECT_OFFER',
  CANCEL_OFFER: 'CANCEL_OFFER',
  ADD_BETTING_EVENT: 'ADD_BETTING_EVENT',
  CLEAR_HOLE_EVENTS: 'CLEAR_HOLE_EVENTS',
  RESET: 'RESET',
};

export const OFFER_TYPES = {
  DOUBLE: 'DOUBLE',
  FLOAT: 'FLOAT',
  OPTION: 'OPTION',
  PRESS: 'PRESS',
};

export const initialOfferState = () => ({
  pendingOffer: null,
  currentHoleBettingEvents: [],
});

export function offerReducer(state, action) {
  switch (action.type) {
    case OFFER_ACTIONS.CREATE_OFFER:
      return {
        ...state,
        pendingOffer: {
          type: action.offerType,
          from: action.from,
          to: action.to,
          wagerMultiplier: action.wagerMultiplier || 1,
          timestamp: Date.now(),
        },
      };

    case OFFER_ACTIONS.ACCEPT_OFFER:
      if (!state.pendingOffer) return state;
      return {
        ...state,
        pendingOffer: null,
        currentHoleBettingEvents: [
          ...state.currentHoleBettingEvents,
          {
            ...state.pendingOffer,
            status: 'accepted',
            acceptedAt: Date.now(),
          },
        ],
      };

    case OFFER_ACTIONS.REJECT_OFFER:
      if (!state.pendingOffer) return state;
      return {
        ...state,
        pendingOffer: null,
        currentHoleBettingEvents: [
          ...state.currentHoleBettingEvents,
          {
            ...state.pendingOffer,
            status: 'rejected',
            rejectedAt: Date.now(),
          },
        ],
      };

    case OFFER_ACTIONS.CANCEL_OFFER:
      return { ...state, pendingOffer: null };

    case OFFER_ACTIONS.ADD_BETTING_EVENT:
      return {
        ...state,
        currentHoleBettingEvents: [
          ...state.currentHoleBettingEvents,
          { ...action.event, timestamp: Date.now() },
        ],
      };

    case OFFER_ACTIONS.CLEAR_HOLE_EVENTS:
      return { ...state, currentHoleBettingEvents: [] };

    case OFFER_ACTIONS.RESET:
      return initialOfferState();

    default:
      return state;
  }
}

export function useBettingOffers() {
  const [state, dispatch] = useReducer(offerReducer, null, initialOfferState);

  const actions = useMemo(() => ({
    createOffer: (offerType, from, to, wagerMultiplier) =>
      dispatch({ type: OFFER_ACTIONS.CREATE_OFFER, offerType, from, to, wagerMultiplier }),
    acceptOffer: () => dispatch({ type: OFFER_ACTIONS.ACCEPT_OFFER }),
    rejectOffer: () => dispatch({ type: OFFER_ACTIONS.REJECT_OFFER }),
    cancelOffer: () => dispatch({ type: OFFER_ACTIONS.CANCEL_OFFER }),
    addBettingEvent: (event) => dispatch({ type: OFFER_ACTIONS.ADD_BETTING_EVENT, event }),
    clearHoleEvents: () => dispatch({ type: OFFER_ACTIONS.CLEAR_HOLE_EVENTS }),
    reset: () => dispatch({ type: OFFER_ACTIONS.RESET }),
  }), []);

  const hasPendingOffer = useMemo(() => state.pendingOffer !== null, [state.pendingOffer]);

  const holeEventCount = useMemo(() =>
    state.currentHoleBettingEvents.length,
  [state.currentHoleBettingEvents]);

  const acceptedEvents = useMemo(() =>
    state.currentHoleBettingEvents.filter(e => e.status === 'accepted'),
  [state.currentHoleBettingEvents]);

  return { state, dispatch, actions, hasPendingOffer, holeEventCount, acceptedEvents };
}

export default useBettingOffers;
