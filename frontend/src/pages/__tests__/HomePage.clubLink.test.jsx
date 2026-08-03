import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { useNavigate } from 'react-router-dom';
import usePlayerProfile from '../../hooks/usePlayerProfile';
import HomePage from '../HomePage';

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  useNavigate: vi.fn(),
}));

vi.mock('../../hooks/usePlayerProfile', () => ({
  default: vi.fn(),
}));

vi.mock('../../components/auth', () => ({
  LoginButton: () => null,
  AuthHealthCheck: () => null,
}));

vi.mock('../../components/game/StaleGameBanner', () => ({
  default: () => null,
}));

describe('HomePage club-player reminder', () => {
  const navigate = vi.fn();

  beforeEach(() => {
    useNavigate.mockReturnValue(navigate);
    useAuth0.mockReturnValue({
      isAuthenticated: true,
      user: { name: 'New Golfer' },
    });
    usePlayerProfile.mockReturnValue({
      profile: { id: 7, legacy_name: null },
      legacyNameSkipped: true,
    });
  });

  test('shows a contextual recovery action after onboarding is skipped', () => {
    render(<HomePage />);

    expect(screen.getByText(/Finish linking your club player/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Choose my player/i }));
    expect(navigate).toHaveBeenCalledWith('/account#club-player');
  });

  test('hides the reminder once the profile is linked', () => {
    usePlayerProfile.mockReturnValue({
      profile: { id: 7, legacy_name: 'New Golfer' },
      legacyNameSkipped: false,
    });

    render(<HomePage />);

    expect(screen.queryByText(/Finish linking your club player/i)).not.toBeInTheDocument();
  });
});
