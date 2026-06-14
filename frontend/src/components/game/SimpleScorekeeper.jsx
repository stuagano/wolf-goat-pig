// frontend/src/components/game/SimpleScorekeeper.jsx
// Updated: Offline-first sync for unreliable golf course connectivity
// Refactored: Using custom hooks for state management (incremental migration)
import React, {
  useState,
  useEffect,
  useMemo,
  useReducer,
  useCallback,
  useRef,
} from "react";
import PropTypes from "prop-types";
import { useTheme } from "../../theme/Provider";
import { Input } from "../ui";
import GameCompletionView from "./GameCompletionView";
import Scorecard from "./Scorecard";
import ShotAnalysisWidget from "./ShotAnalysisWidget";
import BettingOddsPanel from "../betting/BettingOddsPanel";
import CommissionerChat from "./CommissionerChat";
import EditPlayerNameModal from "./EditPlayerNameModal";
import EditHoleModal from "./EditHoleModal";
import { SyncStatusBanner } from "../ui/SyncStatusIndicator";
import { useHoleSync, useUIState, useBettingState } from "../../hooks";
import { gameReducer, createInitialState } from "./gameReducer";
import syncManager from "../../services/syncManager";
import { fetchJson } from "../../services/fetchJson";
// NOTE: only getStrokesForHole is shared with utils/strokeAllocation — its
// calculateStrokeAllocation applies USGA course-handicap conversion, which
// this component's raw-handicap fallback intentionally does not.
import { getStrokesForHole } from "../../utils/strokeAllocation";
import {
  HoleHeader,
  TeamSelector,
  QuartersPanel,
  HoleNavigation,
  StuartModePanel,
  OptionalEntryPanels,
  AnalysisPanels,
  UsageStatsPanel,
  SpecialActionsPanel,
  ScorekeeperBanners,
  ErrorBanner,
  ScorecardSection,
  StuartModeToggle,
  HolePhaseStrip,
  DoubleOfferControl,
} from "./scorekeeper";
import "../../styles/mobile-touch.css";
import { apiConfig } from "../../config/api.config";
import { aiPartnerResponse } from "../../utils/stuartModeAiDecisions";
import useStuartMode from "../../hooks/useStuartMode";
import useGameActions from "./useGameActions";
import useAchievements from "../../hooks/useAchievements";
import useScorekeeperSync from "../../hooks/useScorekeeperSync";
import useHoleSubmission from "../../hooks/useHoleSubmission";

const API_URL = apiConfig.baseUrl;

/**
 * Helper component to display player name with authentication indicator
 */
const PlayerName = ({ name, isAuthenticated }) => (
  <>
    {name}
    {isAuthenticated && (
      <span style={{ marginLeft: "4px", fontSize: "12px" }}>🔒</span>
    )}
  </>
);

PlayerName.propTypes = {
  name: PropTypes.string.isRequired,
  isAuthenticated: PropTypes.bool,
};

/**
 * Create an object keyed by player ID from a list of players
 * @param {Array} players - Array of player objects with id property
 * @param {Function} getValue - Function that takes a player and returns the value
 * @returns {Object} Object with player IDs as keys
 */
const createPlayerMap = (players, getValue) =>
  Object.fromEntries(players.map((p) => [p.id, getValue(p)]));

/**
 * Simplified scorekeeper component - no game engine, just direct data entry
 * Client-side betting UI, single API call to complete each hole
 */
