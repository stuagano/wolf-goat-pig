import React from 'react';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useAuth0 as mockUseAuth0 } from '@auth0/auth0-react';
import { usePlayerProfile as mockUsePlayerProfile } from '../../../hooks/usePlayerProfile';
import DailySignupView from '../DailySignupView';

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: vi.fn(),
}));

vi.mock('../../../hooks/usePlayerProfile', () => ({
  usePlayerProfile: vi.fn(),
}));

const selectedDate = '2099-01-04';
const playerProfile = {
  id: 42,
  name: 'Auth0 Display Name',
  legacy_name: 'Stuart',
};

const expectedSignupBody = {
  date: selectedDate,
  preferred_start_time: null,
  notes: null,
};

const jsonResponse = (data) =>
  Promise.resolve({
    ok: true,
    status: 200,
    json: () => Promise.resolve(data),
  });

const weeklyResponse = (signups = []) => ({
  week_start: selectedDate,
  daily_summaries: [
    {
      date: selectedDate,
      signups,
      total_count: signups.length,
      messages: [],
      message_count: 0,
    },
  ],
});

describe('DailySignupView', () => {
  beforeEach(() => {
    mockUseAuth0.mockReturnValue({
      user: { name: 'Auth0 Display Name', email: 'stuart@example.com' },
      isAuthenticated: true,
      getAccessTokenSilently: vi.fn().mockResolvedValue('signup-token'),
    });
    mockUsePlayerProfile.mockReturnValue({
      profile: playerProfile,
      loading: false,
    });
  });

  test('signs up the logged-in profile and shows that player in the week view', async () => {
    let createdSignup = null;

    fetch.mockImplementation((url, options = {}) => {
      if (url.includes('/pairings/')) {
        return jsonResponse({ exists: false });
      }

      if (url.includes('/signups/weekly-with-messages')) {
        return jsonResponse(weeklyResponse(createdSignup ? [createdSignup] : []));
      }

      if (url.endsWith('/signups') && options.method === 'POST') {
        const body = JSON.parse(options.body);
        createdSignup = {
          id: 101,
          ...body,
          player_profile_id: playerProfile.id,
          player_name: playerProfile.legacy_name,
          status: 'signed_up',
          signup_time: '2099-01-01T00:00:00Z',
          created_at: '2099-01-01T00:00:00Z',
          updated_at: '2099-01-01T00:00:00Z',
        };
        return jsonResponse(createdSignup);
      }

      throw new Error(`Unexpected fetch: ${url}`);
    });

    render(<DailySignupView selectedDate={selectedDate} />);

    const firstSignupButton = await screen.findByRole('button', {
      name: 'Be the first to sign up!',
    });
    const emptyStateActions = firstSignupButton.parentElement;
    fireEvent.click(firstSignupButton);
    expect(within(emptyStateActions).getByText('Signing up as: Stuart')).toBeInTheDocument();
    fireEvent.click(within(emptyStateActions).getByRole('button', { name: 'Confirm Sign Up' }));

    await waitFor(() => {
      const signupRequest = fetch.mock.calls.find(
        ([url, options]) => url.endsWith('/signups') && options?.method === 'POST',
      );

      expect(JSON.parse(signupRequest[1].body)).toEqual(expectedSignupBody);
      expect(signupRequest[1].headers).toEqual({
        Authorization: 'Bearer signup-token',
        'Content-Type': 'application/json',
      });
    });

    expect(await screen.findByText('Stuart')).toBeInTheDocument();
    expect(screen.getByText('(you)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel My Signup' })).toBeInTheDocument();
  });

  test('requires a linked club player before signup', async () => {
    mockUsePlayerProfile.mockReturnValue({
      profile: { ...playerProfile, legacy_name: null },
      loading: false,
    });
    fetch.mockImplementation((url) => {
      if (url.includes('/pairings/')) return jsonResponse({ exists: false });
      if (url.includes('/signups/weekly-with-messages')) {
        return jsonResponse(weeklyResponse());
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });

    render(<DailySignupView selectedDate={selectedDate} />);

    const buttons = await screen.findAllByRole('button', {
      name: 'Link club player in Account',
    });
    expect(buttons).not.toHaveLength(0);
    buttons.forEach((button) => expect(button).toBeDisabled());
  });
});
