import React, { useEffect, useState } from 'react';
import { Link, Navigate, useParams, useSearchParams } from 'react-router-dom';
import { readRoundResponse, reviewUrl } from '../services/roundIdentity';

export default function RoundStoryPage() {
  const { date, group } = useParams();
  const [params] = useSearchParams();
  const location = params.get('location') || '';
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    let cancelled = false;
    setResult(null);
    setError('');
    fetch(reviewUrl(`/aliases?${new URLSearchParams({ date, group: group || '', location })}`))
      .then(readRoundResponse).then(data => { if (!cancelled) setResult(data); })
      .catch(err => { if (!cancelled) setError(err.message); });
    return () => { cancelled = true; };
  }, [date, group, location]);
  if (error) return <p role="alert">{error}</p>;
  if (!result) return <p>Loading round alias…</p>;
  if (result.status === 'resolved' && result.game_ids.length === 1) return <Navigate replace to={`/game/${encodeURIComponent(result.game_ids[0])}`} />;
  if (!result.game_ids.length) return <p>Round not found. No persisted association exists for this old link.</p>;
  return <main><h1>Ambiguous round link</h1><p>This old link refers to multiple games. Identity review is required; no scores or discussion have been assigned by guesswork.</p>
    <ul>{result.game_ids.map(id => <li key={id}><Link to={`/game/${encodeURIComponent(id)}`}>Game {id}</Link></li>)}</ul>
    <Link to="/round-reconciliation">Review identity issues</Link>
  </main>;
}
