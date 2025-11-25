/**
 * useSimulationApi - Simulation API operations hook (Refactored)
 *
 * Uses useFetchAsync for consistent loading/error handling.
 * All simulation-related API operations in one place.
 */

import { useCallback } from 'react';
import useFetchAsync from './useFetchAsync';

/**
 * Custom hook for simulation-related API calls
 * Uses centralized fetch handling via useFetchAsync
 */
export const useSimulationApi = () => {
  const { loading, error, clearError, get, post } = useFetchAsync();

  // Setup simulation game
  const setupSimulation = useCallback(async (config) => {
    return post('/simulation/setup', config, 'Setup simulation');
  }, [post]);

  // Play next shot in simulation
  const playNextShot = useCallback(async (decision = {}) => {
    return post('/simulation/play-next-shot', decision, 'Play shot');
  }, [post]);

  // Make simulation decision
  const makeSimulationDecision = useCallback(async (decision) => {
    return post('/simulation/play-hole', decision, 'Make decision');
  }, [post]);

  // Fetch available personalities
  const fetchPersonalities = useCallback(async () => {
    const data = await get('/simulation/available-personalities', 'Fetch personalities');
    return data?.personalities || [];
  }, [get]);

  // Fetch suggested opponents
  const fetchSuggestedOpponents = useCallback(async () => {
    const data = await get('/simulation/suggested-opponents', 'Fetch opponents');
    return data?.opponents || [];
  }, [get]);

  // Fetch shot probabilities
  const fetchShotProbabilities = useCallback(async () => {
    const data = await get('/simulation/shot-probabilities', 'Fetch probabilities');
    return data?.probabilities || {};
  }, [get]);

  // Make betting decision
  const makeBettingDecision = useCallback(async (decision) => {
    return post('/simulation/betting-decision', decision, 'Make betting decision');
  }, [post]);

  return {
    loading,
    error,
    clearError,
    setupSimulation,
    playNextShot,
    makeSimulationDecision,
    fetchPersonalities,
    fetchSuggestedOpponents,
    fetchShotProbabilities,
    makeBettingDecision
  };
};

export default useSimulationApi;
