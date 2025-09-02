import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import MatchmakingSuggestions from '../MatchmakingSuggestions';

// Mock fetch
global.fetch = jest.fn();

const mockMatches = [
  {
    day_of_week: 0,
    overlap_start: "9:00 AM",
    overlap_end: "1:00 PM", 
    suggested_tee_time: "10:00 AM",
    overlap_duration_hours: 4.0,
    match_quality: 85.5,
    players: [
      { player_id: 1, player_name: "John Doe", email: "john@test.com" },
      { player_id: 2, player_name: "Jane Smith", email: "jane@test.com" },
      { player_id: 3, player_name: "Bob Wilson", email: "bob@test.com" },
      { player_id: 4, player_name: "Alice Brown", email: "alice@test.com" }
    ]
  }
];

describe('MatchmakingSuggestions', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('renders loading state initially', () => {
    fetch.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<MatchmakingSuggestions />);
    
    expect(screen.getByText(/Finding perfect golf matches/i)).toBeInTheDocument();
  });

  test('renders match suggestions after loading', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ matches: mockMatches, total_matches_found: 1, filtered_matches: 1 })
    });

    render(<MatchmakingSuggestions />);

    await waitFor(() => {
      expect(screen.getByText(/Monday/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/10:00 AM/i)).toBeInTheDocument();
    expect(screen.getByText(/Excellent Match/i)).toBeInTheDocument();
    expect(screen.getByText(/John Doe/i)).toBeInTheDocument();
  });

  test('handles empty results', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ matches: [], total_matches_found: 0, filtered_matches: 0 })
    });

    render(<MatchmakingSuggestions />);

    await waitFor(() => {
      expect(screen.getByText(/No matches found with current criteria/i)).toBeInTheDocument();
    });
  });

  test('handles API errors', async () => {
    fetch.mockRejectedValueOnce(new Error('API Error'));

    render(<MatchmakingSuggestions />);

    await waitFor(() => {
      expect(screen.getByText(/API Error/i)).toBeInTheDocument();
    });
  });

  test('updates minimum overlap hours', async () => {
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ matches: [], total_matches_found: 0, filtered_matches: 0 })
    });

    render(<MatchmakingSuggestions />);

    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: '3' } });

    await waitFor(() => {
      expect(screen.getByText('3h')).toBeInTheDocument();
    });

    // Should trigger a new API call with updated parameters
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('min_overlap_hours=3'),
      expect.any(Object)
    );
  });

  test('toggles day selection', async () => {
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({ matches: [], total_matches_found: 0, filtered_matches: 0 })
    });

    render(<MatchmakingSuggestions />);

    const mondayButton = screen.getByText('Monday');
    fireEvent.click(mondayButton);

    await waitFor(() => {
      // Should trigger API call with preferred days parameter
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('preferred_days=0'),
        expect.any(Object)
      );
    });
  });

  test('sends notifications', async () => {
    // Mock initial load
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ matches: mockMatches, total_matches_found: 1, filtered_matches: 1 })
    });

    // Mock notification API
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ notifications_sent: 1, notifications_failed: 0, matches_created: 1 })
    });

    render(<MatchmakingSuggestions />);

    await waitFor(() => {
      expect(screen.getByText(/Monday/i)).toBeInTheDocument();
    });

    const notifyButton = screen.getByText('Send All Notifications');
    fireEvent.click(notifyButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/matchmaking/create-and-notify'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });
});