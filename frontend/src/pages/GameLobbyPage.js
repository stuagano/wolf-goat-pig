import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTheme } from '../theme/Provider';

const API_URL = process.env.REACT_APP_API_URL || "";

function GameLobbyPage() {
  const theme = useTheme();
  const navigate = useNavigate();
  const { gameId } = useParams();

  const [lobby, setLobby] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [starting, setStarting] = useState(false);
  const [copied, setCopied] = useState(false);

  // Poll lobby status every 2 seconds
  useEffect(() => {
    const fetchLobby = async () => {
      try {
        const response = await fetch(`${API_URL}/games/${gameId}/lobby`);

        if (!response.ok) {
          throw new Error('Game not found');
        }

        const data = await response.json();
        setLobby(data);
        setError('');

        // Update session in localStorage to keep it fresh
        const currentSession = localStorage.getItem(`wgp_session_${gameId}`);
        if (currentSession) {
          const sessionData = JSON.parse(currentSession);
          sessionData.timestamp = Date.now();
          sessionData.status = data.status;
          localStorage.setItem(`wgp_session_${gameId}`, JSON.stringify(sessionData));
        }

        // If game has started, redirect to game page
        if (data.status === 'in_progress' || data.status === 'completed') {
          navigate(`/game/${gameId}`);
        }
      } catch (err) {
        console.error('Error fetching lobby:', err);
        setError(err.message || 'Failed to load lobby');
      } finally {
        setLoading(false);
      }
    };

    fetchLobby();
    const interval = setInterval(fetchLobby, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [gameId, navigate]);

  const startGame = async () => {
    setStarting(true);
    setError('');

    try {
      const response = await fetch(`${API_URL}/games/${gameId}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to start game');
      }

      // Navigate to game page
      navigate(`/game/${gameId}`);

    } catch (err) {
      console.error('Error starting game:', err);
      setError(err.message || 'Failed to start game');
      setStarting(false);
    }
  };

  const copyJoinCode = () => {
    if (lobby?.join_code) {
      navigator.clipboard.writeText(lobby.join_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const copyJoinLink = () => {
    if (lobby?.join_code) {
      const link = `${window.location.origin}/join/${lobby.join_code}`;
      navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div style={{
        maxWidth: 600,
        margin: '0 auto',
        padding: 20,
        fontFamily: theme.typography.fontFamily
      }}>
        <div style={theme.cardStyle}>
          <p style={{ textAlign: 'center', color: theme.colors.textPrimary }}>
            Loading lobby...
          </p>
        </div>
      </div>
    );
  }

  if (error && !lobby) {
    return (
      <div style={{
        maxWidth: 600,
        margin: '0 auto',
        padding: 20,
        fontFamily: theme.typography.fontFamily
      }}>
        <div style={theme.cardStyle}>
          <h2 style={{ color: theme.colors.error }}>Error</h2>
          <p>{error}</p>
          <button
            onClick={() => navigate('/')}
            style={{
              ...theme.buttonStyle,
              marginTop: 16
            }}
          >
            ← Back to Home
          </button>
        </div>
      </div>
    );
  }

  const canStart = lobby?.players_joined >= 2 && lobby?.players_joined <= lobby?.max_players;

  return (
    <div style={{
      maxWidth: 600,
      margin: '0 auto',
      padding: 20,
      fontFamily: theme.typography.fontFamily
    }}>
      <div style={theme.cardStyle}>
        <h1 style={{ color: theme.colors.primary, marginBottom: 8 }}>
          🎮 Game Lobby
        </h1>
        <p style={{ color: theme.colors.textSecondary, marginBottom: 24 }}>
          Waiting for players to join...
        </p>

        {/* Join Code Display */}
        <div style={{
          background: theme.colors.primary,
          color: 'white',
          padding: 24,
          borderRadius: 12,
          textAlign: 'center',
          marginBottom: 24
        }}>
          <div style={{ fontSize: 14, marginBottom: 8, opacity: 0.9 }}>
            Join Code:
          </div>
          <div style={{
            fontSize: 48,
            fontWeight: 700,
            letterSpacing: 8,
            fontFamily: 'monospace',
            marginBottom: 16
          }}>
            {lobby?.join_code}
          </div>
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
            <button
              onClick={copyJoinCode}
              style={{
                padding: '8px 16px',
                background: 'rgba(255,255,255,0.2)',
                color: 'white',
                border: 'none',
                borderRadius: 6,
                cursor: 'pointer',
                fontSize: 14,
                fontWeight: 600
              }}
            >
              {copied ? '✓ Copied!' : '📋 Copy Code'}
            </button>
            <button
              onClick={copyJoinLink}
              style={{
                padding: '8px 16px',
                background: 'rgba(255,255,255,0.2)',
                color: 'white',
                border: 'none',
                borderRadius: 6,
                cursor: 'pointer',
                fontSize: 14,
                fontWeight: 600
              }}
            >
              🔗 Copy Link
            </button>
          </div>
        </div>

        {/* Game Info */}
        <div style={{
          background: '#f5f5f5',
          padding: 16,
          borderRadius: 8,
          marginBottom: 24
        }}>
          <div style={{ marginBottom: 8 }}>
            <strong>Course:</strong> {lobby?.course_name || 'Not selected'}
          </div>
          <div style={{ marginBottom: 8 }}>
            <strong>Players:</strong> {lobby?.players_joined} / {lobby?.max_players}
          </div>
          <div>
            <strong>Status:</strong>{' '}
            <span style={{
              color: canStart ? theme.colors.success : theme.colors.warning,
              fontWeight: 600
            }}>
              {canStart ? 'Ready to start!' : `Waiting for ${Math.max(2 - lobby?.players_joined, 0)} more player(s)`}
            </span>
          </div>
        </div>

        {/* Players List */}
        <h3 style={{ color: theme.colors.primary, marginBottom: 12 }}>
          Players Joined:
        </h3>
        <div style={{ marginBottom: 24 }}>
          {lobby?.players && lobby.players.length > 0 ? (
            lobby.players.map((player, index) => (
              <div
                key={player.player_slot_id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: 16,
                  background: index % 2 === 0 ? 'white' : '#f9f9f9',
                  borderRadius: 8,
                  marginBottom: 8,
                  border: `1px solid ${theme.colors.border}`
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{
                    width: 40,
                    height: 40,
                    borderRadius: '50%',
                    background: theme.colors.primary,
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: 700,
                    fontSize: 18
                  }}>
                    {index + 1}
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 16 }}>
                      {player.player_name}
                    </div>
                    <div style={{ fontSize: 13, color: theme.colors.textSecondary }}>
                      Handicap: {player.handicap}
                      {player.is_authenticated && ' • 🔒 Authenticated'}
                    </div>
                  </div>
                </div>
                <div style={{
                  padding: '4px 12px',
                  background: '#e8f5e9',
                  color: '#2e7d32',
                  borderRadius: 12,
                  fontSize: 12,
                  fontWeight: 600
                }}>
                  ✓ Joined
                </div>
              </div>
            ))
          ) : (
            <p style={{ color: theme.colors.textSecondary, fontStyle: 'italic' }}>
              No players have joined yet
            </p>
          )}
        </div>

        {error && (
          <div style={{
            background: '#ffebee',
            color: theme.colors.error,
            padding: 12,
            borderRadius: 8,
            marginBottom: 16
          }}>
            {error}
          </div>
        )}

        {/* Start Game Button (for creator or anyone in dev mode) */}
        <button
          onClick={startGame}
          disabled={!canStart || starting}
          style={{
            ...theme.buttonStyle,
            width: '100%',
            fontSize: 18,
            padding: '16px 24px',
            background: (!canStart || starting) ? theme.colors.textSecondary : theme.colors.success,
            cursor: (!canStart || starting) ? 'not-allowed' : 'pointer'
          }}
        >
          {starting ? 'Starting Game...' : canStart ? '🚀 Start Game' : `Need ${Math.max(2 - lobby?.players_joined, 0)} More Player(s)`}
        </button>

        {/* Instructions */}
        <div style={{
          marginTop: 24,
          padding: 16,
          background: '#e3f2fd',
          borderRadius: 8,
          fontSize: 14
        }}>
          <p style={{ margin: '0 0 8px 0', fontWeight: 600 }}>
            📱 Share this code with your friends:
          </p>
          <ol style={{ margin: 0, paddingLeft: 20 }}>
            <li>They visit {window.location.origin}</li>
            <li>Click "Join Game"</li>
            <li>Enter code: <strong>{lobby?.join_code}</strong></li>
          </ol>
          <p style={{ margin: '12px 0 0 0', fontSize: 13, color: theme.colors.textSecondary }}>
            Or share the direct link using the "Copy Link" button above!
          </p>
        </div>

        {/* Testing Note */}
        <div style={{
          marginTop: 16,
          padding: 12,
          background: '#fff3e0',
          borderRadius: 8,
          fontSize: 13,
          color: '#e65100'
        }}>
          <strong>💡 Testing Tip:</strong> Open <code>/join/{lobby?.join_code}</code> in
          multiple browser windows (or incognito) to simulate different players joining!
        </div>
      </div>
    </div>
  );
}

export default GameLobbyPage;
