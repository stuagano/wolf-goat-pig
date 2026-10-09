import React, { useState } from 'react';
import { useAuthenticatedFetch } from '../../hooks/useAuthenticatedFetch';
import { useLegacyPlayers } from '../../hooks/useLegacyPlayers';
import { Card } from '../../components/ui';
import { apiConfig } from '../../config/api.config';
import ClaimRequests from './ClaimRequests';

const inputClass = 'w-full px-3 py-2 border border-gray-300 rounded-lg';
const buttonClass = 'px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50';

export default function AccountLinkingManager() {
  const request = useAuthenticatedFetch();
  const roster = useLegacyPlayers();
  const [query, setQuery] = useState('');
  const [players, setPlayers] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const [selected, setSelected] = useState(null);
  const [form, setForm] = useState({ legacyName: '', email: '', auth0Id: '' });
  const [reviewing, setReviewing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const jsonRequest = async (path, options) => {
    const response = await request(`${apiConfig.baseUrl}${path}`, options);
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Unable to save or load this account link. Check the fields and try again.');
    return data;
  };

  const search = async event => {
    event.preventDefault();
    setBusy(true); setError(''); setSuccess(''); setSelected(null); setReviewing(false); setPlayers(null); setHasMore(false);
    try {
      const data = await jsonRequest(`/players/admin/account-links?query=${encodeURIComponent(query.trim())}`);
      setPlayers(data.players); setHasMore(data.has_more);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  const select = player => {
    setSelected(player);
    setForm({ legacyName: player.legacy_name || '', email: player.email || '', auth0Id: player.auth0_id || '' });
    setReviewing(false); setError(''); setSuccess('');
  };

  const update = (field, value) => {
    setForm(current => ({ ...current, [field]: value }));
    setReviewing(false); setError(''); setSuccess('');
  };

  const save = async () => {
    setBusy(true); setError('');
    try {
      const data = await jsonRequest('/players/admin/relink-auth0', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_id: selected.id, legacy_name: form.legacyName,
          email: form.email.trim(), auth0_id: form.auth0Id.trim() || null, expected_updated_at: selected.updated_at }),
      });
      select(data);
      setPlayers(current => current.map(player => player.id === data.id ? data : player));
      setSuccess(`Account linked to ${data.legacy_name}. Existing scores and history are preserved. The player can refresh the app to see their name.`);
    } catch (err) { setError(err.message); setReviewing(false); }
    finally { setBusy(false); }
  };

  const retire = async () => {
    if (!window.confirm(`Retire profile #${selected.id}? It is hidden from search and its email and Auth0 login are released so they can be linked to the player's real profile.`)) return;
    setBusy(true); setError('');
    try {
      await jsonRequest(`/players/${selected.id}`, { method: 'DELETE' });
      setPlayers(current => current.filter(player => player.id !== selected.id));
      setSuccess(`Profile #${selected.id} retired. Its email and login can now be linked to another profile.`);
      setSelected(null); setReviewing(false);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  return (
    <Card className="p-6 space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Account links</h2>
        <p className="text-gray-600 mt-2">Connect an existing player profile to their club roster name, email, and Auth0 login. Start with a name or email, then select the profile whose history belongs to that player.</p>
      </div>
      <ClaimRequests />
      <form onSubmit={search} className="flex flex-wrap items-end gap-3">
        <label className="flex-1 min-w-48"><span className="block font-medium mb-1">Search name or email</span>
          <input className={inputClass} value={query} onChange={event => setQuery(event.target.value)} required minLength={2} maxLength={100} placeholder="Kevin Gent, Casey McFarland, or email" disabled={busy} />
        </label>
        <button className={buttonClass} disabled={busy || query.trim().length < 2}>Search profiles</button>
      </form>
      {error && <div role="alert" className="p-3 rounded-lg bg-red-50 text-red-800">{error}</div>}
      {success && <div role="status" className="p-3 rounded-lg bg-green-50 text-green-800">{success}</div>}
      {busy && <p role="status">Working…</p>}
      {players?.length === 0 && <p>No matching profiles. Try the player's email or another spelling.</p>}
      {hasMore && <p>Showing the first 50 profiles. Narrow your search to find the right account.</p>}
      {players?.length > 0 && <div className="overflow-x-auto"><table className="w-full text-left text-sm">
        <thead><tr><th className="p-2">Player / roster name</th><th className="p-2">Email / Auth0 login</th><th className="p-2">Profile</th></tr></thead>
        <tbody>{players.map(player => <tr key={player.id} className="border-t">
          <td className="p-2"><strong>{player.legacy_name || player.name}</strong><div>{player.legacy_name ? `Profile name: ${player.name}` : 'Not linked to the club roster'}</div></td>
          <td className="p-2 break-all">{player.email || 'No email'}<div className="text-gray-500">{player.auth0_id || 'No Auth0 login linked'}</div></td>
          <td className="p-2"><button type="button" className="text-blue-700 underline" disabled={busy} onClick={() => select(player)} aria-label={`Select profile ${player.id}: ${player.legacy_name || player.name}`}>Select #{player.id}</button></td>
        </tr>)}</tbody>
      </table></div>}
      {selected && <form onSubmit={event => { event.preventDefault(); setReviewing(true); }} className="border-t pt-5 space-y-4 max-w-xl">
        <h3 className="font-semibold">Edit profile #{selected.id} — {selected.name}</h3>
        {roster.error && <p role="alert">Could not load the roster: {roster.error}</p>}
        <fieldset disabled={busy} className="space-y-4">
          <label className="block">Roster player
            <select className={inputClass} value={form.legacyName} onChange={event => update('legacyName', event.target.value)} required disabled={roster.loading || Boolean(roster.error)}>
              <option value="">{roster.loading ? 'Loading roster…' : 'Select an existing roster player'}</option>
              {roster.players.map(name => <option key={name} value={name}>{name}</option>)}
            </select>
          </label>
          <label className="block">Player email
            <input className={inputClass} type="email" required maxLength={320} value={form.email} onChange={event => update('email', event.target.value)} />
          </label>
          <label className="block">Auth0 user ID
            <input className={inputClass} maxLength={255} value={form.auth0Id} onChange={event => update('auth0Id', event.target.value)} placeholder="auth0|… or google-oauth2|…" />
          </label>
          <p className="text-sm text-gray-500">The existing login is filled in when available. To change it, copy the user ID from Auth0 → User Management → Users. Leaving this blank keeps the current login link.</p>
          <button className={buttonClass} disabled={!form.legacyName || !form.email.trim() || roster.loading || Boolean(roster.error)}>Review link</button>
        </fieldset>
        {reviewing && <div className="p-4 bg-blue-50 rounded-lg space-y-2">
          <p><strong>Profile #{selected.id} will display as {form.legacyName}.</strong></p>
          <p>Email: {form.email.trim()}</p>
          <p className="break-all">Auth0 login: {form.auth0Id.trim() || selected.auth0_id || 'No login ID yet; matching email will link on sign-in'}</p>
          <p className="text-sm">This updates this profile only. Scores and history stay with it. A conflicting account link will stop the save.</p>
          <button type="button" className={buttonClass} onClick={save} disabled={busy}>Save account link</button>
          <button type="button" className="ml-3 underline" onClick={() => setReviewing(false)} disabled={busy}>Back to editing</button>
        </div>}
        <div className="border-t pt-4">
          <p className="text-sm text-gray-500">Duplicate profile with no history (for example, one named after an email)? Retire it to free its email and login.</p>
          <button type="button" className="mt-2 text-red-700 underline" onClick={retire} disabled={busy}>Retire this duplicate profile</button>
        </div>
      </form>}
    </Card>
  );
}
