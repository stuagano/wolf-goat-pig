import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { apiConfig } from '../config/api.config';
import { usePlayerProfile } from '../hooks/usePlayerProfile';
import './PlayerProfilePage.css';

const API_URL = apiConfig.baseUrl;

const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const DAY_NAMES_FULL = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const RARITY_ORDER = ['mythic', 'legendary', 'epic', 'rare', 'common'];
const LOCKED_SLOT_COUNT = 4;

const formatDate = (iso) => {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
};

const formatGameDate = (dateStr) => {
  if (!dateStr) return '—';
  // dateStr is "YYYY-MM-DD"; parse as local date to avoid UTC-midnight day-shift.
  const [y, m, d] = dateStr.split('-').map(Number);
  if (!y || !m || !d) return dateStr;
  return new Date(y, m - 1, d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

const formatScore = (q) => `${q >= 0 ? '+' : ''}${q}`;

const PlayerProfilePage = () => {
  const { playerId } = useParams();
  const navigate = useNavigate();
  const { getAccessTokenSilently } = useAuth0();
  const { profile: myProfile } = usePlayerProfile();
  const fileInputRef = useRef(null);

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [livsowTeam, setLivsowTeam] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [avatarVersion, setAvatarVersion] = useState(0);

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/players/${playerId}/public-profile`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Player not found`);
      }
      const p = await res.json();
      setProfile(p);
      setError(null);
      // Look up LivSow team by name (no auth needed). Best-effort — the
      // badge simply doesn't render if this fails.
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

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playerId]);

  const isOwnProfile = myProfile && String(myProfile.id) === String(playerId);

  const handleAvatarFileChange = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = ''; // allow re-selecting the same file later
    if (!file) return;

    setUploading(true);
    setUploadError(null);
    try {
      const token = await getAccessTokenSilently();
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${API_URL}/players/me/avatar`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Upload failed');
      }
      setAvatarVersion(v => v + 1);
      setProfile(p => (p ? { ...p, has_avatar_image: true } : p));
    } catch (e) {
      setUploadError(e.message);
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <div className="wgp-profile">
        <div style={{ display: 'flex', justifyContent: 'center', padding: 80, color: '#6b7280' }}>
          Loading...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="wgp-profile">
        <div style={{ maxWidth: 600, margin: '0 auto', padding: '60px 20px', textAlign: 'center' }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>🏌️</div>
          <p style={{ color: '#9a3412' }}>{error}</p>
          <button onClick={() => navigate(-1)} style={{ marginTop: 12, padding: '8px 20px', borderRadius: 8, border: '1px solid #d1d5db', background: '#fff', cursor: 'pointer' }}>
            Go back
          </button>
        </div>
      </div>
    );
  }

  const { name, handicap, description, avatar_url, has_avatar_image, last_played, created_at, available_days, match_history, game_history, badges, stats } = profile;
  const avatarSrc = has_avatar_image
    ? `${API_URL}/players/${playerId}/avatar${avatarVersion ? `?v=${avatarVersion}` : ''}`
    : avatar_url;

  const badgesByRarity = [...badges].sort(
    (a, b) => RARITY_ORDER.indexOf(a.rarity) - RARITY_ORDER.indexOf(b.rarity)
  );
  const lockedSlots = Math.max(0, LOCKED_SLOT_COUNT - badges.length);

  return (
    <div className="wgp-profile">
      <div className="wgp-profile__inner">

        {/* Header */}
        <div className="wgp-profile__section">
          <div className="wgp-profile__header-row">
            <div
              className={`wgp-profile__avatar-frame${isOwnProfile ? ' wgp-profile__avatar-frame--clickable' : ''}`}
              onClick={() => isOwnProfile && fileInputRef.current?.click()}
              title={isOwnProfile ? 'Change photo' : undefined}
            >
              {avatarSrc ? (
                <img
                  className="wgp-profile__avatar"
                  src={avatarSrc}
                  alt={name}
                  style={{ opacity: uploading ? 0.5 : 1 }}
                />
              ) : (
                <div className="wgp-profile__avatar-fallback" style={{ opacity: uploading ? 0.5 : 1 }}>
                  🏌️
                </div>
              )}
              {isOwnProfile && <div className="wgp-profile__camera-badge">📷</div>}
            </div>
            {isOwnProfile && (
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp,image/heic,image/heif"
                style={{ display: 'none' }}
                onChange={handleAvatarFileChange}
              />
            )}
            <div style={{ flex: 1, minWidth: 0 }}>
              <h1 className="wgp-profile__name">{name}</h1>
              <div className="wgp-profile__meta-row">
                <span>Handicap <strong>{handicap != null ? handicap : '—'}</strong></span>
                {livsowTeam && (
                  <span className="wgp-profile__livsow-pill">
                    ⛳ {livsowTeam.team} · {livsowTeam.role}
                  </span>
                )}
                {last_played && <span>Last played <strong>{formatDate(last_played)}</strong></span>}
                {created_at && <span>Member since <strong>{formatDate(created_at)}</strong></span>}
              </div>
              {uploadError && <div className="wgp-profile__upload-error">{uploadError}</div>}
            </div>
          </div>

          <div className="wgp-profile__scoreboard">
            {[
              { label: 'Games', value: stats.games_played },
              { label: 'Wins', value: stats.games_won },
              { label: 'Earnings', value: `${stats.total_earnings >= 0 ? '+' : ''}${stats.total_earnings.toFixed(0)}¢` },
            ].map(({ label, value }) => (
              <div key={label} className="wgp-profile__stat">
                <div className="wgp-profile__stat-value">{value}</div>
                <div className="wgp-profile__stat-label">{label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Bio */}
        {description && (
          <div className="wgp-profile__section">
            <p className="wgp-profile__bio">&ldquo;{description}&rdquo;</p>
          </div>
        )}

        {/* Availability days */}
        {available_days.length > 0 && (
          <div className="wgp-profile__section">
            <span className="wgp-profile__section-title">Plays on</span>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {DAY_NAMES.map((d, i) => (
                <span
                  key={i}
                  className={`wgp-profile__day-pill${available_days.includes(i) ? ' wgp-profile__day-pill--active' : ''}`}
                >
                  {d}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Match history */}
        <div className="wgp-profile__section">
          <span className="wgp-profile__section-title">
            Match History {match_history.length > 0 && <span className="wgp-profile__section-count">({match_history.length})</span>}
          </span>
          {match_history.length === 0 ? (
            <p className="wgp-profile__empty">No confirmed matches yet</p>
          ) : (
            <div className="wgp-profile__ledger">
              {match_history.map(m => (
                <div key={m.match_id} className="wgp-profile__ledger-row">
                  <div>
                    <div className="wgp-profile__ledger-primary">
                      {DAY_NAMES_FULL[m.day_of_week]}
                      {m.suggested_tee_time && (
                        <span className="wgp-profile__ledger-secondary">{m.suggested_tee_time}</span>
                      )}
                    </div>
                    {m.players.length > 0 && (
                      <div className="wgp-profile__ledger-sub">
                        with{' '}
                        {m.players.map((p, i) => (
                          <span key={p.id}>
                            <button onClick={() => navigate(`/players/${p.id}`)} className="wgp-profile__link">
                              {p.name}
                            </button>
                            {i < m.players.length - 1 ? ', ' : ''}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <span className="wgp-profile__confirmed">✓ Confirmed</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Game history — actual played/scored rounds */}
        <div className="wgp-profile__section">
          <span className="wgp-profile__section-title">
            Game History {game_history.length > 0 && <span className="wgp-profile__section-count">({game_history.length})</span>}
          </span>
          {game_history.length === 0 ? (
            <p className="wgp-profile__empty">No recorded rounds yet</p>
          ) : (
            <div className="wgp-profile__ledger">
              {game_history.map((g, i) => (
                <div key={`${g.date}-${i}`} className="wgp-profile__ledger-row">
                  <div className="wgp-profile__ledger-primary">
                    {formatGameDate(g.date)}
                    {g.location && <span className="wgp-profile__ledger-secondary">{g.location}</span>}
                  </div>
                  <span className={`wgp-profile__score ${g.score >= 0 ? 'wgp-profile__score--win' : 'wgp-profile__score--loss'}`}>
                    {formatScore(g.score)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Badges — always visible, even at zero, so the badge system is discoverable */}
        <div className="wgp-profile__section">
          <span className="wgp-profile__section-title">
            Badges {badges.length > 0 && <span className="wgp-profile__section-count">({badges.length})</span>}
          </span>
          <div className="wgp-profile__badges">
            {badgesByRarity.map((b, i) => (
              <div key={i} className="wgp-profile__badge" title={b.description}>
                <div className={`wgp-profile__medallion wgp-profile__medallion--${b.rarity || 'common'}`}>
                  {b.emoji || '🏅'}
                </div>
                <div className="wgp-profile__badge-name">{b.name}</div>
              </div>
            ))}
            {Array.from({ length: lockedSlots }).map((_, i) => (
              <div key={`locked-${i}`} className="wgp-profile__badge" title="Not earned yet">
                <div className="wgp-profile__medallion wgp-profile__medallion--locked">🔒</div>
                <div className="wgp-profile__badge-name">Locked</div>
              </div>
            ))}
          </div>
          {badges.length === 0 && (
            <p className="wgp-profile__badges-hint">No badges earned yet — keep playing to unlock some!</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default PlayerProfilePage;
