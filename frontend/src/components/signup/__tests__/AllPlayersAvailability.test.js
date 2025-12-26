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

    expect(screen.getByText(/Loading.../i)).toBeInTheDocument();
  });

  test('renders day grid after loading', async () => {
    fetch.mockResolvedValueOnce(createMockFetchResponse(mockPlayersData));

    render(<AllPlayersAvailability />);

    // Wait for loading to complete - look for stats section
    await screen.findByText('Total Players');

    // Should show all day abbreviations
    expect(screen.getByText('Tue')).toBeInTheDocument();
    expect(screen.getByText('Wed')).toBeInTheDocument();
    expect(screen.getByText('Thu')).toBeInTheDocument();
    expect(screen.getByText('Fri')).toBeInTheDocument();
    expect(screen.getByText('Sat')).toBeInTheDocument();
    expect(screen.getByText('Sun')).toBeInTheDocument();
  });

  test('shows player count for each day', async () => {
    fetch.mockResolvedValueOnce(createMockFetchResponse(mockPlayersData));

    render(<AllPlayersAvailability />);

    await screen.findByText('Total Players');

    // Monday should show 2 players (John and Jane)
    const dayButtons = screen.getAllByRole('button');
    const mondayButton = dayButtons.find(btn => btn.textContent.includes('Mon'));
    expect(mondayButton).toHaveTextContent('2');
  });

  test('expands day detail panel when clicking day', async () => {
    fetch.mockResolvedValueOnce(createMockFetchResponse(mockPlayersData));

    render(<AllPlayersAvailability />);

    await screen.findByText('Total Players');

    // Click Monday
    const dayButtons = screen.getAllByRole('button');
    const mondayButton = dayButtons.find(btn => btn.textContent.includes('Mon'));
    fireEvent.click(mondayButton);

    // Should show expanded panel with day name
    expect(screen.getByText('Monday')).toBeInTheDocument();
    expect(screen.getByText(/Available Players/)).toBeInTheDocument();
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('Jane Smith')).toBeInTheDocument();
  });

  test('displays player time ranges correctly', async () => {
    fetch.mockResolvedValueOnce(createMockFetchResponse(mockPlayersData));

    render(<AllPlayersAvailability />);

    await screen.findByText('Total Players');

    // Click Monday to expand
    const dayButtons = screen.getAllByRole('button');
    const mondayButton = dayButtons.find(btn => btn.textContent.includes('Mon'));
    fireEvent.click(mondayButton);

    // Check time formatting
    expect(screen.getByText(/9:00 AM - 5:00 PM/)).toBeInTheDocument();
    expect(screen.getByText(/10:00 AM - 3:00 PM/)).toBeInTheDocument();
  });

  test('displays player notes when available', async () => {
    fetch.mockResolvedValueOnce(createMockFetchResponse(mockPlayersData));

    render(<AllPlayersAvailability />);

    await screen.findByText('Total Players');

    // Click Monday to expand
    const dayButtons = screen.getAllByRole('button');
    const mondayButton = dayButtons.find(btn => btn.textContent.includes('Mon'));
    fireEvent.click(mondayButton);

    expect(screen.getByText('💬 Flexible schedule')).toBeInTheDocument();
  });

  test('handles empty availability data', async () => {
    fetch.mockResolvedValueOnce(createMockFetchResponse([]));

    render(<AllPlayersAvailability />);

    await screen.findByText('Total Players');

    // Statistics should show 0 total players
    const zeros = screen.getAllByText('0');
    expect(zeros.length).toBeGreaterThan(0);
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

    await screen.findByText('Total Players');

    expect(screen.getByText('Best Day')).toBeInTheDocument();
    expect(screen.getByText('Most Popular')).toBeInTheDocument();
  });

  test('closes detail panel when clicking close button', async () => {
    fetch.mockResolvedValueOnce(createMockFetchResponse(mockPlayersData));

    render(<AllPlayersAvailability />);

    await screen.findByText('Total Players');

    // Click Monday to expand
    const dayButtons = screen.getAllByRole('button');
    const mondayButton = dayButtons.find(btn => btn.textContent.includes('Mon'));
    fireEvent.click(mondayButton);

    expect(screen.getByText('Monday')).toBeInTheDocument();

    // Click close button
    const closeButton = screen.getByText('×');
    fireEvent.click(closeButton);

    // Panel should close - Monday heading should be gone
    expect(screen.queryByRole('heading', { name: 'Monday' })).not.toBeInTheDocument();
  });
});
