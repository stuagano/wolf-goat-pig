import React from 'react';
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useAuth0 as mockUseAuth0 } from '@auth0/auth0-react';
import { usePlayerProfile as mockUsePlayerProfile } from '../../../hooks/usePlayerProfile';
import DailySignupView from '../DailySignupView';

const mockNavigate = vi.fn();

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: vi.fn(),
}));

vi.mock('react-router-dom', () => ({
  useNavigate: () => mockNavigate,
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
  afterEach(() => vi.useRealTimers());

  test('hides past club days and prevents navigating back into them', async () => {
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(new Date('2026-10-10T03:00:00Z'));
    fetch.mockImplementation((request) => jsonResponse(
      request.url.includes('/pairings/') ? { exists: false } : { daily_summaries: [] }
    ));
    render(<DailySignupView selectedDate="2026-10-04" />);
    expect(await screen.findByRole('button', { name: 'Fri' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sat' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Sun' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Thu' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Previous Week' })).toBeDisabled();
    expect(screen.getByText('Fri - Sat: Oct 9 - Oct 10')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Signed up for Friday, October 9' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Sat' }));
    fireEvent.click(screen.getByRole('button', { name: 'Next Week' }));
    expect(await screen.findByRole('heading', { name: 'Signed up for Saturday, October 17' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Sun' }));
    fireEvent.click(screen.getByRole('button', { name: 'Previous Week' }));
    expect(await screen.findByRole('heading', { name: 'Signed up for Friday, October 9' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Previous Week' })).toBeDisabled();
  });

  test.each(['2026-10-09T17:00:00', '2026-10-09T17:00:00Z', '2026-10-09T10:00:00-07:00'])('shows the original signup time %s after editing a note', async (signupTime) => {
    let notes = null;
    fetch.mockImplementation(async (request) => {
      if (request.method === 'PUT') {
        notes = JSON.parse(await request.clone().text()).notes;
        return jsonResponse({});
      }
      if (request.url.includes('/pairings/')) return jsonResponse({ exists: false });
      return jsonResponse(weeklyResponse([{
        id: 101, player_profile_id: playerProfile.id, player_name: 'Stuart',
        signup_time: signupTime, notes, status: 'signed_up',
      }]));
    });
    render(<DailySignupView selectedDate={selectedDate} />);
    const timestamp = await screen.findByText(/Signed up Oct 9, 2026, 10:00:00 AM PDT/);
    const expectedTimestamp = signupTime === '2026-10-09T17:00:00' ? `${signupTime}Z` : signupTime;
    expect(timestamp).toHaveAttribute('datetime', expectedTimestamp);
    fireEvent.click(screen.getByText('Add a note…'));
    const input = screen.getByPlaceholderText('Add a note…');
    fireEvent.change(input, { target: { value: 'Can play early' } });
    fireEvent.blur(input);
    expect(await screen.findByText('Can play early')).toBeInTheDocument();
    expect(screen.getByText(/Signed up Oct 9, 2026, 10:00:00 AM PDT/)).toHaveAttribute('datetime', expectedTimestamp);
  });

  beforeEach(() => {
    mockNavigate.mockReset();
    mockUseAuth0.mockReturnValue({
      user: { name: 'Auth0 Display Name', email: 'stuart@example.com' },
      isAuthenticated: true,
      getAccessTokenSilently: vi.fn().mockResolvedValue('signup-token'),
    });
    mockUsePlayerProfile.mockReturnValue({
      profile: { ...playerProfile, is_admin: false },
      loading: false,
      isAdmin: false,
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
    expect(screen.queryByRole('button', { name: 'Generate pairings' })).not.toBeInTheDocument();
  });

  test.each([false, true])('leaves pairings to the in-person group for admin=%s', async (isAdmin) => {
    mockUsePlayerProfile.mockReturnValue({ profile: playerProfile, loading: false, isAdmin });
    fetch.mockImplementation((request) => {
      if (request.url.includes('/signups/weekly-with-messages')) return jsonResponse(weeklyResponse());
      if (request.url.endsWith('/signups/admin/players')) return jsonResponse({ players: [] });
      if (request.url.includes('/pairings/')) return jsonResponse({
        exists: true, pairings: { teams: [{ players: [{ player_name: 'Generated Player' }] }] },
      });
      throw new Error(`Unexpected fetch: ${request.url}`);
    });
    render(<DailySignupView selectedDate={selectedDate} />);
    expect(await screen.findByText('Pairings will be arranged in person.')).toBeInTheDocument();
    expect(screen.queryByText('Official Pairings')).not.toBeInTheDocument();
    expect(screen.queryByText('Generated Player')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Generate pairings|Overwrite pairings/ })).not.toBeInTheDocument();
    expect(fetch.mock.calls.some(([request]) => request.url.includes('/pairings/'))).toBe(false);
    if (isAdmin) expect(screen.getByLabelText('Add a player')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Be the first to sign up!' })).toBeEnabled();
  });

  test('unlinked player can sign up using their display name without being blocked', async () => {
    mockUsePlayerProfile.mockReturnValue({
      profile: { ...playerProfile, legacy_name: null, name: 'Kevin Gent' },
      loading: false,
      legacyNameSkipped: true,
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

    // No blocking banner
    await waitFor(() => {
      expect(screen.queryByText(/Link your club player before signing up/i)).not.toBeInTheDocument();
    });

    // Signup buttons are present and enabled, labelled with their display name
    const buttons = await screen.findAllByRole('button', { name: /Sign Up/i });
    expect(buttons).not.toHaveLength(0);
    buttons.forEach((button) => expect(button).toBeEnabled());
  });
});


describe('DailySignupView admin sign-up controls', () => {
  const other = {
    id: 201, date: selectedDate, player_profile_id: 7, player_name: 'Gregg Colburn', status: 'signed_up',
    notes: null, preferred_start_time: null, signup_time: '2099-01-01T00:00:00Z',
    created_at: '2099-01-01T00:00:00Z', updated_at: '2099-01-01T00:00:00Z',
  };

  beforeEach(() => {
    mockUseAuth0.mockReturnValue({
      user: { name: 'Admin', email: 'admin@example.com' },
      isAuthenticated: true,
      getAccessTokenSilently: vi.fn().mockResolvedValue('admin-token'),
    });
  });

  const installFetch = (signups, extra = () => null) => {
    fetch.mockImplementation(async (request) => {
      const url = request.url;
      const handled = await extra(request);
      if (handled) return handled;
      if (url.includes('/pairings/')) return jsonResponse({ exists: false });
      if (url.includes('/signups/weekly-with-messages')) return jsonResponse(weeklyResponse(signups));
      if (url.endsWith('/signups/admin/players')) {
        return jsonResponse({ players: [{ id: 7, legacy_name: 'Gregg Colburn' }, { id: 8, legacy_name: 'Terry Fuerst' }] });
      }
      throw new Error(`Unexpected fetch: ${request.method} ${url}`);
    });
  };

  test('admin adds a player to an upcoming day', async () => {
    mockUsePlayerProfile.mockReturnValue({ profile: playerProfile, loading: false, isAdmin: true });
    installFetch([other], async (request) => {
      if (request.url.endsWith('/signups/admin') && request.method === 'POST') {
        return jsonResponse({ ...other, id: 202, player_profile_id: 8, player_name: 'Terry Fuerst' });
      }
      return null;
    });
    render(<DailySignupView selectedDate={selectedDate} />);

    const picker = await screen.findByLabelText('Player to add');
    await waitFor(() => expect(within(picker).getAllByRole('option')).toHaveLength(2));
    expect(within(picker).queryByRole('option', { name: 'Gregg Colburn' })).not.toBeInTheDocument();
    fireEvent.change(picker, { target: { value: '8' } });
    fireEvent.click(screen.getByRole('button', { name: 'Add' }));

    expect(await screen.findByText('Added Terry Fuerst.')).toBeInTheDocument();
    const post = fetch.mock.calls.map(([r]) => r).find(r => r.url.endsWith('/signups/admin') && r.method === 'POST');
    expect(JSON.parse(await post.clone().text())).toEqual({ date: selectedDate, player_profile_id: 8 });
    expect(post.headers.get('Authorization')).toBe('Bearer admin-token');
  });

  test('admin can remove someone else after confirming, with the auth token', async () => {
    mockUsePlayerProfile.mockReturnValue({ profile: playerProfile, loading: false, isAdmin: true });
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true);
    installFetch([other], async (request) => {
      if (request.url.endsWith('/signups/201') && request.method === 'DELETE') return jsonResponse({ message: 'ok' });
      return null;
    });
    render(<DailySignupView selectedDate={selectedDate} />);

    fireEvent.click(await screen.findByRole('button', { name: 'Remove Gregg Colburn' }));
    await waitFor(() => expect(fetch.mock.calls.some(([r]) => r.method === 'DELETE')).toBe(true));
    const del = fetch.mock.calls.map(([r]) => r).find(r => r.method === 'DELETE');
    expect(del.url).toMatch(/\/signups\/201$/);
    expect(del.headers.get('Authorization')).toBe('Bearer admin-token');
    expect(confirm).toHaveBeenCalled();
    confirm.mockRestore();
  });

  test('non-admins see neither the picker nor Remove on other players', async () => {
    mockUsePlayerProfile.mockReturnValue({ profile: playerProfile, loading: false, isAdmin: false });
    installFetch([other]);
    render(<DailySignupView selectedDate={selectedDate} />);

    expect(await screen.findByText('Gregg Colburn')).toBeInTheDocument();
    expect(screen.queryByLabelText('Player to add')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Remove Gregg Colburn' })).not.toBeInTheDocument();
  });
});
