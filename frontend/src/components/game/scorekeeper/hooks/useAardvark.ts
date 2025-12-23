// =============================================================================
// useAardvark Hook - Aardvark Mechanics
// Manages 5-man (real aardvark) and 4-man (invisible aardvark) game modes
// =============================================================================

import { useState, useCallback, useMemo } from 'react';
import {
  AardvarkState,
  AardvarkMode,
  UseAardvarkReturn,
  Player,
} from '../types';

// =============================================================================
// Aardvark Mode Determination
// =============================================================================

function determineAardvarkMode(playerCount: number): AardvarkMode {
  switch (playerCount) {
    case 5:
      return 'real'; // Real 5th player sits out each hole
    case 4:
      return 'invisible'; // Virtual aardvark score
    default:
      return 'none';
  }
}

function calculateInvisibleAardvarkHandicap(players: Player[]): number {
  // Invisible aardvark handicap is average of all players' handicaps
  if (players.length === 0) return 0;
  const totalHandicap = players.reduce((sum, p) => sum + p.handicap, 0);
  return Math.round(totalHandicap / players.length);
}

// =============================================================================
// Initial State Factory
// =============================================================================

function createInitialAardvarkState(
  players: Player[],
  tunkarriEnabled: boolean = false
): AardvarkState {
  const mode = determineAardvarkMode(players.length);

  // For 5-man: create rotation order (typically by tee order or handicap)
  const aardvarkRotation = mode === 'real'
    ? players.slice().sort((a, b) => a.teeOrder - b.teeOrder).map(p => p.id)
    : [];

  return {
    mode,
    aardvarkPlayerId: mode === 'real' ? aardvarkRotation[0] : null,
    aardvarkRotation,
    aardvarkIndex: 0,
    invisibleAardvarkHandicap: mode === 'invisible'
      ? calculateInvisibleAardvarkHandicap(players)
      : 0,
    invisibleAardvarkScore: null,
    tunkarriActive: tunkarriEnabled,
  };
}

// =============================================================================
// Hook Implementation
// =============================================================================

interface UseAardvarkOptions {
  players: Player[];
  tunkarriEnabled?: boolean;
}

export function useAardvark({
  players,
  tunkarriEnabled = false,
}: UseAardvarkOptions): UseAardvarkReturn {
  const [aardvark, setAardvark] = useState<AardvarkState>(() =>
    createInitialAardvarkState(players, tunkarriEnabled)
  );

  // Recalculate when players change
  useMemo(() => {
    const newMode = determineAardvarkMode(players.length);
    if (newMode !== aardvark.mode) {
      setAardvark(createInitialAardvarkState(players, tunkarriEnabled));
    }
  }, [players.length, tunkarriEnabled]);

  const setInvisibleAardvarkScore = useCallback((score: number) => {
    if (aardvark.mode !== 'invisible') return;

    setAardvark(prev => ({
      ...prev,
      invisibleAardvarkScore: score,
    }));
  }, [aardvark.mode]);

  const getCurrentAardvark = useCallback((): string | null => {
    if (aardvark.mode !== 'real') return null;
    return aardvark.aardvarkPlayerId;
  }, [aardvark.mode, aardvark.aardvarkPlayerId]);

  const advanceAardvark = useCallback(() => {
    if (aardvark.mode !== 'real') return;

    setAardvark(prev => {
      const nextIndex = (prev.aardvarkIndex + 1) % prev.aardvarkRotation.length;
      return {
        ...prev,
        aardvarkIndex: nextIndex,
        aardvarkPlayerId: prev.aardvarkRotation[nextIndex],
      };
    });
  }, [aardvark.mode]);

  const isPlayerAardvark = useCallback((playerId: string): boolean => {
    if (aardvark.mode !== 'real') return false;
    return aardvark.aardvarkPlayerId === playerId;
  }, [aardvark.mode, aardvark.aardvarkPlayerId]);

  // Get active players (excludes aardvark in 5-man mode)
  // Reserved for future use in team formation validation
  const _activePlayers = useMemo((): Player[] => {
    if (aardvark.mode !== 'real' || !aardvark.aardvarkPlayerId) {
      return players;
    }
    return players.filter(p => p.id !== aardvark.aardvarkPlayerId);
  }, [aardvark.mode, aardvark.aardvarkPlayerId, players]);

  // Suppress unused warning - reserved for team formation
  void _activePlayers;

  return {
    aardvark,
    setInvisibleAardvarkScore,
    getCurrentAardvark,
    advanceAardvark,
    isPlayerAardvark,
  };
}

export default useAardvark;

// =============================================================================
// Utility Functions (exported for testing)
// =============================================================================

export const aardvarkUtils = {
  determineAardvarkMode,
  calculateInvisibleAardvarkHandicap,
  createInitialAardvarkState,
};
