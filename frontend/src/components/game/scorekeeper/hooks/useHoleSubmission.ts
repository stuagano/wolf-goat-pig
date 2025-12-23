// =============================================================================
// useHoleSubmission Hook - Hole Submission & Game Completion
// Handles API calls for submitting holes and completing games
// =============================================================================

import { useState, useCallback } from 'react';
import {
  SubmitHolePayload,
  SubmitHoleResponse,
  Achievement,
  UseHoleSubmissionReturn,
} from '../types';

// =============================================================================
// API Functions
// =============================================================================

async function submitHoleToApi(payload: SubmitHolePayload): Promise<SubmitHoleResponse> {
  const response = await fetch(`/api/games/${payload.gameId}/quarters-only`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      holeNumber: payload.holeNumber,
      teams: payload.teams,
      grossScores: payload.grossScores,
      quarters: payload.quarters,
      wager: payload.wager,
      bets: payload.bets,
      notes: payload.notes,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || `Failed to submit hole: ${response.statusText}`);
  }

  return response.json();
}

async function checkAchievementsFromApi(playerId: string): Promise<Achievement[]> {
  const response = await fetch(`/api/badges/admin/check-achievements/${playerId}`, {
    method: 'POST',
  });

  if (!response.ok) {
    // Non-fatal: achievements check failure shouldn't block game flow
    console.warn('Failed to check achievements:', response.statusText);
    return [];
  }

  const data = await response.json();
  return data.newAchievements || [];
}

async function completeGameFromApi(gameId: string): Promise<void> {
  const response = await fetch(`/api/games/${gameId}/complete`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || `Failed to complete game: ${response.statusText}`);
  }
}

// =============================================================================
// Hook Implementation
// =============================================================================

export function useHoleSubmission(): UseHoleSubmissionReturn {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitHole = useCallback(async (payload: SubmitHolePayload): Promise<SubmitHoleResponse> => {
    setIsSubmitting(true);
    setError(null);

    try {
      const response = await submitHoleToApi(payload);

      // Check achievements for all players after submission
      const playerIds = Object.keys(payload.grossScores);
      const achievementPromises = playerIds.map(playerId =>
        checkAchievementsFromApi(playerId).catch(() => [])
      );

      const achievementResults = await Promise.all(achievementPromises);
      const allAchievements = achievementResults.flat();

      return {
        ...response,
        achievements: allAchievements,
      };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to submit hole';
      setError(errorMessage);
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  const checkAchievements = useCallback(async (playerId: string): Promise<Achievement[]> => {
    try {
      return await checkAchievementsFromApi(playerId);
    } catch (err) {
      console.warn('Achievement check failed:', err);
      return [];
    }
  }, []);

  const completeGame = useCallback(async (gameId: string): Promise<void> => {
    setIsSubmitting(true);
    setError(null);

    try {
      await completeGameFromApi(gameId);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to complete game';
      setError(errorMessage);
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  return {
    isSubmitting,
    error,
    submitHole,
    checkAchievements,
    completeGame,
  };
}

export default useHoleSubmission;

// =============================================================================
// Utility Functions (exported for testing)
// =============================================================================

export const submissionUtils = {
  submitHoleToApi,
  checkAchievementsFromApi,
  completeGameFromApi,
};
