import React, { useMemo } from 'react';
import { useTheme } from '../../theme/Provider';
import { Timeline, PokerBettingPanel, HoleVisualization } from './';
import SimulationDecisionPanel from './SimulationDecisionPanel';
import createEnhancedSimulationLayoutStyles from './styles/enhancedSimulationLayout';

const DEFAULT_TIMELINE_MAX_HEIGHT = 400;

/**
 * Enhanced Simulation Layout with Timeline and Poker Betting
 * Combines the TV Poker layout with Texas Hold'em style betting and timeline
 */
const EnhancedSimulationLayout = ({
  gameState,
  shotState,
  probabilities,
  onDecision,
  onPlayNextShot,
  timelineEvents = [],
  timelineLoading = false,
  pokerState = {},
  bettingOptions = [],
  onBettingAction,
  currentPlayer = 'human',
  interactionNeeded,
  hasNextShot,
  feedback = [],
}) => {
  const theme = useTheme();
  const styles = useMemo(
    () => createEnhancedSimulationLayoutStyles(theme),
    [theme]
  );
  const pendingInteraction = interactionNeeded ?? gameState?.interactionNeeded ?? null;
  const shotAvailable = hasNextShot ?? gameState?.hasNextShot ?? false;
  const feedbackItems = useMemo(() => {
    if (Array.isArray(feedback) && feedback.length > 0) {
      return feedback;
    }
    if (Array.isArray(gameState?.feedback)) {
      return gameState.feedback;
    }
    return [];
  }, [feedback, gameState]);

  // Export hole feed data for review
  const exportHoleFeed = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      hole: gameState?.current_hole || 1,
      par: gameState?.hole_par || 4,
      distance: gameState?.hole_distance || 0,
      players: players.map(p => ({
        id: p.id,
        name: p.name,
        handicap: p.handicap,
        points: p.points,
        status: p.status
      })),
      ballPositions: gameState?.hole_state?.ball_positions || {},
      currentShot: gameState?.hole_state?.current_shot_number || 1,
      nextPlayer: gameState?.hole_state?.next_player_to_hit,
      feedback: gameState?.feedback || [],
      gameComplete: gameState?.hole_state?.hole_complete || false,
      probabilities: probabilities,
      shotState: shotState,
      timelineEvents: timelineEvents,
      pokerState: pokerState
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `wgp-hole-${gameState?.current_hole || 1}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Handle shot progression button click
  const handlePlayShot = () => {
    if (onPlayNextShot && shotAvailable && !pendingInteraction) {
      onPlayNextShot();
    }
  };

  // Use real player data from game state
  const players = gameState?.players || [];

  const shotMetaEntries = useMemo(() => {
    if (!shotState || typeof shotState !== 'object') {
      return [];
    }

    const entries = [];
    const pushEntry = (label, rawValue, formatter) => {
      if (rawValue === undefined || rawValue === null || rawValue === '') {
        return;
      }
      const value = formatter ? formatter(rawValue) : rawValue;
      entries.push({ label, value });
    };

    pushEntry('Suggested Club', shotState.club || shotState.recommended_club);
    pushEntry(
      'Distance to Pin',
      shotState.distance_to_pin ?? shotState.remaining_distance ?? shotState.target_distance,
      (value) => (typeof value === 'number' ? `${Math.round(value)} yds` : value)
    );
    pushEntry('Lie', shotState.lie || shotState.lie_type || shotState.ball_lie);
    pushEntry(
      'Wind',
      shotState.wind || shotState.wind_speed || shotState.wind_direction,
      (value) => {
        if (typeof value === 'number') {
          return `${Math.round(value)} mph`;
        }
        return value;
      }
    );
    pushEntry('Shot Type', shotState.shot_type || shotState.strategy);
    pushEntry('Target', shotState.target || shotState.aim_point);
    pushEntry(
      'Confidence',
      shotState.confidence,
      (value) => (typeof value === 'number' ? `${Math.round(value * 100)}%` : value)
    );

    return entries;
  }, [shotState]);

  // Generate win probabilities based on real players
  const winProbabilities = probabilities?.win || (() => {
    const probs = {};
    players.forEach((player, index) => {
      const baseProbabilities = [28, 35, 22, 15];
      probs[player.name] = baseProbabilities[index] || 20;
    });
    return probs;
  })();

  const shotProbabilities = probabilities?.shot || {
    'Great': 15,
    'Good': 45,
    'OK': 30,
    'Poor': 10
  };

  // Generate partnership EVs
  const partnershipEVs = probabilities?.partnerships || (() => {
    const evs = {};
    players.forEach((player, index) => {
      if (player.id !== 'human') {
        const baseEVs = [2.3, 1.1, -0.5];
        evs[player.name] = baseEVs[index - 1] || 0.5;
      }
    });
    evs['Solo'] = 3.5;
    return evs;
  })();

  return (
    <div style={styles.container}>
      {/* Top Status Bar */}
      <div style={styles.topBar}>
        <div style={styles.topBarStat}>
          <span style={styles.topBarLabel}>Current Hole</span>
          <span style={styles.topBarValue}>
            Hole {gameState?.current_hole || 1} · Par {gameState?.hole_par || 4} · {gameState?.hole_distance || 435} yards
          </span>
        </div>
        <div style={styles.topBarStat}>
          <span style={styles.topBarLabel}>Wager Status</span>
          <span style={styles.topBarValue}>
            Base Wager: ${gameState?.base_wager || 10} · {gameState?.multiplier || '1'}x Active
          </span>
        </div>
        <div style={styles.autoPlayControl}>
          {shotAvailable && !pendingInteraction && (
            <button
              type="button"
              onClick={handlePlayShot}
              style={styles.playNextShotButton}
            >
              ⛳ Play Next Shot
            </button>
          )}
          {pendingInteraction && (
            <div style={styles.pendingBadge}>
              ⚠️ Decision Required
            </div>
          )}
          <button
            type="button"
            onClick={exportHoleFeed}
            style={styles.exportButton}
          >
            📊 Export Feed
          </button>
        </div>
      </div>

      {/* Left Panel - Players and Timeline */}
      <div style={styles.leftPanel}>
        {/* Player Panel */}
        <div style={styles.playerPanel}>
          <h3 style={styles.panelTitle}>Players</h3>
          {players.map(player => (
            <div
              key={player.id}
              style={{
                ...styles.playerCard,
                ...(player.isCurrent ? styles.playerCardActive : {})
              }}
            >
              <div style={styles.playerName}>
                {player.id === 'human' ? '👤' : '💻'} {player.name}
              </div>
              <div style={styles.playerMeta}>
                Hdcp: {player.handicap}
              </div>
              <div style={{
                ...styles.playerPoints,
                color: player.points >= 0 ? theme.colors.successLight : theme.colors.errorLight
              }}>
                {player.points >= 0 ? '+' : ''}{player.points} pts
              </div>
            </div>
          ))}
        </div>

        {/* Timeline Component */}
        <div style={styles.flexGrow}>
          <Timeline
            events={timelineEvents}
            loading={timelineLoading}
            maxHeight={DEFAULT_TIMELINE_MAX_HEIGHT}
            autoScroll={true}
            showPokerStyle={true}
          />
        </div>
      </div>

      {/* Center Panel - Course View */}
      <div style={styles.centerPanel}>
        <HoleVisualization
          holeNumber={gameState?.current_hole}
          holeDistance={gameState?.hole_distance}
          par={gameState?.hole_par}
          players={players}
          ballPositions={gameState?.hole_state?.ball_positions}
          nextPlayerId={gameState?.hole_state?.next_player_to_hit}
          currentShotNumber={gameState?.hole_state?.current_shot_number}
        />

        {/* Poker Betting Panel */}
        <div style={styles.flexGrow}>
          <PokerBettingPanel
            pokerState={pokerState}
            bettingOptions={bettingOptions}
            onBettingAction={onBettingAction}
            currentPlayer={currentPlayer}
            disabled={!pendingInteraction && bettingOptions.length === 0}
          />
        </div>

        {shotState && (
          <div style={styles.shotDetails}>
            <h3 style={styles.shotPlannerTitle}>🎯 Shot Planner</h3>
            {shotState.description && (
              <p style={styles.shotDescription}>
                {shotState.description}
              </p>
            )}

            {shotMetaEntries.length > 0 && (
              <div style={styles.shotMetaGrid}>
                {shotMetaEntries.map(({ label, value }) => (
                  <div key={label} style={styles.shotMetaItem}>
                    <div style={styles.shotMetaLabel}>{label}</div>
                    <div style={styles.shotMetaValue}>{value}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <SimulationDecisionPanel
          gameState={gameState}
          interactionNeeded={pendingInteraction}
          onDecision={onDecision}
          onNextShot={onPlayNextShot}
          hasNextShot={shotAvailable}
        />
      </div>

      {/* Right Panel - Analytics */}
      <div style={styles.rightPanel}>
        <div style={styles.metricsPanel}>
          <h3 style={styles.panelTitle}>Live Analytics</h3>

          {/* Win Probabilities */}
          <div style={styles.metricSection}>
            <h4 style={styles.metricSectionTitle}>Win Probability</h4>
            {Object.entries(winProbabilities).map(([player, prob]) => (
              <div key={player}>
                <div style={styles.metricLabel}>{player}</div>
                <div style={styles.probabilityBar}>
                  <div style={{ ...styles.probabilityFill, width: `${prob}%` }}>
                    {prob}%
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Shot Success */}
          <div style={styles.metricSection}>
            <h4 style={styles.metricSectionTitle}>Shot Success</h4>
            {Object.entries(shotProbabilities).map(([outcome, prob]) => (
              <div key={outcome} style={styles.metricRow}>
                <span>{outcome}</span>
                <span>{prob}%</span>
              </div>
            ))}
          </div>

          {/* Partnership EVs */}
          <div style={styles.metricSection}>
            <h4 style={styles.metricSectionTitle}>Partnership EV</h4>
            {Object.entries(partnershipEVs).map(([partner, ev]) => (
              <div key={partner} style={styles.metricRow}>
                <span>{partner}</span>
                <span style={ev >= 0 ? styles.metricValuePositive : styles.metricValueNegative}>
                  {ev >= 0 ? '+' : ''}{ev}
                </span>
              </div>
            ))}
          </div>
        </div>

        {feedbackItems.length > 0 && (
          <div style={styles.feedbackPanel}>
            <h3 style={styles.panelTitle}>📚 Educational Feedback</h3>
            {feedbackItems.map((entry, index) => {
              const isObject = entry && typeof entry === 'object';
              const title = isObject
                ? entry.title || entry.heading || `Update ${index + 1}`
                : `Update ${index + 1}`;
              const message = isObject
                ? entry.message || entry.body || entry.text || ''
                : entry;

              return (
                <div key={index} style={styles.feedbackItem}>
                  <div style={styles.feedbackTitle}>{title}</div>
                  <div style={styles.feedbackBody}>{String(message)}</div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedSimulationLayout;