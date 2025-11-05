// frontend/src/hooks/useBettingState.js
import { useState, useCallback } from 'react';
import { BettingEventTypes, createBettingEvent } from '../constants/bettingEvents';

const useBettingState = (gameId, holeNumber) => {
  const [state, setState] = useState({
    holeNumber,
    currentMultiplier: 1,
    baseAmount: 1.00,
    currentBet: 1.00,
    teams: [],
    pendingAction: null,
    presses: []
  });

  const [eventHistory, setEventHistory] = useState({
    currentHole: [],
    lastHole: [],
    gameHistory: []
  });

  const addEvent = useCallback((eventType, actor, data) => {
    const event = createBettingEvent({
      gameId,
      holeNumber,
      eventType,
      actor,
      data
    });

    setEventHistory(prev => ({
      ...prev,
      currentHole: [...prev.currentHole, event],
      gameHistory: [...prev.gameHistory, event]
    }));

    return event;
  }, [gameId, holeNumber]);

  const offerDouble = useCallback((playerId, proposedMultiplier) => {
    addEvent(BettingEventTypes.DOUBLE_OFFERED, playerId, {
      currentMultiplier: state.currentMultiplier,
      proposedMultiplier
    });

    setState(prev => ({
      ...prev,
      pendingAction: {
        type: 'DOUBLE_OFFERED',
        by: playerId,
        proposedMultiplier
      }
    }));
  }, [addEvent, state.currentMultiplier]);

  const acceptDouble = useCallback((playerId) => {
    if (!state.pendingAction || state.pendingAction.type !== 'DOUBLE_OFFERED') return;

    const newMultiplier = state.pendingAction.proposedMultiplier;

    addEvent(BettingEventTypes.DOUBLE_ACCEPTED, playerId, {
      previousMultiplier: state.currentMultiplier,
      newMultiplier
    });

    setState(prev => ({
      ...prev,
      currentMultiplier: newMultiplier,
      currentBet: prev.baseAmount * newMultiplier,
      pendingAction: null
    }));
  }, [addEvent, state.pendingAction, state.currentMultiplier]);

  const declineDouble = useCallback((playerId) => {
    if (!state.pendingAction || state.pendingAction.type !== 'DOUBLE_OFFERED') return;

    addEvent(BettingEventTypes.DOUBLE_DECLINED, playerId, {
      declinedMultiplier: state.pendingAction.proposedMultiplier
    });

    setState(prev => ({
      ...prev,
      pendingAction: null
    }));
  }, [addEvent, state.pendingAction]);

  return {
    state,
    eventHistory,
    actions: {
      offerDouble,
      acceptDouble,
      declineDouble
    }
  };
};

export default useBettingState;
