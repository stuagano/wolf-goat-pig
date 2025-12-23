// =============================================================================
// useRotationWager Hook - Rotation & Wager API Integration
// Fetches rotation order and wager info from the backend API
// =============================================================================

import { useState, useCallback } from 'react';
import {
  RotationState,
  RotationApiResponse,
  WagerApiResponse,
  UseRotationWagerReturn,
  RotationPlayer,
} from '../types';

// =============================================================================
// API Functions
// =============================================================================

async function fetchRotationFromApi(
  gameId: string,
  holeNumber: number
): Promise<RotationApiResponse> {
  const response = await fetch(`/api/games/${gameId}/next-rotation?hole=${holeNumber}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch rotation: ${response.statusText}`);
  }
  return response.json();
}

async function fetchWagerFromApi(
  gameId: string,
  holeNumber: number
): Promise<WagerApiResponse> {
  const response = await fetch(`/api/games/${gameId}/next-hole-wager?hole=${holeNumber}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch wager: ${response.statusText}`);
  }
  return response.json();
}

// =============================================================================
// Hoepfinger Phase Calculation
// =============================================================================

function getHoepfingerStartHole(playerCount: number): number {
  // Hoepfinger phase starts:
  // 4-man: hole 17 (2 holes left)
  // 5-man: hole 16 (3 holes left)
  // 6-man: hole 13 (6 holes left)
  switch (playerCount) {
    case 4: return 17;
    case 5: return 16;
    case 6: return 13;
    default: return 17;
  }
}

function isHoepfingerPhase(holeNumber: number, playerCount: number): boolean {
  const startHole = getHoepfingerStartHole(playerCount);
  return holeNumber >= startHole;
}

// =============================================================================
// Hook Implementation
// =============================================================================

interface UseRotationWagerOptions {
  playerCount: number;
}

export function useRotationWager({
  playerCount,
}: UseRotationWagerOptions): UseRotationWagerReturn {
  const [rotation, setRotation] = useState<RotationState>({
    holeNumber: 1,
    rotationOrder: [],
    captainIndex: 0,
    isHoepfingerPhase: false,
    hoepfingerStartHole: getHoepfingerStartHole(playerCount),
    goatPlayerIndex: null,
  });

  const [wager, setWager] = useState<WagerApiResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRotation = useCallback(async (gameId: string, holeNumber: number) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetchRotationFromApi(gameId, holeNumber);

      // Transform API response to RotationState
      const rotationOrder: RotationPlayer[] = response.rotation.map((p, index) => ({
        playerId: p.playerId,
        name: p.name,
        teeOrder: p.teeOrder,
        strokesOnHole: 0, // Will be filled by stroke allocation hook
        isHoepfinger: index === response.captainIndex, // Captain is "Wolf"
      }));

      const hoepfingerPhase = isHoepfingerPhase(holeNumber, playerCount);

      setRotation({
        holeNumber,
        rotationOrder,
        captainIndex: response.captainIndex,
        isHoepfingerPhase: hoepfingerPhase,
        hoepfingerStartHole: getHoepfingerStartHole(playerCount),
        // In Hoepfinger phase, last player in rotation is "Goat"
        goatPlayerIndex: hoepfingerPhase ? rotationOrder.length - 1 : null,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch rotation');
    } finally {
      setIsLoading(false);
    }
  }, [playerCount]);

  const fetchWager = useCallback(async (gameId: string, holeNumber: number) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetchWagerFromApi(gameId, holeNumber);
      setWager(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch wager');
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    rotation,
    wager,
    isLoading,
    error,
    fetchRotation,
    fetchWager,
  };
}

export default useRotationWager;

// =============================================================================
// Utility Functions (exported for testing)
// =============================================================================

export const rotationUtils = {
  getHoepfingerStartHole,
  isHoepfingerPhase,
};
