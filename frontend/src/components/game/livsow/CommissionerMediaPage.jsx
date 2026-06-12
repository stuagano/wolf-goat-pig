// frontend/src/components/game/livsow/CommissionerMediaPage.jsx
// "Messages from the Commissioner" — the league's video archive, harvested
// from the GroupMe group so clips never scroll away. Poster-first grid;
// videos only load bytes when played.

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiConfig } from '../../../config/api.config';

const API_URL = apiConfig.baseUrl;

const monthLabel = (iso) => {
  if (!iso) return 'Undated';
  try {
    return new Date(iso).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  } catch {
    return 'Undated';
  }
};

const dayLabel = (iso) => {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return '';
  }
};

function VideoCard({ m }) {
  const [playing, setPlaying] = useState(false);
  return (
    <div style={{
      background: '#fff', border: '1px solid #e5e7eb', borderRadius: 14,
      overflow: 'hidden', display: 'flex', flexDirection: 'column',
    }}>
      <div style={{ position: 'relative', background: '#0f172a', aspectRatio: '9 / 12' }}>
        {playing ? (
          <video
            controls
            autoPlay
            playsInline
            preload="auto"
            style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }}
          >
            <source src={m.url} type="video/mp4" />
          </video>
        ) : (
          <button
            onClick={() => setPlaying(true)}
            aria-label={`Play video from ${m.author}`}
            style={{
              width: '100%', height: '100%', border: 'none', cursor: 'pointer',
              background: m.preview_url
                ? `center / cover no-repeat url(${m.preview_url})`
                : 'linear-gradient(135deg, #1e293b, #0f172a)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <span style={{
              width: 58, height: 58, borderRadius: '50%',
              background: 'rgba(255,255,255,0.92)', color: '#0f172a',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 22, paddingLeft: 4, boxShadow: '0 4px 14px rgba(0,0,0,0.35)',
            }}>
              ▶
            </span>
          </button>
        )}
      </div>
      <div style={{ padding: '10px 12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 8 }}>
          <span style={{ fontWeight: 700, fontSize: 13, color: '#111827' }}>{m.author}</span>
          <span style={{ fontSize: 11, color: '#9ca3af', whiteSpace: 'nowrap' }}>
            {dayLabel(m.posted_at)}{m.likes > 0 && <span style={{ color: '#dc2626' }}> · ♥ {m.likes}</span>}
          </span>
        </div>
        {m.caption && (
          <div style={{ fontSize: 12, color: '#6b7280', marginTop: 3, lineHeight: 1.4 }}>
            {m.caption}
          </div>
        )}
      </div>
    </div>
  );
}

const CommissionerMediaPage = () => {
  const [media, setMedia] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/groupme/media?kind=video&limit=200`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((d) => setMedia(d.media || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  // Group by month, newest first (API is already newest-first)
  const groups = [];
  for (const m of media) {
    const label = monthLabel(m.posted_at);
    const last = groups[groups.length - 1];
    if (last && last.label === label) last.items.push(m);
    else groups.push({ label, items: [m] });
  }

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', padding: '24px 16px' }}>
      <Link to="/livsow" style={{ fontSize: 13, color: '#6b7280', textDecoration: 'none' }}>
        ← LivSow standings
      </Link>

      <div style={{ margin: '12px 0 24px' }}>
        <h1 style={{ margin: 0, fontSize: 26, fontWeight: 800, color: '#111827' }}>
          🎥 Messages from the Commissioner
        </h1>
        <p style={{ margin: '6px 0 0', fontSize: 13, color: '#6b7280' }}>
          Every clip ever posted to the league chat, archived for posterity.
        </p>
      </div>

      {loading && (
        <p style={{ color: '#9ca3af', textAlign: 'center', marginTop: 60 }}>Loading the archive…</p>
      )}
      {error && (
        <p style={{ color: '#dc2626', textAlign: 'center', marginTop: 60 }}>
          Couldn't load the archive: {error}
        </p>
      )}
      {!loading && !error && media.length === 0 && (
        <p style={{ color: '#9ca3af', fontStyle: 'italic', textAlign: 'center', marginTop: 60 }}>
          No videos archived yet — they'll appear after the next harvest.
        </p>
      )}

      {groups.map((g) => (
        <div key={g.label} style={{ marginBottom: 28 }}>
          <h2 style={{
            fontSize: 12, fontWeight: 700, textTransform: 'uppercase',
            letterSpacing: '1px', color: '#6b7280', margin: '0 0 12px',
          }}>
            {g.label}
          </h2>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
            gap: 14,
          }}>
            {g.items.map((m) => (
              <VideoCard key={m.id} m={m} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default CommissionerMediaPage;
