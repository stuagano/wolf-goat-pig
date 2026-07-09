import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiConfig } from '../config/api.config';

const API_URL = apiConfig.baseUrl;

const PlayersRosterPage = () => {
  const navigate = useNavigate();
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_URL}/players/all`);
        if (!res.ok) throw new Error('Failed to load players');
        const data = await res.json();
        const humans = data
          .filter(p => !p.is_ai)
          .sort((a, b) => a.name.localeCompare(b.name));
        setPlayers(humans);
        setError(null);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 80, color: '#6b7280' }}>
        Loading...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ maxWidth: 600, margin: '40px auto', padding: 20, textAlign: 'center' }}>
        <p style={{ color: '#dc2626' }}>{error}</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 720, margin: '0 auto', padding: '20px 16px' }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, color: '#1f2937', marginBottom: 4 }}>Players</h1>
      <p style={{ fontSize: 13, color: '#6b7280', marginTop: 0, marginBottom: 20 }}>
        {players.length} player{players.length === 1 ? '' : 's'}
      </p>

      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12,
      }}>
        {players.map(p => (
          <button
            key={p.id}
            onClick={() => navigate(`/players/${p.id}`)}
            style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
              background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16,
              padding: '20px 12px', cursor: 'pointer', textAlign: 'center',
            }}
          >
            {p.has_avatar_image || p.avatar_url ? (
              <img
                src={p.has_avatar_image ? `${API_URL}/players/${p.id}/avatar` : p.avatar_url}
                alt={p.name}
                style={{
                  width: 56, height: 56, borderRadius: '50%',
                  objectFit: 'cover', border: '2px solid #10b981',
                }}
              />
            ) : (
              <div style={{
                width: 56, height: 56, borderRadius: '50%',
                background: '#f0fdf4', border: '2px solid #10b981',
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 24,
              }}>
                🏌️
              </div>
            )}
            <div style={{ fontWeight: 600, fontSize: 14, color: '#1f2937' }}>{p.name}</div>
            <div style={{ fontSize: 12, color: '#6b7280' }}>
              Handicap {p.handicap != null ? p.handicap : '—'}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default PlayersRosterPage;
