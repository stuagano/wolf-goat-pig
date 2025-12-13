// frontend/src/hooks/useZeroSumValidation.js
// Hook for validating zero-sum scoring (all quarters per hole must sum to zero)
import { useMemo, useCallback } from 'react';

/**
 * Zero-sum validation hook
 * Ensures all quarters for each hole sum to zero (it's a zero-sum game)
 *
 * @param {Object} holeQuarters - Shape: { holeNumber: { playerId: quarters, ... }, ... }
 * @param {Array} playerIds - Array of player IDs to validate against
 * @returns {Object} Validation utilities
 */
const useZeroSumValidation = (holeQuarters, playerIds) => {
  /**
   * Validate a single hole's quarters sum to zero
   */
  const validateHole = useCallback((holeNumber) => {
    const holeData = holeQuarters[holeNumber];
    if (!holeData || Object.keys(holeData).length === 0) {
      return {
        valid: true,
        sum: 0,
        hasData: false,
        missingPlayers: playerIds,
        enteredPlayers: []
      };
    }

    const enteredPlayers = Object.keys(holeData);
    const missingPlayers = playerIds.filter(id => !(id in holeData));
    const sum = Object.values(holeData).reduce((acc, val) => acc + (val || 0), 0);

    return {
      valid: sum === 0,
      sum,
      hasData: true,
      missingPlayers,
      enteredPlayers,
      allPlayersEntered: missingPlayers.length === 0
    };
  }, [holeQuarters, playerIds]);

  /**
   * Validate all holes up to a given hole number
   */
  const validateUpToHole = useCallback((maxHole) => {
    const results = {};
    let allValid = true;

    for (let h = 1; h <= maxHole; h++) {
      const result = validateHole(h);
      results[h] = result;
      if (result.hasData && !result.valid) {
        allValid = false;
      }
    }

    return { results, allValid };
  }, [validateHole]);

  /**
   * Validate all 18 holes
   */
  const validateAllHoles = useMemo(() => {
    return validateUpToHole(18);
  }, [validateUpToHole]);

  /**
   * Get holes with validation errors
   */
  const invalidHoles = useMemo(() => {
    return Object.entries(validateAllHoles.results)
      .filter(([_, result]) => result.hasData && !result.valid)
      .map(([hole, result]) => ({
        hole: parseInt(hole),
        ...result
      }));
  }, [validateAllHoles]);

  /**
   * Check if the game is ready to be completed
   * (all entered holes sum to zero)
   */
  const isReadyToComplete = useMemo(() => {
    return validateAllHoles.allValid;
  }, [validateAllHoles]);

  /**
   * Calculate current standings from all hole data
   */
  const calculateStandings = useMemo(() => {
    const standings = {};
    playerIds.forEach(id => {
      standings[id] = 0;
    });

    Object.values(holeQuarters).forEach(holeData => {
      Object.entries(holeData).forEach(([playerId, quarters]) => {
        if (playerId in standings) {
          standings[playerId] += quarters || 0;
        }
      });
    });

    return standings;
  }, [holeQuarters, playerIds]);

  /**
   * Verify standings sum to zero (should always be true if all holes are valid)
   */
  const standingsSumToZero = useMemo(() => {
    const total = Object.values(calculateStandings).reduce((acc, val) => acc + val, 0);
    return total === 0;
  }, [calculateStandings]);

  return {
    // Single hole validation
    validateHole,

    // Range validation
    validateUpToHole,
    validateAllHoles,

    // Error info
    invalidHoles,

    // Game state
    isReadyToComplete,
    calculateStandings,
    standingsSumToZero,
  };
};

export default useZeroSumValidation;
