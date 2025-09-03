/**
 * SetupPage Component Tests
 * Tests the game setup and configuration page
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import SetupPage from '../SetupPage';
import { ThemeProvider } from '../../theme/Provider';
import { GameProvider } from '../../context/GameProvider';

// Mock API calls
global.fetch = jest.fn();

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <ThemeProvider>
      <GameProvider>
        {children}
      </GameProvider>
    </ThemeProvider>
  </BrowserRouter>
);

describe('SetupPage', () => {
  beforeEach(() => {
    fetch.mockClear();
    mockNavigate.mockClear();
    
    // Mock successful course fetch
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        'Wing Point Golf & Country Club': {
          name: 'Wing Point Golf & Country Club',
          holes: [],
          total_par: 72
        }
      }),
    });
  });

  test('renders setup page with form elements', () => {
    render(
      <TestWrapper>
        <SetupPage />
      </TestWrapper>
    );

    // Should have page title
    expect(screen.getByRole('heading', { name: /setup/i })).toBeInTheDocument();
    
    // Should have player setup section
    expect(screen.getByText(/players/i)).toBeInTheDocument();
  });

  test('displays player input fields', () => {
    render(
      <TestWrapper>
        <SetupPage />
      </TestWrapper>
    );

    // Should have input fields for player names
    const playerInputs = screen.getAllByLabelText(/player.*name/i);
    expect(playerInputs.length).toBeGreaterThanOrEqual(4);
    
    // Should have handicap inputs
    const handicapInputs = screen.getAllByLabelText(/handicap/i);
    expect(handicapInputs.length).toBeGreaterThanOrEqual(4);
  });

  test('allows entering player information', () => {
    render(
      <TestWrapper>
        <SetupPage />
      </TestWrapper>
    );

    const firstPlayerInput = screen.getByLabelText(/player 1.*name/i);
    fireEvent.change(firstPlayerInput, { target: { value: 'John Doe' } });
    
    expect(firstPlayerInput.value).toBe('John Doe');
  });

  test('displays course selection dropdown', async () => {
    render(
      <TestWrapper>
        <SetupPage />
      </TestWrapper>
    );

    await waitFor(() => {
      const courseSelect = screen.getByLabelText(/course/i);
      expect(courseSelect).toBeInTheDocument();
    });
  });

  test('loads available courses', async () => {
    render(
      <TestWrapper>
        <SetupPage />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/courses'),
        expect.any(Object)
      );
    });
  });

  test('validates required player information', () => {
    render(
      <TestWrapper>
        <SetupPage />
      </TestWrapper>
    );

    const startButton = screen.getByRole('button', { name: /start.*game/i });
    fireEvent.click(startButton);

    // Should show validation errors for empty fields
    expect(screen.getByText(/required/i)).toBeInTheDocument();
  });

  test('handles game creation with valid data', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        success: true,
        game_id: 'test-game-123'
      }),
    });

    render(
      <TestWrapper>
        <SetupPage />
      </TestWrapper>
    );

    // Fill in player information
    const player1Input = screen.getByLabelText(/player 1.*name/i);
    const handicap1Input = screen.getByLabelText(/player 1.*handicap/i);
    
    fireEvent.change(player1Input, { target: { value: 'John' } });
    fireEvent.change(handicap1Input, { target: { value: '12' } });

    const startButton = screen.getByRole('button', { name: /start.*game/i });
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/game');
    });
  });

  test('shows error message on setup failure', async () => {
    fetch.mockRejectedValueOnce(new Error('Setup failed'));

    render(
      <TestWrapper>
        <SetupPage />
      </TestWrapper>
    );

    const startButton = screen.getByRole('button', { name: /start.*game/i });
    fireEvent.click(startButton);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  test('allows selecting different game modes', () => {
    render(
      <TestWrapper>
        <SetupPage />
      </TestWrapper>
    );

    // Should have options for different game types
    const gameModeSelect = screen.getByLabelText(/game.*mode/i);
    expect(gameModeSelect).toBeInTheDocument();
    
    // Should have options for 4-man, 5-man, 6-man
    expect(screen.getByText(/4.*man/i)).toBeInTheDocument();
  });

  test('handles handicap validation', () => {
    render(
      <TestWrapper>
        <SetupPage />
      </TestWrapper>
    );

    const handicapInput = screen.getByLabelText(/player 1.*handicap/i);
    
    // Test invalid handicap (negative)
    fireEvent.change(handicapInput, { target: { value: '-5' } });
    fireEvent.blur(handicapInput);
    
    expect(screen.getByText(/invalid.*handicap/i)).toBeInTheDocument();
  });

  test('shows advanced options when expanded', () => {
    render(
      <TestWrapper>
        <SetupPage />
      </TestWrapper>
    );

    const advancedButton = screen.getByRole('button', { name: /advanced/i });
    fireEvent.click(advancedButton);

    // Should show additional options
    expect(screen.getByText(/starting.*hole/i)).toBeInTheDocument();
  });

  test('preserves form data during validation', () => {
    render(
      <TestWrapper>
        <SetupPage />
      </TestWrapper>
    );

    const playerInput = screen.getByLabelText(/player 1.*name/i);
    fireEvent.change(playerInput, { target: { value: 'Test Player' } });

    const startButton = screen.getByRole('button', { name: /start.*game/i });
    fireEvent.click(startButton);

    // Form data should still be there after validation
    expect(playerInput.value).toBe('Test Player');
  });
});