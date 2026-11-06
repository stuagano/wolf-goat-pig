// frontend/src/components/game/Scorecard.jsx
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Card } from '../ui';
import { useScorecardEditing } from './scorecardParts/useScorecardEditing';
import { BACK_NINE, FRONT_NINE, getStrokeAllocationWarning } from './scorecardParts/scorecardUtils';
import StandingsView from './scorecardParts/StandingsView';
import ScorecardHeader from './scorecardParts/ScorecardHeader';
import ScorecardNineTable from './scorecardParts/ScorecardNineTable';
import TotalsSummary from './scorecardParts/TotalsSummary';
import CollapsedSummary from './scorecardParts/CollapsedSummary';
import ScorecardEditHoleModal from './scorecardParts/ScorecardEditHoleModal';
import PlayerNameModal from './scorecardParts/PlayerNameModal';
/**
 * Unified Scorecard component for both real games and simulations
 * Displays all 18 holes with strokes and quarters, with click-to-edit functionality
 *
 * Optional features (enabled via props):
 * - Player name editing (onPlayerNameChange)
 * - Standings view toggle (captainId)
 *
 * Subcomponents, the editing hook and pure helpers live in ./scorecardParts/.
 */
const Scorecard = ({
  players = [],
  holeHistory = [],
  currentHole = 1,
  onEditHole,
  onPlayerNameChange, // Optional: enables player name editing in simulations
  captainId, // Optional: enables standings view and captain highlighting
  courseHoles = [],
  strokeAllocation = {},
  isEditingCompleteGame = false, // Optional: when true, highlights all completed holes as editable
  defaultExpanded = false // Optional: start expanded instead of collapsed
}) => {
  const editing = useScorecardEditing({ holeHistory, currentHole, onEditHole, onPlayerNameChange });
  const [viewMode, setViewMode] = useState('scorecard'); // 'scorecard' or 'standings'
  const [isCollapsed, setIsCollapsed] = useState(!defaultExpanded); // Start minimized unless defaultExpanded
  // Auto-select front/back based on current hole
  const [activeNine, setActiveNine] = useState(() => currentHole > 9 ? 'back' : 'front');

  // Auto-switch to back 9 when current hole moves there
  useEffect(() => {
    if (currentHole > 9) {
      setActiveNine('back');
    } else {
      setActiveNine('front');
    }
  }, [currentHole]);

  // Track if stroke allocation data is missing or incomplete
  const [strokeAllocationWarning, setStrokeAllocationWarning] = useState(null);

  // Validate stroke allocation on mount and when it changes
  useEffect(() => {
    setStrokeAllocationWarning(getStrokeAllocationWarning(strokeAllocation, players));
  }, [strokeAllocation, players]);

  const nineTableProps = {
    players,
    holeHistory,
    currentHole,
    courseHoles,
    strokeAllocation,
    isEditingCompleteGame,
    onPlayerNameChange,
    onPlayerNameClick: editing.handlePlayerNameClick,
    onCellClick: editing.handleCellClick
  };

  return (
    <Card style={{ height: '100%', overflow: 'auto', padding: '8px' }}>
      {/* Compact Header */}
      <ScorecardHeader
        isCollapsed={isCollapsed}
        setIsCollapsed={setIsCollapsed}
        viewMode={viewMode}
        setViewMode={setViewMode}
        activeNine={activeNine}
        setActiveNine={setActiveNine}
        captainId={captainId}
      />

      {/* Stroke allocation warning */}
      {strokeAllocationWarning && !isCollapsed && (
        <div style={{
          background: '#fff3e0',
          border: '1px solid #ff9800',
          borderRadius: '4px',
          padding: '8px 12px',
          marginBottom: '12px',
          fontSize: '12px',
          color: '#e65100',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <span>⚠️</span>
          <span>{strokeAllocationWarning}</span>
        </div>
      )}

      {!isCollapsed && (viewMode === 'standings' ? (
        <StandingsView players={players} holeHistory={holeHistory} captainId={captainId} />
      ) : (
        <div style={{ overflowX: 'auto' }}>
          {/* Show only active nine (mobile-friendly) */}
          {activeNine === 'front' ? (
            <ScorecardNineTable sectionHoles={FRONT_NINE} sectionLabel="FRONT" totalLabel="OUT" {...nineTableProps} />
          ) : (
            <ScorecardNineTable sectionHoles={BACK_NINE} sectionLabel="BACK" totalLabel="IN" {...nineTableProps} />
          )}

          {/* Totals Summary - always show */}
          <TotalsSummary players={players} holeHistory={holeHistory} courseHoles={courseHoles} />
        </div>
      ))}

      {isCollapsed && <CollapsedSummary players={players} holeHistory={holeHistory} />}

      {/* Edit Hole Modal */}
      {editing.editingHole && editing.editingPlayer && (
        <ScorecardEditHoleModal players={players} holeHistory={holeHistory} editing={editing} />
      )}

      {/* Edit Player Name Modal (simulation mode only) */}
      {editing.editingPlayerName && onPlayerNameChange && (
        <PlayerNameModal
          value={editing.editPlayerNameValue}
          onChange={editing.setEditPlayerNameValue}
          onSave={editing.handleSavePlayerName}
          onCancel={editing.handleCancelPlayerNameEdit}
        />
      )}
    </Card>
  );
};

Scorecard.propTypes = {
  // Array of player objects
  players: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    points: PropTypes.number,
    handicap: PropTypes.number,
    handicap_index: PropTypes.number,
    is_human: PropTypes.bool
  })).isRequired,

  // Array of completed hole data
  holeHistory: PropTypes.arrayOf(PropTypes.shape({
    hole: PropTypes.number.isRequired,
    // Object mapping playerId -> quarters won/lost
    points_delta: PropTypes.objectOf(PropTypes.number),
    // Object mapping playerId -> gross score
    gross_scores: PropTypes.objectOf(PropTypes.number),
    // Optional betting narrative string showing betting actions (e.g., "Stuart doubles → accepted")
    betting_narrative: PropTypes.string,
    // Optional wager amount for the hole
    wager: PropTypes.number
  })).isRequired,

  // Current hole number (1-18)
  currentHole: PropTypes.number,

  // Callback when user edits a hole: (data: {hole, playerId, strokes, quarters}) => void
  onEditHole: PropTypes.func,

  // Optional: Callback for player name changes in simulation mode
  onPlayerNameChange: PropTypes.func,

  // Optional: Captain ID for highlighting in standings view
  captainId: PropTypes.string,

  // Course hole information (par, handicap, yards)
  courseHoles: PropTypes.arrayOf(PropTypes.shape({
    hole: PropTypes.number.isRequired,
    par: PropTypes.number,
    handicap: PropTypes.number, // Stroke index (1-18)
    yards: PropTypes.number
  })).isRequired,

  // Stroke allocation: { playerId: { holeNumber: strokes } }
  // e.g., { "player1": { 1: 1, 2: 0, 3: 0.5, ... } }
  strokeAllocation: PropTypes.objectOf(
    PropTypes.objectOf(PropTypes.number)
  ).isRequired,

  // Optional: When true, highlights all completed holes as editable
  isEditingCompleteGame: PropTypes.bool,

  // Optional: When true, starts expanded instead of collapsed
  defaultExpanded: PropTypes.bool
};

// Default props to ensure we never work with undefined arrays
Scorecard.defaultProps = {
  players: [],
  holeHistory: [],
  courseHoles: [],
  strokeAllocation: {},
  currentHole: 1,
  isEditingCompleteGame: false,
  defaultExpanded: false
};

export default React.memo(Scorecard);
