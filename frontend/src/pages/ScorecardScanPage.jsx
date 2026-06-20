import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ScorecardPhoto from '../components/game/ScorecardPhoto';
import { apiConfig } from '../config/api.config';

const API_URL = apiConfig.baseUrl;

/**
 * PlayerPickStep — roster multiselect shown before the camera in new-round mode.
 * Enforces 4–6 players selected before allowing Continue.
 */
const PlayerPickStep = ({ rosterNames, onConfirm, onCancel }) => {
  const [selected, setSelected] = useState([]);

  const toggle = (name) => {
    setSelected(prev =>
      prev.includes(name) ? prev.filter(n => n !== name) : [...prev, name],
    );
  };

  const canContinue = selected.length >= 4 && selected.length <= 6;

  return (
    <div style={{ minHeight: '100vh', background: '#F9FAFB', padding: '16px' }}>
      <div style={{ maxWidth: '500px', margin: '0 auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px', paddingTop: '8px' }}>
          <button
            onClick={onCancel}
            style={{ background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer', padding: '4px', color: '#6B7280' }}
          >
            ←
          </button>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 'bold', color: '#111827' }}>
              📷 Scan Scorecard
            </h1>
            <p style={{ margin: 0, fontSize: '13px', color: '#6B7280' }}>
              Select the players in this round (4–6)
            </p>
          </div>
        </div>

        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '20px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
        }}>
          <h2 style={{ margin: '0 0 16px', fontSize: '1rem', fontWeight: '600', color: '#374151' }}>
            Who played? ({selected.length} selected)
          </h2>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '20px' }}>
            {rosterNames.map(name => {
              const isSelected = selected.includes(name);
              return (
                <label
                  key={name}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '10px 14px',
                    background: isSelected ? '#ECFDF5' : '#F9FAFB',
                    border: `2px solid ${isSelected ? '#047857' : '#E5E7EB'}`,
                    borderRadius: '10px',
                    cursor: 'pointer',
                    fontWeight: isSelected ? '600' : '400',
                    color: '#111827',
                    transition: 'all 0.15s',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggle(name)}
                    style={{ accentColor: '#047857', width: '16px', height: '16px' }}
                  />
                  {name}
                </label>
              );
            })}
          </div>

          {!canContinue && selected.length > 0 && (
            <p style={{ fontSize: '13px', color: '#6B7280', marginBottom: '12px', textAlign: 'center' }}>
              {selected.length < 4
                ? `Select at least ${4 - selected.length} more player${4 - selected.length > 1 ? 's' : ''}`
                : 'Maximum 6 players allowed'}
            </p>
          )}

          <button
            onClick={() => onConfirm(selected)}
            disabled={!canContinue}
            style={{
              width: '100%',
              padding: '14px',
              background: canContinue ? '#047857' : '#D1D5DB',
              color: canContinue ? 'white' : '#9CA3AF',
              border: 'none',
              borderRadius: '10px',
              fontWeight: '600',
              fontSize: '15px',
              cursor: canContinue ? 'pointer' : 'not-allowed',
            }}
          >
            Continue →
          </button>
        </div>
      </div>
    </div>
  );
};

