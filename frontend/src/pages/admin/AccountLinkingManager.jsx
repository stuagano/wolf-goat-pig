import React, { useState } from 'react';
import { useAuthenticatedFetch } from '../../hooks/useAuthenticatedFetch';
import { Card } from '../../components/ui';
import { apiConfig } from '../../config/api.config';

const API_URL = apiConfig.baseUrl;

export default function AccountLinkingManager() {
  const authenticatedFetch = useAuthenticatedFetch();
  const [email, setEmail] = useState('');
  const [auth0Id, setAuth0Id] = useState('');
  const [status, setStatus] = useState(null); // null | {ok, message, data}
  const [loading, setLoading] = useState(false);

  const handleFix = async () => {
    if (!email.trim() || !auth0Id.trim()) return;
    setLoading(true);
    setStatus(null);
    try {
      const res = await authenticatedFetch(`${API_URL}/players/admin/relink-auth0`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim(), auth0_id: auth0Id.trim() }),
      });
      const data = await res.json();
      if (res.ok) {
        setStatus({
          ok: true,
          message: `Linked — ${data.name} (${data.legacy_name || 'no legacy name'}) → ${data.auth0_id}`,
          data,
        });
      } else {
        setStatus({ ok: false, message: data.detail || 'Error' });
      }
    } catch (err) {
      setStatus({ ok: false, message: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-2">Account Linking</h2>
        <p className="text-gray-500 text-sm mb-6">
          Use this when a player has two Auth0 accounts (e.g. Google + password) and the
          wrong one is linked to their WGP profile. Enter their email and the Auth0 sub ID
          you want to use — it will be set as the active link and any duplicates cleared.
        </p>

        <div className="space-y-4 max-w-lg">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Player email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="kdgent@gmail.com"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Auth0 user ID to link</label>
            <input
              type="text"
              value={auth0Id}
              onChange={(e) => setAuth0Id(e.target.value)}
              placeholder="auth0|6a99b7e32d4c5cfff4bc16e4"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
            />
            <p className="text-xs text-gray-400 mt-1">
              Find this in Auth0 dashboard → User Management → Users → click the user → copy the &quot;user_id&quot; field.
            </p>
          </div>

          <button
            onClick={handleFix}
            disabled={loading || !email.trim() || !auth0Id.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {loading ? 'Fixing…' : 'Fix Link'}
          </button>

          {status && (
            <div className={`p-4 rounded-lg text-sm ${status.ok ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'}`}>
              {status.ok ? '✓ ' : '✗ '}{status.message}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
