// frontend/src/hooks/__tests__/useScoreValidation.test.js
import { renderHook } from '@testing-library/react';
import { useScoreValidation, SCORE_CONSTRAINTS } from '../useScoreValidation';
import { createMockPlayers } from '../../test-utils/mockFactories';

describe('useScoreValidation', () => {
  describe('SCORE_CONSTRAINTS', () => {
    test('should have expected constraint values', () => {
      expect(SCORE_CONSTRAINTS.MIN_STROKES).toBe(1);
      expect(SCORE_CONSTRAINTS.MAX_STROKES).toBe(15);
      expect(SCORE_CONSTRAINTS.MIN_QUARTERS).toBe(-10);
      expect(SCORE_CONSTRAINTS.MAX_QUARTERS).toBe(10);
      expect(SCORE_CONSTRAINTS.MIN_PLAYERS_PER_TEAM).toBe(1);
      expect(SCORE_CONSTRAINTS.MAX_PLAYERS).toBe(4);
    });
  });

  describe('validateStrokes', () => {
    test('should return valid for score within range', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.validateStrokes(4)).toEqual({
        valid: true,
        error: null,
        value: 4,
      });
    });

    test('should return valid for minimum score (1)', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.validateStrokes(1)).toEqual({
        valid: true,
        error: null,
        value: 1,
      });
    });

    test('should return valid for maximum score (15)', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.validateStrokes(15)).toEqual({
        valid: true,
        error: null,
        value: 15,
      });
    });

    test('should parse string scores correctly', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.validateStrokes('5')).toEqual({
        valid: true,
        error: null,
        value: 5,
      });
    });

    test('should return error for empty string', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.validateStrokes('')).toEqual({
        valid: false,
        error: 'Score is required',
        value: null,
      });
    });

    test('should return error for null', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.validateStrokes(null)).toEqual({
        valid: false,
        error: 'Score is required',
        value: null,
      });
    });

    test('should return error for undefined', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.validateStrokes(undefined)).toEqual({
        valid: false,
        error: 'Score is required',
        value: null,
      });
    });

    test('should return error for NaN', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.validateStrokes('abc')).toEqual({
        valid: false,
        error: 'Score must be a number',
        value: null,
      });
    });

    test('should return error for score below minimum', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.validateStrokes(0)).toEqual({
        valid: false,
        error: 'Score must be at least 1',
        value: null,
      });
    });

    test('should return error for score above maximum', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.validateStrokes(16)).toEqual({
        valid: false,
        error: 'Score cannot exceed 15',
        value: null,
      });
    });
  });

  describe('validateQuarters', () => {
    test('should return valid for quarters within range', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.validateQuarters(5)).toEqual({
        valid: true,
        error: null,
        value: 5,
      });
    });

    test('should return valid with 0 for empty values', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.validateQuarters('')).toEqual({
        valid: true,
        error: null,
        value: 0,
      });

      expect(result.current.validateQuarters(null)).toEqual({
        valid: true,
        error: null,
        value: 0,
      });

      expect(result.current.validateQuarters(undefined)).toEqual({
        valid: true,
        error: null,
        value: 0,
      });
    });

    test('should return valid for negative quarters', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.validateQuarters(-5)).toEqual({
        valid: true,
        error: null,
        value: -5,
      });
    });

    test('should parse string quarters correctly', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.validateQuarters('3.5')).toEqual({
        valid: true,
        error: null,
        value: 3.5,
      });
    });

    test('should return error for quarters below minimum', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.validateQuarters(-11)).toEqual({
        valid: false,
        error: 'Quarters must be at least -10',
        value: null,
      });
    });

    test('should return error for quarters above maximum', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.validateQuarters(11)).toEqual({
        valid: false,
        error: 'Quarters cannot exceed 10',
        value: null,
      });
    });

    test('should return error for non-numeric quarters', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.validateQuarters('xyz')).toEqual({
        valid: false,
        error: 'Quarters must be a number',
        value: null,
      });
    });
  });

  describe('validateTeams', () => {
    const mockPlayers = createMockPlayers(4).map((player, idx) => ({
      id: `p${idx + 1}`,
      name: `Player ${idx + 1}`
    }));

    describe('partners mode', () => {
      test('should return valid for proper team split', () => {
        const { result } = renderHook(() => useScoreValidation());

        const validation = result.current.validateTeams({
          mode: 'partners',
          team1: ['p1', 'p2'],
          players: mockPlayers,
        });

        expect(validation.valid).toBe(true);
        expect(validation.error).toBeNull();
      });

      test('should return error when team1 is empty', () => {
        const { result } = renderHook(() => useScoreValidation());

        const validation = result.current.validateTeams({
          mode: 'partners',
          team1: [],
          players: mockPlayers,
        });

        expect(validation.valid).toBe(false);
        expect(validation.error).toBe('Please select at least one player for Team 1');
      });

      test('should return error when team1 is null', () => {
        const { result } = renderHook(() => useScoreValidation());

        const validation = result.current.validateTeams({
          mode: 'partners',
          team1: null,
          players: mockPlayers,
        });

        expect(validation.valid).toBe(false);
        expect(validation.error).toBe('Please select at least one player for Team 1');
      });

      test('should return error when all players selected for team1', () => {
        const { result } = renderHook(() => useScoreValidation());

        const validation = result.current.validateTeams({
          mode: 'partners',
          team1: ['p1', 'p2', 'p3', 'p4'],
          players: mockPlayers,
        });

        expect(validation.valid).toBe(false);
        expect(validation.error).toContain('Cannot select all players');
      });

      test('should return error for uneven team split', () => {
        const { result } = renderHook(() => useScoreValidation());

        const validation = result.current.validateTeams({
          mode: 'partners',
          team1: ['p1'],
          players: mockPlayers,
        });

        expect(validation.valid).toBe(false);
        expect(validation.error).toContain('Select exactly 2 players');
      });
    });

    describe('solo mode', () => {
      test('should return valid when captain is selected', () => {
        const { result } = renderHook(() => useScoreValidation());

        const validation = result.current.validateTeams({
          mode: 'solo',
          captain: 'p1',
          players: mockPlayers,
        });

        expect(validation.valid).toBe(true);
        expect(validation.error).toBeNull();
      });

      test('should return error when no captain is selected', () => {
        const { result } = renderHook(() => useScoreValidation());

        const validation = result.current.validateTeams({
          mode: 'solo',
          captain: null,
          players: mockPlayers,
        });

        expect(validation.valid).toBe(false);
        expect(validation.error).toBe('Please select a captain');
      });
    });
  });

  describe('validateAllScores', () => {
    test('should return valid when all players have scores', () => {
      const { result } = renderHook(() => useScoreValidation());

      const validation = result.current.validateAllScores(
        { p1: 4, p2: 5, p3: 3, p4: 6 },
        ['p1', 'p2', 'p3', 'p4']
      );

      expect(validation.valid).toBe(true);
      expect(validation.error).toBeNull();
      expect(validation.missingPlayers).toEqual([]);
    });

    test('should return error when scores is null', () => {
      const { result } = renderHook(() => useScoreValidation());

      const validation = result.current.validateAllScores(null, ['p1', 'p2']);

      expect(validation.valid).toBe(false);
      expect(validation.error).toBe('Scores data is missing');
    });

    test('should return error when player has no score', () => {
      const { result } = renderHook(() => useScoreValidation());

      const validation = result.current.validateAllScores(
        { p1: 4 },
        ['p1', 'p2']
      );

      expect(validation.valid).toBe(false);
      expect(validation.error).toBe('Please enter scores for all players');
      expect(validation.missingPlayers).toContain('p2');
    });

    test('should return error when player has 0 score', () => {
      const { result } = renderHook(() => useScoreValidation());

      const validation = result.current.validateAllScores(
        { p1: 4, p2: 0 },
        ['p1', 'p2']
      );

      // Score of 0 is invalid (below minimum of 1), not "missing"
      expect(validation.valid).toBe(false);
      expect(validation.error).toBe('Score must be at least 1');
    });

    test('should return error for invalid score', () => {
      const { result } = renderHook(() => useScoreValidation());

      const validation = result.current.validateAllScores(
        { p1: 20, p2: 4 },
        ['p1', 'p2']
      );

      expect(validation.valid).toBe(false);
      expect(validation.error).toBe('Score cannot exceed 15');
    });

    test('should handle null playerIds gracefully', () => {
      const { result } = renderHook(() => useScoreValidation());

      const validation = result.current.validateAllScores({ p1: 4 }, null);

      expect(validation.valid).toBe(true);
    });
  });

  describe('validateWinner', () => {
    describe('partners mode', () => {
      test('should return valid for team1 winner', () => {
        const { result } = renderHook(() => useScoreValidation());

        expect(result.current.validateWinner('team1', 'partners')).toEqual({
          valid: true,
          error: null,
        });
      });

      test('should return valid for team2 winner', () => {
        const { result } = renderHook(() => useScoreValidation());

        expect(result.current.validateWinner('team2', 'partners')).toEqual({
          valid: true,
          error: null,
        });
      });

      test('should return valid for push', () => {
        const { result } = renderHook(() => useScoreValidation());

        expect(result.current.validateWinner('push', 'partners')).toEqual({
          valid: true,
          error: null,
        });
      });

      test('should return valid for team1_flush', () => {
        const { result } = renderHook(() => useScoreValidation());

        expect(result.current.validateWinner('team1_flush', 'partners')).toEqual({
          valid: true,
          error: null,
        });
      });

      test('should return valid for team2_flush', () => {
        const { result } = renderHook(() => useScoreValidation());

        expect(result.current.validateWinner('team2_flush', 'partners')).toEqual({
          valid: true,
          error: null,
        });
      });

      test('should return error for invalid winner in partners mode', () => {
        const { result } = renderHook(() => useScoreValidation());

        expect(result.current.validateWinner('captain', 'partners')).toEqual({
          valid: false,
          error: 'Invalid winner selection for partners mode',
        });
      });
    });

    describe('solo mode', () => {
      test('should return valid for captain winner', () => {
        const { result } = renderHook(() => useScoreValidation());

        expect(result.current.validateWinner('captain', 'solo')).toEqual({
          valid: true,
          error: null,
        });
      });

      test('should return valid for opponents winner', () => {
        const { result } = renderHook(() => useScoreValidation());

        expect(result.current.validateWinner('opponents', 'solo')).toEqual({
          valid: true,
          error: null,
        });
      });

      test('should return valid for captain_flush', () => {
        const { result } = renderHook(() => useScoreValidation());

        expect(result.current.validateWinner('captain_flush', 'solo')).toEqual({
          valid: true,
          error: null,
        });
      });

      test('should return error for invalid winner in solo mode', () => {
        const { result } = renderHook(() => useScoreValidation());

        expect(result.current.validateWinner('team1', 'solo')).toEqual({
          valid: false,
          error: 'Invalid winner selection for solo mode',
        });
      });
    });

    test('should return error when no winner selected', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.validateWinner(null, 'partners')).toEqual({
        valid: false,
        error: 'Please select a winner',
      });

      expect(result.current.validateWinner('', 'partners')).toEqual({
        valid: false,
        error: 'Please select a winner',
      });
    });
  });

  describe('validateHole', () => {
    const mockPlayers = createMockPlayers(4).map((player, idx) => ({
      id: `p${idx + 1}`,
      name: `Player ${idx + 1}`
    }));

    test('should return valid for complete partners hole data', () => {
      const { result } = renderHook(() => useScoreValidation());

      const validation = result.current.validateHole({
        teamMode: 'partners',
        team1: ['p1', 'p2'],
        players: mockPlayers,
        scores: { p1: 4, p2: 5, p3: 3, p4: 6 },
        winner: 'team1',
      });

      expect(validation.valid).toBe(true);
      expect(validation.error).toBeNull();
    });

    test('should return valid for complete solo hole data', () => {
      const { result } = renderHook(() => useScoreValidation());

      const validation = result.current.validateHole({
        teamMode: 'solo',
        captain: 'p1',
        opponents: ['p2', 'p3', 'p4'],
        players: mockPlayers,
        scores: { p1: 3, p2: 4, p3: 5, p4: 4 },
        winner: 'captain',
      });

      expect(validation.valid).toBe(true);
    });

    test('should return team validation error first', () => {
      const { result } = renderHook(() => useScoreValidation());

      const validation = result.current.validateHole({
        teamMode: 'partners',
        team1: [],
        players: mockPlayers,
        scores: { p1: 4 },
        winner: null,
      });

      expect(validation.valid).toBe(false);
      expect(validation.error).toContain('Team 1');
    });

    test('should return scores validation error', () => {
      const { result } = renderHook(() => useScoreValidation());

      const validation = result.current.validateHole({
        teamMode: 'partners',
        team1: ['p1', 'p2'],
        players: mockPlayers,
        scores: { p1: 4 },
        winner: 'team1',
      });

      expect(validation.valid).toBe(false);
      expect(validation.error).toContain('scores');
    });

    test('should return winner validation error', () => {
      const { result } = renderHook(() => useScoreValidation());

      const validation = result.current.validateHole({
        teamMode: 'partners',
        team1: ['p1', 'p2'],
        players: mockPlayers,
        scores: { p1: 4, p2: 5, p3: 3, p4: 6 },
        winner: null,
      });

      expect(validation.valid).toBe(false);
      expect(validation.error).toBe('Please select a winner');
    });
  });

  describe('parseScoreInput', () => {
    test('should parse valid number', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.parseScoreInput(5)).toBe(5);
    });

    test('should parse valid string', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.parseScoreInput('7')).toBe(7);
    });

    test('should return 0 for empty string', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.parseScoreInput('')).toBe(0);
    });

    test('should return 0 for null', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.parseScoreInput(null)).toBe(0);
    });

    test('should return 0 for undefined', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.parseScoreInput(undefined)).toBe(0);
    });

    test('should return 0 for NaN', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.parseScoreInput('abc')).toBe(0);
    });
  });

  describe('isValidScoreEntry', () => {
    test('should return true for valid score', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.isValidScoreEntry(5)).toBe(true);
    });

    test('should return true for empty value (allows partial entry)', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.isValidScoreEntry('')).toBe(true);
      expect(result.current.isValidScoreEntry(null)).toBe(true);
      expect(result.current.isValidScoreEntry(undefined)).toBe(true);
    });

    test('should return true for boundary values', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.isValidScoreEntry(1)).toBe(true);
      expect(result.current.isValidScoreEntry(15)).toBe(true);
    });

    test('should return false for values outside range', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.isValidScoreEntry(-1)).toBe(false);
      expect(result.current.isValidScoreEntry(16)).toBe(false);
    });

    test('should handle string values', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.isValidScoreEntry('5')).toBe(true);
      expect(result.current.isValidScoreEntry('20')).toBe(false);
    });
  });

  describe('constraints', () => {
    test('should expose constraints', () => {
      const { result } = renderHook(() => useScoreValidation());

      expect(result.current.constraints).toEqual(SCORE_CONSTRAINTS);
    });
  });
});
