import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { useAuthenticatedFetch } from '../hooks/useAuthenticatedFetch';
import { readRoundResponse, reviewUrl } from '../services/roundIdentity';
import { IssueReview } from '../components/game/RoundConflictReview';

export default function RoundReconciliationPage() {
  const { isAuthenticated, loginWithRedirect } = useAuth0();
  const request = useAuthenticatedFetch();
  const [params, setParams] = useSearchParams();
  const issueId = params.get('issue');
  const offset = Math.max(0, Number(params.get('offset')) || 0);
  const [page, setPage] = useState(null);
  const [health, setHealth] = useState(null);
  const [error, setError] = useState('');
  const [attestation, setAttestation] = useState(null);
  const [confirmed, setConfirmed] = useState(false);
  const [profileId, setProfileId] = useState('');
  const [proofId, setProofId] = useState('');
  const [reason, setReason] = useState('');
  const [status, setStatus] = useState('');
  const [version, setVersion] = useState(0);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (!isAuthenticated) return;
    let cancelled = false;
    setPage(null);
    setError('');
    Promise.all([
      request(reviewUrl(`/issues?status=open&offset=${offset}`)).then(readRoundResponse),
      request(reviewUrl('/health')).then(readRoundResponse),
    ]).then(([items, state]) => { if (!cancelled) { setPage(items); setHealth(state); } })
      .catch(err => { if (!cancelled) setError(err.message); });
    return () => { cancelled = true; };
  }, [isAuthenticated, request, offset, version]);
  async function submit(path, method, body) {
    if (busy) return;
    setBusy(true);
    setStatus('');
    try {
      const result = await readRoundResponse(await request(reviewUrl(path), { method,
        headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }));
      if (path === '/recipient/attest') { setAttestation(result); setProofId(result.attestation_id); }
      setStatus(path.endsWith('revoke') ? 'Self-attestation revoked.' : path === '/recipient' ? `Server confirmed recipient profile ${result.profile_id}.` : 'Self-attestation recorded; no recipient selected and no alerts sent.');
      setConfirmed(false);
      setVersion(v => v + 1);
    } catch (err) { setStatus(err.message); } finally { setBusy(false); }
  }
  if (!isAuthenticated) return <main><h1>Round reconciliation</h1><button onClick={() => loginWithRedirect()}>Sign in to request review access</button></main>;
  return <main style={{ maxWidth: 1000, margin: 'auto', padding: 20 }}><h1>Round reconciliation</h1>
    {error && <p role="alert">{error}</p>}
    {page && <>
      <h2>Open review inbox ({page.total})</h2>
      <ul>{page.items.map(i => <li key={i.id}><Link to={`?issue=${encodeURIComponent(i.id)}&offset=${offset}`}>{i.kind}: {i.field} — {i.id}</Link>{' '}
        {i.game_id ? <Link to={`/game/${encodeURIComponent(i.game_id)}`}>Shared game</Link> : <span>Unbound issue</span>}
      </li>)}</ul>
      {offset > 0 && <button onClick={() => setParams({ offset: String(Math.max(0, offset - 50)) })}>Previous issues</button>}
      {offset + page.limit < page.total && <button onClick={() => setParams({ offset: String(offset + page.limit) })}>Next issues</button>}
      {issueId && <IssueReview key={issueId} issueId={issueId} onResolved={() => setVersion(v => v + 1)} />}
      <h2>Routing and delivery status</h2><pre>{JSON.stringify(health, null, 2)}</pre>
    </>}
    <section aria-label="Recipient consent"><h2>Prospective recipient self-attestation</h2>
      <p>This records consent for your own server-verified account for up to 24 hours. It does not select a recipient or send notifications. An administrator must explicitly select the matching proof.</p>
      <label><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} />I confirm my own account as a prospective conflict-review recipient.</label>
      <button disabled={!confirmed || busy} onClick={() => submit('/recipient/attest', 'POST', { confirmed: true })}>Record my self-attestation</button>
      <button disabled={busy} onClick={() => submit('/recipient/attest/revoke', 'POST', {})}>Revoke my self-attestation</button>
      {attestation && <p>Proof ID: {attestation.attestation_id} · expires {attestation.expires_at}</p>}
    </section>
    {page && <form onSubmit={e => { e.preventDefault(); submit('/recipient', 'PUT', { profile_id: Number(profileId), attestation_id: proofId, confirmed: true, reason }); }}>
      <h2>Administrator recipient selection</h2><p>The server requires administrator authority and a current matching attestation. Review access alone does not grant selection permission. Existing alerts are not automatically requeued.</p>
      <label>Recipient profile ID<input required type="number" min="1" value={profileId} onChange={e => setProfileId(e.target.value)} /></label>
      <label>Attestation ID<input required value={proofId} onChange={e => setProofId(e.target.value)} /></label>
      <label>Selection reason<textarea required maxLength={1000} value={reason} onChange={e => setReason(e.target.value)} /></label>
      <label><input type="checkbox" required />I explicitly confirm this recipient and matching proof.</label>
      <button disabled={busy || !reason.trim()}>Confirm recipient selection</button>
    </form>}
    {status && <p role="status">{status}</p>}
  </main>;
}
