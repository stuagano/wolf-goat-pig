import React, { useEffect, useMemo, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { api } from '../../api/client';
import { errorDetail } from '../../api/http';
import { acquireAccessToken, apiTokenOptions } from '../../services/authToken';

/**
 * Admin-only: put a linked player on this day's sign-up sheet
 * (e.g. someone who asked an organizer by text).
 *   GET  /signups/admin/players — active profiles with a roster name
 *   POST /signups/admin {date, player_profile_id}
 */
const authHeaders = async getAccessTokenSilently => ({
  Authorization: `Bearer ${await acquireAccessToken(getAccessTokenSilently, apiTokenOptions)}`,
});

export default function AdminAddSignup({ date, signedUpProfileIds = [], onAdded }) {
  const { getAccessTokenSilently } = useAuth0();
  const [players, setPlayers] = useState([]);
  const [choice, setChoice] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { data, error } = await api.GET('/signups/admin/players', { headers: await authHeaders(getAccessTokenSilently) });
        if (error) throw new Error(errorDetail(error) || 'Could not load players');
        if (!cancelled) setPlayers(data?.players || []);
      } catch (err) {
        if (!cancelled) setMessage({ error: true, text: err.message });
      }
    })();
    return () => { cancelled = true; };
  }, [getAccessTokenSilently]);

  const available = useMemo(
    () => players.filter(p => !signedUpProfileIds.includes(p.id)),
    [players, signedUpProfileIds],
  );

  const add = async () => {
    const player = available.find(p => String(p.id) === choice);
    if (!player) return;
    setBusy(true); setMessage(null);
    try {
      const { error } = await api.POST('/signups/admin', {
        headers: await authHeaders(getAccessTokenSilently),
        body: { date, player_profile_id: player.id },
      });
      if (error) throw new Error(errorDetail(error) || 'Could not add that player');
      setChoice('');
      setMessage({ error: false, text: `Added ${player.legacy_name}.` });
      onAdded?.();
    } catch (err) {
      setMessage({ error: true, text: err.message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div aria-label="Add a player" style={{ marginTop: '12px', padding: '10px', background: '#f9fafb', borderRadius: '8px' }}>
      <div style={{ fontWeight: 600, fontSize: '13px', color: '#374151', marginBottom: '6px' }}>Admin: add a player</div>
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <select
          aria-label="Player to add"
          value={choice}
          onChange={e => setChoice(e.target.value)}
          disabled={busy}
          style={{ flex: 1, minWidth: '180px', padding: '6px', border: '1px solid #d1d5db', borderRadius: '6px' }}
        >
          <option value="">Choose a player…</option>
          {available.map(p => <option key={p.id} value={p.id}>{p.legacy_name}</option>)}
        </select>
        <button
          type="button"
          onClick={add}
          disabled={busy || !choice}
          style={{ padding: '6px 14px', background: '#2d5016', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 600, opacity: busy || !choice ? 0.5 : 1 }}
        >
          {busy ? 'Adding…' : 'Add'}
        </button>
      </div>
      {message && (
        <div role={message.error ? 'alert' : 'status'} style={{ marginTop: '6px', fontSize: '13px', color: message.error ? '#b91c1c' : '#047857' }}>
          {message.text}
        </div>
      )}
    </div>
  );
}
