import React, { useState, useEffect, useCallback } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { useTheme } from '../theme/Provider';

const STORAGE_KEY = 'wgp_account_settings';

const loadSettings = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return JSON.parse(stored);
  } catch {
    // ignore
  }
  return null;
};

const saveSettings = (settings) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch {
    // ignore
  }
};

/**
 * Gather personal stats from localStorage game history
 */
const gatherStats = () => {
  const stats = {
    gamesPlayed: 0,
    gamesWon: 0,
    totalEarnings: 0,
    averageScore: 0,
    bestScore: null,
    recentGames: [],
  };

  try {
    // Scan localStorage for completed game data
    const keys = Object.keys(localStorage);
    const gameKeys = keys.filter(k => k.startsWith('wgp_game_result_') || k.startsWith('wgp_completed_'));
    const sessionKeys = keys.filter(k => k.startsWith('wgp_session_'));

    let totalScores = 0;
    let scoreCount = 0;

    // Check completed game results
    gameKeys.forEach(key => {
      try {
        const data = JSON.parse(localStorage.getItem(key));
        if (data) {
          stats.gamesPlayed++;
          if (data.won || data.position === 1) stats.gamesWon++;
          if (typeof data.earnings === 'number') stats.totalEarnings += data.earnings;
          if (typeof data.totalScore === 'number') {
            totalScores += data.totalScore;
            scoreCount++;
            if (stats.bestScore === null || data.totalScore < stats.bestScore) {
              stats.bestScore = data.totalScore;
            }
          }
          if (data.date || data.completedAt) {
            stats.recentGames.push({
              date: data.date || data.completedAt,
              score: data.totalScore,
              earnings: data.earnings,
              course: data.courseName || data.course,
            });
          }
        }
      } catch {
        // skip malformed entries
      }
    });

    // Also check session data for completed sessions
    sessionKeys.forEach(key => {
      try {
        const data = JSON.parse(localStorage.getItem(key));
        if (data && data.status === 'completed') {
          // Avoid double-counting if already counted above
          const gameId = key.replace('wgp_session_', '');
          const alreadyCounted = gameKeys.some(gk => gk.includes(gameId));
          if (!alreadyCounted) {
            stats.gamesPlayed++;
          }
        }
      } catch {
        // skip
      }
    });

    if (scoreCount > 0) {
      stats.averageScore = Math.round(totalScores / scoreCount);
    }

    // Sort recent games by date, newest first
    stats.recentGames.sort((a, b) => new Date(b.date) - new Date(a.date));
    stats.recentGames = stats.recentGames.slice(0, 5);
  } catch {
    // If anything fails, return defaults
  }

  return stats;
};