const ScorecardScanPage = () => {
  const navigate = useNavigate();
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedGame, setSelectedGame] = useState(null);
  const [saved, setSaved] = useState(false);
  const [mode, setMode] = useState(null); // null = landing, 'new-round', 'attach'
  const [rosterNames, setRosterNames] = useState([]);
  const [pickedPlayers, setPickedPlayers] = useState([]);
  const [savedGameId, setSavedGameId] = useState(null);

  useEffect(() => {
    const fetchGames = async () => {
      try {
        const res = await fetch(`${API_URL}/games/active`);
        if (res.ok) {
          const data = await res.json();
          setGames(data);
        }
      } catch (err) {
        // silently fail — user can still pick
      } finally {
        setLoading(false);
      }
    };
    fetchGames();
  }, []);

  useEffect(() => {
    fetch(`${API_URL}/legacy-players`)
      .then(r => (r.ok ? r.json() : { players: [] }))
      .then(d => setRosterNames(d.players || []))
      .catch(() => {});
  }, []);

  if (saved) {
    return (
      <div style={{
        minHeight: '100vh',
        background: '#F9FAFB',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '16px',
        padding: '24px',
        textAlign: 'center',
      }}>
        <div style={{ fontSize: '4rem' }}>✅</div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#111827' }}>Quarters Saved!</h2>
        <p style={{ color: '#6B7280' }}>All 18 holes have been recorded.</p>
        <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
          {(savedGameId || selectedGame?.game_id) && (
            <button
              onClick={() => navigate(`/game/${savedGameId || selectedGame?.game_id}`)}
              style={{
                padding: '12px 24px',
                background: '#047857',
                color: 'white',
                border: 'none',
                borderRadius: '10px',
                fontWeight: '600',
                fontSize: '15px',
                cursor: 'pointer',
              }}
            >
              View Game
            </button>
          )}
          <button
            onClick={() => navigate('/')}
            style={{
              padding: '12px 24px',
              background: '#E5E7EB',
              color: '#374151',
              border: 'none',
              borderRadius: '10px',
              fontWeight: '600',
              fontSize: '15px',
              cursor: 'pointer',
            }}
          >
            Home
          </button>
        </div>
      </div>
    );
  }

  if (mode === 'new-round') {
    // Pre-pick step: gate on player selection before showing the camera
    if (pickedPlayers.length === 0) {
      return (
        <PlayerPickStep
          rosterNames={rosterNames}
          onConfirm={setPickedPlayers}
          onCancel={() => setMode(null)}
        />
      );
    }
    return (
      <div style={{ minHeight: '100vh', background: '#F9FAFB', padding: '16px' }}>
        <div style={{ maxWidth: '600px', margin: '0 auto' }}>
          <div style={{
            background: 'white',
            borderRadius: '16px',
            padding: '20px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
          }}>
            <ScorecardPhoto
              mode="new-round"
              rosterNames={rosterNames}
              pickedPlayers={pickedPlayers}
              players={[]}
              onSaved={(result) => { setSavedGameId(result?.game_id || null); setSaved(true); }}
              onCancel={() => { setPickedPlayers([]); setMode(null); }}
            />
          </div>
        </div>
      </div>
    );
  }

  if (mode === 'attach' && selectedGame) {
    const players = selectedGame.players || [];
    const attachPickedPlayers = players.map(p => p.name).filter(Boolean);
    return (
      <div style={{ minHeight: '100vh', background: '#F9FAFB', padding: '16px' }}>
        <div style={{ maxWidth: '600px', margin: '0 auto' }}>
          <div style={{
            background: 'white',
            borderRadius: '16px',
            padding: '20px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
          }}>
            <ScorecardPhoto
              gameId={selectedGame.game_id}
              players={players}
              pickedPlayers={attachPickedPlayers}
              onSaved={() => setSaved(true)}
              onCancel={() => setSelectedGame(null)}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#F9FAFB', padding: '16px' }}>
      <div style={{ maxWidth: '500px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px', paddingTop: '8px' }}>
          <button
            onClick={() => (mode === null ? navigate('/') : setMode(null))}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '20px',
              cursor: 'pointer',
              padding: '4px',
              color: '#6B7280',
            }}
          >
            ←
          </button>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 'bold', color: '#111827' }}>
              📷 Scan Scorecard
            </h1>
            <p style={{ margin: 0, fontSize: '13px', color: '#6B7280' }}>
              Photo → reads the scorecard → save the round
            </p>
          </div>
        </div>

        {/* Landing: choose what to scan into */}
        {mode === null && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <button
              onClick={() => setMode('new-round')}
              style={{
                width: '100%',
                padding: '20px',
                background: '#047857',
                color: 'white',
                border: 'none',
                borderRadius: '14px',
                fontWeight: '600',
                fontSize: '16px',
                cursor: 'pointer',
                textAlign: 'left',
                boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
              }}
            >
              📷 Scan a finished round
              <div style={{ fontSize: '13px', fontWeight: '400', opacity: 0.9, marginTop: '4px' }}>
                Record a completed scorecard as a new round
              </div>
            </button>
            <button
              onClick={() => setMode('attach')}
              style={{
                width: '100%',
                padding: '20px',
                background: 'white',
                color: '#111827',
                border: '2px solid #E5E7EB',
                borderRadius: '14px',
                fontWeight: '600',
                fontSize: '16px',
                cursor: 'pointer',
                textAlign: 'left',
                boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
              }}
            >
              ➕ Add to an active game
              <div style={{ fontSize: '13px', fontWeight: '400', color: '#6B7280', marginTop: '4px' }}>
                Save scanned quarters to a game in progress
              </div>
            </button>
          </div>
        )}

        {/* Game picker */}
        {mode === 'attach' && (
        <div style={{
          background: 'white',
          borderRadius: '16px',
          padding: '20px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
        }}>
          <h2 style={{ margin: '0 0 16px', fontSize: '1rem', fontWeight: '600', color: '#374151' }}>
            Select a game to save scores to:
          </h2>

          {loading ? (
            <p style={{ color: '#9CA3AF', textAlign: 'center', padding: '20px 0' }}>Loading games…</p>
          ) : games.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '24px 0', color: '#6B7280' }}>
              <p>No active games found.</p>
              <button
                onClick={() => navigate('/game')}
                style={{
                  marginTop: '12px',
                  padding: '10px 20px',
                  background: '#047857',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                Create a Game
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {games.map((game) => {
                const playerNames = (game.players || []).map(p => p.name).join(', ');
                const date = game.created_at
                  ? new Date(game.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
                  : '';
                return (
                  <button
                    key={game.game_id}
                    onClick={() => setSelectedGame(game)}
                    style={{
                      width: '100%',
                      padding: '14px 16px',
                      background: '#F9FAFB',
                      border: '2px solid #E5E7EB',
                      borderRadius: '10px',
                      textAlign: 'left',
                      cursor: 'pointer',
                      transition: 'border-color 0.15s',
                    }}
                    onMouseEnter={e => e.currentTarget.style.borderColor = '#047857'}
                    onMouseLeave={e => e.currentTarget.style.borderColor = '#E5E7EB'}
                  >
                    <div style={{ fontWeight: '600', color: '#111827', fontSize: '14px' }}>
                      {playerNames || game.game_id}
                    </div>
                    {date && (
                      <div style={{ fontSize: '12px', color: '#9CA3AF', marginTop: '2px' }}>{date}</div>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>
        )}
      </div>
    </div>
  );
};

export default ScorecardScanPage;
