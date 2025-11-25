/**
 * useGameApi - Game API operations hook (Refactored)
 *
 * Uses useFetchAsync for consistent loading/error handling.
 * All game-related API operations in one place.
 */

import { useCallback } from 'react';
import useFetchAsync from './useFetchAsync';

/**
 * Custom hook for game-related API calls
 * Uses centralized fetch handling via useFetchAsync
 */
export const useGameApi = () => {
  const { loading, error, clearError, get, post } = useFetchAsync();

  // Fetch current game state
  const fetchGameState = useCallback(async () => {
    return get('/game/state', 'Fetch game state');
  }, [get]);

  // Start a new game
  const startGame = useCallback(async (gameConfig = {}) => {
    return post('/game/start', gameConfig, 'Start game');
  }, [post]);

  // Perform a game action
  const performGameAction = useCallback(async (action, payload = {}) => {
    return post('/game/action', { action, ...payload }, 'Perform game action');
  }, [post]);

  // Fetch betting tips
  const fetchBettingTips = useCallback(async () => {
    const data = await get('/game/tips', 'Fetch betting tips');
    return data?.tips || [];
  }, [get]);

  // Fetch player strokes
  const fetchPlayerStrokes = useCallback(async () => {
    return get('/game/player_strokes', 'Fetch player strokes');
  }, [get]);

  // Fetch game rules
  const fetchRules = useCallback(async () => {
    return get('/rules', 'Fetch rules');
  }, [get]);

  return {
    loading,
    error,
    clearError,
    fetchGameState,
    startGame,
    performGameAction,
    fetchBettingTips,
    fetchPlayerStrokes,
    fetchRules
  };
};

export default useGameApi;
