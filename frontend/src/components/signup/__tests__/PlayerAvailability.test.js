import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import PlayerAvailability from '../PlayerAvailability';
import { useAuth0 as mockUseAuth0 } from '@auth0/auth0-react';
import { createMockFetchResponse, createMockUser } from '../../../test-utils/mockFactories';

// Mock Auth0
jest.mock('@auth0/auth0-react', () => ({
  useAuth0: jest.fn()
}));

// Mock fetch
global.fetch = jest.fn();

const mockAvailabilityData = [
  {
    id: 1,
    day_of_week: 0,
    is_available: true,
    available_from_time: "9:00 AM",
    available_to_time: "5:00 PM",
    notes: "Flexible"
  },
  {
    id: 2,
    day_of_week: 1,
    is_available: false,
    available_from_time: null,
    available_to_time: null,
    notes: ""
  }
];

const defaultAvailabilityResponse = () => createMockFetchResponse([]);

describe('PlayerAvailability', () => {
  beforeEach(() => {
    fetch.mockReset();
    fetch.mockImplementation(defaultAvailabilityResponse);
    mockUseAuth0.mockReturnValue({
      user: createMockUser({ id: 'user123', name: 'Test User' }),
      getAccessTokenSilently: jest.fn().mockResolvedValue('mock-token'),
      isAuthenticated: true
    });
  });

  test('renders loading state initially', () => {
    fetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<PlayerAvailability />);

    expect(screen.getByText(/Loading.../i)).toBeInTheDocument();
  });

  test('renders day grid after loading', async () => {
    fetch.mockImplementationOnce(() => createMockFetchResponse(mockAvailabilityData));

    render(<PlayerAvailability />);

    await waitFor(() => {
      expect(screen.getByText('Mon')).toBeInTheDocument();
    });

    expect(screen.getByText('Tue')).toBeInTheDocument();
    expect(screen.getByText('Wed')).toBeInTheDocument();
    expect(screen.getByText('Thu')).toBeInTheDocument();
    expect(screen.getByText('Fri')).toBeInTheDocument();
    expect(screen.getByText('Sat')).toBeInTheDocument();
    expect(screen.getByText('Sun')).toBeInTheDocument();
  });

  test('shows correct initial state from API data', async () => {
    fetch.mockResolvedValueOnce(createMockFetchResponse(mockAvailabilityData));

    render(<PlayerAvailability />);

    await waitFor(() => {
      expect(screen.getByText('Mon')).toBeInTheDocument();
    });

    // Monday should show as available (checkmark)
    const dayButtons = screen.getAllByRole('button');
    const mondayButton = dayButtons.find(btn => btn.textContent.includes('Mon'));
    expect(mondayButton.textContent).toContain('✓');
    expect(mondayButton.textContent).toContain('Available');

    // Tuesday should show as off
    const tuesdayButton = dayButtons.find(btn => btn.textContent.includes('Tue'));
    expect(tuesdayButton.textContent).toContain('Off');
  });

  test('toggles availability when day button is clicked', async () => {
    fetch.mockResolvedValueOnce(createMockFetchResponse(mockAvailabilityData));

    render(<PlayerAvailability />);

    await waitFor(() => {
      expect(screen.getByText('Mon')).toBeInTheDocument();
    });

    // Click Tuesday to toggle it on
    const dayButtons = screen.getAllByRole('button');
    const tuesdayButton = dayButtons.find(btn => btn.textContent.includes('Tue') && btn.textContent.includes('Off'));
    fireEvent.click(tuesdayButton);

    // Tuesday should now show as available
    await waitFor(() => {
      expect(tuesdayButton.textContent).toContain('Available');
    });
  });

  test('shows time selectors when day is available', async () => {
    fetch.mockImplementationOnce(() => createMockFetchResponse(mockAvailabilityData));

    render(<PlayerAvailability />);

    await waitFor(() => {
      expect(screen.getByText('Mon')).toBeInTheDocument();
    });

    // Monday is available, so detail card should show
    expect(screen.getByText('Monday')).toBeInTheDocument();
    expect(screen.getByText('From')).toBeInTheDocument();
    expect(screen.getByText('Until')).toBeInTheDocument();
    expect(screen.getByText('Notes')).toBeInTheDocument();
  });

  test('saves availability when save button is clicked', async () => {
    fetch
      .mockImplementationOnce(() => createMockFetchResponse(mockAvailabilityData))
      .mockImplementationOnce(() => createMockFetchResponse({ ...mockAvailabilityData[0], notes: 'Updated note' }));

    render(<PlayerAvailability />);

    await waitFor(() => {
      expect(screen.getByText('Monday')).toBeInTheDocument();
    });

    // Find the Monday notes input and update it
    const notesInput = screen.getAllByPlaceholderText(/Prefer mornings/i)[0];
    fireEvent.change(notesInput, { target: { value: 'Updated note' } });

    // Click save button for Monday
    const saveButton = screen.getAllByText('Save')[0];
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/players/me/availability'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer mock-token'
          }),
          body: expect.stringContaining('Updated note')
        })
      );
    });
  });

  test('handles save errors', async () => {
    fetch
      .mockImplementationOnce(() => createMockFetchResponse(mockAvailabilityData))
      .mockRejectedValueOnce(new Error('Save failed'));

    render(<PlayerAvailability />);

    await waitFor(() => {
      expect(screen.getByText('Monday')).toBeInTheDocument();
    });

    const saveButton = screen.getAllByText('Save')[0];
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/Failed to save Monday/i)).toBeInTheDocument();
    });
  });

  test('quick preset buttons work correctly', async () => {
    fetch.mockImplementationOnce(() => createMockFetchResponse([]));

    render(<PlayerAvailability />);

    await waitFor(() => {
      expect(screen.getByText('Mon')).toBeInTheDocument();
    });

    // Test "Weekdays" button
    const weekdaysButton = screen.getByText('Weekdays');
    fireEvent.click(weekdaysButton);

    // Check that Monday-Friday buttons show as available
    const dayButtons = screen.getAllByRole('button');
    const mondayButton = dayButtons.find(btn => btn.textContent.includes('Mon'));
    const saturdayButton = dayButtons.find(btn => btn.textContent.includes('Sat'));

    await waitFor(() => {
      expect(mondayButton.textContent).toContain('Available');
      expect(saturdayButton.textContent).toContain('Off');
    });
  });

  test('handles unauthenticated user', async () => {
    // Mock unauthenticated state
    mockUseAuth0.mockReturnValue({
      user: null,
      getAccessTokenSilently: jest.fn(),
      isAuthenticated: false
    });

    render(<PlayerAvailability />);

    // Should not show loading indefinitely
    await waitFor(() => {
      expect(screen.queryByText(/Loading.../i)).not.toBeInTheDocument();
    });
  });

  test('All Days preset marks all days available', async () => {
    fetch.mockImplementationOnce(() => createMockFetchResponse([]));

    render(<PlayerAvailability />);

    await waitFor(() => {
      expect(screen.getByText('Mon')).toBeInTheDocument();
    });

    // Click "All Days" preset
    const allDaysButton = screen.getByText('All Days');
    fireEvent.click(allDaysButton);

    // All days should now show as available
    const dayButtons = screen.getAllByRole('button');
    const availableButtons = dayButtons.filter(btn => btn.textContent.includes('Available'));
    expect(availableButtons.length).toBe(7);
  });

  test('Clear preset removes all availability', async () => {
    fetch.mockImplementationOnce(() => createMockFetchResponse(mockAvailabilityData));

    render(<PlayerAvailability />);

    await waitFor(() => {
      expect(screen.getByText('Monday')).toBeInTheDocument();
    });

    // Click "Clear" preset
    const clearButton = screen.getByText('Clear');
    fireEvent.click(clearButton);

    // No day detail cards should be visible
    await waitFor(() => {
      expect(screen.queryByText('Monday')).not.toBeInTheDocument();
    });
  });
});
