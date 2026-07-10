import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { apiConfig } from '../config/api.config';
import { usePlayerProfile } from '../hooks/usePlayerProfile';
import '../styles/clubhouse-theme.css';
import './PlayerProfilePage.css';

const API_URL = apiConfig.baseUrl;

const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const RARITY_ORDER = ['mythic', 'legendary', 'epic', 'rare', 'common'];
const LOCKED_PREVIEW_COUNT = 3;

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
  const [togglingBadgeId, setTogglingBadgeId] = useState(null);
  const [showcaseError, setShowcaseError] = useState(null);
  const [expandedRound, setExpandedRound] = useState(null);

  const load = async (silent = false) => {
    if (!silent) setLoading(true);
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

  const handleToggleShowcase = async (badgeEarnedId) => {
    setTogglingBadgeId(badgeEarnedId);
    setShowcaseError(null);
    try {
      const token = await getAccessTokenSilently();
      const res = await fetch(`${API_URL}/api/badges/me/${badgeEarnedId}/showcase`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Could not update showcase');
      }
      await load(true);
    } catch (e) {
      setShowcaseError(e.message);
    } finally {
      setTogglingBadgeId(null);
    }
  };

  if (loading) {
    return (
      <div className="wgp-clubhouse wgp-profile">
        <div style={{ display: 'flex', justifyContent: 'center', padding: 80, color: '#6b7280' }}>
          Loading...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="wgp-clubhouse wgp-profile">
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

  const { name, handicap, description, avatar_url, has_avatar_image, last_played, created_at, available_days, game_history, badges, total_badges, stats } = profile;
  const avatarSrc = has_avatar_image
    ? `${API_URL}/players/${playerId}/avatar${avatarVersion ? `?v=${avatarVersion}` : ''}`
    : avatar_url;

  const badgesByRarity = [...badges].sort((a, b) => {
    if (a.showcased !== b.showcased) return a.showcased ? -1 : 1;
    return RARITY_ORDER.indexOf(a.rarity) - RARITY_ORDER.indexOf(b.rarity);
  });
  const remainingBadges = Math.max(0, (total_badges ?? badges.length) - badges.length);
  const lockedSlots = Math.min(remainingBadges, LOCKED_PREVIEW_COUNT);

  const roundsWithoutDetail = game_history.filter(g => !g.holes || g.holes.length === 0).length;

  return (
    <div className="wgp-clubhouse wgp-profile">
      <div className="wgp-clubhouse__inner wgp-profile__inner">

        {/* Header */}
        <div className="wgp-clubhouse__section">
          <div className="wgp-profile__header-row">
            <div
              className={`wgp-clubhouse__avatar-frame${isOwnProfile ? ' wgp-clubhouse__avatar-frame--clickable' : ''}`}
              onClick={() => isOwnProfile && fileInputRef.current?.click()}
              title={isOwnProfile ? 'Change photo' : undefined}
            >
              {avatarSrc ? (
                <img
                  className="wgp-clubhouse__avatar"
                  src={avatarSrc}
                  alt={name}
                  style={{ opacity: uploading ? 0.5 : 1 }}
                />
              ) : (
                <div className="wgp-clubhouse__avatar-fallback" style={{ opacity: uploading ? 0.5 : 1 }}>
                  🏌️
                </div>
              )}
              {isOwnProfile && <div className="wgp-clubhouse__camera-badge">📷</div>}
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
          <div className="wgp-clubhouse__section">
            <p className="wgp-profile__bio">&ldquo;{description}&rdquo;</p>
          </div>
        )}

        {/* Availability days */}
        {available_days.length > 0 && (
          <div className="wgp-clubhouse__section">
            <span className="wgp-clubhouse__section-title">Plays on</span>
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

        {/* Game history — actual played/scored rounds */}
        <div className="wgp-clubhouse__section">
          <span className="wgp-clubhouse__section-title">
            Game History {game_history.length > 0 && <span className="wgp-clubhouse__section-count">({game_history.length})</span>}
          </span>
          {game_history.length === 0 ? (
            <p className="wgp-clubhouse__empty">No recorded rounds yet</p>
          ) : (
            <div className="wgp-profile__ledger">
              {game_history.map((g, i) => {
                const hasHoleDetail = Array.isArray(g.holes) && g.holes.length > 0;
                const isExpanded = expandedRound === i;
                return (
                  <div key={`${g.date}-${i}`} className="wgp-profile__ledger-item">
                    <div
                      className={`wgp-profile__ledger-row${hasHoleDetail ? ' wgp-profile__ledger-row--clickable' : ''}`}
                      onClick={() => hasHoleDetail && setExpandedRound(isExpanded ? null : i)}
                    >
                      <div className="wgp-profile__ledger-primary">
                        {formatGameDate(g.date)}
                        {g.location && <span className="wgp-profile__ledger-secondary">{g.location}</span>}
                        {hasHoleDetail && <span className="wgp-profile__ledger-expand-hint">{isExpanded ? '▲' : '▾'} hole-by-hole</span>}
                      </div>
                      <span className={`wgp-profile__score ${g.score >= 0 ? 'wgp-profile__score--win' : 'wgp-profile__score--loss'}`}>
                        {formatScore(g.score)}
                      </span>
                    </div>
                    {hasHoleDetail && isExpanded && (
                      <div className="wgp-profile__holes-grid">
                        {g.holes.map(h => (
                          <div key={h.hole} className="wgp-profile__hole-cell">
                            <div className="wgp-profile__hole-num">{h.hole}</div>
                            <div className={`wgp-profile__hole-quarters ${h.quarters >= 0 ? 'wgp-profile__score--win' : 'wgp-profile__score--loss'}`}>
                              {formatScore(h.quarters)}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
          {roundsWithoutDetail > 0 && (
            <p className="wgp-profile__badges-hint">
              💡 Score live in the app or scan your scorecard to capture hole-by-hole detail for future rounds
              {game_history.length > roundsWithoutDetail ? ` (${game_history.length - roundsWithoutDetail} of ${game_history.length} rounds already have it)` : ''}.
            </p>
          )}
        </div>

        {/* Badges — always visible, even at zero, so the badge system is discoverable */}
        <div className="wgp-clubhouse__section">
          <span className="wgp-clubhouse__section-title">
            Badges{' '}
            <span className="wgp-clubhouse__section-count">
              ({badges.length}{total_badges != null ? ` of ${total_badges}` : ''})
            </span>
          </span>
          <div className="wgp-profile__badges">
            {badgesByRarity.map((b, i) => (
              <div
                key={i}
                className={`wgp-profile__badge${isOwnProfile ? ' wgp-profile__badge--clickable' : ''}`}
                title={isOwnProfile ? (b.showcased ? 'Click to unequip' : 'Click to equip on your showcase') : b.description}
                onClick={() => isOwnProfile && togglingBadgeId === null && handleToggleShowcase(b.id)}
                style={{ opacity: togglingBadgeId === b.id ? 0.5 : 1 }}
              >
                <div className={`wgp-profile__medallion wgp-profile__medallion--${b.rarity || 'common'}`}>
                  {b.emoji || '🏅'}
                  {b.showcased && <div className="wgp-profile__equipped-mark">★</div>}
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
          {showcaseError && <div className="wgp-profile__upload-error">{showcaseError}</div>}
          {badges.length === 0 && (
            <p className="wgp-profile__badges-hint">No badges earned yet — keep playing to unlock some!</p>
          )}
          {badges.length > 0 && remainingBadges > 0 && (
            <p className="wgp-profile__badges-hint">{remainingBadges} more to unlock</p>
          )}
          {isOwnProfile && badges.length > 0 && (
            <p className="wgp-profile__badges-hint">Click a badge to showcase it on your profile (up to 6)</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default PlayerProfilePage;