function AccountPage() {
  const { user, isAuthenticated, logout } = useAuth0();
  const theme = useTheme();
  const useMockAuth = process.env.REACT_APP_USE_MOCK_AUTH === 'true';

  const [editing, setEditing] = useState(false);
  const [saved, setSaved] = useState(false);
  const [stats, setStats] = useState(null);
  const [settings, setSettings] = useState({
    displayName: '',
    handicap: '',
    homeCourse: 'Wing Point Golf & Country Club',
    preferredTees: 'white',
    bettingStyle: 'moderate',
  });

  // Load settings and stats
  useEffect(() => {
    const stored = loadSettings();
    if (stored) {
      setSettings(prev => ({ ...prev, ...stored }));
    } else if (user?.name) {
      setSettings(prev => ({ ...prev, displayName: user.name }));
    }
    setStats(gatherStats());
  }, [user]);

  const handleSave = useCallback(() => {
    saveSettings(settings);
    setEditing(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }, [settings]);

  const handleChange = (field, value) => {
    setSettings(prev => ({ ...prev, [field]: value }));
  };

  const handleLogout = () => {
    logout({ logoutParams: { returnTo: window.location.origin } });
  };

  // Styles
  const containerStyle = {
    maxWidth: '700px',
    margin: '0 auto',
    padding: '24px 16px 100px',
  };

  const cardStyle = {
    ...theme.cardStyle,
    marginBottom: '20px',
    padding: '24px',
  };

  const sectionTitle = {
    fontSize: '18px',
    fontWeight: 700,
    color: theme.colors.textPrimary,
    marginBottom: '16px',
    margin: 0,
  };

  const labelStyle = {
    display: 'block',
    fontSize: '13px',
    fontWeight: 600,
    color: theme.colors.textSecondary,
    marginBottom: '6px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  };

  const valueStyle = {
    fontSize: '16px',
    color: theme.colors.textPrimary,
    fontWeight: 500,
  };

  const inputStyle = {
    ...theme.inputStyle,
    boxSizing: 'border-box',
    marginBottom: '16px',
  };

  const selectStyle = {
    ...inputStyle,
    appearance: 'auto',
  };

  const statBoxStyle = {
    textAlign: 'center',
    padding: '16px 8px',
    background: theme.isDark ? theme.colors.gray200 : theme.colors.gray50,
    borderRadius: '12px',
    flex: '1 1 0',
    minWidth: '0',
  };

  const statValueStyle = {
    fontSize: '24px',
    fontWeight: 700,
    color: theme.colors.primary,
    lineHeight: 1.2,
  };

  const statLabelStyle = {
    fontSize: '12px',
    color: theme.colors.textSecondary,
    marginTop: '4px',
    fontWeight: 500,
  };

  return (
    <div style={containerStyle}>
      {/* Profile Header */}
      <div style={{
        ...cardStyle,
        display: 'flex',
        alignItems: 'center',
        gap: '20px',
        padding: '28px 24px',
      }}>
        {/* Avatar */}
        <div style={{
          width: '72px',
          height: '72px',
          borderRadius: '50%',
          overflow: 'hidden',
          flexShrink: 0,
          border: `3px solid ${theme.colors.primary}`,
          background: theme.colors.gray200,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          {user?.picture ? (
            <img
              src={user.picture}
              alt={user.name || 'Profile'}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          ) : (
            <span style={{ fontSize: '32px', color: theme.colors.primary, fontWeight: 700 }}>
              {(settings.displayName || user?.name || 'U').charAt(0).toUpperCase()}
            </span>
          )}
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontSize: '22px',
            fontWeight: 700,
            color: theme.colors.textPrimary,
            marginBottom: '4px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}>
            {settings.displayName || user?.name || 'Player'}
          </div>
          <div style={{
            fontSize: '14px',
            color: theme.colors.textSecondary,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}>
            {user?.email || ''}
          </div>
          {settings.handicap && (
            <div style={{
              display: 'inline-block',
              marginTop: '8px',
              padding: '4px 12px',
              background: theme.isDark ? 'rgba(16, 185, 129, 0.15)' : 'rgba(4, 120, 87, 0.1)',
              color: theme.colors.primary,
              borderRadius: '20px',
              fontSize: '13px',
              fontWeight: 600,
            }}>
              Handicap: {settings.handicap}
            </div>
          )}
        </div>
      </div>

      {/* Personal Stats */}
      <div style={cardStyle}>
        <h3 style={sectionTitle}>Personal Stats</h3>

        {stats && stats.gamesPlayed > 0 ? (
          <>
            <div style={{
              display: 'flex',
              gap: '12px',
              marginTop: '16px',
              flexWrap: 'wrap',
            }}>
              <div style={statBoxStyle}>
                <div style={statValueStyle}>{stats.gamesPlayed}</div>
                <div style={statLabelStyle}>Games Played</div>
              </div>
              <div style={statBoxStyle}>
                <div style={statValueStyle}>{stats.gamesWon}</div>
                <div style={statLabelStyle}>Wins</div>
              </div>
              <div style={statBoxStyle}>
                <div style={{
                  ...statValueStyle,
                  color: stats.totalEarnings >= 0 ? theme.colors.success : theme.colors.error,
                }}>
                  {stats.totalEarnings >= 0 ? '+' : ''}{stats.totalEarnings.toFixed(0)}
                </div>
                <div style={statLabelStyle}>Earnings</div>
              </div>
            </div>

            <div style={{
              display: 'flex',
              gap: '12px',
              marginTop: '12px',
              flexWrap: 'wrap',
            }}>
              {stats.averageScore > 0 && (
                <div style={statBoxStyle}>
                  <div style={statValueStyle}>{stats.averageScore}</div>
                  <div style={statLabelStyle}>Avg Score</div>
                </div>
              )}
              {stats.bestScore !== null && (
                <div style={statBoxStyle}>
                  <div style={statValueStyle}>{stats.bestScore}</div>
                  <div style={statLabelStyle}>Best Score</div>
                </div>
              )}
              {stats.gamesPlayed > 0 && (
                <div style={statBoxStyle}>
                  <div style={statValueStyle}>
                    {stats.gamesPlayed > 0 ? Math.round((stats.gamesWon / stats.gamesPlayed) * 100) : 0}%
                  </div>
                  <div style={statLabelStyle}>Win Rate</div>
                </div>
              )}
            </div>

            {/* Recent Games */}
            {stats.recentGames.length > 0 && (
              <div style={{ marginTop: '20px' }}>
                <div style={{
                  fontSize: '14px',
                  fontWeight: 600,
                  color: theme.colors.textSecondary,
                  marginBottom: '10px',
                }}>
                  Recent Games
                </div>
                {stats.recentGames.map((game, i) => (
                  <div key={i} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '10px 12px',
                    background: i % 2 === 0
                      ? (theme.isDark ? theme.colors.gray100 : theme.colors.gray50)
                      : 'transparent',
                    borderRadius: '8px',
                  }}>
                    <div>
                      <div style={{ fontSize: '14px', color: theme.colors.textPrimary, fontWeight: 500 }}>
                        {game.course || 'Round'}
                      </div>
                      <div style={{ fontSize: '12px', color: theme.colors.textSecondary }}>
                        {new Date(game.date).toLocaleDateString()}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      {game.score != null && (
                        <div style={{ fontSize: '14px', fontWeight: 600, color: theme.colors.textPrimary }}>
                          {game.score}
                        </div>
                      )}
                      {game.earnings != null && (
                        <div style={{
                          fontSize: '12px',
                          fontWeight: 600,
                          color: game.earnings >= 0 ? theme.colors.success : theme.colors.error,
                        }}>
                          {game.earnings >= 0 ? '+' : ''}{game.earnings.toFixed(2)}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <div style={{
            textAlign: 'center',
            padding: '32px 16px',
            color: theme.colors.textSecondary,
          }}>
            <div style={{ fontSize: '40px', marginBottom: '12px' }}>
              {isAuthenticated ? '🏌️' : '🔒'}
            </div>
            <p style={{ margin: 0, fontSize: '15px' }}>
              {isAuthenticated
                ? 'No game data yet. Play some rounds to see your stats here!'
                : 'Log in to track your personal stats.'}
            </p>
          </div>
        )}
      </div>

      {/* Account Settings */}
      <div style={cardStyle}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px',
        }}>
          <h3 style={{ ...sectionTitle, marginBottom: 0 }}>Account Settings</h3>
          {!editing ? (
            <button
              onClick={() => setEditing(true)}
              style={{
                ...theme.buttonStyle,
                padding: '8px 16px',
                fontSize: '14px',
                background: 'transparent',
                color: theme.colors.primary,
                border: `1px solid ${theme.colors.primary}`,
              }}
            >
              Edit
            </button>
          ) : (
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => setEditing(false)}
                style={{
                  ...theme.buttonStyle,
                  padding: '8px 16px',
                  fontSize: '14px',
                  background: theme.colors.gray200,
                  color: theme.colors.textPrimary,
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                style={{
                  ...theme.buttonStyle,
                  padding: '8px 16px',
                  fontSize: '14px',
                }}
              >
                Save
              </button>
            </div>
          )}
        </div>

        {saved && (
          <div style={{
            padding: '10px 16px',
            background: theme.isDark ? 'rgba(16, 185, 129, 0.15)' : '#ecfdf5',
            color: theme.colors.success,
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: 500,
            marginBottom: '16px',
          }}>
            Settings saved successfully
          </div>
        )}

        {editing ? (
          <div>
            <label style={labelStyle}>Display Name</label>
            <input
              type="text"
              value={settings.displayName}
              onChange={(e) => handleChange('displayName', e.target.value)}
              placeholder="Your display name"
              style={inputStyle}
            />

            <label style={labelStyle}>Handicap</label>
            <input
              type="number"
              min="0"
              max="54"
              step="0.1"
              value={settings.handicap}
              onChange={(e) => handleChange('handicap', e.target.value)}
              placeholder="e.g., 12.5"
              style={inputStyle}
            />

            <label style={labelStyle}>Home Course</label>
            <input
              type="text"
              value={settings.homeCourse}
              onChange={(e) => handleChange('homeCourse', e.target.value)}
              placeholder="Your home course"
              style={inputStyle}
            />

            <label style={labelStyle}>Preferred Tees</label>
            <select
              value={settings.preferredTees}
              onChange={(e) => handleChange('preferredTees', e.target.value)}
              style={selectStyle}
            >
              <option value="red">Red</option>
              <option value="white">White</option>
              <option value="blue">Blue</option>
              <option value="black">Black</option>
              <option value="gold">Gold</option>
            </select>

            <label style={labelStyle}>Betting Style</label>
            <select
              value={settings.bettingStyle}
              onChange={(e) => handleChange('bettingStyle', e.target.value)}
              style={selectStyle}
            >
              <option value="conservative">Conservative</option>
              <option value="moderate">Moderate</option>
              <option value="aggressive">Aggressive</option>
            </select>
          </div>
        ) : (
          <div>
            <SettingRow
              label="Display Name"
              value={settings.displayName || user?.name || 'Not set'}
              theme={theme}
            />
            <SettingRow
              label="Handicap"
              value={settings.handicap || 'Not set'}
              theme={theme}
            />
            <SettingRow
              label="Home Course"
              value={settings.homeCourse || 'Not set'}
              theme={theme}
            />
            <SettingRow
              label="Preferred Tees"
              value={settings.preferredTees
                ? settings.preferredTees.charAt(0).toUpperCase() + settings.preferredTees.slice(1)
                : 'Not set'}
              theme={theme}
            />
            <SettingRow
              label="Betting Style"
              value={settings.bettingStyle
                ? settings.bettingStyle.charAt(0).toUpperCase() + settings.bettingStyle.slice(1)
                : 'Not set'}
              theme={theme}
              noBorder
            />
          </div>
        )}
      </div>

      {/* Auth Info */}
      {isAuthenticated && (
        <div style={cardStyle}>
          <h3 style={sectionTitle}>Account</h3>
          <SettingRow
            label="Email"
            value={user?.email || 'N/A'}
            theme={theme}
          />
          <SettingRow
            label="Auth Provider"
            value={useMockAuth ? 'Mock (Dev)' : 'Auth0'}
            theme={theme}
            noBorder
          />
        </div>
      )}

      {/* Logout Button */}
      {isAuthenticated && !useMockAuth && (
        <button
          onClick={handleLogout}
          style={{
            width: '100%',
            padding: '16px',
            background: 'transparent',
            color: theme.colors.error,
            border: `2px solid ${theme.colors.error}`,
            borderRadius: '12px',
            fontSize: '16px',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all 0.2s',
            marginBottom: '20px',
          }}
        >
          Log Out
        </button>
      )}
    </div>
  );
}

function SettingRow({ label, value, theme, noBorder = false }) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '14px 0',
      borderBottom: noBorder ? 'none' : `1px solid ${theme.colors.border}`,
    }}>
      <span style={{
        fontSize: '14px',
        color: theme.colors.textSecondary,
        fontWeight: 500,
      }}>
        {label}
      </span>
      <span style={{
        fontSize: '15px',
        color: theme.colors.textPrimary,
        fontWeight: 500,
        textAlign: 'right',
        maxWidth: '60%',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
      }}>
        {value}
      </span>
    </div>
  );
}

export default AccountPage;
