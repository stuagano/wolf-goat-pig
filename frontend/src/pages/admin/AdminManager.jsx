import React, { useCallback, useEffect, useState } from 'react';
import { useAuthenticatedFetch } from '../../hooks/useAuthenticatedFetch';
import { usePlayerProfile } from '../../hooks/usePlayerProfile';
import { Card } from '../../components/ui';
import { apiConfig } from '../../config/api.config';

const inputClass = 'w-full px-3 py-2 border border-gray-300 rounded-lg';
const buttonClass = 'px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50';
const label = player => player.legacy_name || player.name;

export default function AdminManager() {
  const request = useAuthenticatedFetch();
  const { profile, isSuperAdmin } = usePlayerProfile();
  const [admins, setAdmins] = useState(null);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const jsonRequest = useCallback(async (path, options) => {
    const response = await request(`${apiConfig.baseUrl}${path}`, options);
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Request failed. Try again.');
    return data;
  }, [request]);

  const load = useCallback(async () => {
    try { setAdmins(await jsonRequest('/players/admin/admins')); }
    catch (err) { setError(err.message); }
  }, [jsonRequest]);

  useEffect(() => { load(); }, [load]);

  const run = async (action, message) => {
    setBusy(true); setError(''); setSuccess('');
    try { await action(); setSuccess(message); await load(); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  const search = async event => {
    event.preventDefault();
    setBusy(true); setError(''); setResults(null);
    try { setResults((await jsonRequest(`/players/admin/account-links?query=${encodeURIComponent(query.trim())}`)).players); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  const grant = player => run(
    () => jsonRequest(`/players/admin/admins/${player.id}`, { method: 'POST' }),
    `${label(player)} is now an admin.`,
  );

  const revoke = player => {
    if (!window.confirm(`Remove admin access for ${label(player)}?`)) return;
    run(() => jsonRequest(`/players/admin/admins/${player.id}`, { method: 'DELETE' }), `Removed admin access for ${label(player)}.`);
  };

  return (
    <Card className="p-6 space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Admins</h2>
        <p className="text-gray-600 mt-2">Admins can use every tab on this page. See docs/admin-permissions.md in the repo for the full list of what that includes.</p>
      </div>
      {error && <div role="alert" className="p-3 rounded-lg bg-red-50 text-red-800">{error}</div>}
      {success && <div role="status" className="p-3 rounded-lg bg-green-50 text-green-800">{success}</div>}
      {admins && <ul className="divide-y">
        {admins.env_admins.map(email => <li key={email} className="py-2">
          <strong>{email}</strong>
          <div className="text-sm text-gray-500">Set in deployment config — can't be removed here.</div>
        </li>)}
        {admins.profile_admins.map(player => <li key={player.id} className="py-2 flex items-center justify-between gap-3">
          <div>
            <strong>{label(player)}</strong> <span className="text-gray-500">{player.email}</span>
            <div className="text-sm text-gray-500">granted by {player.admin_granted_by || 'unknown'}{player.admin_granted_at ? ` on ${player.admin_granted_at.slice(0, 10)}` : ''}</div>
          </div>
          {(isSuperAdmin || player.id !== profile?.id) && (
            <button type="button" className="text-red-700 underline" disabled={busy} onClick={() => revoke(player)} aria-label={`Remove admin ${label(player)}`}>Remove</button>
          )}
        </li>)}
      </ul>}
      <form onSubmit={search} className="flex flex-wrap items-end gap-3 border-t pt-5">
        <label className="flex-1 min-w-48"><span className="block font-medium mb-1">Find a player</span>
          <input className={inputClass} value={query} onChange={event => setQuery(event.target.value)} required minLength={2} maxLength={100} placeholder="Name or email" disabled={busy} />
        </label>
        <button className={buttonClass} disabled={busy || query.trim().length < 2}>Search</button>
      </form>
      {results?.length === 0 && <p>No matching profiles.</p>}
      {results?.length > 0 && <ul className="divide-y">{results.map(player => <li key={player.id} className="py-2 flex items-center justify-between gap-3">
        <div><strong>{label(player)}</strong> <span className="text-gray-500">{player.email || 'No email'}</span></div>
        {player.auth0_id
          ? <button type="button" className={buttonClass} disabled={busy} onClick={() => grant(player)} aria-label={`Make admin ${label(player)}`}>Make admin</button>
          : <span className="text-sm text-gray-500">Needs to sign in first</span>}
      </li>)}</ul>}
    </Card>
  );
}
