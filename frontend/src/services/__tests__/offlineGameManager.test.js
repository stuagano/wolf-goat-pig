// frontend/src/services/__tests__/offlineGameManager.test.js
import {
  createOfflineGame,
  updateOfflineGame,
  completeOfflineHole,
  isOfflineGame,
  syncOfflineGame,
} from '../offlineGameManager';

describe('offlineGameManager', () => {
  beforeEach(() => {
    jest.spyOn(console, 'log').mockImplementation(() => {});
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('createOfflineGame', () => {
    const mockPlayers = [
      { id: 'p1', name: 'Player 1', handicap: 10 },
      { id: 'p2', name: 'Player 2', handicap: 15 },
    ];

    test('should create a game with a unique ID', () => {
      const game = createOfflineGame({ players: mockPlayers });

      expect(game.game_id).toBeDefined();
      expect(game.game_id).toMatch(/^offline-/);
    });

    test('should generate a 6-character join code', () => {
      const game = createOfflineGame({ players: mockPlayers });

      expect(game.join_code).toBeDefined();
      expect(game.join_code.length).toBe(6);
      expect(game.join_code).toMatch(/^[A-Z0-9]+$/);
    });

    test('should set initial game status to setup', () => {
      const game = createOfflineGame({ players: mockPlayers });

      expect(game.game_status).toBe('setup');
    });

    test('should mark as offline mode', () => {
      const game = createOfflineGame({ players: mockPlayers });

      expect(game.offline_mode).toBe(true);
    });

    test('should include players from config', () => {
      const game = createOfflineGame({ players: mockPlayers });

      expect(game.players).toEqual(mockPlayers);
    });

    test('should use default player_count of 4', () => {
      const game = createOfflineGame({ players: mockPlayers });

      expect(game.player_count).toBe(4);
    });

    test('should allow custom player_count', () => {
      const game = createOfflineGame({
        players: mockPlayers,
        player_count: 2,
      });

      expect(game.player_count).toBe(2);
    });

    test('should use default course name', () => {
      const game = createOfflineGame({ players: mockPlayers });

      expect(game.course_name).toBe('Default Course');
    });

    test('should allow custom course name', () => {
      const game = createOfflineGame({
        players: mockPlayers,
        course_name: 'Wing Point Golf',
      });

      expect(game.course_name).toBe('Wing Point Golf');
    });

    test('should initialize game state correctly', () => {
      const game = createOfflineGame({ players: mockPlayers });

      expect(game.current_hole).toBe(1);
      expect(game.total_holes).toBe(18);
      expect(game.hole_history).toEqual([]);
    });

    test('should initialize player scores for each player', () => {
      const game = createOfflineGame({ players: mockPlayers });

      mockPlayers.forEach((player) => {
        expect(game.player_scores[player.id]).toEqual({
          total_strokes: 0,
          holes_completed: 0,
          holes_won: 0,
        });
      });
    });

    test('should initialize player earnings to 0', () => {
      const game = createOfflineGame({ players: mockPlayers });

      mockPlayers.forEach((player) => {
        expect(game.player_earnings[player.id]).toBe(0);
      });
    });

    test('should initialize betting state', () => {
      const game = createOfflineGame({ players: mockPlayers });

      expect(game.betting_state).toEqual({
        current_wager: 1,
        wager_history: [],
      });
    });

    test('should set creator_user_id to offline-user', () => {
      const game = createOfflineGame({ players: mockPlayers });

      expect(game.creator_user_id).toBe('offline-user');
    });

    test('should include timestamps', () => {
      const before = new Date().toISOString();
      const game = createOfflineGame({ players: mockPlayers });
      const after = new Date().toISOString();

      expect(game.created_at).toBeDefined();
      expect(game.updated_at).toBeDefined();
      expect(game.created_at >= before).toBe(true);
      expect(game.updated_at <= after).toBe(true);
    });

    test('should handle empty players array', () => {
      const game = createOfflineGame({ players: [] });

      expect(game.players).toEqual([]);
      expect(game.player_scores).toEqual({});
      expect(game.player_earnings).toEqual({});
    });

    test('should handle undefined players', () => {
      const game = createOfflineGame({});

      expect(game.players).toEqual([]);
    });
  });

  describe('updateOfflineGame', () => {
    const mockGame = {
      game_id: 'offline-123',
      current_hole: 1,
      game_status: 'setup',
      updated_at: '2024-01-01T00:00:00Z',
    };

    test('should merge update into current state', () => {
      const updated = updateOfflineGame(mockGame, { current_hole: 2 });

      expect(updated.current_hole).toBe(2);
      expect(updated.game_id).toBe('offline-123');
    });

    test('should update the updated_at timestamp', () => {
      const before = new Date().toISOString();
      const updated = updateOfflineGame(mockGame, { game_status: 'active' });

      expect(updated.updated_at >= before).toBe(true);
    });

    test('should not mutate original state', () => {
      const original = { ...mockGame };
      updateOfflineGame(mockGame, { current_hole: 5 });

      expect(mockGame.current_hole).toBe(original.current_hole);
    });

    test('should handle multiple updates', () => {
      const updated = updateOfflineGame(mockGame, {
        current_hole: 3,
        game_status: 'active',
        players: [{ id: 'p1' }],
      });

      expect(updated.current_hole).toBe(3);
      expect(updated.game_status).toBe('active');
      expect(updated.players).toEqual([{ id: 'p1' }]);
    });
  });

  describe('completeOfflineHole', () => {
    const createMockGameState = () => ({
      game_id: 'offline-123',
      current_hole: 1,
      total_holes: 18,
      hole_history: [],
      player_earnings: { p1: 0, p2: 0 },
      game_status: 'active',
    });

    test('should add hole to history', () => {
      const game = createMockGameState();
      const holeData = {
        hole_number: 1,
        player_scores: { p1: 4, p2: 5 },
        winner: 'p1',
        wager: 2,
      };

      const updated = completeOfflineHole(game, holeData);

      expect(updated.hole_history.length).toBe(1);
      expect(updated.hole_history[0].hole_number).toBe(1);
      expect(updated.hole_history[0].player_scores).toEqual({ p1: 4, p2: 5 });
    });

    test('should include completed_at timestamp in hole history', () => {
      const game = createMockGameState();
      const holeData = {
        hole_number: 1,
        player_scores: { p1: 4 },
        winner: 'p1',
        wager: 1,
      };

      const updated = completeOfflineHole(game, holeData);

      expect(updated.hole_history[0].completed_at).toBeDefined();
    });

    test('should update player earnings for winner', () => {
      const game = createMockGameState();
      const holeData = {
        hole_number: 1,
        player_scores: { p1: 4, p2: 5 },
        winner: 'p1',
        wager: 2,
      };

      const updated = completeOfflineHole(game, holeData);

      expect(updated.player_earnings.p1).toBe(2);
    });

    test('should increment current_hole', () => {
      const game = createMockGameState();
      const holeData = {
        hole_number: 1,
        player_scores: { p1: 4 },
        winner: 'p1',
        wager: 1,
      };

      const updated = completeOfflineHole(game, holeData);

      expect(updated.current_hole).toBe(2);
    });

    test('should not exceed total_holes when incrementing', () => {
      const game = createMockGameState();
      game.current_hole = 18;

      const holeData = {
        hole_number: 18,
        player_scores: { p1: 4 },
        winner: 'p1',
        wager: 1,
      };

      const updated = completeOfflineHole(game, holeData);

      expect(updated.current_hole).toBe(18);
    });

    test('should cap current_hole at total_holes after completing hole 18', () => {
      const game = createMockGameState();
      game.current_hole = 18;
      game.total_holes = 18;

      const holeData = {
        hole_number: 18,
        player_scores: { p1: 4 },
        winner: 'p1',
        wager: 1,
      };

      const updated = completeOfflineHole(game, holeData);

      // Current hole should be capped at 18 (total_holes)
      expect(updated.current_hole).toBe(18);
      // The hole should be recorded in history
      expect(updated.hole_history.length).toBe(1);
    });

    test('should update updated_at timestamp', () => {
      const game = createMockGameState();
      const before = new Date().toISOString();

      const holeData = {
        hole_number: 1,
        player_scores: { p1: 4 },
        winner: 'p1',
        wager: 1,
      };

      const updated = completeOfflineHole(game, holeData);

      expect(updated.updated_at >= before).toBe(true);
    });

    test('should handle no winner (push)', () => {
      const game = createMockGameState();
      const holeData = {
        hole_number: 1,
        player_scores: { p1: 4, p2: 4 },
        winner: null,
        wager: 1,
      };

      const updated = completeOfflineHole(game, holeData);

      // Earnings should remain 0
      expect(updated.player_earnings.p1).toBe(0);
      expect(updated.player_earnings.p2).toBe(0);
    });

    test('should initialize earnings for player if not exists', () => {
      const game = createMockGameState();
      game.player_earnings = {};

      const holeData = {
        hole_number: 1,
        player_scores: { p1: 4, p2: 5 },
        winner: 'p1',
        wager: 2,
      };

      const updated = completeOfflineHole(game, holeData);

      expect(updated.player_earnings.p1).toBe(2);
    });

    test('should accumulate earnings across multiple holes', () => {
      let game = createMockGameState();

      game = completeOfflineHole(game, {
        hole_number: 1,
        player_scores: { p1: 4, p2: 5 },
        winner: 'p1',
        wager: 2,
      });

      game = completeOfflineHole(game, {
        hole_number: 2,
        player_scores: { p1: 3, p2: 4 },
        winner: 'p1',
        wager: 1,
      });

      expect(game.player_earnings.p1).toBe(3);
    });
  });

  describe('isOfflineGame', () => {
    test('should return true when offline_mode is true', () => {
      expect(isOfflineGame({ offline_mode: true })).toBe(true);
    });

    test('should return true when game_id starts with offline-', () => {
      expect(isOfflineGame({ game_id: 'offline-123456' })).toBe(true);
    });

    test('should return false for regular game', () => {
      expect(isOfflineGame({ game_id: 'abc123', offline_mode: false })).toBe(
        false
      );
    });

    test('should return falsy for null/undefined', () => {
      expect(isOfflineGame(null)).toBeFalsy();
      expect(isOfflineGame(undefined)).toBeFalsy();
    });

    test('should return falsy for empty object', () => {
      expect(isOfflineGame({})).toBeFalsy();
    });
  });

  describe('syncOfflineGame', () => {
    const mockGameState = {
      game_id: 'offline-123',
      offline_mode: true,
      players: [{ id: 'p1', name: 'Player 1' }],
    };

    test('should return failure for non-offline games', async () => {
      const fetchCallsBefore = global.fetch.mock.calls.length;

      const result = await syncOfflineGame(
        { game_id: 'regular-123', offline_mode: false },
        'http://api.example.com'
      );

      expect(result.success).toBe(false);
      expect(result.message).toBe('Not an offline game');
      // No new fetch calls should have been made
      expect(global.fetch.mock.calls.length).toBe(fetchCallsBefore);
    });

    test('should send POST request to import endpoint', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({ success: true, game_id: 'synced-123' }),
      });

      await syncOfflineGame(mockGameState, 'http://api.example.com');

      expect(global.fetch).toHaveBeenCalledWith(
        'http://api.example.com/game/import-offline',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(mockGameState),
        }
      );
    });

    test('should return success with backend game ID', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({ success: true, game_id: 'synced-123' }),
      });

      const result = await syncOfflineGame(
        mockGameState,
        'http://api.example.com'
      );

      expect(result.success).toBe(true);
      expect(result.backend_game_id).toBe('synced-123');
      expect(result.message).toBe('Game synced successfully');
    });

    test('should return failure on HTTP error', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      const result = await syncOfflineGame(
        mockGameState,
        'http://api.example.com'
      );

      expect(result.success).toBe(false);
      expect(result.message).toContain('500');
    });

    test('should return failure on network error', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      const result = await syncOfflineGame(
        mockGameState,
        'http://api.example.com'
      );

      expect(result.success).toBe(false);
      expect(result.message).toBe('Network error');
      expect(result.error).toBeDefined();
    });
  });

  describe('ID generation', () => {
    test('should generate unique game IDs', () => {
      const ids = new Set();
      for (let i = 0; i < 100; i++) {
        const game = createOfflineGame({ players: [] });
        ids.add(game.game_id);
      }
      expect(ids.size).toBe(100);
    });

    test('should generate unique join codes', () => {
      const codes = new Set();
      for (let i = 0; i < 100; i++) {
        const game = createOfflineGame({ players: [] });
        codes.add(game.join_code);
      }
      // Allow some collisions for 6-char codes, but should be mostly unique
      expect(codes.size).toBeGreaterThan(90);
    });
  });
});
