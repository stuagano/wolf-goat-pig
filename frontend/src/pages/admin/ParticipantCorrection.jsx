import React, { useState } from 'react';
import { Card } from '../../components/ui';
import { useAuthenticatedFetch } from '../../hooks/useAuthenticatedFetch';
import { apiConfig } from '../../config/api.config';

const inputClass = 'w-full px-3 py-2 border border-gray-300 rounded-lg';
const buttonClass = 'px-4 py-2 bg-blue-600 text-white rounded-lg disabled:opacity-50';
const profileLabel = profile => profile ? `#${profile.id} — ${profile.name}` : 'Unlinked';

export default function ParticipantCorrection() {
  const request = useAuthenticatedFetch();
  const [resultId, setResultId] = useState('');
  const [replacementId, setReplacementId] = useState('');
  const [view, setView] = useState(null);
  const [reason, setReason] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(null);
  const [requestKey, setRequestKey] = useState('');

  const jsonRequest = async (path, options) => {
    const response = await request(`${apiConfig.baseUrl}${path}`, options);
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Correction refused. Preview again.');
    return data;
  };
  const invalidate = () => { setView(null); setConfirmed(false); setSaved(null); setError(''); };
  const preview = async event => {
    event.preventDefault();
    invalidate(); setBusy(true);
    try {
      const data = await jsonRequest(`/admin/participant-results/${resultId}?replacement_profile_id=${replacementId}`);
      setView(data); setRequestKey(crypto.randomUUID());
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };
  const apply = async () => {
    if (!view || !confirmed || !reason.trim()) return;
    setBusy(true); setError('');
    try {
      const data = await jsonRequest(`/admin/participant-results/${view.result.id}/correct`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          replacement_profile_id: view.replacement_profile.id,
          expected_old_profile_id: view.result.player_profile_id,
          expected_epoch: view.epoch, expected_snapshot: view.snapshot,
          reason: reason.trim(), confirmed: true, request_key: requestKey,
        }),
      });
      setSaved(data); setView(null); setConfirmed(false);
    } catch (err) {
      setError(`${err.message} Reload the preview before any further correction.`);
      setView(null); setConfirmed(false);
    } finally { setBusy(false); }
  };

  return <Card className="p-6 space-y-5">
    <div>
      <h2 className="text-xl font-semibold">Correct participant</h2>
      <p className="text-gray-600 mt-2">Change one saved result’s profile link only. The spreadsheet remains primary. Scores, earnings and game UUID stay unchanged. No profile merge, statistics recalculation, achievements, sheet writes or notifications.</p>
      <p className="text-gray-600 mt-2">Canonical, already-mapped and conflicted games require separate identity review and cannot be corrected here.</p>
    </div>
    {error && <div role="alert" className="p-3 rounded-lg bg-red-50 text-red-800">{error}</div>}
    <form onSubmit={preview} className="flex flex-wrap items-end gap-3">
      <label className="flex-1">Saved result ID
        <input className={inputClass} type="number" min="1" required value={resultId} disabled={busy} onChange={e => { setResultId(e.target.value); invalidate(); }} />
      </label>
      <label className="flex-1">Replacement profile ID
        <input className={inputClass} type="number" min="1" required value={replacementId} disabled={busy} onChange={e => { setReplacementId(e.target.value); invalidate(); }} />
      </label>
      <button className={buttonClass} disabled={busy}>Preview correction</button>
    </form>
    {view && <section aria-label="Correction preview" className="border rounded-lg p-4 space-y-3">
      <h3 className="font-semibold">Review this single participant</h3>
      <dl className="space-y-2">
        <div><dt className="font-medium">Game UUID</dt><dd className="break-all">{view.game_id}</dd></div>
        <div><dt className="font-medium">Saved game / result</dt><dd>#{view.game_record_id} / #{view.result.id}</dd></div>
        <div><dt className="font-medium">Player name</dt><dd>{view.result.player_name}</dd></div>
        <div><dt className="font-medium">Current profile</dt><dd>{profileLabel(view.current_profile)}</dd></div>
        <div><dt className="font-medium">Proposed replacement</dt><dd>{profileLabel(view.replacement_profile)}</dd></div>
        <div><dt className="font-medium">Stored earnings (unchanged)</dt><dd>{view.result.total_earnings ?? 'Not recorded'}</dd></div>
      </dl>
      <label className="block">Reason for correction
        <textarea className={inputClass} required maxLength={1000} value={reason} disabled={busy} onChange={e => { setReason(e.target.value); setConfirmed(false); }} />
      </label>
      <label className="flex gap-2 items-start">
        <input type="checkbox" checked={confirmed} disabled={busy} onChange={e => setConfirmed(e.target.checked)} />
        I verified this participant and confirm changing only this saved result’s profile link.
      </label>
      <button type="button" className={buttonClass} disabled={busy || !confirmed || !reason.trim()} onClick={apply}>Confirm participant correction</button>
    </section>}
    {saved && <div role="status" className="p-4 rounded-lg bg-green-50 text-green-800">
      <strong>Saved and read back from the server.</strong>
      <p>Game {saved.game_id}; result #{saved.result.id}; profile #{saved.result.player_profile_id}; earnings {saved.result.total_earnings ?? 'Not recorded'}.</p>
      <p className="break-all">Audit: {saved.audit_id}</p>
    </div>}
  </Card>;
}
