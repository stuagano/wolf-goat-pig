import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ScorecardPhoto from '../components/game/ScorecardPhoto';
import { apiConfig } from '../config/api.config';

const API_URL = apiConfig.baseUrl;

const ScorecardScanPage = () => {
  const navigate = useNavigate();
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedGame, setSelectedGame] = useState(null);
  const [saved, setSaved] = useState(false);

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
          <button
            onClick={() => navigate(`/game/${selectedGame.game_id}`)}
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

  if (selectedGame) {
    const players = selectedGame.players || [];
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
            onClick={() => navigate('/')}
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
              Photo → Gemini extracts quarters → save to game
            </p>
          </div>
        </div>

        {/* Game picker */}
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
      </div>
    </div>
  );
};

export default ScorecardScanPage;
