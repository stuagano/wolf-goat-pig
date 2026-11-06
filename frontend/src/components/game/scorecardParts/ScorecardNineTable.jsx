// frontend/src/components/game/scorecardParts/ScorecardNineTable.jsx
// Table for one nine (front or back) of the Scorecard.
import React from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../../theme/Provider';
import NineCourseRows from './NineCourseRows';
import PlayerNineRows from './PlayerNineRows';
import {
  calculateStrokeTotals,
  calculateTotals,
  headerCellStyle,
  sumPar
} from './scorecardUtils';

const ScorecardNineTable = ({
  sectionHoles,
  sectionLabel,
  totalLabel,
  players,
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
  const isFrontNine = sectionLabel === 'FRONT';
  const sectionParTotal = isFrontNine ? sumPar(courseHoles, 0, 9) : sumPar(courseHoles, 9, 18);

  return (
    <table style={{
      width: '100%',
      borderCollapse: 'collapse',
      fontSize: '12px',
      marginBottom: isFrontNine ? '16px' : '0'
    }}>
      <thead>
        <tr style={{ backgroundColor: theme.colors.backgroundSecondary }}>
          <th style={{ ...headerCellStyle, minWidth: '80px' }}>HOLE</th>
          {sectionHoles.map(hole => (
            <th
              key={hole}
              style={{
                ...headerCellStyle,
                backgroundColor: hole === currentHole ? 'rgba(255, 215, 0, 0.2)' : 'transparent',
                fontWeight: hole === currentHole ? 'bold' : 'normal',
                color: hole === currentHole ? '#FFD700' : 'inherit',
                minWidth: '32px'
              }}
            >
              {hole}
            </th>
          ))}
          <th style={{ ...headerCellStyle, backgroundColor: 'rgba(0, 0, 0, 0.05)', minWidth: '40px' }}>{totalLabel}</th>
        </tr>
        {Array.isArray(courseHoles) && courseHoles.length > 0 && (
          <NineCourseRows
            sectionHoles={sectionHoles}
            courseHoles={courseHoles}
            holeHistory={holeHistory}
            sectionParTotal={sectionParTotal}
          />
        )}
      </thead>
      <tbody>
        {Array.isArray(players) && players.map((player, idx) => {
          if (!player || !player.id) return null;

          const totals = calculateTotals(holeHistory, player.id);
          const strokeTotals = calculateStrokeTotals(holeHistory, player.id);

          return (
            <PlayerNineRows
              key={`${player.id}-${sectionLabel}`}
              player={player}
              idx={idx}
              sectionHoles={sectionHoles}
              sectionStrokeTotal={isFrontNine ? strokeTotals.front9 : strokeTotals.back9}
              sectionQuarterTotal={isFrontNine ? totals.front9 : totals.back9}
              holeHistory={holeHistory}
              currentHole={currentHole}
              courseHoles={courseHoles}
              strokeAllocation={strokeAllocation}
              isEditingCompleteGame={isEditingCompleteGame}
              onPlayerNameChange={onPlayerNameChange}
              onPlayerNameClick={onPlayerNameClick}
              onCellClick={onCellClick}
            />
          );
        })}
      </tbody>
    </table>
  );
};

ScorecardNineTable.propTypes = {
  sectionHoles: PropTypes.arrayOf(PropTypes.number).isRequired,
  sectionLabel: PropTypes.string.isRequired,
  totalLabel: PropTypes.string.isRequired,
  players: PropTypes.array,
  holeHistory: PropTypes.array,
  currentHole: PropTypes.number,
  courseHoles: PropTypes.array,
  strokeAllocation: PropTypes.object,
  isEditingCompleteGame: PropTypes.bool,
  onPlayerNameChange: PropTypes.func,
  onPlayerNameClick: PropTypes.func.isRequired,
  onCellClick: PropTypes.func.isRequired
};

export default ScorecardNineTable;
