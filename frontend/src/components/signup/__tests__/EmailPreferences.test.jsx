import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useAuth0 } from '@auth0/auth0-react';
import EmailPreferences from '../EmailPreferences';
import { createMockFetchResponse } from '../../../test-utils/mockFactories';

vi.mock('@auth0/auth0-react', () => ({ useAuth0: vi.fn() }));

const savedPreferences = {
  daily_signups_enabled: false,
  signup_confirmations_enabled: true,
  signup_reminders_enabled: false,
  game_invitations_enabled: true,
  weekly_summary_enabled: false,
  callout_list_enabled: true,
  email_frequency: 'weekly',
  preferred_notification_time: '10:00 AM',
};

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn());
  useAuth0.mockReturnValue({
    user: { sub: 'test-user' },
    getAccessTokenSilently: vi.fn().mockResolvedValue('test-access-token'),
  });
});

afterEach(() => vi.unstubAllGlobals());

test('loads and saves preferences using Auth0 access tokens', async () => {
  fetch.mockResolvedValueOnce(createMockFetchResponse(savedPreferences))
    .mockResolvedValueOnce(createMockFetchResponse({ ...savedPreferences, daily_signups_enabled: true }));
  render(<EmailPreferences />);
  const daily = await screen.findByRole('checkbox', { name: /Daily Sign-up Summaries/ });
  expect(daily).not.toBeChecked();
  expect(fetch.mock.calls[0][0].headers.get('Authorization')).toBe('Bearer test-access-token');
  fireEvent.click(daily);
  fireEvent.click(screen.getByRole('button', { name: /Save Preferences/ }));
  await screen.findByText(/Preferences saved!/);
  const request = fetch.mock.calls[1][0];
  expect(request.method).toBe('PUT');
  expect(request.headers.get('Authorization')).toBe('Bearer test-access-token');
  expect(await request.json()).toEqual({ ...savedPreferences, daily_signups_enabled: true });
  expect(useAuth0().getAccessTokenSilently).toHaveBeenCalledTimes(2);
});

test('shows load failures without editable defaults and allows retry', async () => {
  fetch.mockResolvedValueOnce(createMockFetchResponse({ detail: 'Not authenticated' }, { status: 401 }))
    .mockResolvedValueOnce(createMockFetchResponse(savedPreferences));
  render(<EmailPreferences />);
  expect(await screen.findByRole('alert')).toHaveTextContent('Not authenticated');
  expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: /Save Preferences/ })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /Retry/ }));
  await screen.findByRole('checkbox', { name: /Daily Sign-up Summaries/ });
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

test('preserves edits and reports a failed save without claiming success', async () => {
  fetch.mockResolvedValueOnce(createMockFetchResponse(savedPreferences))
    .mockResolvedValueOnce(createMockFetchResponse({ detail: 'Unable to save preferences' }, { status: 500 }));
  render(<EmailPreferences />);
  const daily = await screen.findByRole('checkbox', { name: /Daily Sign-up Summaries/ });
  fireEvent.click(daily);
  fireEvent.click(screen.getByRole('button', { name: /Save Preferences/ }));
  expect(await screen.findByText('Unable to save preferences')).toBeInTheDocument();
  expect(daily).toBeChecked();
  expect(screen.queryByText(/Preferences saved!/)).not.toBeInTheDocument();
  await waitFor(() => expect(screen.getByRole('button', { name: /Save Preferences/ })).toBeEnabled());
});

test('disables every preference control throughout token acquisition and saving', async () => {
  let resolveToken;
  let resolveSave;
  fetch.mockResolvedValueOnce(createMockFetchResponse(savedPreferences))
    .mockImplementationOnce(() => new Promise(resolve => { resolveSave = resolve; }));
  render(<EmailPreferences />);
  await screen.findByRole('checkbox', { name: /Daily Sign-up Summaries/ });
  useAuth0().getAccessTokenSilently.mockImplementationOnce(
    () => new Promise(resolve => { resolveToken = resolve; }),
  );
  fireEvent.click(screen.getByRole('button', { name: /Save Preferences/ }));
  const controls = [
    ...screen.getAllByRole('checkbox'), ...screen.getAllByRole('combobox'),
    ...['All Emails', 'Essential', 'Minimal'].map(name => screen.getByRole('button', { name })),
  ];
  controls.forEach(control => expect(control).toBeDisabled());
  expect(fetch).toHaveBeenCalledTimes(1);
  resolveToken('test-access-token');
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  controls.forEach(control => expect(control).toBeDisabled());
  resolveSave(await createMockFetchResponse(savedPreferences));
  await screen.findByText(/Preferences saved!/);
  controls.forEach(control => expect(control).toBeEnabled());
});
