import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiConfig } from '../config/api.config';
import '../styles/clubhouse-theme.css';
import './PlayersRosterPage.css';

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
      <div className="wgp-clubhouse wgp-roster">
        <div style={{ display: 'flex', justifyContent: 'center', padding: 80, color: '#6b7280' }}>
          Loading...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="wgp-clubhouse wgp-roster">
        <div style={{ maxWidth: 600, margin: '0 auto', padding: '60px 20px', textAlign: 'center' }}>
          <p style={{ color: '#9a3412' }}>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="wgp-clubhouse wgp-roster">
      <div className="wgp-clubhouse__inner wgp-roster__inner">
        <h1 className="wgp-roster__heading">Players</h1>
        <p className="wgp-roster__subheading">
          {players.length} player{players.length === 1 ? '' : 's'}
        </p>

        <div className="wgp-roster__grid">
          {players.map(p => (
            <button
              key={p.id}
              onClick={() => navigate(`/players/${p.id}`)}
              className="wgp-clubhouse__section wgp-roster__card"
            >
              {p.has_avatar_image || p.avatar_url ? (
                <img
                  className="wgp-clubhouse__avatar"
                  src={p.has_avatar_image ? `${API_URL}/players/${p.id}/avatar` : p.avatar_url}
                  alt={p.name}
                />
              ) : (
                <div className="wgp-clubhouse__avatar-fallback">🏌️</div>
              )}
              <div className="wgp-roster__name">{p.name}</div>
              <div className="wgp-roster__handicap">
                Handicap {p.handicap != null ? p.handicap : '—'}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PlayersRosterPage;
