// frontend/src/pages/SimpleScorekeeperPage.js
import React, { useEffect, useState, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { SimpleScorekeeper } from '../components/game';
import ScorecardBackfill from '../components/game/ScorecardBackfill';
import { Card } from '../components/ui';
import { useTheme } from '../theme/Provider';
import ErrorBoundary, { GameErrorFallback } from '../components/common/ErrorBoundary';
import { apiConfig } from '../config/api.config';
import syncManager from '../services/syncManager';

const API_URL = apiConfig.baseUrl;

/**
 * Wrapper page for SimpleScorekeeper that loads game data
 */
const SimpleScorekeeperPage = () => {
  const { gameId } = useParams();
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [gameData, setGameData] = useState(null);
  const [showBackfill, setShowBackfill] = useState(false);

  const loadGame = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/games/${gameId}/state`);

      if (!response.ok) {
        throw new Error('Failed to load game');
      }

      const data = await response.json();
      // Reconcile the local cache against server truth: flush unsynced edits,
      // or heal a stale/duplicated cache by overwriting it with server state.
      // Map GET /state (snake_case) into the local cache shape (camelCase).
      syncManager.reconcileOnLoad(gameId, {
        holeHistory: data.hole_history || [],
        currentHole: data.current_hole,
        playerStandings: data.standings || {},
      });
      setGameData(data);
      setLoading(false);
    } catch (err) {
      console.error('Error loading game:', err);
      setError(err.message);
      setLoading(false);
    }
  }, [gameId]);

  useEffect(() => {
    if (gameId) {
      loadGame();
    }
  }, [gameId, loadGame]);

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
  // Completed games (including scorecard-scan rounds) have no current_hole in
  // their state; use 19 so SimpleScorekeeper's isGameComplete gate fires.
  const currentHoleNumber = gameData.current_hole || (gameData.game_status === 'completed' ? 19 : 1);

  // Get hole history and stroke allocation for SimpleScorekeeper
  const holeHistory = gameData.hole_history || [];
  const strokeAllocation = gameData.stroke_allocation || null;
  const courseName = gameData.course_name || 'Wing Point Golf & Country Club';
  const baseWager = gameData.base_wager || 1;

  const isCompleted = gameData.game_status === 'completed';

  // "Fill in holes" backfill editor — only available for completed rounds
  if (isCompleted && showBackfill) {
    return (
      <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
        <ScorecardBackfill
          gameId={gameId}
          players={players}
          holeHistory={holeHistory}
          standings={gameData.standings || {}}
          photoUrl={`${API_URL}/games/${gameId}/scorecard-photo`}
          onSaved={() => {
            setShowBackfill(false);
            loadGame();
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
        initialCurrentHole={currentHoleNumber}
        courseName={courseName}
        initialStrokeAllocation={strokeAllocation}
      />
      {isCompleted && (
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
