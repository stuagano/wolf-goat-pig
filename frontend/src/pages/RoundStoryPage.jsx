import React, { useCallback, useEffect, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { apiConfig } from '../config/api.config';
import { useAccessToken } from '../hooks/useAccessToken';
import PlayerName from '../components/game/leaderboard/PlayerName';
import ReactionBar from '../components/game/leaderboard/ReactionBar';

const API_URL = apiConfig.baseUrl;

const formatGameDate = (dateStr) => {
  if (!dateStr) return 'Round';
  const [y, m, d] = dateStr.split('-').map(Number);
  if (!y || !m || !d) return dateStr;
  return new Date(y, m - 1, d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

const formatScore = (q) => `${q >= 0 ? '+' : ''}${q}`;

export default function RoundStoryPage() {
  const { date, group } = useParams();
  const [searchParams] = useSearchParams();
  const location = searchParams.get('location') || '';
  const { isAuthenticated, loginWithRedirect } = useAuth0();
  const { getToken } = useAccessToken();

  const [round, setRound] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [draft, setDraft] = useState('');
  const [posting, setPosting] = useState(false);
  const [postError, setPostError] = useState(null);
  const [myProfileId, setMyProfileId] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [copied, setCopied] = useState(false);

  const query = location ? `?location=${encodeURIComponent(location)}` : '';
  const storyPath = `${API_URL}/data/rounds/${encodeURIComponent(date)}/${encodeURIComponent(group || '')}`;
  const storyUrl = `${storyPath}${query}`;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(storyUrl);
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Round not found');
      }
      const story = await res.json();
      setRound(story);
      setError(null);
      if (story.date_sortable && story.date_sortable !== date) {
        const canonical = `/rounds/${encodeURIComponent(story.date_sortable)}/${encodeURIComponent(group || '')}${query}`;
        window.history.replaceState(null, '', canonical);
      }
    } catch (err) {
      setError(err.message || 'Could not load this round');
    } finally {
      setLoading(false);
    }
  }, [storyUrl, date, group, query]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!isAuthenticated) {
      setMyProfileId(null);
      setIsAdmin(false);
      return undefined;
    }
    let cancelled = false;
    (async () => {
      try {
        const token = await getToken();
        const res = await fetch(`${API_URL}/players/me`, { headers: { Authorization: `Bearer ${token}` } });
        if (!res.ok || cancelled) return;
        const me = await res.json();
        if (!cancelled) {
          setMyProfileId(me.id ?? null);
          setIsAdmin(Boolean(me.is_admin));
        }
      } catch {
        if (!cancelled) setMyProfileId(null);
      }
    })();
    return () => { cancelled = true; };
  }, [isAuthenticated, getToken]);

  const postComment = async (event) => {
    event.preventDefault();
    const body = draft.trim();
    if (!body || posting) return;
    setPosting(true);
    setPostError(null);
    try {
      const token = await getToken();
      const res = await fetch(`${storyPath}/comments${query}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ body }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Could not post that comment');
      }
      const created = await res.json();
      setRound((current) => current && { ...current, comments: [...current.comments, created] });
      setDraft('');
    } catch (err) {
      setPostError(err.message || 'Could not post that comment');
    } finally {
      setPosting(false);
    }
  };

  const applyReactions = (next, commentId) => {
    setRound((current) => {
      if (!current) return current;
      if (commentId == null) return { ...current, reactions: next };
      return {
        ...current,
        comments: current.comments.map((comment) => (
          comment.id === commentId ? { ...comment, reactions: next } : comment
        )),
      };
    });
  };

  const toggleReaction = async (emoji, commentId) => {
    try {
      const token = await getToken();
      const url = commentId == null
        ? `${storyPath}/reactions${query}`
        : `${API_URL}/data/rounds/comments/${commentId}/reactions`;
      const res = await fetch(url, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ emoji }),
      });
      if (!res.ok) throw new Error('Could not save that reaction');
      applyReactions(await res.json(), commentId);
    } catch (err) {
      setPostError(err.message || 'Could not save that reaction');
    }
  };

  const copyLink = async () => {
    const key = round?.date_sortable || date;
    const url = `${window.location.origin}/rounds/${encodeURIComponent(key)}/${encodeURIComponent(group || '')}${location ? `?location=${encodeURIComponent(location)}` : ''}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setPostError('Could not copy that link');
    }
  };

  const removeComment = async (commentId) => {
    try {
      const token = await getToken();
      const res = await fetch(`${API_URL}/data/rounds/comments/${commentId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Could not delete that comment');
      setRound((current) => current && {
        ...current,
        comments: current.comments.filter((comment) => comment.id !== commentId),
      });
    } catch (err) {
      setPostError(err.message || 'Could not delete that comment');
    }
  };

  if (loading) {
    return <div className="min-h-screen bg-gray-50 py-8"><p className="text-center text-gray-600">Loading round...</p></div>;
  }
  if (error || !round) {
    return <div className="min-h-screen bg-gray-50 py-8"><p className="text-center text-gray-600">{error || 'Round not found'}</p></div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <Link to="/leaderboard" className="text-sm text-blue-700 hover:underline">← Leaderboard</Link>
        <h1 className="text-3xl font-bold text-gray-900 mt-2">{formatGameDate(round.date_sortable)}</h1>
        <p className="text-gray-600 mt-1">
          {round.location || 'Unknown location'}{round.group ? ` · Group ${round.group}` : ''}
        </p>
        <button type="button" onClick={copyLink} className="mt-2 text-sm text-blue-700 hover:underline">
          {copied ? 'Link copied' : 'Copy link'}
        </button>

        <ul className="mt-6 bg-white rounded-lg divide-y divide-gray-200 shadow-sm">
          {round.players.map((player) => (
            <li key={player.member} className="flex items-center justify-between px-4 py-3">
              <PlayerName name={player.member} playerId={player.player_id} className="font-medium text-gray-900" />
              <span className={player.quarters >= 0 ? 'text-green-700 font-semibold' : 'text-red-700 font-semibold'}>
                {formatScore(player.quarters)}
              </span>
            </li>
          ))}
        </ul>
        <ReactionBar
          reactions={round.reactions || []}
          canReact={isAuthenticated}
          onToggle={(emoji) => toggleReaction(emoji)}
          onSignIn={loginWithRedirect}
        />

        <section className="mt-8" aria-labelledby="round-comments-heading">
          <h2 id="round-comments-heading" className="text-xl font-semibold text-gray-900">Comments</h2>
          {round.comments.length === 0 ? (
            <p className="text-sm text-gray-500 mt-2">No comments yet. What happened in this game?</p>
          ) : (
            <ul className="mt-3 space-y-3">
              {round.comments.map((comment) => (
                <li key={comment.id} className="bg-white rounded-lg px-4 py-3 shadow-sm">
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="text-sm font-medium text-gray-900">{comment.author_name}</span>
                    <span className="text-xs text-gray-500">{formatGameDate(comment.created_at?.slice(0, 10))}</span>
                  </div>
                  <p className="text-sm text-gray-800 mt-1 whitespace-pre-wrap">{comment.body}</p>
                  <ReactionBar
                    reactions={comment.reactions || []}
                    canReact={isAuthenticated}
                    onToggle={(emoji) => toggleReaction(emoji, comment.id)}
                    onSignIn={loginWithRedirect}
                  />
                  {isAuthenticated && (isAdmin || comment.author_profile_id === myProfileId) && (
                    <button type="button" onClick={() => removeComment(comment.id)} className="mt-2 text-xs text-red-700 hover:underline">
                      Delete
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}

          {isAuthenticated ? (
            <form onSubmit={postComment} className="mt-4">
              <label htmlFor="round-comment" className="text-sm font-medium text-gray-700">Add a comment</label>
              <textarea
                id="round-comment"
                value={draft}
                maxLength={2000}
                onChange={(event) => setDraft(event.target.value)}
                className="mt-1 w-full border rounded-lg px-3 py-2 text-sm"
                rows={3}
              />
              {postError && <p className="text-sm text-red-700 mt-1">{postError}</p>}
              <button
                type="submit"
                disabled={posting || !draft.trim()}
                className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium disabled:opacity-50"
              >
                {posting ? 'Posting...' : 'Post comment'}
              </button>
            </form>
          ) : (
            <button
              type="button"
              onClick={() => loginWithRedirect()}
              className="mt-4 text-sm text-blue-700 hover:underline"
            >
              Sign in to comment
            </button>
          )}
        </section>
      </div>
    </div>
  );
}
