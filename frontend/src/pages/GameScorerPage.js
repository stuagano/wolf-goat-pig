// frontend/src/pages/GameScorerPage.js
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/ui';
import { useTheme } from '../theme/Provider';

const API_URL = process.env.REACT_APP_API_URL || "";

/**
 * GameScorerPage - Entry point for single-device game scoring
 * Creates a test game with mock players and redirects to the real game interface
 */
const GameScorerPage = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const createTestGame = async () => {
      setCreating(true);
      setError(null);

      try {
        const response = await fetch(`${API_URL}/games/create-test?player_count=4&course_name=Wing%20Point`, {
          method: 'POST'
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Failed to create test game: ${errorText}`);
        }

        const data = await response.json();

        if (data.game_id) {
          // Successfully created test game, navigate to it
          console.log('Test game created:', data);
          navigate(`/game/${data.game_id}`);
        } else {
          throw new Error('No game_id returned from server');
        }
      } catch (err) {
        console.error('Error creating test game:', err);
        setError(err.message);
        setCreating(false);
      }
    };

    createTestGame();
  }, [navigate]);

  if (error) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        padding: '20px'
      }}>
        <Card variant="error" style={{ maxWidth: '500px' }}>
          <h2 style={{ marginTop: 0, marginBottom: '16px', color: theme.colors.error }}>
            ❌ Error Creating Test Game
          </h2>
          <p style={{ marginBottom: '16px' }}>
            {error}
          </p>
          <button
            style={{
              ...theme.buttonStyle,
              padding: '12px 24px'
            }}
            onClick={() => window.location.reload()}
          >
            Try Again
          </button>
        </Card>
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      padding: '20px'
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
};

export default GameScorerPage;
