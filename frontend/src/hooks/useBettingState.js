// frontend/src/hooks/useBettingState.js
import { useState, useCallback, useEffect } from 'react';
import { BettingEventTypes, createBettingEvent } from '../constants/bettingEvents';
import { syncBettingEvents } from '../api/bettingApi';

/**
 * Custom hook for managing betting state and actions in a golf game hole.
 *
 * @param {string} gameId - Unique identifier for the game
 * @param {number} holeNumber - Current hole number (1-18)
 * @returns {Object} Betting state, event history, and action handlers
 * @returns {Object} return.state - Current betting state
 * @returns {Object} return.eventHistory - History of betting events
 * @returns {Object} return.actions - Action handlers for betting operations
 */
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

  // Track unsynced events and sync status
  const [unsyncedEvents, setUnsyncedEvents] = useState([]);
  const [syncStatus, setSyncStatus] = useState('synced'); // 'synced' | 'pending' | 'error'

  // Auto-sync every 5 events
  useEffect(() => {
    if (unsyncedEvents.length >= 5) {
      const performSync = async () => {
        setSyncStatus('pending');
        try {
          await syncBettingEvents(gameId, holeNumber, unsyncedEvents);
          setUnsyncedEvents([]);
          setSyncStatus('synced');
        } catch (error) {
          console.error('Sync failed:', error);
          setSyncStatus('error');
        }
      };
      performSync();
    }
  }, [unsyncedEvents, gameId, holeNumber]);

  /**
   * Offers a double bet to increase the multiplier.
   *
   * @param {string} playerId - ID of the player offering the double
   * @param {number} proposedMultiplier - The new multiplier being proposed
   * @throws {Error} If validation fails
   */
  const offerDouble = useCallback((playerId, proposedMultiplier) => {
    // Input validation
    if (!playerId || typeof playerId !== 'string') {
      throw new Error('playerId must be a non-empty string');
    }
    if (typeof proposedMultiplier !== 'number' || proposedMultiplier <= 0) {
      throw new Error('proposedMultiplier must be a positive number');
    }

    setState(prev => {
      // Create event with current state values from prev
      const event = createBettingEvent({
        gameId,
        holeNumber,
        eventType: BettingEventTypes.DOUBLE_OFFERED,
        actor: playerId,
        data: {
          currentMultiplier: prev.currentMultiplier,
          proposedMultiplier
        }
      });

      // Update event history
      setEventHistory(prevHistory => ({
        ...prevHistory,
        currentHole: [...prevHistory.currentHole, event],
        gameHistory: [...prevHistory.gameHistory, event]
      }));

      // Track unsynced event
      setUnsyncedEvents(prevUnsynced => [...prevUnsynced, event]);

      return {
        ...prev,
        pendingAction: {
          type: 'DOUBLE_OFFERED',
          by: playerId,
          proposedMultiplier
        }
      };
    });
  }, [gameId, holeNumber]);

  /**
   * Accepts a pending double bet offer.
   *
   * @param {string} playerId - ID of the player accepting the double
   * @throws {Error} If validation fails
   */
  const acceptDouble = useCallback((playerId) => {
    // Input validation
    if (!playerId || typeof playerId !== 'string') {
      throw new Error('playerId must be a non-empty string');
    }

    setState(prev => {
      // Validate pending action exists
      if (!prev.pendingAction || prev.pendingAction.type !== 'DOUBLE_OFFERED') {
        return prev; // No-op if no pending double offer
      }

      const newMultiplier = prev.pendingAction.proposedMultiplier;

      // Create event with current state values from prev
      const event = createBettingEvent({
        gameId,
        holeNumber,
        eventType: BettingEventTypes.DOUBLE_ACCEPTED,
        actor: playerId,
        data: {
          previousMultiplier: prev.currentMultiplier,
          newMultiplier
        }
      });

      // Update event history
      setEventHistory(prevHistory => ({
        ...prevHistory,
        currentHole: [...prevHistory.currentHole, event],
        gameHistory: [...prevHistory.gameHistory, event]
      }));

      // Track unsynced event
      setUnsyncedEvents(prevUnsynced => [...prevUnsynced, event]);

      return {
        ...prev,
        currentMultiplier: newMultiplier,
        currentBet: prev.baseAmount * newMultiplier,
        pendingAction: null
      };
    });
  }, [gameId, holeNumber]);

  /**
   * Declines a pending double bet offer.
   *
   * @param {string} playerId - ID of the player declining the double
   * @throws {Error} If validation fails
   */
  const declineDouble = useCallback((playerId) => {
    // Input validation
    if (!playerId || typeof playerId !== 'string') {
      throw new Error('playerId must be a non-empty string');
    }

    setState(prev => {
      // Validate pending action exists
      if (!prev.pendingAction || prev.pendingAction.type !== 'DOUBLE_OFFERED') {
        return prev; // No-op if no pending double offer
      }

      // Create event with current state values from prev
      const event = createBettingEvent({
        gameId,
        holeNumber,
        eventType: BettingEventTypes.DOUBLE_DECLINED,
        actor: playerId,
        data: {
          declinedMultiplier: prev.pendingAction.proposedMultiplier
        }
      });

      // Update event history
      setEventHistory(prevHistory => ({
        ...prevHistory,
        currentHole: [...prevHistory.currentHole, event],
        gameHistory: [...prevHistory.gameHistory, event]
      }));

      // Track unsynced event
      setUnsyncedEvents(prevUnsynced => [...prevUnsynced, event]);

      return {
        ...prev,
        pendingAction: null
      };
    });
  }, [gameId, holeNumber]);

  return {
    state,
    eventHistory,
    actions: {
      offerDouble,
      acceptDouble,
      declineDouble
    },
    syncStatus
  };
};

export default useBettingState;
