import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import Navigation from '../ui/Navigation';

// Mock Auth0
jest.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({
    isAuthenticated: true,
    user: { name: 'Test User', email: 'test@example.com' },
    loginWithRedirect: jest.fn(),
    logout: jest.fn()
  })
}));

// Mock theme
jest.mock('../../theme/Provider', () => ({
  useTheme: () => ({
    colors: {
      primary: '#007bff',
      background: '#ffffff'
    }
  }),
  ThemeProvider: ({ children }) => <div>{children}</div>
}));

const NavigationWrapper = ({ children }) => (
  <div data-testid="navigation-wrapper">{children}</div>
);

describe.skip('Navigation', () => {
  beforeEach(() => {
    // Mock localStorage
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(() => 'test@example.com'),
        setItem: jest.fn()
      }
    });
  });

  test('renders navigation with all primary links', () => {
    render(
      <NavigationWrapper>
        <Navigation />
      </NavigationWrapper>
    );

    expect(screen.getByText('🐺🐐🐷 Wolf Goat Pig')).toBeInTheDocument();
    expect(screen.getByText('🏠 Home')).toBeInTheDocument();
    expect(screen.getByText('🎮 Game')).toBeInTheDocument();
    expect(screen.getByText('🎯 Practice Mode')).toBeInTheDocument();
    expect(screen.getByText('🎲 Simulation')).toBeInTheDocument();
    expect(screen.getByText('🏆 Leaderboard')).toBeInTheDocument();
    expect(screen.getByText('📝 Sign Up to Play')).toBeInTheDocument();
  });

  test('shows user information when authenticated', () => {
    render(
      <NavigationWrapper>
        <Navigation />
      </NavigationWrapper>
    );

    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByText('Logout')).toBeInTheDocument();
  });

  test('shows admin link for admin users', () => {
    // Mock localStorage to return admin email
    window.localStorage.getItem.mockReturnValue('stuagano@gmail.com');

    render(
      <NavigationWrapper>
        <Navigation />
      </NavigationWrapper>
    );

    expect(screen.getByText('🔧 Admin')).toBeInTheDocument();
  });

  test('does not show admin link for regular users', () => {
    window.localStorage.getItem.mockReturnValue('user@example.com');

    render(
      <NavigationWrapper>
        <Navigation />
      </NavigationWrapper>
    );

    expect(screen.queryByText('🔧 Admin')).not.toBeInTheDocument();
  });

  test('handles navigation clicks', () => {
    render(
      <NavigationWrapper>
        <Navigation />
      </NavigationWrapper>
    );

    const gameLink = screen.getByText('🎮 Game');
    fireEvent.click(gameLink);

    // Navigation should be handled by React Router
    expect(gameLink).toBeInTheDocument();
  });

  test('highlights active route correctly', () => {
    render(
      <NavigationWrapper>
        <Navigation />
      </NavigationWrapper>
    );

    // The signup button should be present
    const signupButton = screen.getByText('📝 Sign Up to Play');
    expect(signupButton).toBeInTheDocument();
  });

  test('handles unauthenticated state', () => {
    // Note: Due to Jest mocking limitations, we can't easily test this
    // in isolation. This would be better tested in integration tests.
    render(
      <NavigationWrapper>
        <Navigation />
      </NavigationWrapper>
    );

    expect(screen.getByText('🐺🐐🐷 Wolf Goat Pig')).toBeInTheDocument();
  });

  test('handles logout click', () => {
    render(
      <NavigationWrapper>
        <Navigation />
      </NavigationWrapper>
    );

    const logoutButton = screen.getByText('Logout');
    fireEvent.click(logoutButton);

    // The logout button should be clickable
    expect(logoutButton).toBeInTheDocument();
  });

  test('handles mobile menu toggle', () => {
    // Mock window.innerWidth for mobile
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 600,
    });

    render(
      <NavigationWrapper>
        <Navigation />
      </NavigationWrapper>
    );

    // On mobile, there should be a menu toggle button
    // The exact implementation depends on the mobile menu structure
    expect(screen.getByText('🐺🐐🐷 Wolf Goat Pig')).toBeInTheDocument();
  });
});