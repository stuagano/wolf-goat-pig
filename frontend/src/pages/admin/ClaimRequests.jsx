import React, { useCallback, useEffect, useState } from 'react';
import { useAuthenticatedFetch } from '../../hooks/useAuthenticatedFetch';
import { apiConfig } from '../../config/api.config';

const buttonClass = 'px-3 py-1 bg-blue-600 text-white rounded-lg disabled:opacity-50';

/** Returning players asking to be connected to their original profile (admin approves). */
export default function ClaimRequests() {
  const request = useAuthenticatedFetch();
  const [claims, setClaims] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const call = useCallback(async (path, options) => {
    const response = await request(`${apiConfig.baseUrl}${path}`, options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `HTTP ${response.status}`);
    return data;
  }, [request]);

  const load = useCallback(async () => {
    try { setClaims((await call('/players/admin/claims?status=pending')).claims); }
    catch (err) { setError(err.message); }
  }, [call]);

  useEffect(() => { load(); }, [load]);

  const resolve = async (claim, action) => {
    if (action === 'approve' && !window.confirm(`Connect ${claim.requester_email || 'this sign-in'} to ${claim.canonical_name} (profile #${claim.target?.id})? Their new profile #${claim.requester?.id} will be retired.`)) return;
    setBusy(true); setError(''); setSuccess('');
    try {
      await call(`/players/admin/claims/${claim.id}/${action}`, { method: 'POST' });
      setSuccess(action === 'approve'
        ? `Connected ${claim.canonical_name}. They can refresh the app to see their history.`
        : `Dismissed the claim for ${claim.canonical_name}.`);
      await load();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  };

  return (
    <section aria-label="Claim requests" className="space-y-3">
      <h3 className="font-semibold">Claim requests</h3>
      {error && <div role="alert" className="p-3 rounded-lg bg-red-50 text-red-800">{error}</div>}
      {success && <div role="status" className="p-3 rounded-lg bg-green-50 text-green-800">{success}</div>}
      {claims?.length === 0 && <p className="text-gray-500">No claim requests.</p>}
      {claims?.length > 0 && <ul className="divide-y">{claims.map(claim => (
        <li key={claim.id} className="py-2 flex flex-wrap items-center justify-between gap-3">
          <div>
            <strong>{claim.requester_email || `Profile #${claim.requester?.id}`}</strong> wants to be <strong>{claim.canonical_name}</strong>
            <div className="text-sm text-gray-500">Original profile #{claim.target?.id} · requested {claim.created_at?.slice(0, 10)}</div>
          </div>
          <div className="flex gap-3">
            <button type="button" className={buttonClass} disabled={busy} onClick={() => resolve(claim, 'approve')} aria-label={`Approve claim for ${claim.canonical_name}`}>Approve</button>
            <button type="button" className="underline disabled:opacity-50" disabled={busy} onClick={() => resolve(claim, 'dismiss')} aria-label={`Dismiss claim for ${claim.canonical_name}`}>Dismiss</button>
          </div>
        </li>
      ))}</ul>}
    </section>
  );
}
