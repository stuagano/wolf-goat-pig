// frontend/src/components/simulation/visual/ShotContextCard.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { Card } from '../../ui';
import { useTheme } from '../../../theme/Provider';

const ShotContextCard = ({ shotState = {}, holeState = {}, probabilities = {} }) => {
  const theme = useTheme();
  const shotNumber = holeState?.current_shot_number || 1;
  const totalShots = holeState?.total_shots || shotNumber;
  const distance = shotState?.distance_to_hole || 0;
  const lie = shotState?.lie || 'unknown';
  const recommendedShot = shotState?.recommended_shot || 'N/A';
  const winProb = probabilities?.win_probability || 0;

  return (
    <Card style={{ height: '100%' }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 'bold' }}>
        SHOT CONTEXT
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {/* Shot Number */}
        <div style={{ fontSize: '14px', color: theme.colors.textSecondary }}>
          Shot {shotNumber} of {totalShots}
        </div>

        {/* Distance */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
          <span style={{ fontSize: '12px' }}>🎯</span>
          <span style={{ fontSize: '24px', fontWeight: 'bold' }}>
            {distance}
          </span>
          <span style={{ fontSize: '14px', color: theme.colors.textSecondary }}>
            yards
          </span>
        </div>

        {/* Lie */}
        <div style={{ fontSize: '14px' }}>
          Lie: <span style={{
            fontWeight: 'bold',
            color: lie === 'fairway' ? '#4CAF50' : theme.colors.textSecondary,
            textTransform: 'capitalize'
          }}>
            {lie}
          </span>
        </div>

        {/* Recommended Shot */}
        <div style={{
          padding: theme.spacing[2],
          background: '#f5f5f5',
          borderRadius: theme.borderRadius.sm,
          fontSize: '14px'
        }}>
          <div style={{ color: theme.colors.textSecondary, marginBottom: '4px' }}>Recommended:</div>
          <div style={{ fontWeight: 'bold', fontSize: '16px' }}>
            {recommendedShot}
          </div>
        </div>

        {/* Win Probability */}
        {winProb > 0 && (
          <div style={{
            marginTop: '4px',
            padding: theme.spacing[2],
            background: winProb >= 0.5 ? '#E8F5E9' : '#FFF3E0',
            borderRadius: theme.borderRadius.sm,
            fontSize: '14px',
            textAlign: 'center'
          }}>
            Win Prob: <span style={{
              fontWeight: 'bold',
              fontSize: '18px',
              color: winProb >= 0.5 ? '#4CAF50' : '#FF9800'
            }}>
              {Math.round(winProb * 100)}%
            </span>
          </div>
        )}
      </div>
    </Card>
  );
};

ShotContextCard.propTypes = {
  shotState: PropTypes.shape({
    distance_to_hole: PropTypes.number,
    lie: PropTypes.string,
    recommended_shot: PropTypes.string
  }),
  holeState: PropTypes.shape({
    current_shot_number: PropTypes.number,
    total_shots: PropTypes.number
  }),
  probabilities: PropTypes.shape({
    win_probability: PropTypes.number
  })
};

export default ShotContextCard;
