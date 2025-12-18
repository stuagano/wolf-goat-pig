import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import AllPlayersAvailability from '../AllPlayersAvailability';
import { createMockFetchResponse } from '../../../test-utils/mockFactories';

// Mock fetch
global.fetch = jest.fn();

const mockPlayersData = [
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
        notes: "Flexible schedule"
      },
      {
        day_of_week: 5,
        is_available: true,
        available_from_time: "8:00 AM",
        available_to_time: "12:00 PM",
        notes: "Morning only"
      }
    ]
  },
  {
    player_id: 2,
    player_name: "Jane Smith", 
    email: "jane@test.com",
    availability: [
      {
        day_of_week: 0,
        is_available: true,
        available_from_time: "10:00 AM",
        available_to_time: "3:00 PM",
        notes: ""
      }
    ]
  }
];

describe('AllPlayersAvailability', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('renders loading state initially', () => {
    fetch.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<AllPlayersAvailability />);
    
    expect(screen.getByText(/Loading players' availability/i)).toBeInTheDocument();
  });

  test('renders weekly overview by default', async () => {
    fetch.mockResolvedValueOnce(createMockFetchResponse(mockPlayersData));

    render(<AllPlayersAvailability />);

    await screen.findByRole('heading', { level: 4, name: /^Monday/ });

    expect(screen.getByRole('heading', { level: 4, name: /^Saturday/ })).toBeInTheDocument();
    expect(screen.getByText('2 available')).toBeInTheDocument();
    expect(screen.getByText('1 available')).toBeInTheDocument();
  });

  test('switches to day detail view when clicking day tab', async () => {
    fetch.mockResolvedValueOnce(createMockFetchResponse(mockPlayersData));

    render(<AllPlayersAvailability />);

    const mondayTab = await screen.findByRole('button', { name: /Monday 2/i });
    fireEvent.click(mondayTab);

    expect(screen.getByText('Monday Availability')).toBeInTheDocument();
    expect(screen.getByText('2 players available')).toBeInTheDocument();
    expect(screen.getByText(/John Doe/)).toBeInTheDocument();
    expect(screen.getByText(/Jane Smith/)).toBeInTheDocument();
  });

  test('shows "All Days" view when clicking All Days tab', async () => {
    fetch.mockResolvedValueOnce(createMockFetchResponse(mockPlayersData));

    render(<AllPlayersAvailability />);

    // Click Monday first to switch to day view
    const mondayTab = await screen.findByRole('button', { name: /Monday 2/i });
    fireEvent.click(mondayTab);

    // Then click All Days to go back
    const allDaysTab = screen.getByRole('button', { name: /All Days/i });
    fireEvent.click(allDaysTab);

    expect(screen.getByRole('heading', { level: 4, name: /^Monday/ })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 4, name: /^Saturday/ })).toBeInTheDocument();
  });

  test('displays player time ranges correctly', async () => {
    fetch.mockResolvedValueOnce(createMockFetchResponse(mockPlayersData));

    render(<AllPlayersAvailability />);

    await screen.findByRole('heading', { level: 4, name: /^Monday/ });

    // Check time formatting
    expect(screen.getByText(/9:00 AM - 5:00 PM/)).toBeInTheDocument();
    expect(screen.getByText(/10:00 AM - 3:00 PM/)).toBeInTheDocument();
    expect(screen.getByText(/8:00 AM - 12:00 PM/)).toBeInTheDocument();
  });

  test('displays player notes when available', async () => {
    fetch.mockResolvedValueOnce(createMockFetchResponse(mockPlayersData));

    render(<AllPlayersAvailability />);

    await screen.findByRole('heading', { level: 4, name: /^Monday/ });

    expect(screen.getByText('💬 Flexible schedule')).toBeInTheDocument();
    expect(screen.getByText('💬 Morning only')).toBeInTheDocument();
  });

  test('handles empty availability data', async () => {
    fetch.mockResolvedValueOnce(createMockFetchResponse([]));

    render(<AllPlayersAvailability />);

    const totalPlayersLabel = await screen.findByText('Total Players');
    expect(totalPlayersLabel.previousElementSibling).toHaveTextContent('0');

    // All days should show "No players available"
    const noPlayersTexts = screen.getAllByText('No players available');
    expect(noPlayersTexts.length).toBeGreaterThan(0);
  });

  test('handles API error', async () => {
    fetch.mockRejectedValueOnce(new Error('Failed to load availability data'));

    render(<AllPlayersAvailability />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load availability data/i)).toBeInTheDocument();
    });
  });

  test('shows correct statistics', async () => {
    fetch.mockResolvedValueOnce(createMockFetchResponse(mockPlayersData));

    render(<AllPlayersAvailability />);

    const totalPlayersLabel = await screen.findByText('Total Players');
    expect(totalPlayersLabel.previousElementSibling).toHaveTextContent('2');

    expect(totalPlayersLabel).toBeInTheDocument();
    expect(screen.getByText('Most Available (Single Day)')).toBeInTheDocument();
    expect(screen.getByText('Most Popular Day')).toBeInTheDocument();
  });
});
