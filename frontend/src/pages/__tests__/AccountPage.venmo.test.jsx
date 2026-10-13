import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import AccountPage from '../AccountPage';

const user = { name: 'casey@example.com', email: 'casey@example.com' };
const getToken = vi.fn().mockResolvedValue('test-token');
vi.mock('@auth0/auth0-react', () => ({ useAuth0: () => ({ user, isAuthenticated: true }) }));
vi.mock('../../hooks/useAccessToken', () => ({ useAccessToken: () => ({ getToken }) }));
vi.mock('../../theme/Provider', () => ({ useTheme: () => ({ colors: {} }) }));
vi.mock('../../components/auth/ClubPlayerSection', () => ({ default: () => null }));
vi.mock('../../components/signup/PlayerAvailability', () => ({ default: () => null }));
vi.mock('../../components/signup/EmailPreferences', () => ({ default: () => null }));
vi.mock('../../components/signup/MyMatches', () => ({ default: () => null }));

const mockServer = (venmo) => {
  const puts = [];
  global.fetch.mockImplementation(async (url, opts = {}) => {
    if (opts.method === 'PUT') {
      const body = JSON.parse(opts.body);
      puts.push({ url: String(url), body });
      return { ok: true, json: async () => ({ venmo_handle: body.venmo_handle ? `@${body.venmo_handle.replace(/^@/, '')}` : null }) };
    }
    return {
      ok: true,
      json: async () => (String(url).endsWith('/players/me')
        ? { name: 'Casey', legacy_name: 'Casey', description: '', venmo_handle: venmo }
        : { found: false }),
    };
  });
  return puts;
};

afterEach(() => localStorage.removeItem('wgp_account_settings'));

test('shows the Venmo handle saved on the server, over a stale browser copy', async () => {
  localStorage.setItem('wgp_account_settings', JSON.stringify({ venmoHandle: '' }));
  mockServer('@casey-golf');
  render(<AccountPage />);
  expect(await screen.findByText('@casey-golf')).toBeInTheDocument();
});

test('leaving the Venmo box saves it to the server, whichever button is clicked next', async () => {
  const puts = mockServer(null);
  render(<AccountPage />);
  fireEvent.click(await screen.findByRole('button', { name: 'Edit' }));
  const box = screen.getByPlaceholderText('@your-venmo');
  fireEvent.change(box, { target: { value: 'casey-golf' } });
  fireEvent.blur(box);

  await waitFor(() => expect(puts.filter(p => p.url.endsWith('/players/me/venmo'))).toHaveLength(1));
  expect(puts.find(p => p.url.endsWith('/players/me/venmo')).body).toEqual({ venmo_handle: 'casey-golf' });
});

test('profile Save also persists the Venmo handle to the server', async () => {
  const puts = mockServer(null);
  render(<AccountPage />);
  fireEvent.click(await screen.findByRole('button', { name: 'Edit' }));
  fireEvent.change(screen.getByPlaceholderText('@your-venmo'), { target: { value: '@casey-golf' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save' }));

  await waitFor(() => expect(puts.some(p => p.url.endsWith('/players/me/venmo'))).toBe(true));
  expect(puts.find(p => p.url.endsWith('/players/me/venmo')).body).toEqual({ venmo_handle: '@casey-golf' });
});
