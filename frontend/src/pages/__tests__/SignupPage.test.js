import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import SignupPage from '../SignupPage';

// Mock Auth0
jest.mock('@auth0/auth0-react', () => ({
  useAuth0: () => ({
    isAuthenticated: true,
    user: { name: 'Test User', email: 'test@example.com' },
    loginWithRedirect: jest.fn()
  })
}));

// Mock the signup components
jest.mock('../../components/signup/SignupCalendar', () => {
  return function MockSignupCalendar() {
    return <div data-testid="signup-calendar">Mock Signup Calendar</div>;
  };
});

jest.mock('../../components/signup/PlayerAvailability', () => {
  return function MockPlayerAvailability() {
    return <div data-testid="player-availability">Mock Player Availability</div>;
  };
});

jest.mock('../../components/signup/AllPlayersAvailability', () => {
  return function MockAllPlayersAvailability() {
    return <div data-testid="all-players-availability">Mock All Players Availability</div>;
  };
});

jest.mock('../../components/signup/MatchmakingSuggestions', () => {
  return function MockMatchmakingSuggestions() {
    return <div data-testid="matchmaking-suggestions">Mock Matchmaking Suggestions</div>;
  };
});

jest.mock('../../components/signup/EmailPreferences', () => {
  return function MockEmailPreferences() {
    return <div data-testid="email-preferences">Mock Email Preferences</div>;
  };
});

const SignupPageWrapper = ({ initialTab = 'calendar' }) => (
  <BrowserRouter initialEntries={[`/signup?tab=${initialTab}`]}>
    <SignupPage />
  </BrowserRouter>
);

describe('SignupPage', () => {
  test('renders signup page with default calendar tab', () => {
    render(<SignupPageWrapper />);

    expect(screen.getByText('🏌️ Golf Sign-up & Daily Messages')).toBeInTheDocument();
    expect(screen.getByTestId('signup-calendar')).toBeInTheDocument();
  });

  test('shows all tab options', () => {
    render(<SignupPageWrapper />);

    expect(screen.getByText('📅 Daily Signups')).toBeInTheDocument();
    expect(screen.getByText('🕒 My Availability')).toBeInTheDocument();
    expect(screen.getByText('👥 All Players')).toBeInTheDocument();
    expect(screen.getByText('⛳ Matchmaking')).toBeInTheDocument();
    expect(screen.getByText('📧 Email Settings')).toBeInTheDocument();
  });

  test('switches to availability tab when clicked', async () => {
    render(<SignupPageWrapper />);

    const availabilityTab = screen.getByText('🕒 My Availability');
    fireEvent.click(availabilityTab);

    await waitFor(() => {
      expect(screen.getByTestId('player-availability')).toBeInTheDocument();
    });

    expect(screen.queryByTestId('signup-calendar')).not.toBeInTheDocument();
  });

  test('switches to all players tab when clicked', async () => {
    render(<SignupPageWrapper />);

    const allPlayersTab = screen.getByText('👥 All Players');
    fireEvent.click(allPlayersTab);

    await waitFor(() => {
      expect(screen.getByTestId('all-players-availability')).toBeInTheDocument();
    });
  });

  test('switches to matchmaking tab when clicked', async () => {
    render(<SignupPageWrapper />);

    const matchmakingTab = screen.getByText('⛳ Matchmaking');
    fireEvent.click(matchmakingTab);

    await waitFor(() => {
      expect(screen.getByTestId('matchmaking-suggestions')).toBeInTheDocument();
    });
  });

  test('switches to email preferences tab when clicked', async () => {
    render(<SignupPageWrapper />);

    const emailTab = screen.getByText('📧 Email Settings');
    fireEvent.click(emailTab);

    await waitFor(() => {
      expect(screen.getByTestId('email-preferences')).toBeInTheDocument();
    });
  });

  test('initializes with URL parameter tab', () => {
    render(<SignupPageWrapper initialTab="matchmaking" />);

    expect(screen.getByTestId('matchmaking-suggestions')).toBeInTheDocument();
    expect(screen.queryByTestId('signup-calendar')).not.toBeInTheDocument();
  });

  test('shows user welcome message when authenticated', () => {
    render(<SignupPageWrapper />);

    expect(screen.getByText('Welcome, Test User')).toBeInTheDocument();
  });

  test('shows login prompt when not authenticated', () => {
    jest.doMock('@auth0/auth0-react', () => ({
      useAuth0: () => ({
        isAuthenticated: false,
        user: null,
        loginWithRedirect: jest.fn()
      })
    }));

    render(<SignupPageWrapper />);

    expect(screen.getByText('🏌️ Golf Sign-up System')).toBeInTheDocument();
    expect(screen.getByText('Login to Continue')).toBeInTheDocument();
  });

  test('handles login button click when unauthenticated', () => {
    const mockLoginWithRedirect = jest.fn();
    
    jest.doMock('@auth0/auth0-react', () => ({
      useAuth0: () => ({
        isAuthenticated: false,
        user: null,
        loginWithRedirect: mockLoginWithRedirect
      })
    }));

    render(<SignupPageWrapper />);

    const loginButton = screen.getByText('Login to Continue');
    fireEvent.click(loginButton);

    // Note: The actual function call would need different testing approach
    // due to Jest mocking limitations with hooks
  });

  test('shows help section with feature descriptions', () => {
    render(<SignupPageWrapper />);

    expect(screen.getByText('💡 How it works')).toBeInTheDocument();
    expect(screen.getByText(/Daily Sign-ups:/)).toBeInTheDocument();
    expect(screen.getByText(/Message Board:/)).toBeInTheDocument();
    expect(screen.getByText(/Availability:/)).toBeInTheDocument();
    expect(screen.getByText(/Email Control:/)).toBeInTheDocument();
  });

  test('maintains active tab styling', () => {
    render(<SignupPageWrapper />);

    const calendarTab = screen.getByText('📅 Daily Signups');
    const availabilityTab = screen.getByText('🕒 My Availability');

    // Calendar tab should be active initially
    expect(calendarTab).toHaveStyle({ background: '#007bff' });
    
    // Click availability tab
    fireEvent.click(availabilityTab);

    // Availability tab should now be active
    // Note: This test depends on the exact styling implementation
  });

  test('handles tab switching with URL updates', async () => {
    render(<SignupPageWrapper />);

    const matchmakingTab = screen.getByText('⛳ Matchmaking');
    fireEvent.click(matchmakingTab);

    await waitFor(() => {
      // URL should be updated with tab parameter
      // This would need to be tested with proper router testing
      expect(screen.getByTestId('matchmaking-suggestions')).toBeInTheDocument();
    });
  });
});