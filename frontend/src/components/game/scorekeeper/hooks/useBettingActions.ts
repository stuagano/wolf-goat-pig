// =============================================================================
// useBettingActions Hook - Betting Mechanics
// Manages Float, Option, Duncan, Vinnies invocations and offer/accept flow
// =============================================================================

import { useState, useCallback } from 'react';
import {
  BettingState,
  PlayerBettingUsage,
  BetOffer,
  BetType,
  UseBettingActionsReturn,
} from '../types';

// =============================================================================
// Initial State Factory
// =============================================================================

function createInitialPlayerUsage(playerId: string): PlayerBettingUsage {
  return {
    playerId,
    floatUsed: false,
    floatHole: null,
    optionUsed: false,
    optionHole: null,
    duncanUsed: false,
    duncanHole: null,
  };
}

function createInitialBettingState(
  playerIds: string[],
  baseWager: number
): BettingState {
  const playerUsage: Record<string, PlayerBettingUsage> = {};
  playerIds.forEach(id => {
    playerUsage[id] = createInitialPlayerUsage(id);
  });

  return {
    playerUsage,
    currentWager: baseWager,
    baseWager,
    wagerMultiplier: 1,
    pendingOffers: [],
    duncanActive: false,
    duncanPlayerId: null,
    vinniesActive: false,
    vinniesMultiplier: 1,
  };
}

// =============================================================================
// Hook Implementation
// =============================================================================

interface UseBettingActionsOptions {
  playerIds: string[];
  baseWager: number;
  currentHoleNumber: number;
  // Solo requirement: player must have at least one solo between holes 13-16
  soloRequirementStart?: number;
  soloRequirementEnd?: number;
}

export function useBettingActions({
  playerIds,
  baseWager,
  currentHoleNumber,
  // Reserved for future solo requirement validation (holes 13-16)
  soloRequirementStart: _soloRequirementStart = 13,
  soloRequirementEnd: _soloRequirementEnd = 16,
}: UseBettingActionsOptions): UseBettingActionsReturn {
  // Suppress unused warnings - reserved for future solo requirement feature
  void _soloRequirementStart;
  void _soloRequirementEnd;
  const [betting, setBetting] = useState<BettingState>(() =>
    createInitialBettingState(playerIds, baseWager)
  );

  // =============================================================================
  // Query Functions
  // =============================================================================

  const canInvokeFloat = useCallback((playerId: string): boolean => {
    const usage = betting.playerUsage[playerId];
    if (!usage) return false;
    // Float can only be used once per round
    return !usage.floatUsed;
  }, [betting.playerUsage]);

  const canInvokeOption = useCallback((playerId: string): boolean => {
    const usage = betting.playerUsage[playerId];
    if (!usage) return false;
    // Option can only be used once per round
    return !usage.optionUsed;
  }, [betting.playerUsage]);

  const canInvokeDuncan = useCallback((playerId: string): boolean => {
    const usage = betting.playerUsage[playerId];
    if (!usage) return false;
    // Duncan can only be used once per round
    // Duncan is typically available in solo mode (3-for-2)
    return !usage.duncanUsed;
  }, [betting.playerUsage]);

  const getPlayerUsage = useCallback((playerId: string): PlayerBettingUsage => {
    return betting.playerUsage[playerId] || createInitialPlayerUsage(playerId);
  }, [betting.playerUsage]);

  // =============================================================================
  // Invoke Actions
  // =============================================================================

  const invokeFloat = useCallback((playerId: string) => {
    if (!canInvokeFloat(playerId)) return;

    setBetting(prev => ({
      ...prev,
      playerUsage: {
        ...prev.playerUsage,
        [playerId]: {
          ...prev.playerUsage[playerId],
          floatUsed: true,
          floatHole: currentHoleNumber,
        },
      },
      // Float doubles the wager
      currentWager: prev.currentWager * 2,
      wagerMultiplier: prev.wagerMultiplier * 2,
    }));
  }, [canInvokeFloat, currentHoleNumber]);

  const invokeOption = useCallback((playerId: string) => {
    if (!canInvokeOption(playerId)) return;

    setBetting(prev => ({
      ...prev,
      playerUsage: {
        ...prev.playerUsage,
        [playerId]: {
          ...prev.playerUsage[playerId],
          optionUsed: true,
          optionHole: currentHoleNumber,
        },
      },
      // Option typically doubles the wager for the invoker
      currentWager: prev.currentWager * 2,
      wagerMultiplier: prev.wagerMultiplier * 2,
    }));
  }, [canInvokeOption, currentHoleNumber]);

  const invokeDuncan = useCallback((playerId: string) => {
    if (!canInvokeDuncan(playerId)) return;

    setBetting(prev => ({
      ...prev,
      playerUsage: {
        ...prev.playerUsage,
        [playerId]: {
          ...prev.playerUsage[playerId],
          duncanUsed: true,
          duncanHole: currentHoleNumber,
        },
      },
      duncanActive: true,
      duncanPlayerId: playerId,
      // Duncan is 3-for-2 solo (special wager calculation)
    }));
  }, [canInvokeDuncan, currentHoleNumber]);

  const invokeVinnies = useCallback(() => {
    setBetting(prev => ({
      ...prev,
      vinniesActive: true,
      // Vinnies multiplier based on score differential
      // (actual multiplier calculated during scoring)
    }));
  }, []);

  // =============================================================================
  // Offer/Accept Flow
  // =============================================================================

  const offerBet = useCallback((type: BetType, toPlayerIds: string[]) => {
    const newOffer: BetOffer = {
      id: `offer-${Date.now()}`,
      type,
      offeredBy: '', // Will be set by caller
      offeredTo: toPlayerIds,
      status: 'pending',
      timestamp: new Date().toISOString(),
    };

    setBetting(prev => ({
      ...prev,
      pendingOffers: [...prev.pendingOffers, newOffer],
    }));
  }, []);

  const acceptOffer = useCallback((offerId: string) => {
    setBetting(prev => ({
      ...prev,
      pendingOffers: prev.pendingOffers.map(offer =>
        offer.id === offerId
          ? { ...offer, status: 'accepted' as const }
          : offer
      ),
    }));
  }, []);

  const declineOffer = useCallback((offerId: string) => {
    setBetting(prev => ({
      ...prev,
      pendingOffers: prev.pendingOffers.map(offer =>
        offer.id === offerId
          ? { ...offer, status: 'declined' as const }
          : offer
      ),
    }));
  }, []);

  // =============================================================================
  // Reset for new hole (reserved for future use)
  // =============================================================================

  const _resetHoleState = useCallback(() => {
    setBetting(prev => ({
      ...prev,
      currentWager: prev.baseWager,
      wagerMultiplier: 1,
      pendingOffers: [],
      duncanActive: false,
      duncanPlayerId: null,
      vinniesActive: false,
      vinniesMultiplier: 1,
    }));
  }, []);

  // Suppress unused warning - reserved for hole transition
  void _resetHoleState;

  return {
    betting,
    invokeFloat,
    invokeOption,
    invokeDuncan,
    invokeVinnies,
    offerBet,
    acceptOffer,
    declineOffer,
    canInvokeFloat,
    canInvokeOption,
    canInvokeDuncan,
    getPlayerUsage,
  };
}

export default useBettingActions;

// =============================================================================
// Utility Functions (exported for testing)
// =============================================================================

export const bettingUtils = {
  createInitialPlayerUsage,
  createInitialBettingState,
};
