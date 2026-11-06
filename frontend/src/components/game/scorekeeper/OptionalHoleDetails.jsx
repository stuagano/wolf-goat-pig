// frontend/src/components/game/scorekeeper/OptionalHoleDetails.jsx
// Collapsible "Optional hole details" section of SimpleScorekeeper: hole
// header, scorecard, running totals, Stuart Mode controls, analysis, teams &
// bets, optional entry and strategy panels. JSX moved verbatim.

import React from "react";
import PropTypes from "prop-types";
import HoleHeader from "./HoleHeader";
import ScorecardSection from "./ScorecardSection";
import RunningTotals from "./RunningTotals";
import { StuartModeToggle, HolePhaseStrip } from "./StuartModeControls";
import UsageStatsPanel from "./UsageStatsPanel";
import AnalysisPanels from "./AnalysisPanels";
import TeamSelector from "./TeamSelector";
import SpecialActionsPanel from "./SpecialActionsPanel";
import OptionalEntryPanels from "./OptionalEntryPanels";
import StuartModePanel from "./StuartModePanel";

const OptionalHoleDetails = ({
  theme,
  isEditingCompleteGame,
  // Hole + course
  players,
  localPlayers,
  currentHole,
  setCurrentHole,
  courseData,
  holePar,
  holeHistory,
  setHoleHistory,
  playerStandings,
  setPlayerStandings,
  editingHole,
  strokeAllocation,
  scorecardCourseHoles,
  handleEditHoleFromScorecard,
  resetHole,
  jumpToHole,
  // Rotation / hitting order
  rotationOrder,
  captainIndex,
  isHoepfinger,
  phase,
  editingOrder,
  setEditingOrder,
  onRedoOrder,
  movePlayerInOrder,
  // Wager
  currentWager,
  carryOver,
  // Stuart Mode
  stuartModeEnabled,
  stuartMode,
  coachMode,
  assistMode,
  setAssistMode,
  holePhase,
  setHolePhase,
  aiMoves,
  // Panels
  showUsageStats,
  setShowUsageStats,
  showBettingOdds,
  setShowBettingOdds,
  showShotAnalysis,
  setShowShotAnalysis,
  // Teams & bets
  scores,
  handleScoreChange,
  teamMode,
  setTeamMode,
  team1,
  captain,
  getPlayerName,
  togglePlayerTeam,
  toggleCaptain,
  announceAction,
  duncanInvoked,
  setDuncanInvoked,
  floatInvokedBy,
  setFloatInvokedBy,
  optionInvokedBy,
  setOptionInvokedBy,
  showTeamSelection,
  setShowTeamSelection,
  showSpecialActions,
  setShowSpecialActions,
  aardvarkRequestedTeam,
  setAardvarkRequestedTeam,
  aardvarkTossed,
  setAardvarkTossed,
  aardvarkSolo,
  setAardvarkSolo,
  invisibleAardvarkTossed,
  setInvisibleAardvarkTossed,
  // Optional entry
  holeNotes,
  setHoleNotes,
  showGolfScores,
  setShowGolfScores,
  showCommissioner,
  setShowCommissioner,
  showNotes,
  setShowNotes,
}) => (
  <details
    open={isEditingCompleteGame || undefined}
    style={{ background: theme.colors.paper, border: `1px solid ${theme.colors.border}`, borderRadius: "10px" }}
  >
    <summary style={{ padding: "14px 16px", cursor: "pointer", color: theme.colors.textPrimary }}>
      <strong>Optional hole details</strong>
    </summary>
    <div style={{ padding: "0 12px 12px" }}>
      <HoleHeader
        currentHole={currentHole}
        courseData={courseData}
        players={players}
        rotationOrder={rotationOrder}
        captainIndex={captainIndex}
        currentWager={currentWager}
        carryOver={carryOver}
        phase={phase}
        strokeAllocation={strokeAllocation}
        isHoepfinger={isHoepfinger}
        theme={theme}
        holeHistory={holeHistory}
        holePar={holePar}
        editingHole={editingHole}
        editingOrder={editingOrder}
        setEditingOrder={setEditingOrder}
        onRedoOrder={onRedoOrder}
        jumpToHole={jumpToHole}
        movePlayerInOrder={movePlayerInOrder}
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

      {/* Running totals and scorecard remain available in optional details. */}
      <RunningTotals
        players={players}
        playerStandings={playerStandings}
        theme={theme}
      />

      {stuartModeEnabled && <StuartModeToggle
        assistMode={assistMode}
        setAssistMode={setAssistMode}
        theme={theme}
      />}

      <HolePhaseStrip
        stuartMode={stuartMode}
        holePhase={holePhase}
        setHolePhase={setHolePhase}
        theme={theme}
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

      {stuartModeEnabled && <AnalysisPanels
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
      />}

      <section style={{ marginBottom: "16px" }}>
        <h3 style={{ fontSize: "16px", color: theme.colors.textPrimary }}>
          <strong>Teams &amp; bets</strong>
          <span data-testid="team-details-summary" style={{ display: "block", marginTop: "4px", fontSize: "13px", color: theme.colors.textSecondary }}>
            {teamMode === "solo"
              ? `Solo · ${captain ? getPlayerName(captain) : "Choose captain"}`
              : `Partners · ${team1.length ? team1.map(getPlayerName).join(" & ") : "Choose players"}`}
            {duncanInvoked && " · Duncan"}
            {floatInvokedBy && ` · Float: ${getPlayerName(floatInvokedBy)}`}
            {optionInvokedBy && ` · Option: ${getPlayerName(optionInvokedBy)}`}
          </span>
        </h3>
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
      </section>

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

    </div>
  </details>
);

// Pass-through props; each child component validates its own shape.
OptionalHoleDetails.propTypes = {
  theme: PropTypes.object.isRequired,
  players: PropTypes.array.isRequired,
  playerStandings: PropTypes.object.isRequired,
  team1: PropTypes.array.isRequired,
  getPlayerName: PropTypes.func.isRequired,
};

export default OptionalHoleDetails;
