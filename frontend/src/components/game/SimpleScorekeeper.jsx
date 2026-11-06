// frontend/src/components/game/SimpleScorekeeper.jsx
// Updated: Offline-first sync for unreliable golf course connectivity
// Refactored: Using custom hooks for state management (incremental migration)
// Split: game state, stroke allocation, handlers, running totals, the optional
// details section and propTypes live in ./scorekeeper/ (hook order preserved).
import React, {
  useState,
  useEffect,
  useMemo,
  useCallback,
  useRef,
} from "react";
import { useTheme } from "../../theme/Provider";
import { Input } from "../ui";
import CompletedRoundView from "./CompletedRoundView";
import Scorecard from "./Scorecard";
import ShotAnalysisWidget from "./ShotAnalysisWidget";
import BettingOddsPanel from "../betting/BettingOddsPanel";
import CommissionerChat from "./CommissionerChat";
import EditPlayerNameModal from "./EditPlayerNameModal";
import EditHoleModal from "./EditHoleModal";
import TeeTossModal from "./TeeTossModal";
import { SyncStatusBanner } from "../ui/SyncStatusIndicator";
import { useHoleSync, useUIState, useBettingState } from "../../hooks";
import { allHolesPlayed } from "../../utils/holeHistory";
import { netScoresAndWinner } from "../../utils/holeRules";
import {
  QuartersPanel,
  HoleNavigation,
  ScorekeeperBanners,
  ErrorBanner,
  DoubleOfferControl,
} from "./scorekeeper";
import useScorekeeperGameState from "./scorekeeper/useScorekeeperGameState";
import useStrokeAllocation from "./scorekeeper/useStrokeAllocation";
import buildScorekeeperHandlers from "./scorekeeper/scorekeeperHandlers";
import OptionalHoleDetails from "./scorekeeper/OptionalHoleDetails";
import simpleScorekeeperPropTypes from "./scorekeeper/simpleScorekeeperPropTypes";
import "../../styles/mobile-touch.css";
import useStuartMode from "../../hooks/useStuartMode";
import useAchievements from "../../hooks/useAchievements";
import useScorekeeperSync from "../../hooks/useScorekeeperSync";
import useHoleSubmission from "../../hooks/useHoleSubmission";

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
  // GAME STATE - useReducer + action dispatchers (useScorekeeperGameState)
  // ============================================================
  const { game, actions } = useScorekeeperGameState({
    gameId,
    players,
    baseWager,
    initialHoleHistory,
    initialCurrentHole,
  });
  const {
    currentHole, scores, quarters, holeNotes, winner,
    teamMode, team1, captain, opponents,
    currentWager, floatInvokedBy, optionInvokedBy, duncanInvoked, carryOver,
    rotationOrder, captainIndex, isHoepfinger, phase,
    aardvarkRequestedTeam, aardvarkTossed, aardvarkSolo, invisibleAardvarkTossed,
    holeHistory, playerStandings,
  } = game;
  const {
    setCurrentHole, setScores, setQuarters, setHoleNotes, setWinner,
    setTeamMode, setTeam1, setCaptain, setOpponents,
    setCurrentWager, setNextHoleWager, setFloatInvokedBy, setOptionInvokedBy,
    setDuncanInvoked, setCarryOver, setRotationOrder, reorderHittingOrder,
    setAardvarkRequestedTeam, setAardvarkTossed, setAardvarkSolo,
    setInvisibleAardvarkTossed, setHoleHistory, setPlayerStandings,
  } = actions;

  // ============================================================
  // BETTING STATE HOOK - Interactive betting (offers, events)
  // ============================================================
  const betting = useBettingState({
    currentHole,
    currentWager,
    setCurrentWager,
    players,
  });
  const {
    setCurrentHoleBettingEvents,
    setPendingOffer,
    addBettingEvent,
    logBettingAction,
    getPlayerName,
    pendingOffer,
    createOffer,
    respondToOffer,
  } = betting;

  // UI state (migrated to useUIState hook)
  const {
    submitting, setSubmitting, error, setError,
    showTeamSelection, setShowTeamSelection,
    showGolfScores, setShowGolfScores,
    showCommissioner, setShowCommissioner,
    showNotes, setShowNotes,
    showSpecialActions, setShowSpecialActions,
    showUsageStats, setShowUsageStats,
    showShotAnalysis, setShowShotAnalysis,
    showBettingOdds, setShowBettingOdds,
    editingHole, setEditingHole,
    editingPlayerName, editPlayerNameValue, setEditPlayerNameValue,
    isEditingCompleteGame, setIsEditingCompleteGame,
    isGameMarkedComplete, setIsGameMarkedComplete,
    cancelEditingPlayerName: handleCancelPlayerNameEdit,
    stuartModeEnabled, stuartMode, coachMode, assistMode, setAssistMode,
    toggleStuartMode,
  } = ui;

  // Offline-first sync hook
  const { syncHole } = useHoleSync(gameId);
  const [localPlayers, setLocalPlayers] = useState(players); // Local copy of players for immediate UI updates
  const [courseData, setCourseData] = useState(null); // Course data with hole information
  const [editingOrder, setEditingOrder] = useState(false); // Track if user is editing hitting order
  const [showTeeToss, setShowTeeToss] = useState(false); // Mid-game full hitting-order redo
  // eslint-disable-next-line no-unused-vars -- player-card expansion state (kept)
  const [expandedPlayers, setExpandedPlayers] = useState({ 0: true }); // Track which player cards are expanded (first player by default)
  const [editModalHole, setEditModalHole] = useState(null); // Hole data for edit modal (null = closed)

  // Derive current hole par from course data (pars are constants and don't change)
  // No defaults - only use actual course data
  const holePar = courseData?.holes?.find(
    (h) => h.hole_number === currentHole,
  )?.par;

  // NOTE: declared before the Stuart Mode effects below, which list it in
  // their dependency arrays — referencing it earlier is a TDZ crash.
  const strokeAllocation = useStrokeAllocation({
    courseData,
    localPlayers,
    initialStrokeAllocation,
  });

  // Stuart Mode orchestration (toggle listeners, AI decisions, move log).
  // NOTE: must stay before the course-data/rotation effects below — effect
  // order is preserved from the pre-extraction component.
  const { aiMoves, setAiMoves, holePhase, setHolePhase, stuartTeamInfo } =
    useStuartMode({
      enabled: stuartModeEnabled,
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
      setNextHoleWager,
      setCurrentWager,
      setCarryOver,
    });

  // Post-hole achievement checking (badge notifications + failure banner)
  const { checkAchievements, achievementCheckFailed, setAchievementCheckFailed } =
    useAchievements(players);

  // Hole submission/edit lifecycle (resetHole, submit, edit-save). The ctx is
  // the flattened game state + dispatchers plus the extras below; the hook
  // destructures only the identifiers it needs.
  const {
    resetHole,
    handleSubmitHole,
    handleEditModalSave,
    handleEditHoleFromScorecard,
  } = useHoleSubmission({
    ...game,
    ...actions,
    gameId,
    baseWager,
    players,
    localPlayers,
    editingHole,
    syncHole,
    logBettingAction,
    checkAchievements,
    setError,
    setSubmitting,
    setEditingHole,
    setLocalPlayers,
    setPendingOffer,
    setCurrentHoleBettingEvents,
    setAchievementCheckFailed,
  });

  // Calculate net scores and auto-detect winner
  const calculateNetScoresAndWinner = useMemo(
    () =>
      netScoresAndWinner({
        players,
        scores,
        teamMode,
        team1,
        captain,
        opponents,
        strokeAllocation,
        holeNumber: currentHole,
      }),
    [
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

  // Event handlers (rebuilt each render, as the original inline closures were)
  const {
    togglePlayerTeam,
    toggleCaptain,
    announceAction,
    handleScoreChange,
    movePlayerInOrder,
    handleTeeTossComplete,
    handleSavePlayerName,
    jumpToHole,
  } = buildScorekeeperHandlers({
    gameId, players, localPlayers, setLocalPlayers,
    team1, setTeam1, captain, setCaptain, setOpponents,
    stuartMode, currentHole, setCurrentHole, strokeAllocation,
    playerStandings, setPlayerStandings, setAiMoves, addBettingEvent,
    scores, setScores, rotationOrder, reorderHittingOrder, setRotationOrder,
    setPendingOffer, setCurrentHoleBettingEvents, setShowTeamSelection,
    setShowTeeToss, setEditingOrder,
    editingPlayerName, editPlayerNameValue, handleCancelPlayerNameEdit,
    holeHistory, setEditModalHole, resetHole,
  });

  // Check if game is complete (all 18 holes played). Gate on the DISTINCT set
  // of holes 1-18 actually played, not holeHistory.length — a duplicate entry
  // makes length reach 18 with a real hole still missing, completing early
  // (and a missing hole could also be masked). Mirrors the backend gate.
  const isGameComplete = currentHole > 18 && allHolesPlayed(holeHistory);

  // Show completion view if game is complete and not in edit mode
  if (isGameComplete && !isEditingCompleteGame) {
    return (
      <CompletedRoundView
        gameId={gameId}
        players={players}
        playerStandings={playerStandings}
        holeHistory={holeHistory}
        courseHoles={courseData?.holes || []}
        strokeAllocation={strokeAllocation}
        isMarkedComplete={isGameMarkedComplete}
        onMarkedComplete={() => setIsGameMarkedComplete(true)}
        onSaveHole={handleEditModalSave}
        onEditScores={() => {
          // Enter edit mode - set to hole 19 so ALL holes appear as "completed" and editable
          setIsEditingCompleteGame(true);
          setCurrentHole(19); // All holes 1-18 will show as completed (editable)
        }}
      />
    );
  }

  return (
    <div
      data-testid="scorekeeper-container"
      className="thumb-zone-container"
      style={{ padding: "20px", maxWidth: "800px", margin: "0 auto" }}
    >
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
        gameId={gameId}
      />

      <h2 data-testid="scoring-hole-heading" style={{ margin: "0 0 16px", color: theme.colors.textPrimary }}>
        {currentHole > 18 ? "Round complete" : `${editingHole ? "Editing hole" : "Hole"} ${currentHole} of 18`}
      </h2>

      <QuartersPanel
        players={players}
        quarters={quarters}
        setQuarters={setQuarters}
        theme={theme}
      />

      <ErrorBanner error={error} setError={setError} theme={theme} />
      <HoleNavigation
        currentHole={currentHole}
        editingHole={editingHole}
        submitting={submitting}
        holeHistory={holeHistory}
        jumpToHole={jumpToHole}
        handleSubmitHole={handleSubmitHole}
      />

      <OptionalHoleDetails
        {...{
          theme, isEditingCompleteGame,
          players, localPlayers, currentHole, setCurrentHole, courseData,
          holePar, holeHistory, setHoleHistory, playerStandings,
          setPlayerStandings, editingHole, strokeAllocation,
          scorecardCourseHoles, handleEditHoleFromScorecard, resetHole,
          jumpToHole,
          rotationOrder, captainIndex, isHoepfinger, phase, editingOrder,
          setEditingOrder, movePlayerInOrder,
          currentWager, carryOver,
          stuartModeEnabled, stuartMode, coachMode, assistMode, setAssistMode,
          holePhase, setHolePhase, aiMoves,
          showUsageStats, setShowUsageStats, showBettingOdds,
          setShowBettingOdds, showShotAnalysis, setShowShotAnalysis,
          scores, handleScoreChange, teamMode, setTeamMode, team1, captain,
          getPlayerName, togglePlayerTeam, toggleCaptain, announceAction,
          duncanInvoked, setDuncanInvoked, floatInvokedBy, setFloatInvokedBy,
          optionInvokedBy, setOptionInvokedBy, showTeamSelection,
          setShowTeamSelection, showSpecialActions, setShowSpecialActions,
          aardvarkRequestedTeam, setAardvarkRequestedTeam, aardvarkTossed,
          setAardvarkTossed, aardvarkSolo, setAardvarkSolo,
          invisibleAardvarkTossed, setInvisibleAardvarkTossed,
          holeNotes, setHoleNotes, showGolfScores, setShowGolfScores,
          showCommissioner, setShowCommissioner, showNotes, setShowNotes,
        }}
        onRedoOrder={() => setShowTeeToss(true)}
      />

      {/* Pending offers and dialogs must remain visible outside collapsed details. */}
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

      {showTeeToss && (
        <TeeTossModal
          players={localPlayers}
          onClose={() => setShowTeeToss(false)}
          onOrderComplete={handleTeeTossComplete}
        />
      )}

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

SimpleScorekeeper.propTypes = simpleScorekeeperPropTypes;

export default SimpleScorekeeper;
