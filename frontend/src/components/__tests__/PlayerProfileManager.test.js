import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

import { ThemeProvider } from '../../theme/Provider';
import PlayerProfileManager from '../PlayerProfileManager';

global.fetch = jest.fn();
global.confirm = jest.fn();

const mockProfiles = [
  {
    id: '1',
    name: 'Alice Johnson',
    handicap: 8.5,
    last_played: '2024-01-15T10:30:00Z'
  },
  {
    id: '2',
    name: 'Bob Smith',
    handicap: 18,
    last_played: null
  },
  {
    id: '3',
    name: 'Carol Davis',
    handicap: 25.5,
    last_played: '2024-01-14T12:00:00Z'
  }
];

const TestWrapper = ({ children }) => (
  <ThemeProvider>
    {children}
  </ThemeProvider>
);

const defaultProfilesResponse = () =>
  Promise.resolve({
    ok: true,
    json: async () => mockProfiles
  });

describe('PlayerProfileManager', () => {
  let mockOnProfileSelect;

  const renderManager = () => {
    render(
      <TestWrapper>
        <PlayerProfileManager onProfileSelect={mockOnProfileSelect} />
      </TestWrapper>
    );
  };

  beforeEach(() => {
    mockOnProfileSelect = jest.fn();
    fetch.mockReset();
    fetch.mockImplementation(defaultProfilesResponse);
    confirm.mockReset();
  });

  test('renders profiles after successful load', async () => {
    renderManager();

    expect(await screen.findByText('Player Profiles')).toBeInTheDocument();
    expect(screen.getByText('All Profiles (3)')).toBeInTheDocument();
    expect(screen.getAllByText('Alice Johnson').length).toBeGreaterThan(0);
  });

  test('invokes onProfileSelect when profile card clicked', async () => {
    const user = userEvent.setup();
    renderManager();

    const aliceCards = await screen.findAllByText('Alice Johnson');
    await user.click(aliceCards[0]);

    expect(mockOnProfileSelect).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'Alice Johnson' })
    );
  });

  test('shows error banner when loading fails', async () => {
    fetch.mockImplementationOnce(() => Promise.reject(new Error('Network error')));

    renderManager();

    expect(
      await screen.findByText(/Failed to load profiles: Network error/)
    ).toBeInTheDocument();
  });

  test('handles null or malformed profiles gracefully', async () => {
    fetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: async () => [null, { id: null, name: 'Mystery Player', handicap: null }]
      })
    );

    renderManager();

    expect(await screen.findByText('Player Profiles')).toBeInTheDocument();
    expect(screen.getAllByText(/Mystery Player|Player 2/).length).toBeGreaterThan(0);
  });
});
