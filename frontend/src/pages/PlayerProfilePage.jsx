import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { apiConfig } from '../config/api.config';

const API_URL = apiConfig.baseUrl;

const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const DAY_NAMES_FULL = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const RARITY_COLORS = {
  common: '#6b7280',
  rare: '#0369a1',
  epic: '#7c3aed',
  legendary: '#d97706',
  mythic: '#dc2626',
};

const formatDate = (iso) => {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
};

const PlayerProfilePage = () => {
  const { playerId } = useParams();
  const navigate = useNavigate();
  const { getAccessTokenSilently } = useAuth0();

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [livsowTeam, setLivsowTeam] = useState(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const token = await getAccessTokenSilently();
        const res = await fetch(`${API_URL}/players/${playerId}/public-profile`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data.detail || `Player not found`);
        }
        const p = await res.json();
        setProfile(p);
        setError(null);
        // Look up LivSow team by name (no auth needed)
        if (p?.name) {
          fetch(`${API_URL}/data/livsow/team-map`)
            .then(r => r.ok ? r.json() : null)
            .then(map => { if (map?.[p.name]) setLivsowTeam(map[p.name]); })
            .catch(() => {});
        }
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [playerId, getAccessTokenSilently]);

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
        <div style={{ fontSize: 40, marginBottom: 12 }}>🏌️</div>
        <p style={{ color: '#dc2626' }}>{error}</p>
        <button onClick={() => navigate(-1)} style={{ marginTop: 12, padding: '8px 20px', borderRadius: 8, border: '1px solid #d1d5db', background: '#fff', cursor: 'pointer' }}>
          Go back
        </button>
      </div>
    );
  }

  const { name, handicap, description, last_played, created_at, available_days, match_history, badges, stats } = profile;

  return (
    <div style={{ maxWidth: 640, margin: '0 auto', padding: '20px 16px' }}>

      {/* Header card */}
      <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 24, marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{
            width: 64, height: 64, borderRadius: '50%',
            background: '#f0fdf4', border: '2px solid #10b981',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 28, flexShrink: 0,
          }}>
            🏌️
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#1f2937' }}>{name}</h1>
            <div style={{ display: 'flex', gap: 12, marginTop: 6, flexWrap: 'wrap', alignItems: 'center' }}>
              <span style={{ fontSize: 13, color: '#6b7280' }}>
                Handicap <strong style={{ color: '#047857' }}>{handicap != null ? handicap : '—'}</strong>
              </span>
              {livsowTeam && (
                <span style={{
                  fontSize: 12, fontWeight: 600, padding: '2px 8px',
                  background: '#eff6ff', color: '#2563eb', borderRadius: 9999,
                  border: '1px solid #bfdbfe',
                }}>
                  ⛳ {livsowTeam.team} · {livsowTeam.role}
                </span>
              )}
              {last_played && (
                <span style={{ fontSize: 13, color: '#6b7280' }}>
                  Last played <strong>{formatDate(last_played)}</strong>
                </span>
              )}
              {created_at && (
                <span style={{ fontSize: 13, color: '#6b7280' }}>
                  Member since <strong>{formatDate(created_at)}</strong>
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Stats row */}
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 12, marginTop: 20, paddingTop: 20,
          borderTop: '1px solid #f3f4f6',
        }}>
          {[
            { label: 'Games', value: stats.games_played },
            { label: 'Wins', value: stats.games_won },
            { label: 'Earnings', value: `${stats.total_earnings >= 0 ? '+' : ''}${stats.total_earnings.toFixed(0)}¢` },
          ].map(({ label, value }) => (
            <div key={label} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 22, fontWeight: 700, color: '#047857' }}>{value}</div>
              <div style={{ fontSize: 12, color: '#6b7280' }}>{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Bio */}
      {description && (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20, marginBottom: 16 }}>
          <p style={{ margin: 0, fontSize: 14, color: '#374151', lineHeight: 1.6 }}>{description}</p>
        </div>
      )}

      {/* Availability days */}
      {available_days.length > 0 && (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20, marginBottom: 16 }}>
          <h2 style={{ margin: '0 0 14px', fontSize: 15, fontWeight: 700, color: '#374151' }}>Plays on</h2>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {DAY_NAMES.map((d, i) => (
              <span key={i} style={{
                padding: '6px 14px', borderRadius: 20, fontSize: 13, fontWeight: 600,
                background: available_days.includes(i) ? '#f0fdf4' : '#f9fafb',
                color: available_days.includes(i) ? '#047857' : '#9ca3af',
                border: `1px solid ${available_days.includes(i) ? '#10b981' : '#e5e7eb'}`,
              }}>
                {d}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Match history */}
      <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20, marginBottom: 16 }}>
        <h2 style={{ margin: '0 0 14px', fontSize: 15, fontWeight: 700, color: '#374151' }}>
          Match History {match_history.length > 0 && <span style={{ fontWeight: 400, color: '#9ca3af', fontSize: 13 }}>({match_history.length})</span>}
        </h2>
        {match_history.length === 0 ? (
          <p style={{ margin: 0, color: '#9ca3af', fontStyle: 'italic', fontSize: 13 }}>No confirmed matches yet</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {match_history.map(m => (
              <div key={m.match_id} style={{
                background: '#f9fafb', borderRadius: 10, padding: '12px 14px',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14, color: '#1f2937' }}>
                    {DAY_NAMES_FULL[m.day_of_week]}
                    {m.suggested_tee_time && (
                      <span style={{ marginLeft: 8, fontSize: 12, fontWeight: 400, color: '#6b7280' }}>
                        {m.suggested_tee_time}
                      </span>
                    )}
                  </div>
                  {m.players.length > 0 && (
                    <div style={{ fontSize: 12, color: '#6b7280', marginTop: 3 }}>
                      with{' '}
                      {m.players.map((p, i) => (
                        <span key={p.id}>
                          <button
                            onClick={() => navigate(`/players/${p.id}`)}
                            style={{ background: 'none', border: 'none', padding: 0, color: '#047857', fontWeight: 600, fontSize: 12, cursor: 'pointer' }}
                          >
                            {p.name}
                          </button>
                          {i < m.players.length - 1 ? ', ' : ''}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <span style={{
                  fontSize: 11, fontWeight: 600, padding: '3px 8px', borderRadius: 6,
                  background: '#d1fae5', color: '#065f46',
                }}>
                  ✓ Confirmed
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Badges */}
      {badges.length > 0 && (
        <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 16, padding: 20 }}>
          <h2 style={{ margin: '0 0 14px', fontSize: 15, fontWeight: 700, color: '#374151' }}>
            Badges <span style={{ fontWeight: 400, color: '#9ca3af', fontSize: 13 }}>({badges.length})</span>
          </h2>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {badges.map((b, i) => (
              <div key={i} title={b.description} style={{
                padding: '6px 12px', borderRadius: 20, fontSize: 12, fontWeight: 600,
                background: '#f9fafb', border: `1px solid ${RARITY_COLORS[b.rarity] || '#e5e7eb'}`,
                color: RARITY_COLORS[b.rarity] || '#374151',
                cursor: 'default',
              }}>
                {b.emoji && <span style={{ marginRight: 5 }}>{b.emoji}</span>}{b.name}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PlayerProfilePage;
