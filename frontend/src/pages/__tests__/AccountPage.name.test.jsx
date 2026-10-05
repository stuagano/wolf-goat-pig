import React from 'react';
import { render, screen } from '@testing-library/react';
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

test('account heading uses the linked roster name even with a stale saved email display name', async () => {
  localStorage.setItem('wgp_account_settings', JSON.stringify({ displayName: 'casey@example.com' }));
  global.fetch.mockImplementation(async url => ({ ok: true, json: async () => String(url).endsWith('/players/me')
    ? { name: 'casey@example.com', legacy_name: 'Casey McFarland', description: '' }
    : { found: false } }));
  render(<AccountPage />);
  expect((await screen.findAllByText('Casey McFarland')).length).toBeGreaterThan(0);
  localStorage.removeItem('wgp_account_settings');
});
