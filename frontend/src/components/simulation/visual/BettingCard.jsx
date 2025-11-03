// frontend/src/components/simulation/visual/BettingCard.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { Card } from '../../ui';
import { useTheme } from '../../../theme/Provider';
import EducationalTooltip from './EducationalTooltip';
import ProbabilityBar from './ProbabilityBar';
import {
  getProbabilityColor,
  formatExpectedValue,
  getProbabilityLabel
} from './utils/oddsHelpers';

const BettingCard = ({ betting = {}, baseWager = 1, pokerState = {}, shotProbabilities = {} }) => {
  const theme = useTheme();
  const currentWager = betting?.current_wager || baseWager;
  const isDoubled = betting?.doubled || false;
  const potSize = pokerState?.pot_size || 0;
  const bettingPhase = pokerState?.betting_phase || 'Pre-tee';

  const renderBettingOdds = () => {
    const bettingAnalysis = shotProbabilities?.betting_analysis;

    if (!bettingAnalysis) return null;

    if (bettingAnalysis.error) {
      return (
        <div className="betting-odds-section">
          <div className="odds-unavailable">
            ⚠️ Odds temporarily unavailable
          </div>
        </div>
      );
    }

    const {
      offer_double,
      expected_value,
      risk_level,
      reasoning
    } = bettingAnalysis;

    const probabilityColor = getProbabilityColor(offer_double);
    const probabilityLabel = getProbabilityLabel(offer_double);
    const evColor = expected_value >= 0 ? '#2e7d32' : '#d32f2f';
    const riskColor = risk_level === 'low' ? '#2e7d32' : risk_level === 'high' ? '#d32f2f' : '#f57c00';

    return (
      <div className="betting-odds-section">
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '8px' }}>
          <h4 style={{
            margin: 0,
            fontSize: '14px',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            📊 Betting Odds
          </h4>
          <EducationalTooltip
            title="What are betting odds?"
            content="These probabilities show how likely betting scenarios are based on game state, player positions, and strategic factors."
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px' }}>
          <span style={{
            fontSize: '14px',
            color: probabilityColor === 'success' ? '#2e7d32' : probabilityColor === 'warning' ? '#f57c00' : '#999'
          }}>
            Double {probabilityLabel}: {Math.round(offer_double * 100)}%
          </span>
          <ProbabilityBar value={offer_double} />
        </div>

        <div style={{
          fontSize: '14px',
          color: evColor,
          marginTop: '4px',
          fontWeight: 500
        }}>
          Expected Value: {formatExpectedValue(expected_value)} pts
          {expected_value >= 0 ? ' 📈' : ' 📉'}
        </div>

        {risk_level && (
          <div style={{
            fontSize: '14px',
            color: riskColor,
            marginTop: '4px'
          }}>
            Risk: {risk_level.charAt(0).toUpperCase() + risk_level.slice(1)}
          </div>
        )}

        {reasoning && (
          <div style={{
            fontSize: '12px',
            color: theme.colors.textSecondary,
            marginTop: '8px',
            fontStyle: 'italic',
            wordBreak: 'break-word',
            overflowWrap: 'break-word'
          }}>
            ℹ️ {reasoning}
          </div>
        )}
      </div>
    );
  };

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

        {/* Betting Odds Section */}
        {renderBettingOdds()}
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
  }),
  shotProbabilities: PropTypes.shape({
    betting_analysis: PropTypes.shape({
      offer_double: PropTypes.number,
      accept_double: PropTypes.number,
      expected_value: PropTypes.number,
      risk_level: PropTypes.string,
      reasoning: PropTypes.string,
      error: PropTypes.string
    })
  })
};

export default BettingCard;
