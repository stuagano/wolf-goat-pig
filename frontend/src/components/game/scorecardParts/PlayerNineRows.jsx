// frontend/src/components/game/scorecardParts/PlayerNineRows.jsx
// Stroke row and quarters row for one player within one nine of the Scorecard.
import React from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../../theme/Provider';
import StrokeCellContent from './StrokeCellContent';
import {
  cellStyle,
  displayName,
  formatSignedQuarters,
  getCourseHoleInfo,
  getHoleData,
  getScoreIndicator,
  getStrokesReceived,
  isHoleCompleted,
  isHumanPlayer,
  quartersColor,
  totalCellStyle
} from './scorecardUtils';

const PlayerNineRows = ({
  player,
  idx,
  sectionHoles,
  sectionStrokeTotal,
  sectionQuarterTotal,
  holeHistory,
  currentHole,
  courseHoles,
  strokeAllocation,
  isEditingCompleteGame,
  onPlayerNameChange,
  onPlayerNameClick,
  onCellClick
}) => {
  const theme = useTheme();
  const isHuman = isHumanPlayer(player);
  const playerName = displayName(player);

  // Shared per-hole cell state for both rows
  const cellState = (hole) => {
    const isCurrentHole = hole === currentHole;
    const isCompleted = isHoleCompleted(hole, currentHole, holeHistory);
    // Determine if this cell is editable
    const isEditable = isCurrentHole || isCompleted;
    // Show edit highlight in edit mode for all completed holes
    const showEditHighlight = isEditingCompleteGame && isCompleted;
    const backgroundColor = isCurrentHole ? 'rgba(255, 215, 0, 0.1)' :
      showEditHighlight ? 'rgba(255, 152, 0, 0.08)' : 'transparent';
    return { isCompleted, isEditable, showEditHighlight, backgroundColor };
  };

  return (
    <>
      {/* Strokes row (Main player row) */}
      <tr style={{
        backgroundColor: idx % 2 === 0 ? 'rgba(0, 0, 0, 0.02)' : 'transparent',
        borderLeft: isHuman ? '3px solid rgba(33, 150, 243, 0.5)' : 'none',
        borderTop: idx > 0 ? `2px solid ${theme.colors.border}`: 'none'
      }}>
        <td style={{ ...cellStyle, fontSize: '10px', fontStyle: 'italic', color: theme.colors.textSecondary, paddingTop: '2px', textAlign: 'left' }}>
          <div style={{ fontWeight: 'bold', fontSize: '11px', marginBottom: '2px', cursor: onPlayerNameChange ? 'pointer' : 'default' }}
            onClick={() => onPlayerNameChange && onPlayerNameClick(player.id, player.name)}
            title={onPlayerNameChange ? 'Click to edit name' : ''}
          >
            {isHuman ? '👤 ' : '🤖 '}
            {playerName}
            {player.handicap != null && (
              <span style={{ fontSize: '10px', marginLeft: '4px', opacity: 0.7 }}>
                {/* Index → course handicap when the index was recorded; strokes use the course handicap. */}
                {player.handicap_index != null ? `(${player.handicap_index} → ${player.handicap})` : `(${player.handicap})`}
              </span>
            )}
            {onPlayerNameChange && <span style={{ fontSize: '10px', marginLeft: '4px', opacity: 0.5 }}>✏️</span>}
          </div>
          <div>Stroke</div>
        </td>
        {sectionHoles.map(hole => {
          const { strokes } = getHoleData(holeHistory, hole, player.id);
          const { isCompleted, isEditable, showEditHighlight, backgroundColor } = cellState(hole);
          const strokesReceived = getStrokesReceived(strokeAllocation, player.id, hole);
          const holePar = getCourseHoleInfo(courseHoles, hole)?.par;
          const indicator = getScoreIndicator(strokes, holePar);

          return (
            <td
              key={hole}
              style={{
                ...cellStyle,
                backgroundColor,
                fontWeight: strokes ? 'bold' : 'normal',
                cursor: isEditable ? 'pointer' : 'default',
                position: 'relative',
                paddingBottom: '2px',
                border: showEditHighlight ? '1px dashed rgba(255, 152, 0, 0.4)' : 'none',
                transition: 'all 0.2s ease'
              }}
              title={isEditable ? 'Click to edit' : ''}
              onClick={() => onCellClick(hole, player.id)}
            >
              <StrokeCellContent
                isCompleted={isCompleted}
                strokes={strokes}
                strokesReceived={strokesReceived}
                indicator={indicator}
              />
            </td>
          );
        })}
        <td style={{ ...totalCellStyle, fontWeight: 'bold', fontSize: '11px', paddingBottom: '2px' }}>
          {sectionStrokeTotal > 0 ? sectionStrokeTotal : '-'}
        </td>
      </tr>

      {/* Quarters Row */}
      <tr style={{
        backgroundColor: idx % 2 === 0 ? 'rgba(0, 0, 0, 0.02)' : 'transparent',
        borderLeft: isHuman ? '3px solid rgba(33, 150, 243, 0.5)' : 'none'
      }}>
        <td style={{ ...cellStyle, fontSize: '10px', fontStyle: 'italic', color: theme.colors.textSecondary, paddingTop: '2px', textAlign: 'left' }}>
          Quarters
        </td>
        {sectionHoles.map(hole => {
          const { quarters } = getHoleData(holeHistory, hole, player.id);
          const { isEditable, showEditHighlight, backgroundColor } = cellState(hole);

          return (
            <td
              key={hole}
              style={{
                ...cellStyle,
                backgroundColor,
                fontSize: '10px',
                fontWeight: '500',
                cursor: isEditable ? 'pointer' : 'default',
                paddingTop: '2px',
                border: showEditHighlight ? '1px dashed rgba(255, 152, 0, 0.4)' : 'none',
                transition: 'all 0.2s ease'
              }}
              title={isEditable ? 'Click to edit' : ''}
              onClick={() => onCellClick(hole, player.id)}
            >
              {quarters !== null && quarters !== 0 ? (
                <span style={{ color: quarters > 0 ? '#4CAF50' : '#f44336' }}>
                  {quarters > 0 ? `+${quarters}` : quarters}
                </span>
              ) : (
                <span style={{ color: theme.colors.textSecondary }}>·</span>
              )}
            </td>
          );
        })}
        <td style={{
          ...totalCellStyle,
          fontWeight: 'bold',
          fontSize: '11px',
          paddingTop: '2px',
          color: quartersColor(sectionQuarterTotal)
        }}>
          {formatSignedQuarters(sectionQuarterTotal)}
        </td>
      </tr>
    </>
  );
};

PlayerNineRows.propTypes = {
  player: PropTypes.object.isRequired,
  idx: PropTypes.number.isRequired,
  sectionHoles: PropTypes.arrayOf(PropTypes.number).isRequired,
  sectionStrokeTotal: PropTypes.number,
  sectionQuarterTotal: PropTypes.number,
  holeHistory: PropTypes.array,
  currentHole: PropTypes.number,
  courseHoles: PropTypes.array,
  strokeAllocation: PropTypes.object,
  isEditingCompleteGame: PropTypes.bool,
  onPlayerNameChange: PropTypes.func,
  onPlayerNameClick: PropTypes.func.isRequired,
  onCellClick: PropTypes.func.isRequired
};

export default PlayerNineRows;
