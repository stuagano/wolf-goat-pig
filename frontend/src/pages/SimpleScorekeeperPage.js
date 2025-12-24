// frontend/src/pages/SimpleScorekeeperPage.js
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { SimpleScorekeeper } from '../components/game';
import { Card } from '../components/ui';
import { useTheme } from '../theme/Provider';

const API_URL = process.env.REACT_APP_API_URL || "";

/**
 * Wrapper page for SimpleScorekeeper that loads game data
 */
const SimpleScorekeeperPage = () => {
  const { gameId } = useParams();
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [gameData, setGameData] = useState(null);

  useEffect(() => {
    const loadGame = async () => {
      try {
        const response = await fetch(`${API_URL}/games/${gameId}/state`);

        if (!response.ok) {
          throw new Error('Failed to load game');
        }

        const data = await response.json();
        setGameData(data);
        setLoading(false);
      } catch (err) {
        console.error('Error loading game:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    if (gameId) {
      loadGame();
    }
  }, [gameId]);

  if (loading) {
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
            Loading Game...
          </h2>
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
            ❌ Error Loading Game
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

  if (!gameData || !gameData.players) {
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
            ❌ Invalid Game Data
          </h2>
          <p>
            The game data is missing or incomplete.
          </p>
        </Card>
      </div>
    );
  }

  const players = gameData.players || [];
  const currentHoleNumber = gameData.current_hole || 1;

  // Get hole history and stroke allocation for SimpleScorekeeper
  const holeHistory = gameData.hole_history || [];
  const strokeAllocation = gameData.stroke_allocation || null;
  const courseName = gameData.course_name || 'Wing Point Golf & Country Club';
  const baseWager = gameData.base_wager || 1;

  return (
    <SimpleScorekeeper
      gameId={gameId}
      players={players}
      baseWager={baseWager}
      initialHoleHistory={holeHistory}
      initialCurrentHole={currentHoleNumber}
      courseName={courseName}
      initialStrokeAllocation={strokeAllocation}
    />
  );
};

export default SimpleScorekeeperPage;
