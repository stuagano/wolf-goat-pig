// frontend/src/pages/GameScorerPage.js
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/ui';
import { useTheme } from '../theme/Provider';
import CommissionerChat from '../components/CommissionerChat';

const API_URL = process.env.REACT_APP_API_URL || "";

/**
 * GameScorerPage - Game scoring options hub
 * Provides options to create, join, or score games with improved navigation integration
 */
const GameScorerPage = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const [activeGameSession, setActiveGameSession] = useState(null);
  const [isCreatingTestGame, setIsCreatingTestGame] = useState(false);
  const [error, setError] = useState(null);

  // Check for active game session on mount
  useEffect(() => {
    const currentGameId = localStorage.getItem('wgp_current_game');
    if (currentGameId) {
      const sessionKey = `wgp_session_${currentGameId}`;
      const sessionData = localStorage.getItem(sessionKey);
      if (sessionData) {
        try {
          const session = JSON.parse(sessionData);
          // Only show if session is recent (within 24 hours)
          const isRecent = (Date.now() - session.timestamp) < 24 * 60 * 60 * 1000;
          if (isRecent && session.status !== 'completed') {
            setActiveGameSession(session);
          } else {
            // Clean up old session
            localStorage.removeItem(sessionKey);
            localStorage.removeItem('wgp_current_game');
          }
        } catch (err) {
          console.error('Error parsing session data:', err);
        }
      }
    }
  }, []);

  const createTestGame = async () => {
    setIsCreatingTestGame(true);
    setError(null);

    try {
      const payload = {
        players: [
          { name: 'Player 1', id: 'player1' },
          { name: 'Player 2', id: 'player2' },
          { name: 'Player 3', id: 'player3' },
          { name: 'Player 4', id: 'player4' }
        ]
      };

      const response = await fetch(`${API_URL}/wgp/simplified/start-game`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to create test game: ${errorText}`);
      }

      const data = await response.json();

      if (data.success && data.game_id) {
        // Successfully created test game, navigate to it
        console.log('Test game created:', data);
        navigate(`/game/${data.game_id}`);
      } else {
        throw new Error('Failed to create game or no game_id returned');
      }
    } catch (err) {
      console.error('Error creating test game:', err);
      setError(err.message);
    } finally {
      setIsCreatingTestGame(false);
    }
  };

  if (isCreatingTestGame) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: '20px',
        background: theme.colors.background
      }}>
        <Card style={{ maxWidth: '500px', textAlign: 'center' }}>
          <div style={{ fontSize: '48px', marginBottom: '24px' }}>
            🏌️
          </div>
          <h2 style={{ marginTop: 0, marginBottom: '16px', color: theme.colors.primary }}>
            Creating Test Game...
          </h2>
          <p style={{ color: theme.colors.textSecondary, marginBottom: '24px' }}>
            Setting up a game with 4 test players for scoring
          </p>
          <div style={{
            display: 'inline-block',
            width: '40px',
            height: '40px',
            border: `4px solid ${theme.colors.border}`,
            borderTop: `4px solid ${theme.colors.primary}`,
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
        </Card>
        <style>
          {`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}
        </style>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      padding: '20px',
      background: theme.colors.background
    }}>
      <div style={{ maxWidth: '800px', margin: '0 auto', paddingTop: '60px' }}>
        {/* Header */}
        <div style={{
          textAlign: 'center',
          marginBottom: '40px'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚽</div>
          <h1 style={{
            fontSize: '2.5rem',
            fontWeight: 'bold',
            color: theme.colors.primary,
            marginBottom: '12px'
          }}>
            Score Rounds
          </h1>
          <p style={{
            color: theme.colors.textSecondary,
            fontSize: '1.1rem'
          }}>
            Start scoring rounds for Wolf Goat Pig games
          </p>
        </div>

        {/* Resume Active Game */}
        {activeGameSession && (
          <Card style={{ marginBottom: '30px' }}>
            <div style={{
              background: 'linear-gradient(135deg, #F59E0B, #D97706)',
              margin: '-20px -20px 20px -20px',
              padding: '20px',
              borderRadius: '8px 8px 0 0',
              color: 'white'
            }}>
              <h3 style={{ margin: '0 0 8px 0', fontSize: '1.3rem' }}>🎮 Active Game Found</h3>
              <p style={{ margin: 0, opacity: 0.9 }}>
                Playing as <strong>{activeGameSession.playerName}</strong> • Code: <strong>{activeGameSession.joinCode}</strong>
              </p>
            </div>
            <button
              onClick={() => navigate(`/game/${activeGameSession.gameId}`)}
              style={{
                ...theme.buttonStyle,
                background: '#F59E0B',
                width: '100%',
                padding: '16px',
                fontSize: '16px',
                fontWeight: '600'
              }}
            >
              ↩️ Resume Game
            </button>
          </Card>
        )}

        {/* Game Options */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '20px',
          marginBottom: '40px'
        }}>
          {/* Create New Game */}
          <Card style={{ textAlign: 'center', padding: '30px' }}>
            <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🎮</div>
            <h3 style={{
              color: theme.colors.primary,
              marginBottom: '12px',
              fontSize: '1.3rem'
            }}>
              Create New Game
            </h3>
            <p style={{
              color: theme.colors.textSecondary,
              marginBottom: '20px',
              minHeight: '48px'
            }}>
              Set up a new multiplayer game and share the join code with friends
            </p>
            <button
              onClick={() => navigate('/game')}
              style={{
                ...theme.buttonStyle,
                background: '#047857',
                width: '100%',
                padding: '14px',
                fontSize: '16px',
                fontWeight: '600'
              }}
            >
              Create Game
            </button>
          </Card>

          {/* Active Games */}
          <Card style={{ textAlign: 'center', padding: '30px' }}>
            <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🎯</div>
            <h3 style={{
              color: theme.colors.primary,
              marginBottom: '12px',
              fontSize: '1.3rem'
            }}>
              Active Games
            </h3>
            <p style={{
              color: theme.colors.textSecondary,
              marginBottom: '20px',
              minHeight: '48px'
            }}>
              View and resume your in-progress games
            </p>
            <button
              onClick={() => navigate('/games/active')}
              style={{
                ...theme.buttonStyle,
                background: '#10B981',
                width: '100%',
                padding: '14px',
                fontSize: '16px',
                fontWeight: '600'
              }}
            >
              View Active Games
            </button>
          </Card>

          {/* Join Existing Game */}
          <Card style={{ textAlign: 'center', padding: '30px' }}>
            <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🔗</div>
            <h3 style={{
              color: theme.colors.primary,
              marginBottom: '12px',
              fontSize: '1.3rem'
            }}>
              Join Game
            </h3>
            <p style={{
              color: theme.colors.textSecondary,
              marginBottom: '20px',
              minHeight: '48px'
            }}>
              Enter a join code to participate in an existing game
            </p>
            <button
              onClick={() => navigate('/join')}
              style={{
                ...theme.buttonStyle,
                background: '#0369A1',
                width: '100%',
                padding: '14px',
                fontSize: '16px',
                fontWeight: '600'
              }}
            >
              Join with Code
            </button>
          </Card>

          {/* Game History */}
          <Card style={{ textAlign: 'center', padding: '30px' }}>
            <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🏆</div>
            <h3 style={{
              color: theme.colors.primary,
              marginBottom: '12px',
              fontSize: '1.3rem'
            }}>
              Game History
            </h3>
            <p style={{
              color: theme.colors.textSecondary,
              marginBottom: '20px',
              minHeight: '48px'
            }}>
              Review completed games and see who won
            </p>
            <button
              onClick={() => navigate('/games/completed')}
              style={{
                ...theme.buttonStyle,
                background: '#8B5CF6',
                width: '100%',
                padding: '14px',
                fontSize: '16px',
                fontWeight: '600'
              }}
            >
              View History
            </button>
          </Card>

          {/* Test Game */}
          <Card style={{ textAlign: 'center', padding: '30px' }}>
            <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🧪</div>
            <h3 style={{
              color: theme.colors.primary,
              marginBottom: '12px',
              fontSize: '1.3rem'
            }}>
              Test Scoring
            </h3>
            <p style={{
              color: theme.colors.textSecondary,
              marginBottom: '20px',
              minHeight: '48px'
            }}>
              Create a test game with mock players to practice scoring
            </p>
            <button
              onClick={createTestGame}
              style={{
                ...theme.buttonStyle,
                background: '#7C2D12',
                width: '100%',
                padding: '14px',
                fontSize: '16px',
                fontWeight: '600'
              }}
            >
              Start Test Game
            </button>
          </Card>
        </div>

        {/* Error Display */}
        {error && (
          <Card variant="error" style={{ marginBottom: '30px' }}>
            <h3 style={{ 
              marginTop: 0, 
              marginBottom: '12px', 
              color: theme.colors.error 
            }}>
              ❌ Error
            </h3>
            <p style={{ marginBottom: '16px' }}>{error}</p>
            <button
              style={{
                ...theme.buttonStyle,
                padding: '12px 24px'
              }}
              onClick={() => setError(null)}
            >
              Dismiss
            </button>
          </Card>
        )}

        {/* Help Section */}
        <Card style={{ textAlign: 'center' }}>
          <h3 style={{ 
            color: theme.colors.primary, 
            marginBottom: '12px' 
          }}>
            📖 Need Help?
          </h3>
          <p style={{ 
            color: theme.colors.textSecondary, 
            marginBottom: '20px' 
          }}>
            Learn the rules or get tutorials on how to play Wolf Goat Pig
          </p>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={() => navigate('/rules')}
              style={{
                ...theme.buttonStyle,
                background: 'transparent',
                color: theme.colors.primary,
                border: `2px solid ${theme.colors.primary}`,
                padding: '10px 20px'
              }}
            >
              Game Rules
            </button>
            <button
              onClick={() => navigate('/tutorial')}
              style={{
                ...theme.buttonStyle,
                background: 'transparent',
                color: theme.colors.primary,
                border: `2px solid ${theme.colors.primary}`,
                padding: '10px 20px'
              }}
            >
              Tutorial
            </button>
            <button
              onClick={() => navigate('/')}
              style={{
                ...theme.buttonStyle,
                background: 'transparent',
                color: theme.colors.primary,
                border: `2px solid ${theme.colors.primary}`,
                padding: '10px 20px'
              }}
            >
              Back to Home
            </button>
          </div>
        </Card>
      </div>
      <CommissionerChat gameState={null} />
    </div>
  );
};

export default GameScorerPage;
