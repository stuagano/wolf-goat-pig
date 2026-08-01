import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../theme/Provider';
import { useAuth0 } from '@auth0/auth0-react';
import { apiConfig } from '../config/api.config';

const API_URL = apiConfig.baseUrl;

// `handicapTouched` tracks whether a human typed this number. Untouched slots
// are sent as null so the server fills in the roster handicap — shipping the 18
// placeholder for a rostered player silently rewrites their strokes for the round.
const emptyPlayer = () => ({ name: '', handicap: 18, handicapTouched: false, isGhost: true, player_profile_id: null });

const normalizeName = (name) => (name || '').toLowerCase().replace(/[^a-z0-9]+/g, '');

const handicapNote = (player) => {
  if (player.handicapTouched) return { text: 'Handicap set by hand for this round', color: '#b45309' };
  if (player.player_profile_id) return { text: `Roster handicap ${player.handicap}`, color: '#15803d' };
  return { text: 'Not on the roster — will play off 18', color: '#b45309' };
};

function CreateGamePage() {
  const theme = useTheme();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth0();

  const [loading, setLoading] = useState(false);
  const [creatingEmpty, setCreatingEmpty] = useState(false);
  const [error, setError] = useState('');
  const [courses, setCourses] = useState([]);
  const [courseName, setCourseName] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [players, setPlayers] = useState(() => {
    // First slot defaults to the logged-in user as a real player.
    const me = { name: '', handicap: 18, handicapTouched: false, isGhost: false, player_profile_id: null };
    return [me, emptyPlayer(), emptyPlayer(), emptyPlayer()];
  });

  useEffect(() => {
    fetch(`${API_URL}/courses`)
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error(`HTTP ${res.status}`))))
      .then((data) => {
        const names = Object.keys(data);
        setCourses(names);
        if (names.length) setCourseName(names[0]);
      })
      .catch(() => {
        setCourses(['Wing Point Golf & Country Club']);
        setCourseName('Wing Point Golf & Country Club');
      });

    fetch(`${API_URL}/games/roster-suggestions`)
      .then((res) => (res.ok ? res.json() : null))
      .then((d) => { if (d?.players) setSuggestions(d.players); })
      .catch(() => {});
  }, []);

  // Prefill the first player's name with the logged-in user once available.
  useEffect(() => {
    if (user?.name) {
      setPlayers((prev) => {
        if (prev[0].name) return prev;
        const next = [...prev];
        next[0] = { ...next[0], name: user.name };
        return next;
      });
    }
  }, [user?.name]);

  // Match on an exact name first, then on an unambiguous prefix so a half-typed
  // "Rainer" still links to the roster instead of falling through to the 18.
  const suggestionByName = (name) => {
    const key = normalizeName(name);
    if (!key) return null;
    const exact = suggestions.find((s) => normalizeName(s.name) === key);
    if (exact) return exact;
    const prefixed = suggestions.filter((s) => normalizeName(s.name).startsWith(key));
    return prefixed.length === 1 ? prefixed[0] : null;
  };

  const updatePlayer = (i, patch) =>
    setPlayers((prev) => prev.map((p, idx) => (idx === i ? { ...p, ...patch } : p)));

  const onNameChange = (i, name) => {
    const match = suggestionByName(name);
    if (!match) {
      updatePlayer(i, { name, player_profile_id: null });
      return;
    }
    setPlayers((prev) => prev.map((p, idx) => (idx === i
      ? {
        ...p,
        name,
        player_profile_id: match.player_profile_id ?? null,
        // A handicap the user typed themselves outranks the roster.
        handicap: p.handicapTouched ? p.handicap : (match.handicap ?? 18),
      }
      : p)));
  };

  // Snap a prefix ("Stu") to the full roster name once the field loses focus.
  const onNameBlur = (i) => {
    const match = suggestionByName(players[i].name);
    if (match && match.name !== players[i].name) updatePlayer(i, { name: match.name });
  };

  const addPlayer = () => players.length < 6 && setPlayers((p) => [...p, emptyPlayer()]);
  const removePlayer = (i) => players.length > 4 && setPlayers((p) => p.filter((_, idx) => idx !== i));

  const ghostCount = players.filter((p) => p.isGhost).length;

  const startGame = async () => {
    setError('');
    const named = players.map((p) => ({ ...p, name: p.name.trim() }));
    if (named.some((p) => !p.name)) {
      setError('Give every player a name (or remove empty slots).');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/games/create-custom`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          course_name: courseName,
          players: named.map((p) => ({
            name: p.name,
            // null lets the server use the roster handicap; only an explicitly
            // typed number overrides it.
            handicap: p.handicapTouched ? (Number(p.handicap) || 0) : null,
            is_ghost: p.isGhost,
            player_profile_id: p.player_profile_id,
            user_id: !p.isGhost && p.name === user?.name && isAuthenticated ? user?.sub : null,
          })),
        }),
      });
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        throw new Error(e.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      // Auto-enable Stuart Mode (full AI) when ghosts are in the game so the AI
      // plays them. Write the canonical assist-mode key — the scorekeeper reads
      // it first; also keep the legacy boolean in sync for older readers.
      const mode = data.has_ghosts ? 'auto' : 'off';
      localStorage.setItem('wgp_assist_mode', mode);
      localStorage.setItem('wgp_stuart_mode', String(data.has_ghosts));
      navigate(`/game/${data.game_id}`);
    } catch (err) {
      setError(err.message || 'Failed to start game.');
    } finally {
      setLoading(false);
    }
  };

  const createEmptyWithCode = async () => {
    setError('');
    setCreatingEmpty(true);
    try {
      const params = new URLSearchParams({ course_name: courseName, player_count: String(players.length) });
      if (isAuthenticated && user?.sub) params.append('user_id', user.sub);
      const res = await fetch(`${API_URL}/games/create?${params.toString()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        throw new Error(e.detail || 'Failed to create game');
      }
      const data = await res.json();
      navigate(`/lobby/${data.game_id}`);
    } catch (err) {
      setError(err.message || 'Failed to create game.');
    } finally {
      setCreatingEmpty(false);
    }
  };

  const labelStyle = { display: 'block', fontWeight: 600, marginBottom: 8, color: theme.colors.textPrimary };
  const inputStyle = {
    padding: 10, fontSize: 15, borderRadius: 8,
    border: `1px solid ${theme.colors.border}`, background: theme.colors.paper, boxSizing: 'border-box',
  };

  return (
    <div style={{ maxWidth: 640, margin: '0 auto', padding: 20, fontFamily: theme.typography.fontFamily }}>
      <div style={theme.cardStyle}>
        <h1 style={{ color: theme.colors.primary, marginBottom: 8 }}>🎮 New Game</h1>
        <p style={{ color: theme.colors.textSecondary, marginBottom: 24 }}>
          Add real players or 👻 ghosts (AI plays as them). Any ghost turns on Stuart Mode automatically.
        </p>

        {/* Course */}
        <div style={{ marginBottom: 20 }}>
          <label style={labelStyle}>Course</label>
          <select
            value={courseName}
            onChange={(e) => setCourseName(e.target.value)}
            style={{ ...inputStyle, width: '100%', padding: 12, fontSize: 16 }}
          >
            {courses.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        {/* Players */}
        <label style={labelStyle}>Players ({players.length})</label>
        <datalist id="roster-suggestions">
          {suggestions.map((s) => <option key={s.name} value={s.name} />)}
        </datalist>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 14 }}>
          {players.map((p, i) => (
            <div key={i} style={{
              padding: 10, borderRadius: 10,
              border: `1px solid ${p.isGhost ? '#f0abfc' : theme.colors.border}`,
              background: p.isGhost ? 'rgba(217,70,239,0.05)' : theme.colors.paper,
            }}>
             <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input
                list="roster-suggestions"
                value={p.name}
                onChange={(e) => onNameChange(i, e.target.value)}
                onBlur={() => onNameBlur(i)}
                placeholder={`Player ${i + 1}`}
                style={{ ...inputStyle, flex: 1, minWidth: 0 }}
                aria-label={`Player ${i + 1} name`}
              />
              <input
                type="number"
                step="0.1"
                value={p.handicap}
                onChange={(e) => updatePlayer(i, { handicap: e.target.value, handicapTouched: true })}
                style={{ ...inputStyle, width: 64 }}
                aria-label={`Player ${i + 1} handicap`}
                title="Handicap"
              />
              <button
                type="button"
                onClick={() => updatePlayer(i, { isGhost: !p.isGhost })}
                aria-pressed={p.isGhost}
                title={p.isGhost ? 'Ghost — AI plays this player' : 'Real player'}
                style={{
                  ...inputStyle, cursor: 'pointer', whiteSpace: 'nowrap',
                  fontWeight: 700, fontSize: 13,
                  background: p.isGhost ? '#d946ef' : '#16a34a', color: '#fff', border: 'none',
                }}
              >
                {p.isGhost ? '👻 Ghost' : '🧑 Real'}
              </button>
              {players.length > 4 && (
                <button
                  type="button"
                  onClick={() => removePlayer(i)}
                  aria-label={`Remove player ${i + 1}`}
                  style={{ ...inputStyle, cursor: 'pointer', color: theme.colors.textSecondary, padding: '10px 12px' }}
                >
                  ×
                </button>
              )}
             </div>
              {p.name.trim() && (
                <div style={{ fontSize: 12, marginTop: 6, color: handicapNote(p).color }}>
                  {handicapNote(p).text}
                </div>
              )}
            </div>
          ))}
        </div>

        {players.length < 6 && (
          <button
            type="button"
            onClick={addPlayer}
            style={{ ...inputStyle, cursor: 'pointer', width: '100%', color: theme.colors.primary, fontWeight: 600, marginBottom: 20, background: 'transparent', borderStyle: 'dashed' }}
          >
            + Add player
          </button>
        )}

        {error && (
          <div style={{ background: '#ffebee', color: theme.colors.error, padding: 12, borderRadius: 8, marginBottom: 16 }}>
            {error}
          </div>
        )}

        <button
          onClick={startGame}
          disabled={loading}
          style={{
            ...theme.buttonStyle, width: '100%', fontSize: 18, padding: '16px 24px',
            background: loading ? theme.colors.textSecondary : theme.colors.primary,
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? 'Starting…' : ghostCount > 0 ? `🧠 Start Game (Stuart Mode · ${ghostCount} ghost${ghostCount > 1 ? 's' : ''})` : '🚀 Start Game'}
        </button>

        {/* Secondary: empty game with a join code for pure multiplayer */}
        <div style={{ marginTop: 18, paddingTop: 16, borderTop: `1px solid ${theme.colors.border}`, textAlign: 'center' }}>
          <button
            onClick={createEmptyWithCode}
            disabled={creatingEmpty}
            style={{ background: 'none', border: 'none', color: theme.colors.primary, fontSize: 14, cursor: 'pointer', textDecoration: 'underline' }}
          >
            {creatingEmpty ? 'Creating…' : 'Or create an empty game with a join code →'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default CreateGamePage;
