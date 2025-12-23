// =============================================================================
// LiveScorekeeperContainer - Main Orchestration Component
// Full feature parity with SimpleScorekeeper (~2807 lines -> modular hooks)
// =============================================================================

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useTheme } from '../../../theme/Provider';

// Import hooks
import {
  useGameState,
  useStrokeAllocation,
  useRotationWager,
  useBettingActions,
  useHoleSubmission,
  useAardvark,
} from './hooks';

// Import types
import {
  LiveScorekeeperContainerProps,
  Game,
  Player,
  Course,
  Hole,
  BettingAction,
  SubmitHolePayload,
  Teams,
  PlayerStandings,
} from './types';

// Import UI components
import LiveScorekeeper from './LiveScorekeeper';
import QuartersPresets from './QuartersPresets';
import HoleNavigation from './HoleNavigation';
import AardvarkPanel from './AardvarkPanel';

// Import external components (JS without type definitions)
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import Scorecard from '../Scorecard';
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import CommissionerChat from '../../CommissionerChat';
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { BadgeNotificationManager, triggerBadgeNotification } from '../../BadgeNotification';

// =============================================================================
// Default Betting Actions
// =============================================================================

const DEFAULT_BETTING_ACTIONS: BettingAction[] = [
  {
    id: 'float',
    label: 'Float',
    description: 'Double the wager',
  },
  {
    id: 'option',
    label: 'Option',
    description: 'Press the bet',
  },
  {
    id: 'duncan',
    label: 'Duncan',
    description: '3-for-2 solo',
  },
  {
    id: 'vinnies',
    label: 'Vinnies',
    description: 'Score multiplier',
  },
];

// =============================================================================
// API URL
// =============================================================================
const API_URL = process.env.REACT_APP_API_URL || '';

// =============================================================================
// Container Component
// =============================================================================

