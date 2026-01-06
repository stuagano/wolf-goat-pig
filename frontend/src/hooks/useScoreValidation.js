/**
 * useScoreValidation - Score validation hook
 *
 * Provides centralized validation rules for golf scores and hole data.
 * Consolidates validation logic that was previously duplicated across
 * SimpleScorekeeper.jsx, LargeScoringButtons.jsx, and Scorecard.jsx.
 */

import { useCallback, useMemo } from 'react';

// Score constraints
export const SCORE_CONSTRAINTS = {
  MIN_STROKES: 1,
  MAX_STROKES: 15,
  MIN_QUARTERS: -999, // No practical limit - quarters can accumulate with doubles, floats, carry-overs
  MAX_QUARTERS: 999,  // No practical limit - quarters can accumulate with doubles, floats, carry-overs
  MIN_PLAYERS_PER_TEAM: 1,
  MAX_PLAYERS: 4
};

/**
 * Custom hook for validating golf scores and hole data
 */
export const useScoreValidation = () => {
  /**
   * Validate a single stroke score
   *
   * @param {number|string} strokes - The stroke value to validate
   * @returns {{ valid: boolean, error: string|null, value: number|null }}
   */
  const validateStrokes = useCallback((strokes) => {
    if (strokes === '' || strokes === null || strokes === undefined) {
      return { valid: false, error: 'Score is required', value: null };
    }

    const numericValue = typeof strokes === 'string' ? parseInt(strokes, 10) : strokes;

    if (isNaN(numericValue)) {
      return { valid: false, error: 'Score must be a number', value: null };
    }

    if (numericValue < SCORE_CONSTRAINTS.MIN_STROKES) {
      return { valid: false, error: `Score must be at least ${SCORE_CONSTRAINTS.MIN_STROKES}`, value: null };
    }

    if (numericValue > SCORE_CONSTRAINTS.MAX_STROKES) {
      return { valid: false, error: `Score cannot exceed ${SCORE_CONSTRAINTS.MAX_STROKES}`, value: null };
    }

    return { valid: true, error: null, value: numericValue };
  }, []);

  /**
   * Validate quarters value
   *
   * @param {number|string} quarters - The quarters value to validate
   * @returns {{ valid: boolean, error: string|null, value: number|null }}
   */
  const validateQuarters = useCallback((quarters) => {
    if (quarters === '' || quarters === null || quarters === undefined) {
      return { valid: true, error: null, value: 0 }; // Quarters default to 0
    }

    const numericValue = typeof quarters === 'string' ? parseFloat(quarters) : quarters;

    if (isNaN(numericValue)) {
      return { valid: false, error: 'Quarters must be a number', value: null };
    }

    if (numericValue < SCORE_CONSTRAINTS.MIN_QUARTERS) {
      return { valid: false, error: `Quarters must be at least ${SCORE_CONSTRAINTS.MIN_QUARTERS}`, value: null };
    }

    if (numericValue > SCORE_CONSTRAINTS.MAX_QUARTERS) {
      return { valid: false, error: `Quarters cannot exceed ${SCORE_CONSTRAINTS.MAX_QUARTERS}`, value: null };
    }

    return { valid: true, error: null, value: numericValue };
  }, []);

  /**
   * Validate team configuration
   *
   * @param {Object} teamConfig - Team configuration object
   * @param {string} teamConfig.mode - 'partners' or 'solo'
   * @param {Array} teamConfig.team1 - Array of player IDs for team 1
   * @param {Array} teamConfig.players - All players
   * @param {string} teamConfig.captain - Captain player ID (for solo mode)
   * @returns {{ valid: boolean, error: string|null }}
   */
  const validateTeams = useCallback(({ mode, team1, players, captain }) => {
    if (mode === 'partners') {
      if (!team1 || team1.length === 0) {
        return { valid: false, error: 'Please select at least one player for Team 1' };
      }

      if (team1.length === players?.length) {
        return { valid: false, error: 'Cannot select all players for Team 1. Select half for Team 1, the rest will automatically be Team 2.' };
      }

      const implicitTeam2 = players?.filter(p => !team1.includes(p.id)).map(p => p.id) || [];

      if (team1.length !== implicitTeam2.length) {
        return { valid: false, error: `Select exactly ${Math.floor(players.length / 2)} players for Team 1. Currently selected: ${team1.length}` };
      }
    } else if (mode === 'solo') {
      if (!captain) {
        return { valid: false, error: 'Please select a captain' };
      }
    }

    return { valid: true, error: null };
  }, []);

  /**
   * Validate all player scores for a hole
   *
   * @param {Object} scores - Map of playerId to score
   * @param {Array} playerIds - Array of player IDs that need scores
   * @returns {{ valid: boolean, error: string|null, missingPlayers: Array }}
   */
  const validateAllScores = useCallback((scores, playerIds) => {
    if (!scores || typeof scores !== 'object') {
      return { valid: false, error: 'Scores data is missing', missingPlayers: playerIds || [] };
    }

    const missingPlayers = [];

    for (const playerId of playerIds || []) {
      // Check for truly missing scores (null, undefined, empty string)
      // Note: 0 is not a valid golf score, but we validate that separately
      if (scores[playerId] === null || scores[playerId] === undefined || scores[playerId] === '') {
        missingPlayers.push(playerId);
      } else {
        const validation = validateStrokes(scores[playerId]);
        if (!validation.valid) {
          return { valid: false, error: validation.error, missingPlayers };
        }
      }
    }

    if (missingPlayers.length > 0) {
      return { valid: false, error: 'Please enter scores for all players', missingPlayers };
    }

    return { valid: true, error: null, missingPlayers: [] };
  }, [validateStrokes]);

  /**
   * Validate winner selection
   *
   * @param {string} winner - Winner value
   * @param {string} mode - Team mode ('partners' or 'solo')
   * @returns {{ valid: boolean, error: string|null }}
   */
  const validateWinner = useCallback((winner, mode) => {
    if (!winner) {
      return { valid: false, error: 'Please select a winner' };
    }

    const validPartnersWinners = ['team1', 'team2', 'push', 'team1_flush', 'team2_flush'];
    const validSoloWinners = ['captain', 'opponents', 'push', 'captain_flush', 'opponents_flush'];

    const validWinners = mode === 'partners' ? validPartnersWinners : validSoloWinners;

    if (!validWinners.includes(winner)) {
      return { valid: false, error: `Invalid winner selection for ${mode} mode` };
    }

    return { valid: true, error: null };
  }, []);

  /**
   * Validate complete hole data before submission
   *
   * @param {Object} holeData - Complete hole data
   * @returns {{ valid: boolean, error: string|null }}
   */
  const validateHole = useCallback((holeData) => {
    const { teamMode, team1, players, captain, opponents, scores, winner } = holeData;

    // Validate teams
    const teamValidation = validateTeams({ mode: teamMode, team1, players, captain });
    if (!teamValidation.valid) {
      return teamValidation;
    }

    // Determine all players who need scores
    let allPlayerIds;
    if (teamMode === 'partners') {
      const implicitTeam2 = players?.filter(p => !team1.includes(p.id)).map(p => p.id) || [];
      allPlayerIds = [...team1, ...implicitTeam2];
    } else {
      allPlayerIds = [captain, ...(opponents || [])];
    }

    // Validate all scores
    const scoresValidation = validateAllScores(scores, allPlayerIds);
    if (!scoresValidation.valid) {
      return scoresValidation;
    }

    // Validate winner
    const winnerValidation = validateWinner(winner, teamMode);
    if (!winnerValidation.valid) {
      return winnerValidation;
    }

    return { valid: true, error: null };
  }, [validateTeams, validateAllScores, validateWinner]);

  /**
   * Parse score input value safely
   *
   * @param {string|number} value - Input value
   * @returns {number} - Parsed integer or 0
   */
  const parseScoreInput = useCallback((value) => {
    if (value === '' || value === null || value === undefined) {
      return 0;
    }
    const parsed = parseInt(value, 10);
    return isNaN(parsed) ? 0 : parsed;
  }, []);

  /**
   * Check if a score is valid for entry (real-time validation)
   *
   * @param {number|string} value - Score value
   * @returns {boolean}
   */
  const isValidScoreEntry = useCallback((value) => {
    if (value === '' || value === null || value === undefined) {
      return true; // Allow empty during entry
    }
    const numericValue = typeof value === 'string' ? parseInt(value, 10) : value;
    return !isNaN(numericValue) &&
      numericValue >= SCORE_CONSTRAINTS.MIN_STROKES &&
      numericValue <= SCORE_CONSTRAINTS.MAX_STROKES;
  }, []);

  // Memoized constraints for external use
  const constraints = useMemo(() => SCORE_CONSTRAINTS, []);

  return {
    // Validation functions
    validateStrokes,
    validateQuarters,
    validateTeams,
    validateAllScores,
    validateWinner,
    validateHole,

    // Utility functions
    parseScoreInput,
    isValidScoreEntry,

    // Constants
    constraints
  };
};

export default useScoreValidation;
