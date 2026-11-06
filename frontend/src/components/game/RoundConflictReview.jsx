import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { useAuthenticatedFetch } from '../../hooks/useAuthenticatedFetch';
import { readRoundResponse, reviewUrl } from '../../services/roundIdentity';

const shown = value => value === undefined ? 'Not supplied' : JSON.stringify(value, null, 2);
// Mirrors resolve_issue: binding is identity/continuity only; integrity
// evidence cannot accept/correct a value, and an unbound hold cannot retract.
const decisionOptions = issue => [
  ['keep', 'Keep accepted'],
  ...(['identity', 'continuity'].includes(issue.kind)
    ? [['bind_existing', 'Bind existing game'], ...(!issue.game_id ? [['confirm_distinct', 'Confirm distinct new round']] : [])] : []),
  ...(issue.game_id && ['value', 'roster'].includes(issue.kind)
    ? [['accept', 'Accept proposed'], ['correct', 'Correct value']] : []),
  ...(issue.game_id ? [['retract', 'Retract']] : []),
];
export function IssueReview({ issueId, onResolved }) {
  const request = useAuthenticatedFetch();
  const [issue, setIssue] = useState(null);
  const [reason, setReason] = useState('');
  const [action, setAction] = useState('keep');
  const [value, setValue] = useState('');
  const [target, setTarget] = useState('');
  const [error, setError] = useState('');
  const [stale, setStale] = useState(false);
  const [busy, setBusy] = useState(false);
  const [version, setVersion] = useState(0);
  useEffect(() => {
    let cancelled = false;
    setIssue(null);
    setError('');
    request(reviewUrl(`/issues/${encodeURIComponent(issueId)}`)).then(readRoundResponse)
      .then(data => { if (!cancelled) { setIssue(data); setStale(false); setAction(!data.game_id && ['identity', 'continuity'].includes(data.kind) ? 'bind_existing' : 'keep'); } })
      .catch(err => { if (!cancelled) setError(err.message); });
    return () => { cancelled = true; };
  }, [request, issueId, version]);
  async function resolve(event) {
    event.preventDefault();
    if (stale || busy) return;
    setBusy(true);
    try {
      const decision = { action, reason, expected_game_revision: issue.game_revision,
        expected_issue_revision: issue.revision, expected_head_revision: issue.current_head_revision,
        ...(action === 'correct' ? { value: JSON.parse(value) } : {}),
        ...(action === 'bind_existing' ? { target_game_id: target, expected_target_game_revision: Number(value) } : {}) };
      const result = await readRoundResponse(await request(reviewUrl(`/issues/${encodeURIComponent(issueId)}/resolve`), {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(decision),
      }));
      setError(result.status === 'held' ? 'Decision recorded; outstanding evidence remains held.' : 'Decision recorded.');
      setStale(true); // No accidental second submission against the consumed revision.
      onResolved?.();
    } catch (err) {
      if (err.status === 409) { setStale(true); setError('Round evidence changed. Reload current evidence before making a new decision; this decision was not resubmitted.'); }
      else setError(err.message);
    } finally { setBusy(false); }
  }
  return <article aria-label={`Review issue ${issueId}`}>
    {error && <p role="alert">{error}</p>}
    {!issue ? <p>Loading issue…</p> : <>
      <h3>{issue.kind}: {issue.field} — {issue.status}</h3>
      {issue.game_id ? <Link to={`/game/${encodeURIComponent(issue.game_id)}`}>Open shared game</Link> : <p>Unbound identity issue — no game has been assigned.</p>}
      <p>Issue {issue.id} · revision {issue.revision} · game revision {issue.game_revision ?? 'Unbound'} · evidence head {issue.current_head_revision}</p>
      <table><thead><tr><th>Accepted</th><th>Proposed</th></tr></thead><tbody><tr>
        <td><pre>{issue.accepted_present ? shown(issue.accepted_value) : 'Not supplied'}</pre></td>
        <td><pre>{issue.proposed_present ? shown(issue.proposed_value) : 'Not supplied'}</pre></td>
      </tr></tbody></table>
      <details><summary>Provenance</summary><pre>{shown(issue.source)}</pre><pre>{shown(issue.observation)}</pre></details>
      <details><summary>Resolution audit ({issue.audit.length})</summary>{issue.audit.map(a => <pre key={a.id}>{shown(a)}</pre>)}</details>
      {issue.status === 'open' && <form onSubmit={resolve}>
        <label>Decision<select value={action} onChange={e => setAction(e.target.value)} disabled={stale || busy}>
          {decisionOptions(issue).map(([key, label]) => <option key={key} value={key}>{label}</option>) }
        </select></label>
        {action === 'bind_existing' && <label>Target game UUID<input value={target} required onChange={e => setTarget(e.target.value)} /></label>}
        {(action === 'correct' || action === 'bind_existing') && <label>{action === 'correct' ? 'Corrected value (JSON)' : 'Target accepted revision'}<input value={value} required onChange={e => setValue(e.target.value)} /></label>}
        <label>Reason<textarea value={reason} maxLength={1000} required onChange={e => setReason(e.target.value)} /></label>
        <button disabled={stale || busy || !reason.trim()}>Record reviewed decision</button>
      </form>}
      <button disabled={busy} onClick={() => { setReason(''); setVersion(v => v + 1); }}>Reload current evidence</button>
    </>}
  </article>;
}

export default function RoundConflictReview({ gameId }) {
  const { isAuthenticated } = useAuth0();
  const request = useAuthenticatedFetch();
  const [issues, setIssues] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    if (!isAuthenticated) return;
    let cancelled = false;
    (async () => {
      try {
        const items = [];
        let offset = 0;
        let total;
        do {
          const page = await readRoundResponse(await request(reviewUrl(`/issues?status=open&limit=100&offset=${offset}`)));
          items.push(...page.items.filter(i => i.game_id === gameId));
          offset += page.items.length;
          total = page.total;
          if (!page.items.length) break;
        } while (offset < total);
        if (!cancelled) setIssues(items);
      } catch (err) { if (!cancelled && err.status !== 403 && err.status !== 401) setError(err.message); }
    })();
    return () => { cancelled = true; };
  }, [request, isAuthenticated, gameId]);
  if (!issues && !error) return null; // Only the server grants review access.
  return <section aria-label="Conflict review"><h2>Conflict review</h2>{error && <p role="alert">{error}</p>}
    <Link to="/round-reconciliation">Review inbox</Link>
    {issues?.length === 0 && <p>No open issues for this game.</p>}
    {issues?.map(i => <IssueReview key={i.id} issueId={i.id} />)}
  </section>;
}