const SimpleScorekeeper = ({
  gameId,
  players,
  baseWager = 1,
  initialHoleHistory = [],
  initialCurrentHole = 1,
  courseName = "Wing Point Golf & Country Club",
  initialStrokeAllocation = null,
}) => {
  const theme = useTheme();

  // UI state management (refactored to custom hook)
  const ui = useUIState();

  // ============================================================
  // GAME STATE - Using useReducer for consolidated state management
  // ============================================================

  // Try to restore from local storage first (survives page refresh)
  const restoredState = useMemo(() => {
    const localState = syncManager.loadLocalGameState(gameId);
    if (
      localState?.holeHistory &&
      localState.holeHistory.length > initialHoleHistory.length
    ) {
      return localState;
    }
    return null;
  }, [gameId, initialHoleHistory.length]);

  // Initialize game state reducer
  const [gameState, dispatch] = useReducer(
    gameReducer,
    {
      baseWager,
      initialCurrentHole,
      initialHoleHistory,
      players,
      restoredState,
    },
    createInitialState,
  );

  // Destructure game state for convenience (maintains existing variable names)
  const {
    hole,
    teams,
    betting: bettingState,
    rotation,
    aardvark,
    history,
  } = gameState;

  // Hole state
  const currentHole = hole.currentHole;
  const scores = hole.scores;
  const quarters = hole.quarters;
  const holeNotes = hole.notes;
  const winner = hole.winner;

  // Team state
  const teamMode = teams.mode;
  const team1 = teams.team1;
  // eslint-disable-next-line no-unused-vars -- team2 computed from team1, kept for clarity
  const team2 = teams.team2;
  const captain = teams.captain;
  const opponents = teams.opponents;

  // Betting state (from reducer)
  const currentWager = bettingState.currentWager;
  // eslint-disable-next-line no-unused-vars -- used in resetHole, exposed for future use
  const nextHoleWager = bettingState.nextHoleWager;
  const floatInvokedBy = bettingState.floatInvokedBy;
  const optionInvokedBy = bettingState.optionInvokedBy;
  // eslint-disable-next-line no-unused-vars -- betting state, exposed for future UI
  const optionActive = bettingState.optionActive;
  // eslint-disable-next-line no-unused-vars -- betting state, exposed for future UI
  const optionTurnedOff = bettingState.optionTurnedOff;
  const duncanInvoked = bettingState.duncanInvoked;
  // eslint-disable-next-line no-unused-vars -- betting state, exposed for future UI
  const carryOver = bettingState.carryOver;
  // eslint-disable-next-line no-unused-vars -- betting state, exposed for future UI
  const vinniesVariation = bettingState.vinniesVariation;
  // eslint-disable-next-line no-unused-vars -- betting state, exposed for future UI
  const joesSpecialWager = bettingState.joesSpecialWager;

  // Rotation state
  const rotationOrder = rotation.order;
  const captainIndex = rotation.captainIndex;
  const isHoepfinger = rotation.isHoepfinger;
  // eslint-disable-next-line no-unused-vars -- rotation state, exposed for Hoepfinger rule UI
  const goatId = rotation.goatId;
  const phase = rotation.phase;

  // Aardvark state
  const aardvarkRequestedTeam = aardvark.requestedTeam;
  const aardvarkTossed = aardvark.tossed;
  const aardvarkSolo = aardvark.solo;
  const invisibleAardvarkTossed = aardvark.invisibleTossed;

  // History state
  const holeHistory = history.holes;
  const playerStandings = history.playerStandings;

  // ============================================================
  // ACTION DISPATCHERS - moved to useGameActions (stable identities)
  // ============================================================
  const {
    setCurrentHole,
    setScores,
    setQuarters,
    setHoleNotes,
    setWinner,
    setTeamMode,
    setTeam1,
    setTeam2,
    setCaptain,
    setOpponents,
    setCurrentWager,
    setNextHoleWager,
    setFloatInvokedBy,
    setOptionInvokedBy,
    setOptionActive,
    setOptionTurnedOff,
    setDuncanInvoked,
    setCarryOver,
    setVinniesVariation,
    setJoesSpecialWager,
    setRotationOrder,
    setCaptainIndex,
    setIsHoepfinger,
    setGoatId,
    setPhase,
    setAardvarkRequestedTeam,
    setAardvarkTossed,
    setAardvarkSolo,
    setInvisibleAardvarkTossed,
    setHoleHistory,
    setPlayerStandings,
  } = useGameActions(dispatch);

  // ============================================================
  // BETTING STATE HOOK - Interactive betting (offers, events)
  // ============================================================

  const betting = useBettingState({
    currentHole,
    currentWager,
    setCurrentWager,
    players,
  });

  // Destructure commonly used betting state
  // Only destructure what's currently used - full API available via `betting` object
  const {
    currentHoleBettingEvents,
    setCurrentHoleBettingEvents,
    setPendingOffer,
    addBettingEvent,
    logBettingAction,
    getPlayerName,
    pendingOffer,
    createOffer,
    respondToOffer,
  } = betting;
  // Additional betting features available: betting.bettingHistory, betting.createOffer,
  // betting.respondToOffer, betting.showBettingHistory, betting.historyTab, betting.pendingOffer

  // UI state (migrated to useUIState hook)
  // Destructure commonly used UI state for convenience
  const {
    submitting,
    setSubmitting,
    error,
    setError,
    showTeamSelection,
    setShowTeamSelection,
    showGolfScores,
    setShowGolfScores,
    showCommissioner,
    setShowCommissioner,
    showNotes,
    setShowNotes,
    showSpecialActions,
    setShowSpecialActions,
    showUsageStats,
    setShowUsageStats,
    // eslint-disable-next-line no-unused-vars -- UI state, exposed for advanced betting accordion
    showAdvancedBetting,
    showShotAnalysis,
    setShowShotAnalysis,
    showBettingOdds,
    setShowBettingOdds,
    editingHole,
    setEditingHole,
    editingPlayerName,
    editPlayerNameValue,
    setEditPlayerNameValue,
    isEditingCompleteGame,
    setIsEditingCompleteGame,
    isGameMarkedComplete,
    setIsGameMarkedComplete,
    startEditingPlayerName,
    cancelEditingPlayerName: handleCancelPlayerNameEdit,
    stuartMode,
    coachMode,
    assistMode,
    setAssistMode,
    toggleStuartMode,
  } = ui;

  // Offline-first sync hook
  const {
    syncHole,
  } = useHoleSync(gameId);
  const [localPlayers, setLocalPlayers] = useState(players); // Local copy of players for immediate UI updates
  const [courseData, setCourseData] = useState(null); // Course data with hole information
  const [editingOrder, setEditingOrder] = useState(false); // Track if user is editing hitting order
  const [expandedPlayers, setExpandedPlayers] = useState({ 0: true }); // Track which player cards are expanded (first player by default)
  const [editModalHole, setEditModalHole] = useState(null); // Hole data for edit modal (null = closed)

  // Betting state (bettingHistory, pendingOffer, currentHoleBettingEvents) migrated to useBettingState hook

  // Derive current hole par from course data (pars are constants and don't change)
  // No defaults - only use actual course data
  const holePar = courseData?.holes?.find(
    (h) => h.hole_number === currentHole,
  )?.par;

  // Track course data loading state

  // Auto-collapse team selection when teams are set
  // Team selection stays visible so players can see teams during the hole
  // (Auto-collapse removed per user request)

  // Use stroke allocation from backend if provided (preferred - calculated with Creecher Feature rules)
  // Falls back to local calculation only if backend data is not available
  // NOTE: declared before the Stuart Mode effects below, which list it in
  // their dependency arrays — referencing it earlier is a TDZ crash.
  const strokeAllocation = useMemo(() => {
    // If we have stroke allocation from the backend, use it (it's more accurate)
    if (
      initialStrokeAllocation &&
      Object.keys(initialStrokeAllocation).length > 0
    ) {
      return initialStrokeAllocation;
    }

    // Fallback: calculate locally if backend didn't provide stroke allocation
    if (!courseData?.holes) return {};

    const allocation = {};

    // Calculate net handicaps relative to lowest handicap player
    const playerHandicaps = createPlayerMap(
      localPlayers,
      (p) => p.handicap || 0,
    );

    // Safe array bounds: ensure we have values before calling Math.min
    const handicapValues = Object.values(playerHandicaps);
    const lowestHandicap =
      handicapValues.length > 0 ? Math.min(...handicapValues) : 0;

    const netHandicaps = {};
    Object.entries(playerHandicaps).forEach(([playerId, handicap]) => {
      netHandicaps[playerId] = Math.max(0, handicap - lowestHandicap);
    });

    // getStrokesForHole imported from utils/strokeAllocation (Creecher Feature).
    localPlayers.forEach((player) => {
      allocation[player.id] = {};
      const netHandicap = netHandicaps[player.id];

      for (let holeNum = 1; holeNum <= 18; holeNum++) {
        const holeData = courseData.holes.find(
          (h) => h.hole_number === holeNum,
        );
        if (holeData?.handicap) {
          allocation[player.id][holeNum] = getStrokesForHole(
            netHandicap,
            holeData.handicap,
          );
        }
      }
    });

    return allocation;
  }, [courseData, localPlayers, initialStrokeAllocation]);

  // Stuart Mode orchestration (toggle listeners, AI decisions, move log).
  // NOTE: must stay before the course-data/rotation effects below — effect
  // order is preserved from the pre-extraction component.
  const { aiMoves, setAiMoves, holePhase, setHolePhase, stuartTeamInfo } =
    useStuartMode({
      stuartMode,
      toggleStuartMode,
      gameId,
      players,
      courseData,
      currentHole,
      scores,
      setScores,
      rotationOrder,
      captainIndex,
      teamMode,
      team1,
      captain,
      setTeamMode,
      setCaptain,
      setTeam1,
      strokeAllocation,
      playerStandings,
      currentWager,
      pendingOffer,
      respondToOffer,
      createOffer,
    });

  // Data-sync effects: course fetch, local persistence, standings init,
  // rotation/wager fetch. NOTE: must stay after useStuartMode (effect order).
  const { courseDataLoading, courseDataError, rotationError } =
    useScorekeeperSync({
      gameId,
      courseName,
      baseWager,
      players,
      holeHistory,
      currentHole,
      playerStandings,
      setCourseData,
      setPlayerStandings,
      setIsHoepfinger,
      setGoatId,
      setPhase,
      setRotationOrder,
      setCaptainIndex,
      setJoesSpecialWager,
      setNextHoleWager,
      setCurrentWager,
      setCarryOver,
      setVinniesVariation,
      setOptionActive,
    });

  // Post-hole achievement checking (badge notifications + failure banner)
  const { checkAchievements, achievementCheckFailed, setAchievementCheckFailed } =
    useAchievements(players);

  // Hole submission/edit lifecycle (resetHole, submit, edit-save) — the ctx
  // object IS the closure surface of the original inline handlers.
  const {
    resetHole,
    getEffectiveQuarters,
    handleSubmitHole,
    handleEditModalSave,
    handleEditHoleFromScorecard,
  } = useHoleSubmission({
    gameId,
    baseWager,
    players,
    localPlayers,
    quarters,
    scores,
    teamMode,
    team1,
    team2,
    captain,
    opponents,
    currentHole,
    currentWager,
    phase,
    rotationOrder,
    captainIndex,
    holeNotes,
    winner,
    editingHole,
    holeHistory,
    playerStandings,
    syncHole,
    logBettingAction,
    checkAchievements,
    setQuarters,
    setScores,
    setError,
    setSubmitting,
    setCurrentHole,
    setHoleHistory,
    setPlayerStandings,
    setHoleNotes,
    setWinner,
    setEditingHole,
    setLocalPlayers,
    setCurrentWager,
    setTeam1,
    setTeam2,
    setCaptain,
    setOpponents,
    setFloatInvokedBy,
    setOptionInvokedBy,
    setJoesSpecialWager,
    setOptionTurnedOff,
    setDuncanInvoked,
    setAardvarkRequestedTeam,
    setAardvarkTossed,
    setAardvarkSolo,
    setInvisibleAardvarkTossed,
    setPendingOffer,
    setCurrentHoleBettingEvents,
    setRotationOrder,
    setAchievementCheckFailed,
  });

  // Handle team selection for partners mode
  // Toggle players in/out of Team 1. Team 2 is automatically all other players.
  const togglePlayerTeam = (playerId) => {
    if (team1.includes(playerId)) {
      // Remove from team1 (they'll go to team2 automatically)
      setTeam1(team1.filter((id) => id !== playerId));
      return;
    }

    // Stuart Mode: when adding an AI player as partner, run their accept
    // /decline heuristic. Decline = don't add + log; accept = add + log.
    if (stuartMode) {
      const target = players.find((p) => p.id === playerId);
      if (target && !target.is_authenticated) {
        const result = aiPartnerResponse({
          aiPlayer: target,
          currentHole,
          strokeAllocation,
          playerStandings,
        });
        setAiMoves((prev) => [
          ...prev,
          {
            type: "partner",
            text:
              result.decision === "accept"
                ? `🤖 ${target.name} accepts partnership — ${result.reason}`
                : `🤖 ${target.name} declines partnership — ${result.reason}`,
            timestamp: Date.now(),
          },
        ]);
        if (result.decision === "decline") return; // don't add
      }
    }

    // Add to team1
    setTeam1([...team1, playerId]);
  };

  // Handle captain selection for solo mode
  const toggleCaptain = (playerId) => {
    if (captain === playerId) {
      setCaptain(null);
    } else {
      setCaptain(playerId);
      // Set all other players as opponents
      setOpponents(players.filter((p) => p.id !== playerId).map((p) => p.id));
    }
  };

  // Betting functions (logBettingAction, getPlayerName, addBettingEvent, createOffer, respondToOffer)
  // are now provided by useBettingState hook

  // Announce an action (Duncan, Option Off) - no accept needed
  const announceAction = (actionType, announcedBy) => {
    addBettingEvent({
      eventType: `${actionType.toUpperCase()}_ANNOUNCED`,
      announced_by: announcedBy,
      actor: announcedBy,
    });
  };

  // Handle score input
  const handleScoreChange = (playerId, value) => {
    setScores({
      ...scores,
      [playerId]: parseInt(value, 10) || 0,
    });
  };

  // Note: calculateQuartersForHole removed - quarters are now entered manually
  // Note: strokeAllocation memo moved above the Stuart Mode effects (TDZ fix)

  // Calculate net scores and auto-detect winner
  const calculateNetScoresAndWinner = useMemo(() => {
    // Need all scores entered and teams formed
    const allScoresEntered = players.every(
      (p) => scores[p.id] !== undefined && scores[p.id] !== null,
    );
    const teamsFormed =
      teamMode === "partners"
        ? team1.length > 0 && team1.length < players.length
        : captain !== null;

    if (!allScoresEntered || !teamsFormed) {
      return {
        netScores: {},
        suggestedWinner: null,
        team1Net: null,
        team2Net: null,
      };
    }

    // Calculate net scores (gross - strokes received)
    const netScores = createPlayerMap(players, (p) => {
      const gross = scores[p.id] || 0;
      const strokesReceived = strokeAllocation?.[p.id]?.[currentHole] || 0;
      return gross - strokesReceived;
    });

    // Calculate team totals based on best ball (lowest net score on team)
    let team1Net, team2Net;

    if (teamMode === "partners") {
      const team2Ids = players
        .filter((p) => !team1.includes(p.id))
        .map((p) => p.id);
      // Safe array bounds: filter undefined values and provide fallback
      const team1Scores = team1
        .map((id) => netScores[id])
        .filter((s) => s !== undefined);
      const team2Scores = team2Ids
        .map((id) => netScores[id])
        .filter((s) => s !== undefined);
      team1Net = team1Scores.length > 0 ? Math.min(...team1Scores) : 0;
      team2Net = team2Scores.length > 0 ? Math.min(...team2Scores) : 0;
    } else {
      // Solo mode: captain vs opponents
      team1Net = netScores[captain] ?? 0; // Captain's net score with fallback
      // Safe array bounds for opponents
      const opponentScores = opponents
        .map((id) => netScores[id])
        .filter((s) => s !== undefined);
      team2Net = opponentScores.length > 0 ? Math.min(...opponentScores) : 0;
    }

    // Determine suggested winner
    let suggestedWinner = null;
    if (team1Net < team2Net) {
      suggestedWinner = teamMode === "partners" ? "team1" : "captain";
    } else if (team2Net < team1Net) {
      suggestedWinner = teamMode === "partners" ? "team2" : "opponents";
    } else {
      suggestedWinner = "push"; // Tied = push
    }

    return { netScores, suggestedWinner, team1Net, team2Net };
  }, [
    scores,
    players,
    team1,
    captain,
    opponents,
    teamMode,
    strokeAllocation,
    currentHole,
  ]);

  // Auto-set winner when scores suggest a clear result
  useEffect(() => {
    const { suggestedWinner } = calculateNetScoresAndWinner;
    if (suggestedWinner && !winner) {
      // Auto-set the winner based on net scores
      setWinner(suggestedWinner);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- setWinner is stable (useCallback)
  }, [calculateNetScoresAndWinner, winner]);


  // Handle player name editing - uses useUIState hook
  // eslint-disable-next-line no-unused-vars
  const handlePlayerNameClick = (playerId, currentName) => {
    startEditingPlayerName(playerId, currentName);
  };

  // Handle reordering hitting order
  const movePlayerInOrder = async (fromIndex, direction) => {
    const toIndex = fromIndex + direction;
    if (toIndex < 0 || toIndex >= rotationOrder.length) return;

    const newOrder = [...rotationOrder];
    [newOrder[fromIndex], newOrder[toIndex]] = [
      newOrder[toIndex],
      newOrder[fromIndex],
    ];

    // Update local state immediately for responsive UI
    setRotationOrder(newOrder);

    // Persist to backend
    try {
      await fetchJson(`${API_URL}/games/${gameId}/tee-order`, {
        method: "PATCH",
        body: JSON.stringify({ player_order: newOrder }),
      });
    } catch (error) {
      console.error("Error updating hitting order:", error);
      // Revert on error
      setRotationOrder(rotationOrder);
    }
  };

  const handleSavePlayerName = async () => {
    if (!editingPlayerName || !editPlayerNameValue.trim()) {
      return;
    }

    try {
      await fetchJson(
        `${API_URL}/games/${gameId}/players/${editingPlayerName}/name`,
        {
          method: "PATCH",
          body: JSON.stringify({ name: editPlayerNameValue.trim() }),
        },
      );

      // Update local players state immediately for better UX
      const updatedPlayers = localPlayers.map((p) =>
        p.id === editingPlayerName
          ? { ...p, name: editPlayerNameValue.trim() }
          : p,
      );
      setLocalPlayers(updatedPlayers);

      // Also update player standings
      if (playerStandings[editingPlayerName]) {
        setPlayerStandings({
          ...playerStandings,
          [editingPlayerName]: {
            ...playerStandings[editingPlayerName],
            name: editPlayerNameValue.trim(),
          },
        });
      }

      // Close the edit modal
      handleCancelPlayerNameEdit();
    } catch (err) {
      console.error("Failed to update player name:", err);
      alert("Failed to update player name. Please try again.");
    }
  };

  // handleCancelPlayerNameEdit is now provided by useUIState hook

  // Memoize courseHoles transformation to prevent Scorecard re-renders
  const scorecardCourseHoles = useMemo(() => {
    if (!courseData?.holes) return [];
    return courseData.holes.map((h) => ({
      hole: h.hole_number,
      par: h.par,
      handicap: h.handicap,
      yards: h.yards,
    }));
  }, [courseData?.holes]);

  // Direct hole jump - open edit modal for completed holes
  const jumpToHole = (holeNumber) => {
    const holeData = holeHistory.find((h) => h.hole === holeNumber);
    if (holeData) {
      setEditModalHole(holeData);
    } else {
      setCurrentHole(holeNumber);
      resetHole();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  // Check if game is complete (all 18 holes played)
  const isGameComplete = currentHole > 18 && holeHistory.length === 18;

  // Handler to mark game as complete in the database
  const handleMarkComplete = async () => {
    if (!gameId) {
      console.error("No game ID available");
      return;
    }

    try {
      const result = await fetchJson(`${API_URL}/games/${gameId}/complete`, {
        method: "POST",
      });
      setIsGameMarkedComplete(true);
    } catch (error) {
      console.error("Error marking game complete:", error);
      alert(`Failed to save game: ${error.message}`);
    }
  };

  // Show completion view if game is complete and not in edit mode
  if (isGameComplete && !isEditingCompleteGame) {
    return (
      <GameCompletionView
        players={players}
        playerStandings={playerStandings}
        holeHistory={holeHistory}
        onNewGame={() => {
          // Reset to start a new game
          window.location.reload();
        }}
        onEditScores={() => {
          // Enter edit mode - set to hole 19 so ALL holes appear as "completed" and editable
          setIsEditingCompleteGame(true);
          setCurrentHole(19); // All holes 1-18 will show as completed (editable)
        }}
        onMarkComplete={handleMarkComplete}
        isCompleted={isGameMarkedComplete}
        courseHoles={courseData?.holes || []}
        strokeAllocation={strokeAllocation}
      />
    );
  }

  return (
    <div
      data-testid="scorekeeper-container"
      className="thumb-zone-container"
      style={{ padding: "20px", maxWidth: "800px", margin: "0 auto" }}
    >
      <StuartModeToggle
        assistMode={assistMode}
        setAssistMode={setAssistMode}
        theme={theme}
      />

      {/* Sync Status Banner - Shows when offline or pending uploads */}
      <SyncStatusBanner />

      <ScorekeeperBanners
        courseDataLoading={courseDataLoading}
        courseDataError={courseDataError}
        rotationError={rotationError}
        achievementCheckFailed={achievementCheckFailed}
        setAchievementCheckFailed={setAchievementCheckFailed}
        isEditingCompleteGame={isEditingCompleteGame}
        setIsEditingCompleteGame={setIsEditingCompleteGame}
        editingHole={editingHole}
        setCurrentHole={setCurrentHole}
        resetHole={resetHole}
        holeHistory={holeHistory}
      />

      <ScorecardSection
        theme={theme}
        players={players}
        localPlayers={localPlayers}
        holeHistory={holeHistory}
        setHoleHistory={setHoleHistory}
        setPlayerStandings={setPlayerStandings}
        currentHole={currentHole}
        setCurrentHole={setCurrentHole}
        editingHole={editingHole}
        scorecardCourseHoles={scorecardCourseHoles}
        strokeAllocation={strokeAllocation}
        isEditingCompleteGame={isEditingCompleteGame}
        handleEditHoleFromScorecard={handleEditHoleFromScorecard}
        jumpToHole={jumpToHole}
        resetHole={resetHole}
      />
      {/* Enhanced Hole Title Section - Combines hole info, hitting order, and strokes */}
      <HoleHeader
        currentHole={currentHole}
        courseData={courseData}
        players={players}
        rotationOrder={rotationOrder}
        captainIndex={captainIndex}
        currentWager={currentWager}
        phase={phase}
        strokeAllocation={strokeAllocation}
        isHoepfinger={isHoepfinger}
        theme={theme}
        holeHistory={holeHistory}
        holePar={holePar}
        editingHole={editingHole}
        editingOrder={editingOrder}
        setEditingOrder={setEditingOrder}
        jumpToHole={jumpToHole}
        movePlayerInOrder={movePlayerInOrder}
      />

      <HolePhaseStrip
        stuartMode={stuartMode}
        holePhase={holePhase}
        setHolePhase={setHolePhase}
        theme={theme}
      />

      <SpecialActionsPanel
        theme={theme}
        players={players}
        playerStandings={playerStandings}
        floatInvokedBy={floatInvokedBy}
        setFloatInvokedBy={setFloatInvokedBy}
        optionInvokedBy={optionInvokedBy}
        setOptionInvokedBy={setOptionInvokedBy}
        showSpecialActions={showSpecialActions}
        setShowSpecialActions={setShowSpecialActions}
      />

      <UsageStatsPanel
        theme={theme}
        players={players}
        playerStandings={playerStandings}
        currentHole={currentHole}
        holeHistory={holeHistory}
        showUsageStats={showUsageStats}
        setShowUsageStats={setShowUsageStats}
      />

      <AnalysisPanels
        theme={theme}
        players={players}
        scores={scores}
        captain={captain}
        team1={team1}
        teamMode={teamMode}
        currentWager={currentWager}
        currentHole={currentHole}
        holePar={holePar}
        playerStandings={playerStandings}
        courseData={courseData}
        showBettingOdds={showBettingOdds}
        setShowBettingOdds={setShowBettingOdds}
        showShotAnalysis={showShotAnalysis}
        setShowShotAnalysis={setShowShotAnalysis}
      />

      {/* Team Mode Selection + Team Selection */}
      <TeamSelector
        players={players}
        teamMode={teamMode}
        team1={team1}
        captain={captain}
        theme={theme}
        duncanInvoked={duncanInvoked}
        setDuncanInvoked={setDuncanInvoked}
        setTeamMode={setTeamMode}
        togglePlayerTeam={togglePlayerTeam}
        toggleCaptain={toggleCaptain}
        announceAction={announceAction}
        showTeamSelection={showTeamSelection}
        setShowTeamSelection={setShowTeamSelection}
        aardvarkRequestedTeam={aardvarkRequestedTeam}
        setAardvarkRequestedTeam={setAardvarkRequestedTeam}
        aardvarkTossed={aardvarkTossed}
        setAardvarkTossed={setAardvarkTossed}
        aardvarkSolo={aardvarkSolo}
        setAardvarkSolo={setAardvarkSolo}
        invisibleAardvarkTossed={invisibleAardvarkTossed}
        setInvisibleAardvarkTossed={setInvisibleAardvarkTossed}
      />

      <DoubleOfferControl
        stuartMode={stuartMode}
        stuartTeamInfo={stuartTeamInfo}
        pendingOffer={pendingOffer}
        currentWager={currentWager}
        getPlayerName={getPlayerName}
        respondToOffer={respondToOffer}
        createOffer={createOffer}
        setAiMoves={setAiMoves}
        theme={theme}
      />

      {/* Quarters Entry (Primary) - Enhanced Player Cards */}
      <QuartersPanel
        players={players}
        quarters={quarters}
        setQuarters={setQuarters}
        theme={theme}
      />

      <OptionalEntryPanels
        theme={theme}
        players={players}
        scores={scores}
        handleScoreChange={handleScoreChange}
        currentHole={currentHole}
        playerStandings={playerStandings}
        holeNotes={holeNotes}
        setHoleNotes={setHoleNotes}
        showGolfScores={showGolfScores}
        setShowGolfScores={setShowGolfScores}
        showCommissioner={showCommissioner}
        setShowCommissioner={setShowCommissioner}
        showNotes={showNotes}
        setShowNotes={setShowNotes}
      />

      <ErrorBanner error={error} setError={setError} theme={theme} />
      {/* Old submit button removed - now in thumb zone below */}

      {/* Sticky Bottom Thumb Zone - Primary Actions */}
      <HoleNavigation
        currentHole={currentHole}
        editingHole={editingHole}
        submitting={submitting}
        holeHistory={holeHistory}
        jumpToHole={jumpToHole}
        handleSubmitHole={handleSubmitHole}
      />

      {/* Strategy panel shows in both Coach (real round, manual scoring) and Auto
          (full AI). aiMoves is empty in Coach since nothing auto-plays. */}
      {(stuartMode || coachMode) && (
        <StuartModePanel
          players={players}
          currentHole={currentHole}
          strokeAllocation={strokeAllocation}
          playerStandings={playerStandings}
          courseData={courseData}
          currentWager={currentWager}
          theme={theme}
          aiMoves={aiMoves}
        />
      )}

      {/* Old scorecard removed - now showing golf-style scorecard at top */}

      {/* Edit Player Name Modal */}
      {editingPlayerName && (
        <EditPlayerNameModal
          value={editPlayerNameValue}
          onChange={setEditPlayerNameValue}
          onSave={handleSavePlayerName}
          onCancel={handleCancelPlayerNameEdit}
          theme={theme}
        />
      )}

      <EditHoleModal
        isOpen={!!editModalHole}
        onClose={() => setEditModalHole(null)}
        onSave={handleEditModalSave}
        holeData={editModalHole}
        players={localPlayers}
      />
    </div>
  );
};

/**
 * PropTypes for SimpleScorekeeper
 * Specific shapes for better validation and documentation
 */
SimpleScorekeeper.propTypes = {
  /** Unique game identifier */
  gameId: PropTypes.string.isRequired,

  /** Array of player objects */
  players: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      handicap: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      user_id: PropTypes.string,
      tee_order: PropTypes.number,
      is_authenticated: PropTypes.bool,
      ghin_id: PropTypes.string,
    }),
  ).isRequired,

  /** Base wager amount in quarters (default: 1) */
  baseWager: PropTypes.number,

  /** History of completed holes */
  initialHoleHistory: PropTypes.arrayOf(
    PropTypes.shape({
      hole: PropTypes.number.isRequired,
      points_delta: PropTypes.objectOf(PropTypes.number),
      gross_scores: PropTypes.objectOf(PropTypes.number),
      teams: PropTypes.shape({
        type: PropTypes.oneOf(["partners", "solo"]),
        team1: PropTypes.arrayOf(PropTypes.string),
        team2: PropTypes.arrayOf(PropTypes.string),
        captain: PropTypes.string,
        opponents: PropTypes.arrayOf(PropTypes.string),
      }),
      winner: PropTypes.oneOf([
        "team1",
        "team2",
        "captain",
        "opponents",
        "push",
        null,
      ]),
      wager: PropTypes.number,
      phase: PropTypes.string,
      rotation_order: PropTypes.arrayOf(PropTypes.string),
      captain_index: PropTypes.number,
      notes: PropTypes.string,
      float_invoked_by: PropTypes.string,
      option_invoked_by: PropTypes.string,
      duncan_invoked: PropTypes.bool,
      option_turned_off: PropTypes.bool,
      betting_events: PropTypes.arrayOf(
        PropTypes.shape({
          eventId: PropTypes.string,
          eventType: PropTypes.string,
          hole: PropTypes.number,
          actor: PropTypes.string,
          timestamp: PropTypes.string,
          details: PropTypes.object,
        }),
      ),
    }),
  ),

  /** Starting hole number (default: 1) */
  initialCurrentHole: PropTypes.number,

  /** Name of the golf course */
  courseName: PropTypes.string,

  /** Pre-calculated stroke allocation from backend */
  initialStrokeAllocation: PropTypes.objectOf(
    PropTypes.objectOf(PropTypes.number),
  ),
};

export default SimpleScorekeeper;
