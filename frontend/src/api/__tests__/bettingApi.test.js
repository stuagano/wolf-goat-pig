// frontend/src/api/__tests__/bettingApi.test.js
import { syncBettingEvents, syncWithRetry } from '../bettingApi';
import { BettingEventTypes } from '../../constants/bettingEvents';

global.fetch = jest.fn();

describe('bettingApi', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('syncBettingEvents', () => {
    test('should sync events successfully', async () => {
      const mockResponse = {
        success: true,
        confirmedEvents: ['event-1'],
        corrections: []
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const events = [{
        eventId: 'event-1',
        eventType: BettingEventTypes.DOUBLE_OFFERED,
        actor: 'Player1',
        data: {},
        timestamp: '2025-11-04T10:00:00Z'
      }];

      const result = await syncBettingEvents('game-123', 5, events);

      expect(result.success).toBe(true);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/games/game-123/betting-events'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.any(String)
        })
      );

      const callArgs = global.fetch.mock.calls[0];
      const body = JSON.parse(callArgs[1].body);
      expect(body.holeNumber).toBe(5);
      expect(body.events).toEqual(events);
      expect(body.clientTimestamp).toBeDefined();
    });

    test('should handle sync failure', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 400
      });

      const events = [{
        eventId: 'event-1',
        eventType: 'INVALID',
        actor: 'Player1',
        data: {},
        timestamp: '2025-11-04T10:00:00Z'
      }];

      await expect(syncBettingEvents('game-123', 5, events)).rejects.toThrow('Sync failed: 400');
    });

    test('should handle network errors', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Network error'));

      const events = [{
        eventId: 'event-1',
        eventType: BettingEventTypes.DOUBLE_OFFERED,
        actor: 'Player1',
        data: {},
        timestamp: '2025-11-04T10:00:00Z'
      }];

      await expect(syncBettingEvents('game-123', 5, events)).rejects.toThrow('Network error');
    });
  });

  describe('syncWithRetry', () => {
    test('should succeed on first attempt', async () => {
      const mockResponse = {
        success: true,
        confirmedEvents: ['event-1'],
        corrections: []
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const events = [{
        eventId: 'event-1',
        eventType: BettingEventTypes.DOUBLE_OFFERED,
        actor: 'Player1',
        data: {},
        timestamp: '2025-11-04T10:00:00Z'
      }];

      const result = await syncWithRetry('game-123', 5, events, 3);

      expect(result.success).toBe(true);
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    test('should retry on failure and eventually succeed', async () => {
      // Mock setTimeout to execute immediately for testing
      const originalSetTimeout = global.setTimeout;
      global.setTimeout = (fn) => fn();

      global.fetch
        .mockResolvedValueOnce({ ok: false, status: 500 })
        .mockResolvedValueOnce({ ok: false, status: 500 })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true, confirmedEvents: ['event-1'], corrections: [] })
        });

      const events = [{
        eventId: 'event-1',
        eventType: BettingEventTypes.DOUBLE_OFFERED,
        actor: 'Player1',
        data: {},
        timestamp: '2025-11-04T10:00:00Z'
      }];

      const result = await syncWithRetry('game-123', 5, events, 3);

      expect(result.success).toBe(true);
      expect(global.fetch).toHaveBeenCalledTimes(3);

      global.setTimeout = originalSetTimeout;
    });

    test('should fail after max retries', async () => {
      // Mock setTimeout to execute immediately for testing
      const originalSetTimeout = global.setTimeout;
      global.setTimeout = (fn) => fn();

      global.fetch.mockResolvedValue({ ok: false, status: 500 });

      const events = [{
        eventId: 'event-1',
        eventType: BettingEventTypes.DOUBLE_OFFERED,
        actor: 'Player1',
        data: {},
        timestamp: '2025-11-04T10:00:00Z'
      }];

      await expect(syncWithRetry('game-123', 5, events, 3)).rejects.toThrow('Sync failed: 500');
      expect(global.fetch).toHaveBeenCalledTimes(3);

      global.setTimeout = originalSetTimeout;
    });

    test('should use exponential backoff delays', async () => {
      const delays = [];
      const originalSetTimeout = global.setTimeout;
      global.setTimeout = (fn, delay) => {
        delays.push(delay);
        return originalSetTimeout(fn, 0); // Execute immediately but track delay
      };

      global.fetch
        .mockResolvedValueOnce({ ok: false, status: 500 })
        .mockResolvedValueOnce({ ok: false, status: 500 })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true, confirmedEvents: ['event-1'], corrections: [] })
        });

      const events = [{
        eventId: 'event-1',
        eventType: BettingEventTypes.DOUBLE_OFFERED,
        actor: 'Player1',
        data: {},
        timestamp: '2025-11-04T10:00:00Z'
      }];

      await syncWithRetry('game-123', 5, events, 3);

      // Check exponential backoff: 1s, 2s
      expect(delays).toEqual([1000, 2000]);

      global.setTimeout = originalSetTimeout;
    });
  });
});
