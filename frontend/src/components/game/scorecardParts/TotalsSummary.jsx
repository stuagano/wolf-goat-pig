// frontend/src/components/game/scorecardParts/TotalsSummary.jsx
// OUT / IN / TOTAL summary table shown under the active nine.
import React from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../../theme/Provider';
import {
  calculateStrokeTotals,
  calculateTotals,
  cellStyle,
  displayName,
  formatSignedQuarters,
  headerCellStyle,
  isHumanPlayer,
  quartersColor,
  sumPar,
  totalCellStyle
} from './scorecardUtils';

const TotalsSummary = ({ players, holeHistory, courseHoles }) => {
  const theme = useTheme();
  const totalParFront = sumPar(courseHoles, 0, 9);
  const totalParBack = sumPar(courseHoles, 9, 18);

  return (
    <table style={{
      width: '100%',
      borderCollapse: 'collapse',
      fontSize: '12px',
      marginTop: '8px',
      borderTop: `3px solid ${theme.colors.border}`
    }}>
      <thead>
        <tr style={{ backgroundColor: theme.colors.backgroundSecondary }}>
          <th style={{ ...headerCellStyle, minWidth: '80px', textAlign: 'left' }}>TOTALS</th>
          <th style={{ ...headerCellStyle, minWidth: '60px' }}>OUT</th>
          <th style={{ ...headerCellStyle, minWidth: '60px' }}>IN</th>
          <th style={{ ...headerCellStyle, minWidth: '60px', backgroundColor: 'rgba(0, 0, 0, 0.05)' }}>TOTAL</th>
        </tr>
        {Array.isArray(courseHoles) && courseHoles.length > 0 && (
          <tr style={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
            <td style={{ ...cellStyle, fontWeight: 'bold', fontSize: '10px', textAlign: 'left' }}>PAR</td>
            <td style={{ ...cellStyle, fontSize: '10px', fontWeight: 'bold' }}>{totalParFront}</td>
            <td style={{ ...cellStyle, fontSize: '10px', fontWeight: 'bold' }}>{totalParBack}</td>
            <td style={{ ...totalCellStyle, fontSize: '10px', fontWeight: 'bold' }}>{totalParFront + totalParBack}</td>
          </tr>
        )}
      </thead>
      <tbody>
        {Array.isArray(players) && players.flatMap((player, idx) => {
          if (!player || !player.id) return [];

          const totals = calculateTotals(holeHistory, player.id);
          const strokeTotals = calculateStrokeTotals(holeHistory, player.id);
          const isHuman = isHumanPlayer(player);
          const playerName = displayName(player);

          return [
            // Strokes totals row
            <tr key={`${player.id}-strokes-total`} style={{
              backgroundColor: idx % 2 === 0 ? 'rgba(0, 0, 0, 0.02)' : 'transparent',
              borderLeft: isHuman ? '3px solid rgba(33, 150, 243, 0.5)' : 'none',
              borderTop: idx > 0 ? `2px solid ${theme.colors.border}`: 'none'
            }}>
              <td style={{ ...cellStyle, fontSize: '11px', fontWeight: 'bold', textAlign: 'left' }}>
                {isHuman ? '👤 ' : '🤖 '}{playerName}
              </td>
              <td style={{ ...cellStyle, fontWeight: 'bold', fontSize: '12px' }}>
                {strokeTotals.front9 > 0 ? strokeTotals.front9 : '-'}
              </td>
              <td style={{ ...cellStyle, fontWeight: 'bold', fontSize: '12px' }}>
                {strokeTotals.back9 > 0 ? strokeTotals.back9 : '-'}
              </td>
              <td style={{ ...totalCellStyle, fontWeight: 'bold', fontSize: '13px' }}>
                {strokeTotals.total > 0 ? strokeTotals.total : '-'}
              </td>
            </tr>,
            // Quarters totals row
            <tr key={`${player.id}-quarters-total`} style={{
              backgroundColor: idx % 2 === 0 ? 'rgba(0, 0, 0, 0.02)' : 'transparent',
              borderLeft: isHuman ? '3px solid rgba(33, 150, 243, 0.5)' : 'none'
            }}>
              <td style={{ ...cellStyle, fontSize: '10px', fontStyle: 'italic', color: theme.colors.textSecondary, textAlign: 'left' }}>
                Quarters
              </td>
              <td style={{ ...cellStyle, fontWeight: 'bold', fontSize: '11px', color: quartersColor(totals.front9) }}>
                {formatSignedQuarters(totals.front9)}
              </td>
              <td style={{ ...cellStyle, fontWeight: 'bold', fontSize: '11px', color: quartersColor(totals.back9) }}>
                {formatSignedQuarters(totals.back9)}
              </td>
              <td style={{ ...totalCellStyle, fontWeight: 'bold', fontSize: '13px', color: quartersColor(totals.total) }}>
                {formatSignedQuarters(totals.total)}
              </td>
            </tr>
          ];
        })}
      </tbody>
    </table>
  );
};

TotalsSummary.propTypes = {
  players: PropTypes.array,
  holeHistory: PropTypes.array,
  courseHoles: PropTypes.array
};

export default TotalsSummary;