const LiveScorekeeperContainer: React.FC<LiveScorekeeperContainerProps> = ({
  gameId,
  // Optional: pass data directly to avoid re-fetching
  initialPlayers,
  initialHoleHistory,
  initialCurrentHole,
  courseName,
  initialStrokeAllocation,
  baseWager,
  // Feature flags
  enableCreecherFeature = true,
  enableAardvark = true,
  enableCommissionerChat = true,
  enableBadgeNotifications = true,
  onGameComplete,
  onError,
}) => {
  const theme = useTheme();

  // =============================================================================
  // Loading State
  // =============================================================================
  const [isInitializing, setIsInitializing] = useState(!initialPlayers);
  const [initError, setInitError] = useState<string | null>(null);
  const [gameData, setGameData] = useState<{
    game: Game;
    players: Player[];
    course: Course;
    holeHistory: Hole[];
  } | null>(null);

  // =============================================================================
  // Initialize Game Data - Only fetch if not provided
  // =============================================================================
  useEffect(() => {
    // If data was passed as props, use it directly
    if (initialPlayers) {
      const game: Game = {
        id: gameId,
        courseId: '',
        courseName: courseName || 'Unknown Course',
        currentHole: initialCurrentHole || 1,
        baseWager: baseWager || 1,
        status: 'in_progress',
      };

      const players: Player[] = initialPlayers.map((p) => ({
        id: p.id || '',
        name: p.name || 'Unknown',
        handicap: p.handicap || 0,
        teeOrder: p.tee_order || p.teeOrder || 0,
        standings: {
          quarters: p.points || 0,
          soloCount: 0,
          floatCount: 0,
          optionCount: 0,
        },
      }));

      const course: Course = {
        id: '',
        name: courseName || 'Unknown Course',
        holes: [],
      };

      // Transform hole history to expected format
      const holeHistory: Hole[] = (initialHoleHistory || []).map((h) => ({
        hole: h.hole,
        par: h.par || 4,
        teams: h.teams || { type: 'partners' as const, team1: [], team2: [] },
        captainId: h.captainId || '',
        grossScores: h.gross_scores || h.grossScores || {},
        pointsDelta: h.points_delta || h.pointsDelta || {},
        wager: h.wager || 1,
        winner: 'push' as const,
        bets: [],
        notes: '',
      }));

      setGameData({ game, players, course, holeHistory });
      setIsInitializing(false);
      return;
    }

    // Otherwise, fetch the data
    async function fetchGameData() {
      try {
        setIsInitializing(true);
        const response = await fetch(`${API_URL}/games/${gameId}/state`);
        if (!response.ok) throw new Error('Failed to fetch game state');
        const data = await response.json();

        const game: Game = {
          id: gameId,
          courseId: data.course_id || '',
          courseName: data.course_name || 'Unknown Course',
          currentHole: data.current_hole || 1,
          baseWager: data.base_wager || 1,
          status: 'in_progress',
        };

        interface ApiPlayer {
          id?: string;
          player_id?: string;
          name?: string;
          handicap?: number;
          tee_order?: number;
          points?: number;
        }

        const players: Player[] = (data.players || []).map((p: ApiPlayer) => ({
          id: p.id || p.player_id || '',
          name: p.name || 'Unknown',
          handicap: p.handicap || 0,
          teeOrder: p.tee_order || 0,
          standings: {
            quarters: p.points || 0,
            soloCount: 0,
            floatCount: 0,
            optionCount: 0,
          },
        }));

        const course: Course = {
          id: data.course_id || '',
          name: data.course_name || 'Unknown Course',
          holes: data.course_holes || [],
        };

        interface ApiHole {
          hole: number;
          par?: number;
          teams?: Teams;
          captain_id?: string;
          gross_scores?: Record<string, number>;
          points_delta?: Record<string, number>;
          wager?: number;
          notes?: string;
        }

        const holeHistory: Hole[] = (data.hole_history || []).map((h: ApiHole) => ({
          hole: h.hole,
          par: h.par || 4,
          teams: h.teams || { type: 'partners' as const, team1: [], team2: [] },
          captainId: h.captain_id || '',
          grossScores: h.gross_scores || {},
          pointsDelta: h.points_delta || {},
          wager: h.wager || 1,
          winner: 'push' as const,
          bets: [],
          notes: h.notes || '',
        }));

        setGameData({ game, players, course, holeHistory });
        setInitError(null);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to initialize game';
        setInitError(message);
        onError?.(err instanceof Error ? err : new Error(message));
      } finally {
        setIsInitializing(false);
      }
    }

    fetchGameData();
  }, [gameId, initialPlayers, initialHoleHistory, initialCurrentHole, courseName, baseWager, onError]);

  // =============================================================================
  // Loading/Error States
  // =============================================================================

  if (isInitializing) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '200px',
        color: theme.colors.textSecondary,
      }}>
        Loading game...
      </div>
    );
  }

  if (initError || !gameData) {
    return (
      <div style={{
        padding: theme.spacing[4],
        backgroundColor: theme.isDark ? 'rgba(220, 38, 38, 0.2)' : 'rgba(220, 38, 38, 0.1)',
        borderRadius: theme.borderRadius.md,
        color: theme.colors.error,
        textAlign: 'center',
      }}>
        <p>Error loading game: {initError}</p>
        <button
          onClick={() => window.location.reload()}
          style={{
            marginTop: theme.spacing[3],
            padding: `${theme.spacing[2]} ${theme.spacing[4]}`,
            backgroundColor: theme.colors.error,
            color: '#ffffff',
            border: 'none',
            borderRadius: theme.borderRadius.base,
            cursor: 'pointer',
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <LiveScorekeeperContainerInner
      {...gameData}
      gameId={gameId}
      initialStrokeAllocation={initialStrokeAllocation}
      enableCreecherFeature={enableCreecherFeature}
      enableAardvark={enableAardvark}
      enableCommissionerChat={enableCommissionerChat}
      enableBadgeNotifications={enableBadgeNotifications}
      onGameComplete={onGameComplete}
      onError={onError}
    />
  );
};

// =============================================================================
// Inner Container (with hooks)
// =============================================================================

interface InnerContainerProps {
  gameId: string;
  game: Game;
  players: Player[];
  course: Course;
  holeHistory: Hole[];
  initialStrokeAllocation?: Record<string, number[]> | Record<string, Record<number, number>> | null;
  enableCreecherFeature?: boolean;
  enableAardvark?: boolean;
  enableCommissionerChat?: boolean;
  enableBadgeNotifications?: boolean;
  onGameComplete?: (standings: Record<string, PlayerStandings>) => void;
  onError?: (error: Error) => void;
}

const LiveScorekeeperContainerInner: React.FC<InnerContainerProps> = ({
  gameId,
  game,
  players: initialPlayers,
  course,
  holeHistory: initialHoleHistory,
  initialStrokeAllocation,
  enableCreecherFeature = true,
  enableAardvark = true,
  enableCommissionerChat = true,
  enableBadgeNotifications = true,
  onGameComplete,
  onError,
}) => {
  const theme = useTheme();

  // =============================================================================
  // UI State
  // =============================================================================
  const [showQuartersPresets, _setShowQuartersPresets] = useState(true);
  const [showAardvarkPanel, setShowAardvarkPanel] = useState(true);
  const [isGameComplete, setIsGameComplete] = useState(false);
  const [showCommissionerChat, setShowCommissionerChat] = useState(false);

  // Suppress unused warning - reserved for future quarters presets toggle
  void _setShowQuartersPresets;

  // =============================================================================
  // Initialize Hooks
  // =============================================================================
  const {
    state: gameState,
    toggleTeam1,
    selectCaptain,
    setTeamMode,
    setScore,
    setQuarters,
    applyQuartersPreset,
    goToHole,
    undoLastHole,
    setNotes,
    editPlayerName,
    validateCurrentHole,
  } = useGameState({
    game,
    players: initialPlayers,
    course,
    initialHoleHistory,
  });

  const {
    allocations: strokeAllocations,
    getPlayerAllocation,
    calculateNetScore: _calculateNetScore,
  } = useStrokeAllocation({
    players: gameState.players,
    course,
    creecherEnabled: enableCreecherFeature,
  });

  // Suppress unused warning
  void _calculateNetScore;

  const {
    rotation,
    wager,
    isLoading: _rotationLoading,
    fetchRotation,
    fetchWager,
  } = useRotationWager({
    playerCount: gameState.players.length,
  });

  // Suppress unused warning - reserved for loading indicator
  void _rotationLoading;

  const {
    betting: _betting,
    invokeFloat,
    invokeOption,
    invokeDuncan,
    invokeVinnies,
    offerBet: _offerBet,
    acceptOffer: _acceptOffer,
    declineOffer: _declineOffer,
    canInvokeFloat: _canInvokeFloat,
    canInvokeOption: _canInvokeOption,
    canInvokeDuncan: _canInvokeDuncan,
    getPlayerUsage: _getPlayerUsage,
  } = useBettingActions({
    playerIds: gameState.players.map(p => p.id),
    baseWager: game.baseWager,
    currentHoleNumber: gameState.currentHole.hole,
  });

  // Suppress unused warnings - reserved for future betting UI integration
  void _betting;
  void _offerBet;
  void _acceptOffer;
  void _declineOffer;
  void _canInvokeFloat;
  void _canInvokeOption;
  void _canInvokeDuncan;
  void _getPlayerUsage;

  const {
    isSubmitting,
    error: submissionError,
    submitHole,
    completeGame,
  } = useHoleSubmission();

  const {
    aardvark,
    setInvisibleAardvarkScore,
    getCurrentAardvark: _getCurrentAardvark,
    advanceAardvark,
    isPlayerAardvark: _isPlayerAardvark,
  } = useAardvark({
    players: gameState.players,
    tunkarriEnabled: false,
  });

  // Suppress unused warnings - reserved for aardvark UI
  void _getCurrentAardvark;
  void _isPlayerAardvark;

  // =============================================================================
  // Fetch Rotation & Wager on Hole Change
  // =============================================================================
  useEffect(() => {
    fetchRotation(gameId, gameState.currentHole.hole);
    fetchWager(gameId, gameState.currentHole.hole);
  }, [gameId, gameState.currentHole.hole, fetchRotation, fetchWager]);

  // =============================================================================
  // Stroke Allocation - Use provided or calculated
  // =============================================================================
  const effectiveStrokeAllocation = useMemo(() => {
    if (initialStrokeAllocation && Object.keys(initialStrokeAllocation).length > 0) {
      return initialStrokeAllocation;
    }
    // Convert from allocations format to strokeAllocation format
    const result: Record<string, Record<number, number>> = {};
    Object.entries(strokeAllocations).forEach(([playerId, holes]) => {
      result[playerId] = {};
      Object.entries(holes as Record<string, { totalStrokes: number }>).forEach(([holeNum, alloc]) => {
        result[playerId][Number(holeNum)] = alloc.totalStrokes;
      });
    });
    return result;
  }, [initialStrokeAllocation, strokeAllocations]);

  // =============================================================================
  // Enhance Rotation with Stroke Data
  // =============================================================================
  const _enhancedRotation = useMemo(() => {
    return {
      ...rotation,
      rotationOrder: rotation.rotationOrder.map(player => {
        const allocation = getPlayerAllocation(player.playerId, gameState.currentHole.hole);
        return {
          ...player,
          strokesOnHole: allocation?.totalStrokes || 0,
        };
      }),
    };
  }, [rotation, getPlayerAllocation, gameState.currentHole.hole]);

  // Suppress unused warning - reserved for enhanced rotation display
  void _enhancedRotation;

  // =============================================================================
  // Build Teams Object for Submission
  // =============================================================================
  const buildTeamsObject = useCallback((): Teams => {
    const { currentHole } = gameState;
    if (currentHole.teamMode === 'partners') {
      return {
        type: 'partners',
        team1: currentHole.team1,
        team2: currentHole.team2,
      };
    }
    return {
      type: 'solo',
      captain: currentHole.captain || '',
      opponents: currentHole.opponents,
    };
  }, [gameState]);

  // =============================================================================
  // Handle Betting Action Invocation
  // =============================================================================
  const handleInvokeBet = useCallback((betType: string, playerId: string) => {
    switch (betType) {
      case 'float':
        invokeFloat(playerId);
        break;
      case 'option':
        invokeOption(playerId);
        break;
      case 'duncan':
        invokeDuncan(playerId);
        break;
      case 'vinnies':
        invokeVinnies();
        break;
    }
  }, [invokeFloat, invokeOption, invokeDuncan, invokeVinnies]);

  // =============================================================================
  // Handle Hole Submission
  // =============================================================================
  const handleSubmitHole = useCallback(async () => {
    const validation = validateCurrentHole();
    if (!validation.isValid) {
      console.warn('Validation failed:', validation.errors);
      return;
    }

    try {
      const payload: SubmitHolePayload = {
        gameId,
        holeNumber: gameState.currentHole.hole,
        teams: buildTeamsObject(),
        grossScores: gameState.currentHole.grossScores,
        quarters: gameState.currentHole.quarters,
        wager: wager?.wager || gameState.currentHole.wager,
        bets: gameState.currentHole.bets,
        notes: gameState.currentHole.notes,
      };

      const response = await submitHole(payload);

      // Advance aardvark if enabled
      if (enableAardvark && aardvark.mode === 'real') {
        advanceAardvark();
      }

      // Navigate to next hole
      if (response.nextHole <= 18) {
        goToHole(response.nextHole);
      } else {
        setIsGameComplete(true);
      }

      // Handle achievements notification
      if (enableBadgeNotifications && response.achievements && response.achievements.length > 0) {
        response.achievements.forEach((badge) => {
          triggerBadgeNotification(badge);
        });
      }
    } catch (err) {
      onError?.(err instanceof Error ? err : new Error('Failed to submit hole'));
    }
  }, [
    validateCurrentHole,
    gameId,
    gameState,
    buildTeamsObject,
    wager,
    submitHole,
    enableAardvark,
    enableBadgeNotifications,
    aardvark.mode,
    advanceAardvark,
    goToHole,
    onError,
  ]);

  // =============================================================================
  // Handle Game Completion
  // =============================================================================
  const handleCompleteGame = useCallback(async () => {
    try {
      await completeGame(gameId);

      // Calculate final standings
      const finalStandings: Record<string, PlayerStandings> = {};
      gameState.players.forEach(player => {
        finalStandings[player.id] = player.standings;
      });

      onGameComplete?.(finalStandings);
    } catch (err) {
      onError?.(err instanceof Error ? err : new Error('Failed to complete game'));
    }
  }, [completeGame, gameId, gameState.players, onGameComplete, onError]);

  // =============================================================================
  // Handle Hole Navigation
  // =============================================================================
  const handleNavigateHole = useCallback((holeNumber: number) => {
    goToHole(holeNumber);
  }, [goToHole]);

  const handlePreviousHole = useCallback(() => {
    if (gameState.currentHole.hole > 1) {
      goToHole(gameState.currentHole.hole - 1);
    }
  }, [gameState.currentHole.hole, goToHole]);

  const handleNextHole = useCallback(() => {
    if (gameState.currentHole.hole < 18) {
      goToHole(gameState.currentHole.hole + 1);
    }
  }, [gameState.currentHole.hole, goToHole]);

  // =============================================================================
  // Handle Scorecard Edit
  // =============================================================================
  const handleScorecardEdit = useCallback((data: { hole: number; playerId: string; strokes: number; quarters: number }) => {
    // Navigate to the hole being edited
    goToHole(data.hole);
    // Update the score for this player
    if (data.strokes !== null) {
      setScore(data.playerId, data.strokes);
    }
    if (data.quarters !== null) {
      setQuarters(data.playerId, data.quarters);
    }
  }, [goToHole, setScore, setQuarters]);

  // =============================================================================
  // Handle Notes - for Commissioner Chat save to notes
  // =============================================================================
  const handleSaveToNotes = useCallback((text: string) => {
    const currentNotes = gameState.currentHole.notes || '';
    const newNotes = currentNotes ? `${currentNotes}\n\n[Commissioner]: ${text}` : `[Commissioner]: ${text}`;
    setNotes(newNotes);
  }, [gameState.currentHole.notes, setNotes]);

  // =============================================================================
  // Validation State
  // =============================================================================
  const validation = useMemo(() => validateCurrentHole(), [validateCurrentHole]);

  // =============================================================================
  // Transform hole history for Scorecard component
  // =============================================================================
  const scorecardHoleHistory = useMemo(() => {
    return gameState.holeHistory.map(h => ({
      hole: h.hole,
      par: h.par,
      points_delta: h.pointsDelta,
      gross_scores: h.grossScores,
      betting_narrative: h.notes || '',
      wager: h.wager,
    }));
  }, [gameState.holeHistory]);

  // =============================================================================
  // Render
  // =============================================================================
  const styles = {
    container: {
      position: 'relative' as const,
      paddingBottom: '100px', // Space for HoleNavigation
    },
    stickyScorecard: {
      position: 'sticky' as const,
      top: 0,
      zIndex: 100,
      backgroundColor: theme.colors.background,
      borderBottom: `1px solid ${theme.colors.border}`,
      marginBottom: theme.spacing[3],
    },
    presetsSection: {
      marginBottom: theme.spacing[4],
    },
    commissionerButton: {
      position: 'fixed' as const,
      bottom: '120px',
      right: theme.spacing[4],
      width: '48px',
      height: '48px',
      borderRadius: '50%',
      backgroundColor: theme.colors.gold,
      border: 'none',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: '24px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
      zIndex: 150,
    },
  };

  if (isGameComplete) {
    return (
      <div style={{
        padding: theme.spacing[6],
        textAlign: 'center' as const,
      }}>
        <h2 style={{
          fontSize: theme.typography['2xl'],
          fontWeight: theme.typography.bold,
          color: theme.colors.gold,
          marginBottom: theme.spacing[4],
        }}>
          🏆 Round Complete!
        </h2>
        <p style={{
          color: theme.colors.textSecondary,
          marginBottom: theme.spacing[4],
        }}>
          Final standings have been recorded.
        </p>
        <button
          onClick={handleCompleteGame}
          style={{
            padding: `${theme.spacing[3]} ${theme.spacing[6]}`,
            backgroundColor: theme.colors.primary,
            color: '#ffffff',
            border: 'none',
            borderRadius: theme.borderRadius.md,
            fontSize: theme.typography.base,
            fontWeight: theme.typography.semibold,
            cursor: 'pointer',
          }}
        >
          View Results
        </button>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Badge Notification Manager */}
      {enableBadgeNotifications && <BadgeNotificationManager />}

      {/* Sticky Scorecard - collapsed by default */}
      <div style={styles.stickyScorecard}>
        <Scorecard
          players={gameState.players.map(p => ({
            id: p.id,
            name: p.name,
            handicap: p.handicap,
            points: p.standings.quarters,
          }))}
          holeHistory={scorecardHoleHistory}
          currentHole={gameState.currentHole.hole}
          onEditHole={handleScorecardEdit}
          onPlayerNameChange={editPlayerName}
          captainId={gameState.currentHole.captain}
          courseHoles={course.holes.map(h => ({
            hole: h.holeNumber,
            par: h.par,
            handicap: h.handicapRank || h.handicap,
            yards: h.yards,
          }))}
          strokeAllocation={effectiveStrokeAllocation}
        />
      </div>

      {/* Aardvark Panel (if enabled and applicable) */}
      {enableAardvark && aardvark.mode !== 'none' && (
        <AardvarkPanel
          aardvark={aardvark}
          players={gameState.players}
          par={gameState.currentHole.par}
          onSetInvisibleScore={setInvisibleAardvarkScore}
          isCollapsed={!showAardvarkPanel}
          onToggleCollapse={() => setShowAardvarkPanel(!showAardvarkPanel)}
        />
      )}

      {/* Quarters Presets */}
      {showQuartersPresets && (
        <div style={styles.presetsSection}>
          <QuartersPresets
            teamMode={gameState.currentHole.teamMode}
            wager={wager?.wager || gameState.currentHole.wager}
            onApplyPreset={applyQuartersPreset}
            disabled={!validation.isValid && validation.errors.some(e => e.includes('team'))}
          />
        </div>
      )}

      {/* Main Scorekeeper UI */}
      <LiveScorekeeper
        game={gameState.game}
        players={gameState.players}
        course={course}
        holeHistory={gameState.holeHistory}
        currentHole={{
          ...gameState.currentHole,
          wager: wager?.wager || gameState.currentHole.wager,
        }}
        bettingActions={DEFAULT_BETTING_ACTIONS}
        onToggleTeam1={toggleTeam1}
        onSelectCaptain={selectCaptain}
        onSetTeamMode={setTeamMode}
        onSetScore={setScore}
        onSetQuarters={setQuarters}
        onInvokeBet={handleInvokeBet}
        onSubmitHole={handleSubmitHole}
        onEditHole={handleNavigateHole}
        onCancelEdit={() => goToHole(gameState.holeHistory.length + 1)}
        onSetNotes={setNotes}
        onEditPlayerName={editPlayerName}
        onCompleteGame={handleCompleteGame}
      />

      {/* Hole Navigation */}
      <HoleNavigation
        currentHole={gameState.currentHole.hole}
        totalHoles={18}
        completedHoles={gameState.holeHistory.length}
        canUndo={gameState.holeHistory.length > 0}
        onPreviousHole={handlePreviousHole}
        onNextHole={handleNextHole}
        onUndoLastHole={undoLastHole}
        onGoToHole={handleNavigateHole}
      />

      {/* Commissioner Chat Toggle Button */}
      {enableCommissionerChat && (
        <button
          style={styles.commissionerButton}
          onClick={() => setShowCommissionerChat(!showCommissionerChat)}
          title="Ask the Commissioner"
        >
          🏆
        </button>
      )}

      {/* Commissioner Chat (floating mode) */}
      {enableCommissionerChat && showCommissionerChat && (
        <CommissionerChat
          {...{
            gameState: {
              current_hole: gameState.currentHole.hole,
              players: gameState.players,
            },
            inline: false,
            onSaveToNotes: handleSaveToNotes,
            startOpen: true,
          } as Record<string, unknown>}
        />
      )}

      {/* Submission Loading Overlay */}
      {isSubmitting && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 300,
        }}>
          <div style={{
            backgroundColor: theme.colors.paper,
            padding: theme.spacing[4],
            borderRadius: theme.borderRadius.md,
            textAlign: 'center',
          }}>
            Saving...
          </div>
        </div>
      )}

      {/* Submission Error Display */}
      {submissionError && (
        <div style={{
          position: 'fixed',
          bottom: '120px',
          left: theme.spacing[4],
          right: theme.spacing[4],
          padding: theme.spacing[3],
          backgroundColor: theme.colors.error,
          color: '#ffffff',
          borderRadius: theme.borderRadius.base,
          textAlign: 'center',
          zIndex: 200,
        }}>
          {submissionError}
        </div>
      )}
    </div>
  );
};

export default LiveScorekeeperContainer;
