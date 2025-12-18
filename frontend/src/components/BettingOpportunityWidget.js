/**
 * BettingOpportunityWidget - Displays available betting opportunities
 *
 * Shows:
 * - Available bets (double, redouble, side bets)
 * - Betting deadlines
 * - Risk/reward information
 * - Quick bet actions
 */

import React from 'react';
import PropTypes from 'prop-types';
import { getRiskColor, getRiskIcon, formatProbability } from '../utils/bettingHelpers';

const BettingOpportunityWidget = ({
  opportunities = [],
  currentWager,
  onPlaceBet,
  disabled = false,
  className = '',
  children
}) => {
  if (opportunities.length === 0) {
    return (
      <div className={`betting-opportunity-widget ${className}`}>
        {children || <p>No betting opportunities available</p>}
      </div>
    );
  }

  return (
    <div className={`betting-opportunity-widget ${className}`}>
      {children}

      <div className="opportunities-list">
        <h3>Available Bets</h3>

        {currentWager && (
          <div className="current-wager">
            <p>Current Wager: ${currentWager}</p>
          </div>
        )}

        {opportunities.map((opportunity, index) => (
          <div key={index} className="opportunity-item">
            <div className="opportunity-header">
              <h4>{opportunity.type}</h4>
              <span className="wager-amount">${opportunity.amount}</span>
            </div>

            {opportunity.description && (
              <p className="description">{opportunity.description}</p>
            )}

            {opportunity.deadline && (
              <p className="deadline">
                Available until: {opportunity.deadline}
              </p>
            )}

            {opportunity.risk && (
              <div className="risk-info">
                <span
                  className="risk"
                  style={{ color: getRiskColor(opportunity.risk) }}
                >
                  {getRiskIcon(opportunity.risk)} Risk: {opportunity.risk}
                </span>
                {opportunity.reward && (
                  <span className="reward">Reward: {opportunity.reward}</span>
                )}
              </div>
            )}

            {opportunity.probability !== undefined && (
              <div className="probability-info">
                <span className="probability">
                  Win Probability: {formatProbability(opportunity.probability)}
                </span>
              </div>
            )}

            {onPlaceBet && (
              <button
                onClick={() => onPlaceBet(opportunity)}
                disabled={disabled || opportunity.disabled}
                className="place-bet-btn"
              >
                {opportunity.buttonText || 'Place Bet'}
              </button>
            )}
          </div>
        ))}
      </div>

      {disabled && (
        <div className="betting-closed">
          <p>Betting is currently closed</p>
        </div>
      )}
    </div>
  );
};

BettingOpportunityWidget.propTypes = {
  opportunities: PropTypes.arrayOf(PropTypes.shape({
    type: PropTypes.string.isRequired,
    amount: PropTypes.number.isRequired,
    description: PropTypes.string,
    deadline: PropTypes.string,
    risk: PropTypes.string,
    reward: PropTypes.string,
    probability: PropTypes.number,
    disabled: PropTypes.bool,
    buttonText: PropTypes.string
  })),
  currentWager: PropTypes.number,
  onPlaceBet: PropTypes.func,
  disabled: PropTypes.bool,
  className: PropTypes.string,
  children: PropTypes.node
};

export default BettingOpportunityWidget;
