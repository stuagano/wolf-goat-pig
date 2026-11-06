// frontend/src/components/game/scorecardParts/NineCourseRows.jsx
// PAR, HDCP and BETS header rows for one nine of the Scorecard.
import React from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../../theme/Provider';
import {
  abbreviateBetting,
  cellStyle,
  getCourseHoleInfo,
  getHoleInfo,
  totalCellStyle
} from './scorecardUtils';

const NineCourseRows = ({ sectionHoles, courseHoles, holeHistory, sectionParTotal }) => {
  const theme = useTheme();

  return (
    <>
      <tr style={{ backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
        <td style={{ ...cellStyle, fontWeight: 'bold', fontSize: '10px' }}>PAR</td>
        {sectionHoles.map(hole => {
          const holeInfo = getCourseHoleInfo(courseHoles, hole);
          const par = holeInfo && typeof holeInfo.par === 'number' ? holeInfo.par : '-';
          return (
            <td key={`par-${hole}`} style={{ ...cellStyle, fontSize: '10px', textAlign: 'center' }}>
              {par}
            </td>
          );
        })}
        <td style={{ ...totalCellStyle, fontSize: '10px', fontWeight: 'bold' }}>
          {sectionParTotal}
        </td>
      </tr>
      <tr style={{ backgroundColor: 'rgba(0, 0, 0, 0.04)' }}>
        <td style={{ ...cellStyle, fontWeight: 'bold', fontSize: '9px' }}>HDCP</td>
        {sectionHoles.map(hole => {
          const holeInfo = getCourseHoleInfo(courseHoles, hole);
          const handicap = holeInfo && typeof holeInfo.handicap === 'number' ? holeInfo.handicap : '-';
          return (
            <td key={`hdcp-${hole}`} style={{ ...cellStyle, fontSize: '9px', textAlign: 'center' }}>
              {handicap}
            </td>
          );
        })}
        <td style={{ ...totalCellStyle, fontSize: '9px' }}>-</td>
      </tr>
      {/* Betting Actions Row - shows abbreviated betting narrative for each hole */}
      <tr style={{ backgroundColor: 'rgba(255, 152, 0, 0.05)' }}>
        <td style={{ ...cellStyle, fontWeight: 'bold', fontSize: '8px', color: '#F57C00' }}>BETS</td>
        {sectionHoles.map(hole => {
          const holeData = getHoleInfo(holeHistory, hole);
          const narrative = holeData?.betting_narrative;
          const wager = holeData?.wager;
          const displayText = abbreviateBetting(narrative, wager);
          return (
            <td
              key={`bets-${hole}`}
              style={{
                ...cellStyle,
                fontSize: '8px',
                textAlign: 'center',
                color: displayText ? '#F57C00' : theme.colors.textSecondary,
                fontWeight: displayText ? 'bold' : 'normal'
              }}
              title={narrative || (wager ? `Wager: ${wager}Q` : '')}
            >
              {displayText || '·'}
            </td>
          );
        })}
        <td style={{ ...totalCellStyle, fontSize: '8px' }}>-</td>
      </tr>
    </>
  );
};

NineCourseRows.propTypes = {
  sectionHoles: PropTypes.arrayOf(PropTypes.number).isRequired,
  courseHoles: PropTypes.array,
  holeHistory: PropTypes.array,
  sectionParTotal: PropTypes.number
};

export default NineCourseRows;
