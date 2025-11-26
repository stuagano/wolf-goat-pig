/**
 * useScoreInput - Score input state management hook
 *
 * Manages score state for multiple players with validation and common operations.
 * Consolidates score input handling that was duplicated across components.
 */

import { useState, useCallback, useMemo } from 'react';
import { useScoreValidation } from './useScoreValidation';

/**
 * Custom hook for managing score input state
 *
 * @param {Array} players - Array of player objects with id property
 * @param {Object} initialScores - Optional initial scores object
 * @returns {Object} Score state and operations
 */
export const useScoreInput = (players = [], initialScores = {}) => {
  const [scores, setScores] = useState(initialScores);
  const { parseScoreInput, validateStrokes, isValidScoreEntry } = useScoreValidation();

  /**
   * Update score for a single player
   *
   * @param {string} playerId - Player ID
   * @param {string|number} value - Score value
   */
  const updateScore = useCallback((playerId, value) => {
    const parsed = parseScoreInput(value);
    setScores(prev => ({
      ...prev,
      [playerId]: parsed
    }));
  }, [parseScoreInput]);

  /**
   * Clear score for a single player
   *
   * @param {string} playerId - Player ID
   */
  const clearScore = useCallback((playerId) => {
    setScores(prev => {
      const newScores = { ...prev };
      delete newScores[playerId];
      return newScores;
    });
  }, []);

  /**
   * Clear all scores
   */
  const clearAllScores = useCallback(() => {
    setScores({});
  }, []);

  /**
   * Set all scores at once (for loading existing data)
   *
   * @param {Object} newScores - Object of playerId -> score
   */
  const setAllScores = useCallback((newScores) => {
    setScores(newScores || {});
  }, []);

  /**
   * Check if a player has a score entered
   *
   * @param {string} playerId - Player ID
   * @returns {boolean}
   */
  const hasScore = useCallback((playerId) => {
    return scores[playerId] !== undefined && scores[playerId] !== null && scores[playerId] !== 0;
  }, [scores]);

  /**
   * Get score for a player
   *
   * @param {string} playerId - Player ID
   * @returns {number|undefined}
   */
  const getScore = useCallback((playerId) => {
    return scores[playerId];
  }, [scores]);

  /**
   * Check if all specified players have valid scores
   *
   * @param {Array} playerIds - Array of player IDs to check
   * @returns {boolean}
   */
  const allPlayersHaveScores = useCallback((playerIds = []) => {
    const idsToCheck = playerIds.length > 0 ? playerIds : players.map(p => p.id);
    return idsToCheck.every(playerId =>
      scores[playerId] !== undefined &&
      scores[playerId] !== null &&
      scores[playerId] > 0
    );
  }, [players, scores]);

  /**
   * Check if at least one player has a score
   *
   * @returns {boolean}
   */
  const hasAnyScore = useCallback(() => {
    return Object.keys(scores).some(pid =>
      scores[pid] !== undefined &&
      scores[pid] !== null &&
      scores[pid] > 0
    );
  }, [scores]);

  /**
   * Get players missing scores
   *
   * @param {Array} playerIds - Optional specific player IDs to check
   * @returns {Array} Array of player IDs without scores
   */
  const getPlayersMissingScores = useCallback((playerIds = []) => {
    const idsToCheck = playerIds.length > 0 ? playerIds : players.map(p => p.id);
    return idsToCheck.filter(playerId =>
      !scores[playerId] || scores[playerId] === 0
    );
  }, [players, scores]);

  /**
   * Validate all current scores
   *
   * @returns {{ valid: boolean, errors: Object }}
   */
  const validateAllCurrentScores = useCallback(() => {
    const errors = {};
    let valid = true;

    Object.entries(scores).forEach(([playerId, score]) => {
      const validation = validateStrokes(score);
      if (!validation.valid) {
        errors[playerId] = validation.error;
        valid = false;
      }
    });

    return { valid, errors };
  }, [scores, validateStrokes]);

  /**
   * Get the lowest score among entered scores
   *
   * @returns {{ playerId: string, score: number }|null}
   */
  const getLowestScore = useCallback(() => {
    const entries = Object.entries(scores).filter(([_, score]) => score > 0);
    if (entries.length === 0) return null;

    const [playerId, score] = entries.reduce((lowest, current) =>
      current[1] < lowest[1] ? current : lowest
    );

    return { playerId, score };
  }, [scores]);

  /**
   * Get score summary statistics
   *
   * @returns {Object} Summary with entered, missing, lowest, highest
   */
  const getScoreSummary = useMemo(() => {
    const enteredScores = Object.entries(scores).filter(([_, score]) => score > 0);
    const playerIds = players.map(p => p.id);

    return {
      entered: enteredScores.length,
      total: players.length,
      missing: playerIds.filter(id => !scores[id] || scores[id] === 0).length,
      lowest: enteredScores.length > 0
        ? Math.min(...enteredScores.map(([_, score]) => score))
        : null,
      highest: enteredScores.length > 0
        ? Math.max(...enteredScores.map(([_, score]) => score))
        : null,
      complete: enteredScores.length === players.length && players.length > 0
    };
  }, [scores, players]);

  /**
   * Handle score input change event (for controlled inputs)
   *
   * @param {string} playerId - Player ID
   * @returns {Function} Event handler function
   */
  const createChangeHandler = useCallback((playerId) => {
    return (e) => {
      const value = e.target.value;
      if (value === '' || isValidScoreEntry(value)) {
        updateScore(playerId, value);
      }
    };
  }, [updateScore, isValidScoreEntry]);

  return {
    // State
    scores,

    // Core operations
    updateScore,
    clearScore,
    clearAllScores,
    setAllScores,

    // Getters
    getScore,
    hasScore,
    getLowestScore,
    getPlayersMissingScores,

    // Validation
    allPlayersHaveScores,
    hasAnyScore,
    validateAllCurrentScores,

    // Summary
    getScoreSummary,

    // Helpers
    createChangeHandler
  };
};

export default useScoreInput;
