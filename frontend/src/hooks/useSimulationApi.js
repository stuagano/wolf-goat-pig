import { useState, useCallback } from 'react';

const API_URL = process.env.REACT_APP_API_URL || '';

/**
 * Custom hook for simulation-related API calls
 */
export const useSimulationApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Setup simulation game
  const setupSimulation = useCallback(async (config) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/simulation/setup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      if (!response.ok) {
        throw new Error(`Simulation setup failed: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Play next shot in simulation
  const playNextShot = useCallback(async (decision = {}) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/simulation/play-next-shot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(decision)
      });
      if (!response.ok) {
        throw new Error(`Play shot failed: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Make simulation decision
  const makeSimulationDecision = useCallback(async (decision) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/simulation/play-hole`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(decision)
      });
      if (!response.ok) {
        throw new Error(`Decision failed: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch available personalities
  const fetchPersonalities = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/simulation/available-personalities`);
      if (!response.ok) {
        throw new Error(`Failed to fetch personalities: ${response.status}`);
      }
      const data = await response.json();
      return data.personalities || [];
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch suggested opponents
  const fetchSuggestedOpponents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/simulation/suggested-opponents`);
      if (!response.ok) {
        throw new Error(`Failed to fetch opponents: ${response.status}`);
      }
      const data = await response.json();
      return data.opponents || [];
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch shot probabilities
  const fetchShotProbabilities = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/simulation/shot-probabilities`);
      if (!response.ok) {
        throw new Error(`Failed to fetch probabilities: ${response.status}`);
      }
      const data = await response.json();
      return data.probabilities || {};
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Make betting decision
  const makeBettingDecision = useCallback(async (decision) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/simulation/betting-decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(decision)
      });
      if (!response.ok) {
        throw new Error(`Betting decision failed: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

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