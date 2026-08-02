import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTheme } from '../theme/Provider';
import { useAuth0 } from '@auth0/auth0-react';
import { Input } from '../components/ui';
import { apiConfig } from '../config/api.config';

const API_URL = apiConfig.baseUrl;

const normalizeName = (name) => (name || '').toLowerCase().replace(/[^a-z0-9]+/g, '');

const suggestionByName = (name, list) => {
  const key = normalizeName(name);
  if (!key) return null;
  const exact = list.find((s) => normalizeName(s.name) === key);
  if (exact) return exact;
  const prefixed = list.filter((s) => normalizeName(s.name).startsWith(key));
  return prefixed.length === 1 ? prefixed[0] : null;
};

function JoinGamePage() {
  const theme = useTheme();
  const navigate = useNavigate();
  const { code } = useParams();
  const { user, isAuthenticated } = useAuth0();

  const [joinCode, setJoinCode] = useState(code || '');
  const [playerName, setPlayerName] = useState('');
  const [handicap, setHandicap] = useState('18');
  const [handicapTouched, setHandicapTouched] = useState(false);
  const [playerProfileId, setPlayerProfileId] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${API_URL}/games/roster-suggestions`)
      .then((res) => (res.ok ? res.json() : null))
      .then((d) => { if (d?.players) setSuggestions(d.players); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (isAuthenticated && user?.name && !playerName) {
      setPlayerName(user.name);
    }
  }, [isAuthenticated, user, playerName]);

  // Once suggestions load, resolve the Auth0 / typed name against the roster.
  useEffect(() => {
    if (!playerName || !suggestions.length || handicapTouched) return;
    const match = suggestionByName(playerName, suggestions);
    if (!match) return;
    setPlayerProfileId(match.player_profile_id ?? null);
    if (match.handicap != null) setHandicap(String(match.handicap));
  }, [suggestions, playerName, handicapTouched]);

  const onNameChange = (name) => {
    setPlayerName(name);
    const match = suggestionByName(name, suggestions);
    if (!match) {
      setPlayerProfileId(null);
      return;
    }
    setPlayerProfileId(match.player_profile_id ?? null);
    if (!handicapTouched) setHandicap(String(match.handicap ?? 18));
  };

  const onNameBlur = () => {
    const match = suggestionByName(playerName, suggestions);
    if (match && match.name !== playerName) setPlayerName(match.name);
  };

  const handicapNote = () => {
    if (handicapTouched) return { text: 'Handicap set by hand for this round', color: '#b45309' };
    if (playerProfileId) return { text: `Roster handicap ${handicap}`, color: '#15803d' };
    if (playerName.trim()) return { text: 'Not on the roster — will play off 18', color: '#b45309' };
    return null;
  };

  const joinGame = async (e) => {
    e.preventDefault();

    if (!joinCode.trim()) {
      setError('Please enter a join code');
      return;
    }

    if (!playerName.trim()) {
      setError('Please enter your name');
      return;
    }

    if (handicapTouched && (handicap === '' || Number.isNaN(parseFloat(handicap)) || parseFloat(handicap) < 0)) {
      setError('Please enter a valid handicap');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const requestBody = {
        player_name: playerName.trim(),
        // null lets the server use the roster; only a typed number overrides.
        handicap: handicapTouched ? parseFloat(handicap) : null,
        player_profile_id: playerProfileId,
      };

      if (isAuthenticated && user?.sub) {
        requestBody.user_id = user.sub;
      }

      const response = await fetch(`${API_URL}/games/join/${joinCode.toUpperCase()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to join game');
      }

      if (data.status === 'joined' || data.status === 'already_joined') {
        const sessionData = {
          gameId: data.game_id,
          playerName: playerName.trim(),
          handicap: data.handicap ?? (handicapTouched ? parseFloat(handicap) : null),
          joinCode: joinCode.toUpperCase(),
          timestamp: Date.now(),
          userId: isAuthenticated ? user?.sub : null,
        };
        localStorage.setItem(`wgp_session_${data.game_id}`, JSON.stringify(sessionData));
        localStorage.setItem('wgp_current_game', data.game_id);
        navigate(`/lobby/${data.game_id}`);
      } else {
        throw new Error(data.message || 'Unexpected response');
      }
    } catch (err) {
      console.error('Error joining game:', err);
      setError(err.message || 'Failed to join game. Please check the code and try again.');
    } finally {
      setLoading(false);
    }
  };

  const note = handicapNote();
  const labelStyle = {
    display: 'block',
    fontWeight: 600,
    marginBottom: 8,
    color: theme.colors.textPrimary,
  };
  const inputStyle = {
    width: '100%',
    padding: 12,
    fontSize: 16,
    borderRadius: 8,
    border: `1px solid ${theme.colors.border}`,
    background: theme.colors.paper,
  };

  return (
    <div style={{
      maxWidth: 500,
      margin: '0 auto',
      padding: 20,
      fontFamily: theme.typography.fontFamily,
    }}>
      <div style={theme.cardStyle}>
        <h1 style={{ color: theme.colors.primary, marginBottom: 8 }}>
          🎯 Join Game
        </h1>
        <p style={{ color: theme.colors.textSecondary, marginBottom: 24 }}>
          Enter the join code your friend shared with you
        </p>

        <form onSubmit={joinGame}>
          <div style={{ marginBottom: 20 }}>
            <label style={labelStyle}>Join Code:</label>
            <Input
              type="text"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
              placeholder="ABC123"
              maxLength={6}
              variant="inline"
              inputStyle={{
                ...inputStyle,
                fontSize: 20,
                fontWeight: 700,
                textAlign: 'center',
                letterSpacing: 4,
                border: `2px solid ${theme.colors.border}`,
                textTransform: 'uppercase',
              }}
              required
            />
            <p style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 4 }}>
              6-character code from game creator
            </p>
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={labelStyle}>Your Name:</label>
            <datalist id="join-roster-suggestions">
              {suggestions.map((s) => <option key={s.name} value={s.name} />)}
            </datalist>
            <Input
              type="text"
              list="join-roster-suggestions"
              value={playerName}
              onChange={(e) => onNameChange(e.target.value)}
              onBlur={onNameBlur}
              placeholder="Enter your name"
              variant="inline"
              inputStyle={inputStyle}
              required
            />
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={labelStyle}>Your Handicap:</label>
            <Input
              type="number"
              step="0.1"
              value={handicap}
              onChange={(e) => {
                setHandicap(e.target.value);
                setHandicapTouched(true);
              }}
              placeholder="Leave as-is to use roster"
              variant="inline"
              inputStyle={inputStyle}
            />
            {note && (
              <p style={{ fontSize: 12, color: note.color, marginTop: 4 }}>
                {note.text}
              </p>
            )}
          </div>

          {error && (
            <div style={{
              background: '#ffebee',
              color: theme.colors.error,
              padding: 12,
              borderRadius: 8,
              marginBottom: 16,
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              ...theme.buttonStyle,
              width: '100%',
              fontSize: 18,
              padding: '16px 24px',
              background: loading ? theme.colors.textSecondary : theme.colors.primary,
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Joining…' : 'Join Game'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default JoinGamePage;
