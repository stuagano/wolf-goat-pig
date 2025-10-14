import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import PlayerAvailability from '../PlayerAvailability';
import { useAuth0 as mockUseAuth0 } from '@auth0/auth0-react';

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

const defaultAvailabilityResponse = () => Promise.resolve({
  ok: true,
  json: async () => []
});

describe('PlayerAvailability', () => {
  beforeEach(() => {
    fetch.mockReset();
    fetch.mockImplementation(defaultAvailabilityResponse);
    mockUseAuth0.mockReturnValue({
      user: { id: 'user123', name: 'Test User' },
      getAccessTokenSilently: jest.fn().mockResolvedValue('mock-token'),
      isAuthenticated: true
    });
  });

  test('renders loading state initially', () => {
    fetch.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<PlayerAvailability />);
    
    expect(screen.getByText(/Loading your availability settings/i)).toBeInTheDocument();
  });

  test('renders availability form after loading', async () => {
    fetch.mockImplementationOnce(() => Promise.resolve({
      ok: true,
      json: async () => mockAvailabilityData
    }));

    render(<PlayerAvailability />);

    await waitFor(() => {
      expect(screen.getByText('Monday')).toBeInTheDocument();
    });

    expect(screen.getByText('Tuesday')).toBeInTheDocument();
    expect(screen.getAllByLabelText(/Available to play/i).length).toBeGreaterThan(0);
  });

  test('shows correct initial state from API data', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAvailabilityData
    });

    render(<PlayerAvailability />);

    await waitFor(() => {
      expect(screen.getByText('Monday')).toBeInTheDocument();
    });

    // Monday should be checked (available)
    const mondayCheckbox = screen.getAllByLabelText(/Available to play/i)[0];
    expect(mondayCheckbox).toBeChecked();

    // Tuesday should not be checked
    const tuesdayCheckbox = screen.getAllByLabelText(/Available to play/i)[1];
    expect(tuesdayCheckbox).not.toBeChecked();
  });

  test('toggles availability when checkbox is clicked', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAvailabilityData
    });

    render(<PlayerAvailability />);

    await waitFor(() => {
      expect(screen.getByText('Monday')).toBeInTheDocument();
    });

    const tuesdayCheckbox = screen.getAllByLabelText(/Available to play/i)[1];
    fireEvent.click(tuesdayCheckbox);

    expect(tuesdayCheckbox).toBeChecked();
  });

  test('shows time selectors when available is checked', async () => {
    fetch.mockImplementationOnce(() => Promise.resolve({
      ok: true,
      json: async () => mockAvailabilityData
    }));

    render(<PlayerAvailability />);

    await waitFor(() => {
      expect(screen.getByText('Monday')).toBeInTheDocument();
    });

    expect(screen.getByText('Available from:')).toBeInTheDocument();
    expect(screen.getByText('Available until:')).toBeInTheDocument();
    expect(screen.getByText('Notes (optional):')).toBeInTheDocument();
  });

  test('saves availability when save button is clicked', async () => {
    fetch
      .mockImplementationOnce(() => Promise.resolve({
        ok: true,
        json: async () => mockAvailabilityData
      }))
      .mockImplementationOnce(() => Promise.resolve({
        ok: true,
        json: async () => ({ ...mockAvailabilityData[0], notes: 'Updated note' })
      }));

    render(<PlayerAvailability />);

    await waitFor(() => {
      expect(screen.getByText('Monday')).toBeInTheDocument();
    });

    // Find the Monday notes input and update it
    const notesInput = screen.getAllByPlaceholderText(/e.g., 'Only after work'/i)[0];
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
      .mockImplementationOnce(() => Promise.resolve({
        ok: true,
        json: async () => mockAvailabilityData
      }))
      .mockRejectedValueOnce(new Error('Save failed'));

    render(<PlayerAvailability />);

    await waitFor(() => {
      expect(screen.getByText('Monday')).toBeInTheDocument();
    });

    const saveButton = screen.getAllByText('Save')[0];
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/Failed to save Monday availability/i)).toBeInTheDocument();
    });
  });

  test('quick actions work correctly', async () => {
    fetch.mockImplementationOnce(() => Promise.resolve({
      ok: true,
      json: async () => []
    }));

    render(<PlayerAvailability />);

    await waitFor(() => {
      expect(screen.getByText('Quick Actions')).toBeInTheDocument();
    });

    // Test "Available Weekdays" button
    const weekdaysButton = screen.getByText('Available Weekdays');
    fireEvent.click(weekdaysButton);

    // Check that Monday-Friday checkboxes are now checked
    const checkboxes = screen.getAllByLabelText(/Available to play/i);
    expect(checkboxes[0]).toBeChecked(); // Monday
    expect(checkboxes[1]).toBeChecked(); // Tuesday
    expect(checkboxes[2]).toBeChecked(); // Wednesday
    expect(checkboxes[3]).toBeChecked(); // Thursday
    expect(checkboxes[4]).toBeChecked(); // Friday
    expect(checkboxes[5]).not.toBeChecked(); // Saturday
    expect(checkboxes[6]).not.toBeChecked(); // Sunday
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
      expect(screen.queryByText(/Loading your availability settings/i)).not.toBeInTheDocument();
    });
  });
});
