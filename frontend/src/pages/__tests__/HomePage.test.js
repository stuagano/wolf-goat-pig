/**
 * HomePage Component Tests
 * Tests the main landing page functionality
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import HomePage from '../HomePage';
import { ThemeProvider } from '../../theme/Provider';
import { AuthProvider } from '../../context/AuthContext';

// Mock the navigation hook
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Mock Auth0
jest.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({
    isAuthenticated: false,
    loginWithRedirect: jest.fn(),
    user: null,
    isLoading: false,
  }),
}));

const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <ThemeProvider>
      <AuthProvider>
        {children}
      </AuthProvider>
    </ThemeProvider>
  </BrowserRouter>
);

describe('HomePage', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  test('renders homepage with welcome content', () => {
    render(
      <TestWrapper>
        <HomePage />
      </TestWrapper>
    );

    // Check for main heading
    expect(screen.getByText(/wolf goat pig/i)).toBeInTheDocument();
    
    // Check for description or subtitle
    expect(screen.getByText(/golf.*game/i)).toBeInTheDocument();
  });

  test('displays navigation options', () => {
    render(
      <TestWrapper>
        <HomePage />
      </TestWrapper>
    );

    // Look for common navigation elements
    const startGameButton = screen.getByRole('button', { name: /start.*game/i });
    expect(startGameButton).toBeInTheDocument();
  });

  test('handles start game button click', () => {
    render(
      <TestWrapper>
        <HomePage />
      </TestWrapper>
    );

    const startGameButton = screen.getByRole('button', { name: /start.*game/i });
    fireEvent.click(startGameButton);

    // Should navigate to game page
    expect(mockNavigate).toHaveBeenCalledWith('/game');
  });

  test('displays other action buttons', () => {
    render(
      <TestWrapper>
        <HomePage />
      </TestWrapper>
    );

    // Check for tutorial or practice buttons
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThan(1);
  });

  test('shows appropriate content for unauthenticated users', () => {
    render(
      <TestWrapper>
        <HomePage />
      </TestWrapper>
    );

    // Should show login or getting started information
    expect(screen.getByText(/wolf goat pig/i)).toBeInTheDocument();
  });

  test('renders without crashing', () => {
    expect(() => {
      render(
        <TestWrapper>
          <HomePage />
        </TestWrapper>
      );
    }).not.toThrow();
  });

  test('has accessible content', () => {
    render(
      <TestWrapper>
        <HomePage />
      </TestWrapper>
    );

    // Check for proper heading hierarchy
    const mainHeading = screen.getByRole('heading', { level: 1 });
    expect(mainHeading).toBeInTheDocument();
  });
});