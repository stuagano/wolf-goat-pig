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

// Real Response so the typed client (openapi-fetch) can parse it.
const jsonResponse = (data) =>
  Promise.resolve(
    new Response(JSON.stringify(data), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }),
  );

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

    // The typed client calls fetch with a single Request object.
    fetch.mockImplementation(async (request) => {
      const url = request.url;
      if (url.includes('/pairings/')) {
        return jsonResponse({ exists: false });
      }

      if (url.includes('/signups/weekly-with-messages')) {
        return jsonResponse(weeklyResponse(createdSignup ? [createdSignup] : []));
      }

      if (url.endsWith('/signups') && request.method === 'POST') {
        const body = JSON.parse(await request.clone().text());
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
      expect(
        fetch.mock.calls.some(([req]) => req.url.endsWith('/signups') && req.method === 'POST'),
      ).toBe(true);
    });

    const signupRequest = fetch.mock.calls.find(
      ([req]) => req.url.endsWith('/signups') && req.method === 'POST',
    )[0];
    expect(JSON.parse(await signupRequest.clone().text())).toEqual(expectedSignupBody);
    expect(signupRequest.headers.get('Authorization')).toBe('Bearer signup-token');
    expect(signupRequest.headers.get('Content-Type')).toContain('application/json');

    expect(await screen.findByText('Stuart')).toBeInTheDocument();
    expect(screen.getByText('(you)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel My Signup' })).toBeInTheDocument();
  });

  test('requires a linked club player before signup', async () => {
    mockUsePlayerProfile.mockReturnValue({
      profile: { ...playerProfile, legacy_name: null },
      loading: false,
    });
    fetch.mockImplementation((request) => {
      const url = request.url;
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
