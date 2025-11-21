import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTheme } from '../theme/Provider';
import { useAuth0 } from '@auth0/auth0-react';
import { Input } from '../components/ui';

const API_URL = process.env.REACT_APP_API_URL || "";

function JoinGamePage() {
  const theme = useTheme();
  const navigate = useNavigate();
  const { code } = useParams(); // Get code from URL if provided
  const { user, isAuthenticated } = useAuth0();

  const [joinCode, setJoinCode] = useState(code || '');
  const [playerName, setPlayerName] = useState('');
  const [handicap, setHandicap] = useState('18');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Auto-fill player name if authenticated
  useEffect(() => {
    if (isAuthenticated && user?.name) {
      setPlayerName(user.name);
    }
  }, [isAuthenticated, user]);

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

    if (!handicap || parseFloat(handicap) < 0) {
      setError('Please enter a valid handicap');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const requestBody = {
        player_name: playerName,
        handicap: parseFloat(handicap)
      };

      // Include user_id if authenticated
      if (isAuthenticated && user?.sub) {
        requestBody.user_id = user.sub;
      }

      const response = await fetch(`${API_URL}/games/join/${joinCode.toUpperCase()}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to join game');
      }

      if (data.status === 'joined' || data.status === 'already_joined') {
        // Store session info in localStorage for reconnection
        const sessionData = {
          gameId: data.game_id,
          playerName: playerName,
          handicap: parseFloat(handicap),
          joinCode: joinCode.toUpperCase(),
          timestamp: Date.now(),
          userId: isAuthenticated ? user?.sub : null
        };
        localStorage.setItem(`wgp_session_${data.game_id}`, JSON.stringify(sessionData));
        localStorage.setItem('wgp_current_game', data.game_id);

        // Navigate to lobby
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

  return (
    <div style={{
      maxWidth: 500,
      margin: '0 auto',
      padding: 20,
      fontFamily: theme.typography.fontFamily
    }}>
      <div style={theme.cardStyle}>
        <h1 style={{ color: theme.colors.primary, marginBottom: 8 }}>
          🎯 Join Game
        </h1>
        <p style={{ color: theme.colors.textSecondary, marginBottom: 24 }}>
          Enter the join code your friend shared with you
        </p>

        <form onSubmit={joinGame}>
          {/* Join Code */}
          <div style={{ marginBottom: 20 }}>
            <label style={{
              display: 'block',
              fontWeight: 600,
              marginBottom: 8,
              color: theme.colors.textPrimary
            }}>
              Join Code:
            </label>
            <Input
              type="text"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
              placeholder="ABC123"
              maxLength={6}
              variant="inline"
              inputStyle={{
                width: '100%',
                padding: 12,
                fontSize: 20,
                fontWeight: 700,
                textAlign: 'center',
                letterSpacing: 4,
                borderRadius: 8,
                border: `2px solid ${theme.colors.border}`,
                background: theme.colors.paper,
                textTransform: 'uppercase'
              }}
              required
            />
            <p style={{
              fontSize: 12,
              color: theme.colors.textSecondary,
              marginTop: 4
            }}>
              6-character code from game creator
            </p>
          </div>

          {/* Player Name */}
          <div style={{ marginBottom: 20 }}>
            <label style={{
              display: 'block',
              fontWeight: 600,
              marginBottom: 8,
              color: theme.colors.textPrimary
            }}>
              Your Name:
            </label>
            <Input
              type="text"
              value={playerName}
              onChange={(e) => setPlayerName(e.target.value)}
              placeholder="Enter your name"
              variant="inline"
              inputStyle={{
                width: '100%',
                padding: 12,
                fontSize: 16,
                borderRadius: 8,
                border: `1px solid ${theme.colors.border}`,
                background: theme.colors.paper
              }}
              required
            />
          </div>

          {/* Handicap */}
          <div style={{ marginBottom: 20 }}>
            <label style={{
              display: 'block',
              fontWeight: 600,
              marginBottom: 8,
              color: theme.colors.textPrimary
            }}>
              Your Handicap:
            </label>
            <Input
              type="number"
              step="0.1"
              value={handicap}
              onChange={(e) => setHandicap(e.target.value)}
              placeholder="18.0"
              variant="inline"
              inputStyle={{
                width: '100%',
                padding: 12,
                fontSize: 16,
                borderRadius: 8,
                border: `1px solid ${theme.colors.border}`,
                background: theme.colors.paper
              }}
              required
            />
            <p style={{
              fontSize: 12,
              color: theme.colors.textSecondary,
              marginTop: 4
            }}>
              Enter 18 if you don't have an official handicap
            </p>
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

          {/* Join Button */}
          <button
            type="submit"
            disabled={loading}
            style={{
              ...theme.buttonStyle,
              width: '100%',
              fontSize: 18,
              padding: '16px 24px',
              background: loading ? theme.colors.textSecondary : theme.colors.primary,
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Joining...' : '🚀 Join Game'}
          </button>

          {/* Back Button */}
          <button
            type="button"
            onClick={() => navigate('/')}
            style={{
              ...theme.buttonStyle,
              width: '100%',
              fontSize: 16,
              marginTop: 12,
              background: 'transparent',
              color: theme.colors.textSecondary,
              border: `1px solid ${theme.colors.border}`
            }}
          >
            ← Back to Home
          </button>
        </form>

        {/* Testing Tip */}
        <div style={{
          marginTop: 24,
          padding: 12,
          background: '#f5f5f5',
          borderRadius: 8,
          fontSize: 13,
          color: theme.colors.textSecondary
        }}>
          <strong>Testing Tip:</strong> Open this page in multiple browser windows
          to simulate multiple players joining the same game!
        </div>
      </div>
    </div>
  );
}

export default JoinGamePage;
