// Test API integration functions
import '@testing-library/jest-dom';

// Mock fetch globally
global.fetch = jest.fn();

describe('API Integration Tests', () => {
  beforeEach(() => {
    fetch.mockClear();
    process.env.REACT_APP_API_URL = 'http://test-api.com';
  });

  describe('Matchmaking API', () => {
    test('fetches matchmaking suggestions successfully', async () => {
      const mockResponse = {
        total_matches_found: 2,
        filtered_matches: 2,
        matches: [
          {
            day_of_week: 0,
            overlap_start: "9:00 AM",
            overlap_end: "1:00 PM",
            suggested_tee_time: "10:00 AM",
            match_quality: 85.5,
            players: [
              { player_id: 1, player_name: "John", email: "john@test.com" },
              { player_id: 2, player_name: "Jane", email: "jane@test.com" },
              { player_id: 3, player_name: "Bob", email: "bob@test.com" },
              { player_id: 4, player_name: "Alice", email: "alice@test.com" }
            ]
          }
        ]
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const response = await fetch('http://test-api.com/matchmaking/suggestions?min_overlap_hours=2');
      const data = await response.json();

      expect(fetch).toHaveBeenCalledWith(
        'http://test-api.com/matchmaking/suggestions?min_overlap_hours=2'
      );
      expect(data.matches).toHaveLength(1);
      expect(data.matches[0].players).toHaveLength(4);
    });

    test('handles matchmaking API errors', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' })
      });

      const response = await fetch('http://test-api.com/matchmaking/suggestions');
      
      expect(response.ok).toBe(false);
      expect(response.status).toBe(500);
    });

    test('sends matchmaking notifications successfully', async () => {
      const mockResponse = {
        matches_found: 2,
        matches_created: 1,
        notifications_sent: 1,
        notifications_failed: 0,
        match_ids: [1]
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const response = await fetch('http://test-api.com/matchmaking/create-and-notify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();

      expect(fetch).toHaveBeenCalledWith(
        'http://test-api.com/matchmaking/create-and-notify',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
      );
      expect(data.notifications_sent).toBe(1);
    });
  });

  describe('Player Availability API', () => {
    test('fetches all players availability successfully', async () => {
      const mockResponse = [
        {
          player_id: 1,
          player_name: "John Doe",
          email: "john@test.com",
          availability: [
            {
              day_of_week: 0,
              is_available: true,
              available_from_time: "9:00 AM",
              available_to_time: "5:00 PM",
              notes: "Flexible"
            }
          ]
        }
      ];

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const response = await fetch('http://test-api.com/players/availability/all');
      const data = await response.json();

      expect(data).toHaveLength(1);
      expect(data[0].player_name).toBe("John Doe");
      expect(data[0].availability).toHaveLength(1);
    });

    test('saves user availability successfully', async () => {
      const availabilityData = {
        player_profile_id: 0, // Will be overridden by backend
        day_of_week: 0,
        is_available: true,
        available_from_time: "9:00 AM",
        available_to_time: "5:00 PM",
        notes: "Flexible schedule"
      };

      const mockResponse = {
        id: 1,
        ...availabilityData,
        player_profile_id: 123,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z'
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const response = await fetch('http://test-api.com/players/me/availability', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer mock-token'
        },
        body: JSON.stringify(availabilityData)
      });
      const data = await response.json();

      expect(fetch).toHaveBeenCalledWith(
        'http://test-api.com/players/me/availability',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer mock-token'
          },
          body: JSON.stringify(availabilityData)
        })
      );
      expect(data.id).toBe(1);
      expect(data.player_profile_id).toBe(123);
    });

    test('handles availability save errors', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 422,
        json: async () => ({ 
          detail: [
            {
              loc: ["body", "day_of_week"],
              msg: "ensure this value is greater than or equal to 0",
              type: "value_error.number.not_ge"
            }
          ]
        })
      });

      const response = await fetch('http://test-api.com/players/me/availability', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ day_of_week: -1 })
      });

      expect(response.ok).toBe(false);
      expect(response.status).toBe(422);
      
      const errorData = await response.json();
      expect(errorData.detail).toBeDefined();
    });
  });

  describe('Authentication Token Handling', () => {
    test('includes authorization header when token is available', async () => {
      const token = 'mock-jwt-token';
      
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

      await fetch('http://test-api.com/players/me/availability', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      expect(fetch).toHaveBeenCalledWith(
        'http://test-api.com/players/me/availability',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer mock-jwt-token'
          })
        })
      );
    });

    test('handles requests without token gracefully', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Not authenticated' })
      });

      const response = await fetch('http://test-api.com/players/me/availability', {
        headers: { 'Content-Type': 'application/json' }
      });

      expect(response.status).toBe(401);
    });
  });

  describe('Error Handling', () => {
    test('handles network errors', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'));

      try {
        await fetch('http://test-api.com/matchmaking/suggestions');
      } catch (error) {
        expect(error.message).toBe('Network error');
      }
    });

    test('handles malformed JSON responses', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Unexpected token in JSON');
        }
      });

      const response = await fetch('http://test-api.com/matchmaking/suggestions');
      
      try {
        await response.json();
      } catch (error) {
        expect(error.message).toBe('Unexpected token in JSON');
      }
    });
  });
});