// frontend/src/pages/SimpleScorekeeperPage.js
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { SimpleScorekeeper, LiveScorekeeperContainer } from '../components/game';
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

  // Feature toggle state - persists to localStorage
  const [useNewScorekeeper, setUseNewScorekeeper] = useState(() => {
    return localStorage.getItem('useNewScorekeeper') === 'true';
  });

  const handleToggleScorekeeper = () => {
    const newValue = !useNewScorekeeper;
    setUseNewScorekeeper(newValue);
    localStorage.setItem('useNewScorekeeper', String(newValue));
  };

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

  // Toggle button styles
  const toggleButtonStyles = {
    container: {
      position: 'fixed',
      top: '12px',
      right: '12px',
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      backgroundColor: theme.colors.paper,
      padding: '8px 12px',
      borderRadius: '20px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      border: `1px solid ${theme.colors.border}`,
    },
    label: {
      fontSize: '11px',
      fontWeight: 600,
      color: theme.colors.textSecondary,
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
    },
    toggle: {
      position: 'relative',
      width: '44px',
      height: '24px',
      backgroundColor: useNewScorekeeper ? theme.colors.primary : theme.colors.gray300,
      borderRadius: '12px',
      cursor: 'pointer',
      transition: 'background-color 0.2s ease',
      border: 'none',
      padding: 0,
    },
    toggleKnob: {
      position: 'absolute',
      top: '2px',
      left: useNewScorekeeper ? '22px' : '2px',
      width: '20px',
      height: '20px',
      backgroundColor: '#ffffff',
      borderRadius: '50%',
      transition: 'left 0.2s ease',
      boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
    },
    versionLabel: {
      fontSize: '11px',
      fontWeight: 500,
      color: useNewScorekeeper ? theme.colors.primary : theme.colors.textSecondary,
      minWidth: '24px',
    },
  };

  return (
    <div>
      {/* Version Toggle Button */}
      <div style={toggleButtonStyles.container}>
        <span style={toggleButtonStyles.label}>
          {useNewScorekeeper ? 'v2' : 'v1'}
        </span>
        <button
          style={toggleButtonStyles.toggle}
          onClick={handleToggleScorekeeper}
          title={useNewScorekeeper ? 'Switch to Classic Scorekeeper' : 'Switch to New Modular Scorekeeper'}
          aria-label="Toggle scorekeeper version"
        >
          <span style={toggleButtonStyles.toggleKnob} />
        </button>
        <span style={toggleButtonStyles.versionLabel}>
          {useNewScorekeeper ? 'New' : 'Classic'}
        </span>
      </div>

      {/* Render appropriate scorekeeper based on toggle */}
      {useNewScorekeeper ? (
        <LiveScorekeeperContainer
          gameId={gameId}
          enableCreecherFeature={true}
          enableAardvark={players.length >= 4}
          enableCommissionerChat={false}
          enableBadgeNotifications={true}
          onGameComplete={(finalStandings) => {
            console.log('Game complete! Final standings:', finalStandings);
          }}
          onError={(err) => {
            console.error('Scorekeeper error:', err);
          }}
        />
      ) : (
        <SimpleScorekeeper
          gameId={gameId}
          players={players}
          baseWager={baseWager}
          initialHoleHistory={holeHistory}
          initialCurrentHole={currentHoleNumber}
          courseName={courseName}
          initialStrokeAllocation={strokeAllocation}
        />
      )}
    </div>
  );
};

export default SimpleScorekeeperPage;
