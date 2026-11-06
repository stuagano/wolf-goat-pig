// frontend/src/components/game/scorecardParts/StrokeCellContent.jsx
// Contents of a single stroke cell: score with par indicator, plus strokes-received markers.
import React from 'react';
import PropTypes from 'prop-types';
import { useTheme } from '../../../theme/Provider';
import { getFullStrokes, hasHalfStroke } from './scorecardUtils';

const StrokeCellContent = ({ isCompleted, strokes, strokesReceived, indicator }) => {
  const theme = useTheme();

  if (isCompleted) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2px' }}>
        {indicator?.symbol ? (
          <span
            style={{
              color: indicator.color,
              border: `1.5px solid ${indicator.color}`,
              borderRadius: indicator.shape === 'circle' ? '50%' : indicator.shape === 'square' ? '2px' : '0%',
              padding: '1px 4px',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              minWidth: '18px',
              height: '18px',
              fontSize: '11px',
              fontWeight: 'bold',
              lineHeight: '1'
            }}
            title={indicator.label}
          >
            {strokes}
          </span>
        ) : (
          <span style={{ color: '#000', fontSize: '11px', fontWeight: 'bold' }}>{strokes || '-'}</span>
        )}
        {/* Display stroke indicators - handle full strokes, half strokes, and combinations */}
        {strokesReceived > 0 && (
          <span style={{ marginLeft: '1px', display: 'inline-flex', alignItems: 'center' }}>
            {/* Full stroke indicator (●) */}
            {getFullStrokes(strokesReceived) >= 1 && (
              <span style={{ color: theme.colors.accent, fontSize: '8px' }} title={`Gets ${getFullStrokes(strokesReceived)} full stroke(s)`}>
                {getFullStrokes(strokesReceived) > 1 ? `●${getFullStrokes(strokesReceived)}` : '●'}
              </span>
            )}
            {/* Half stroke indicator (◐) - for Creecher strokes */}
            {hasHalfStroke(strokesReceived) && (
              <span style={{ color: theme.colors.warning || '#FF9800', fontSize: '8px' }} title="Gets 0.5 stroke (Creecher)">◐</span>
            )}
          </span>
        )}
      </div>
    );
  }

  if (!(strokesReceived > 0)) return null;

  return (
    <div style={{ fontSize: '10px', color: theme.colors.textSecondary, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      {/* Full stroke indicator (●) */}
      {getFullStrokes(strokesReceived) >= 1 && (
        <span title={`Gets ${getFullStrokes(strokesReceived)} full stroke(s)`}>
          {getFullStrokes(strokesReceived) > 1 ? `●${getFullStrokes(strokesReceived)}` : '●'}
        </span>
      )}
      {/* Half stroke indicator (◐) - for Creecher strokes */}
      {hasHalfStroke(strokesReceived) && (
        <span style={{ color: theme.colors.warning || '#FF9800' }} title="Gets 0.5 stroke (Creecher)">◐</span>
      )}
    </div>
  );
};

StrokeCellContent.propTypes = {
  isCompleted: PropTypes.any,
  strokes: PropTypes.number,
  strokesReceived: PropTypes.number,
  indicator: PropTypes.object
};

export default StrokeCellContent;
