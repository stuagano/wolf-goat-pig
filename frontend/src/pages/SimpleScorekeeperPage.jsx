// frontend/src/pages/SimpleScorekeeperPage.js
import React, { useEffect, useState } from 'react';
import CompletedRoundView from '../components/game/CompletedRoundView';
import RoundDiscussion from '../components/game/RoundDiscussion';
import RoundConflictReview from '../components/game/RoundConflictReview';
import { apiConfig } from '../config/api.config';
import { readRoundResponse } from '../services/roundIdentity';
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
const ActiveScorekeeperPage = ({ onCompleted }) => {
  const { gameId } = useParams();
  const theme = useTheme();
  const { loading, error, syncError, game, retrySync } = useGameData(gameId);
  useEffect(() => {
    if (game?.isComplete) onCompleted();
  }, [game?.isComplete, onCompleted]);

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

  if (game.isComplete) return <p>Loading accepted round…</p>;
  const { players, currentHole, holeHistory, strokeAllocation, courseName, baseWager } = game;

  // Non-blocking by design: the round below is usable, so warn beside it rather
  // than replacing it, and never imply the scores were queued or will retry.
  const syncWarning = syncError ? (
    <Card style={{ margin: '16px auto', maxWidth: '800px', borderLeft: `4px solid ${theme.colors.warning}`, color: theme.colors.textPrimary }}>
      <div role="alert">
        <h3 style={{ margin: '0 0 8px', color: theme.colors.warning }}>
          ⚠️ Scores not queued for sync
        </h3>
        <p style={{ margin: '0 0 8px' }}>{syncError}</p>
        <p style={{ margin: 0 }}>
          Your saved round below is still usable. Keep scoring, then retry.
        </p>
      </div>
      <button
        type="button"
        style={{ ...theme.buttonStyle, marginTop: '12px', padding: '10px 20px' }}
        onClick={retrySync}
      >
        Retry sync
      </button>
    </Card>
  ) : null;

  return (
    <ErrorBoundary FallbackComponent={GameErrorFallback}>
      {syncWarning}
      <SimpleScorekeeper
        gameId={gameId}
        players={players}
        baseWager={baseWager}
        initialHoleHistory={holeHistory}
        initialCurrentHole={currentHole}
        courseName={courseName}
        initialStrokeAllocation={strokeAllocation}
      />
    </ErrorBoundary>
  );
};

// Lifecycle is read before mounting anything that can reconcile an offline queue.
function RoundLifecycle({ gameId }) {
  const [snapshot, setSnapshot] = useState(null);
  const [error, setError] = useState('');
  const [version, setVersion] = useState(0);
  const [editing, setEditing] = useState(false);
  useEffect(() => {
    let cancelled = false;
    setSnapshot(null);
    setError('');
    (async () => {
      try {
        const state = await readRoundResponse(await fetch(`${apiConfig.baseUrl}/games/${gameId}/state`));
        const summary = state.game_status === 'completed'
          ? await readRoundResponse(await fetch(`${apiConfig.baseUrl}/games/${gameId}/round-summary`)) : null;
        if (!cancelled) setSnapshot({ state, summary });
      } catch (err) { if (!cancelled) setError(err.message); }
    })();
    return () => { cancelled = true; };
  }, [gameId, version]);
  if (error) return <div role="alert">{error}<button onClick={() => setVersion(v => v + 1)}>Reload round</button></div>;
  if (!snapshot) return <p>Loading round…</p>;
  if (!snapshot.summary) return <ActiveScorekeeperPage onCompleted={() => setVersion(v => v + 1)} />;
  const summary = snapshot.summary;
  const players = summary.players.filter(p => !p.is_retracted).map(p => ({ ...p, id: p.participant_id }));
  const standings = Object.fromEntries(players.map(p => [p.id, p.quarters]));
  return <main style={{ maxWidth: 1000, margin: 'auto', padding: 20 }}>
    {editing ? <ScorecardBackfill gameId={gameId} players={players} holeHistory={summary.hole_history}
      standings={standings} expectedRevision={summary.revision}
      statePlayers={snapshot.state.revision === summary.revision ? snapshot.state.players ?? null : null}
      onCancel={() => setEditing(false)}
      onSaved={() => { setEditing(false); setVersion(v => v + 1); }} />
      : <CompletedRoundView gameId={gameId} players={players} holeHistory={summary.hole_history}
        summary={summary} isMarkedComplete onEditScores={() => setEditing(true)} />}
    <RoundDiscussion key={gameId} gameId={gameId} />
    <RoundConflictReview key={`${gameId}-${version}`} gameId={gameId} />
  </main>;
}
const SimpleScorekeeperPage = () => {
  const { gameId } = useParams();
  return <RoundLifecycle key={gameId} gameId={gameId} />;
};
export default SimpleScorekeeperPage;
