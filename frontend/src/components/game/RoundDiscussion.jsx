import React, { useEffect, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { useAuthenticatedFetch } from '../../hooks/useAuthenticatedFetch';
import { apiConfig } from '../../config/api.config';
import { readRoundResponse } from '../../services/roundIdentity';
import ReactionBar from './leaderboard/ReactionBar';

export default function RoundDiscussion({ gameId }) {
  const { isAuthenticated, loginWithRedirect } = useAuth0();
  const authenticatedFetch = useAuthenticatedFetch();
  const [discussion, setDiscussion] = useState(null);
  const [me, setMe] = useState(null);
  const [draft, setDraft] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const base = `${apiConfig.baseUrl}/data/rounds`;
  const path = `${base}/uuid/${encodeURIComponent(gameId)}`;
  useEffect(() => {
    let cancelled = false;
    fetch(`${path}/discussion`).then(readRoundResponse)
      .then(data => { if (!cancelled) setDiscussion(data); })
      .catch(err => { if (!cancelled) setError(err.message); });
    if (isAuthenticated) authenticatedFetch(`${apiConfig.baseUrl}/players/me`).then(readRoundResponse)
      .then(data => { if (!cancelled) setMe(data); }).catch(() => {});
    return () => { cancelled = true; };
  }, [path, isAuthenticated, authenticatedFetch]);
  async function mutate(url, method, body) {
    setError('');
    return readRoundResponse(await authenticatedFetch(url, { method,
      headers: { 'Content-Type': 'application/json' }, ...(body ? { body: JSON.stringify(body) } : {}) }));
  }
  async function toggle(emoji, id) {
    if (busy) return;
    setBusy(true);
    try {
      const reactions = await mutate(id == null ? `${path}/reactions` : `${base}/comments/${id}/reactions`, 'POST', { emoji });
      setDiscussion(current => id == null ? { ...current, reactions } : { ...current,
        comments: current.comments.map(c => c.id === id ? { ...c, reactions } : c) });
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  async function post(event) {
    event.preventDefault();
    if (busy || !draft.trim()) return;
    setBusy(true);
    try {
      const comment = await mutate(`${path}/comments`, 'POST', { body: draft.trim() });
      setDiscussion(current => ({ ...current, comments: [...current.comments, comment] }));
      setDraft('');
    } catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  async function remove(id) {
    try {
      await mutate(`${base}/comments/${id}`, 'DELETE');
      setDiscussion(current => ({ ...current, comments: current.comments.filter(c => c.id !== id) }));
    } catch (err) { setError(err.message); }
  }
  return <section aria-label="Round discussion"><h2>Comments</h2>
    {error && <p role="alert">{error}</p>}
    {!discussion ? <p>Loading discussion…</p> : <>
      <ReactionBar reactions={discussion.reactions || []} canReact={isAuthenticated && !busy} onToggle={emoji => toggle(emoji)} onSignIn={loginWithRedirect} />
      {!discussion.comments.length && <p>No comments yet.</p>}
      <ul>{discussion.comments.map(c => <li key={c.id}><strong>{c.author_name}</strong> <time>{c.created_at}</time><p>{c.body}</p>
        <ReactionBar reactions={c.reactions || []} canReact={isAuthenticated && !busy} onToggle={emoji => toggle(emoji, c.id)} onSignIn={loginWithRedirect} />
        {isAuthenticated && (c.can_delete || me?.is_admin || me?.id === c.author_profile_id) && <button onClick={() => remove(c.id)}>Delete comment</button>}
      </li>)}</ul>
      {isAuthenticated ? <form onSubmit={post}><label>Add a comment<textarea value={draft} maxLength={2000} onChange={e => setDraft(e.target.value)} /></label><button disabled={busy || !draft.trim()}>Post comment</button></form>
        : <button onClick={() => loginWithRedirect()}>Sign in to comment</button>}
    </>}
  </section>;
}
