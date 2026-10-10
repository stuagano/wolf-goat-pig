// frontend/src/pages/SimpleScorekeeperPage.js
import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { SimpleScorekeeper } from '../components/game';
import ScorecardBackfill from '../components/game/ScorecardBackfill';
import { Card } from '../components/ui';
import { useTheme } from '../theme/Provider';
import ErrorBoundary, { GameErrorFallback } from '../components/common/ErrorBoundary';
import useGameData from '../hooks/useGameData';

/**
 * Wrapper page for SimpleScorekeeper that loads game data
 */
const SimpleScorekeeperPage = () => {
  const { gameId } = useParams();
  const theme = useTheme();
  const { loading, error, game, reload } = useGameData(gameId);
  const [showBackfill, setShowBackfill] = useState(false);

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

  if (!game || !game.players) {
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

  const { players, currentHole, holeHistory, standings, strokeAllocation, courseName, baseWager, isComplete } = game;

  // "Fill in holes" backfill editor — only available for completed rounds
  if (isComplete && showBackfill) {
    return (
      <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
        <ScorecardBackfill
          gameId={gameId}
          players={players}
          holeHistory={holeHistory}
          standings={standings}
          onSaved={() => {
            setShowBackfill(false);
            reload();
          }}
          onCancel={() => setShowBackfill(false)}
        />
      </div>
    );
  }

  return (
    <ErrorBoundary FallbackComponent={GameErrorFallback}>
      <SimpleScorekeeper
        gameId={gameId}
        players={players}
        baseWager={baseWager}
        initialHoleHistory={holeHistory}
        initialCurrentHole={currentHole}
        courseName={courseName}
        initialStrokeAllocation={strokeAllocation}
      />
      {isComplete && (
        <div style={{ padding: '0 20px 20px', maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
          <button
            type="button"
            onClick={() => setShowBackfill(true)}
            style={{
              padding: '12px 24px',
              fontSize: '16px',
              fontWeight: 'bold',
              borderRadius: '8px',
              border: '2px solid #f59e0b',
              background: 'white',
              color: '#b45309',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            ✏️ Fill in holes
          </button>
        </div>
      )}
    </ErrorBoundary>
  );
};

export default SimpleScorekeeperPage;
