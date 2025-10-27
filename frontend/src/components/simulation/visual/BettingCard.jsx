// frontend/src/components/simulation/visual/BettingCard.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { Card } from '../../ui';
import { useTheme } from '../../../theme/Provider';

const BettingCard = ({ betting = {}, baseWager = 1, pokerState = {} }) => {
  const theme = useTheme();
  const currentWager = betting?.current_wager || baseWager;
  const isDoubled = betting?.doubled || false;
  const potSize = pokerState?.pot_size || 0;
  const bettingPhase = pokerState?.betting_phase || 'Pre-tee';

  return (
    <Card style={{ height: '100%' }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 'bold' }}>
        BETTING
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {/* Current Wager */}
        <div>
          <div style={{ fontSize: '12px', color: theme.colors.textSecondary, marginBottom: '4px' }}>
            Current Wager
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '28px', fontWeight: 'bold', color: '#FFC107' }}>
              ${currentWager}
            </span>
            {isDoubled && (
              <span style={{
                background: '#FF9800',
                color: 'white',
                padding: '2px 8px',
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>
                2x
              </span>
            )}
          </div>
        </div>

        {/* Base Wager Reference */}
        <div style={{ fontSize: '14px', color: theme.colors.textSecondary }}>
          Base: ${baseWager}
        </div>

        {/* Pot Size */}
        {potSize > 0 && (
          <div style={{ fontSize: '14px', color: theme.colors.textSecondary }}>
            Pot: <span style={{ fontWeight: 'bold', color: theme.colors.textPrimary }}>${potSize}</span>
          </div>
        )}

        {/* Betting Phase */}
        <div style={{
          marginTop: '8px',
          padding: '8px',
          background: '#f5f5f5',
          borderRadius: theme.borderRadius.sm,
          fontSize: '14px',
          textAlign: 'center'
        }}>
          Phase: <span style={{ fontWeight: 'bold' }}>{bettingPhase}</span>
        </div>
      </div>
    </Card>
  );
};

BettingCard.propTypes = {
  betting: PropTypes.shape({
    current_wager: PropTypes.number,
    doubled: PropTypes.bool
  }),
  baseWager: PropTypes.number,
  pokerState: PropTypes.shape({
    pot_size: PropTypes.number,
    betting_phase: PropTypes.string
  })
};

export default BettingCard;
