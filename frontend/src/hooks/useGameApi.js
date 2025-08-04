import { useState, useCallback } from 'react';

const API_URL = process.env.REACT_APP_API_URL || '';

/**
 * Custom hook for game-related API calls
 */
export const useGameApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Fetch current game state
  const fetchGameState = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/game/state`);
      if (!response.ok) {
        throw new Error(`Failed to fetch game state: ${response.status}`);
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

  // Start a new game
  const startGame = useCallback(async (gameConfig = {}) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/game/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(gameConfig)
      });
      if (!response.ok) {
        throw new Error(`Failed to start game: ${response.status}`);
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

  // Perform a game action
  const performGameAction = useCallback(async (action, payload = {}) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/game/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, ...payload })
      });
      if (!response.ok) {
        throw new Error(`Game action failed: ${response.status}`);
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

  // Fetch betting tips
  const fetchBettingTips = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/game/tips`);
      if (!response.ok) {
        throw new Error(`Failed to fetch betting tips: ${response.status}`);
      }
      const data = await response.json();
      return data.tips || [];
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch player strokes
  const fetchPlayerStrokes = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/game/player_strokes`);
      if (!response.ok) {
        throw new Error(`Failed to fetch player strokes: ${response.status}`);
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

  // Fetch game rules
  const fetchRules = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/rules`);
      if (!response.ok) {
        throw new Error(`Failed to fetch rules: ${response.status}`);
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
    fetchGameState,
    startGame,
    performGameAction,
    fetchBettingTips,
    fetchPlayerStrokes,
    fetchRules
  };
};

export default useGameApi;