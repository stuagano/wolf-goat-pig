/**
 * Custom hook for managing betting state and actions
 * Extracted from SimpleScorekeeper to reduce complexity
 */
import { useState, useCallback } from 'react';

/**
 * useBettingState - Manages betting history and offer/accept flows
 * 
 * @param {Object} options
 * @param {number} options.currentHole - Current hole number
 * @param {number} options.currentWager - Current wager amount
 * @param {Function} options.setCurrentWager - Function to update wager
 * @param {Array} options.players - Array of player objects
 * @returns {Object} Betting state and actions
 */
export function useBettingState({ currentHole, currentWager, setCurrentWager, players }) {
  // Global betting history (all holes)
  const [bettingHistory, setBettingHistory] = useState([]);
  
  // Current hole betting events
  const [currentHoleBettingEvents, setCurrentHoleBettingEvents] = useState([]);
  
  // Pending offer awaiting response
  const [pendingOffer, setPendingOffer] = useState(null);
  
  // UI state
  const [showBettingHistory, setShowBettingHistory] = useState(false);
  const [historyTab, setHistoryTab] = useState('current'); // 'current', 'last', 'game'

  /**
   * Get player name by ID
   */
  const getPlayerName = useCallback((playerId) => {
    return players.find(p => p.id === playerId)?.name || 'Unknown';
  }, [players]);

  /**
   * Log a betting action to history
   */
  const logBettingAction = useCallback((actionType, details = {}) => {
    const playerName = details.playerId
      ? getPlayerName(details.playerId)
      : null;

    const newEvent = {
      eventId: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      hole: currentHole,
      eventType: actionType,
      actor: playerName || details.actor || 'System',
      timestamp: new Date().toISOString(),
      details: {
        ...details,
        wager: currentWager
      }
    };

    setBettingHistory(prev => [...prev, newEvent]);
    return newEvent;
  }, [currentHole, currentWager, getPlayerName]);

  /**
   * Add a betting event to current hole's events
   */
  const addBettingEvent = useCallback((event) => {
    const fullEvent = {
      ...event,
      hole: currentHole,
      timestamp: event.timestamp || new Date().toISOString(),
      actor: event.offered_by || event.response_by || event.actor
    };
    setCurrentHoleBettingEvents(prev => [...prev, fullEvent]);
    // Also log to global betting history
    logBettingAction(event.eventType, fullEvent);
    return fullEvent;
  }, [currentHole, logBettingAction]);

  /**
   * Create a betting offer (Double, Float, etc.)
   */
  const createOffer = useCallback((offerType, offeredBy) => {
    if (pendingOffer) {
      console.warn('Cannot create offer while another is pending');
      return null;
    }

    const offer = {
      offer_id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      offer_type: offerType,
      offered_by: offeredBy,
      wager_before: currentWager,
      wager_after: currentWager * 2,
      timestamp: new Date().toISOString(),
      status: 'pending'
    };
    
    setPendingOffer(offer);
    addBettingEvent({
      eventType: `${offerType.toUpperCase()}_OFFERED`,
      offered_by: offeredBy,
      wager_before: offer.wager_before,
      wager_after: offer.wager_after
    });
    
    return offer;
  }, [pendingOffer, currentWager, addBettingEvent]);

  /**
   * Respond to a pending betting offer
   */
  const respondToOffer = useCallback((response, respondedBy) => {
    if (!pendingOffer) {
      console.warn('No pending offer to respond to');
      return;
    }

    if (response === 'accept') {
      setCurrentWager(pendingOffer.wager_after);
      addBettingEvent({
        eventType: `${pendingOffer.offer_type.toUpperCase()}_ACCEPTED`,
        response_by: respondedBy,
        wager_before: pendingOffer.wager_before,
        wager_after: pendingOffer.wager_after
      });
    } else {
      addBettingEvent({
        eventType: `${pendingOffer.offer_type.toUpperCase()}_DECLINED`,
        response_by: respondedBy,
        wager_before: pendingOffer.wager_before,
        wager_after: pendingOffer.wager_before // Stays the same
      });
    }
    
    setPendingOffer(null);
  }, [pendingOffer, setCurrentWager, addBettingEvent]);

  /**
   * Cancel a pending offer (by the offerer)
   */
  const cancelOffer = useCallback(() => {
    if (!pendingOffer) return;
    
    addBettingEvent({
      eventType: `${pendingOffer.offer_type.toUpperCase()}_CANCELLED`,
      actor: pendingOffer.offered_by,
      wager_before: pendingOffer.wager_before,
      wager_after: pendingOffer.wager_before
    });
    
    setPendingOffer(null);
  }, [pendingOffer, addBettingEvent]);

  /**
   * Reset betting state for a new hole
   */
  const resetForNewHole = useCallback(() => {
    setPendingOffer(null);
    setCurrentHoleBettingEvents([]);
  }, []);

  /**
   * Load betting events for editing a hole
   */
  const loadEventsForEdit = useCallback((events) => {
    setCurrentHoleBettingEvents(events || []);
    setPendingOffer(null);
  }, []);

  /**
   * Get events for a specific hole from history
   */
  const getEventsForHole = useCallback((holeNumber) => {
    return bettingHistory.filter(event => event.hole === holeNumber);
  }, [bettingHistory]);

  /**
   * Get the last hole's events
   */
  const getLastHoleEvents = useCallback(() => {
    if (currentHole <= 1) return [];
    return getEventsForHole(currentHole - 1);
  }, [currentHole, getEventsForHole]);

  return {
    // State
    bettingHistory,
    currentHoleBettingEvents,
    pendingOffer,
    showBettingHistory,
    historyTab,
    
    // Setters
    setBettingHistory,
    setCurrentHoleBettingEvents,
    setPendingOffer,
    setShowBettingHistory,
    setHistoryTab,
    
    // Actions
    logBettingAction,
    addBettingEvent,
    createOffer,
    respondToOffer,
    cancelOffer,
    resetForNewHole,
    loadEventsForEdit,
    getEventsForHole,
    getLastHoleEvents,
    getPlayerName,
  };
}

export default useBettingState;
