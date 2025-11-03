// frontend/src/components/simulation/visual/DecisionButtons.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { Button } from '../../ui';
import { formatExpectedValue } from './utils/oddsHelpers';

const DecisionButtons = ({
  interactionNeeded = null,
  hasNextShot = false,
  onDecision = () => {},
  onNextShot = () => {},
  loading = false,
  gameState = {},
  shotProbabilities = {}
}) => {
  // Helper to get odds hint for betting decisions
  const getOddsHint = (decisionType) => {
    const bettingAnalysis = shotProbabilities?.betting_analysis;
    if (!bettingAnalysis || bettingAnalysis.error) return null;

    let probability = null;
    if (decisionType === 'offer-double' && bettingAnalysis.offer_double !== undefined) {
      probability = bettingAnalysis.offer_double;
    } else if (decisionType === 'accept-double' && bettingAnalysis.accept_double !== undefined) {
      probability = bettingAnalysis.accept_double;
    }

    if (probability === null) return null;

    const { expected_value } = bettingAnalysis;
    const ev = expected_value !== undefined ? formatExpectedValue(expected_value) : null;

    return {
      probability,
      ev,
      isPositiveEV: expected_value >= 0,
      isFavorable: probability >= 0.6 || expected_value >= 1.0
    };
  };

  // Helper to render large decision button with optional odds hints
  const renderButton = (key, icon, label, description, onClick, color = 'primary', oddsHint = null) => {
    // Determine border color based on odds favorability
    let borderColor = null;
    let borderWidth = '3px';

    if (oddsHint) {
      if (oddsHint.isFavorable && oddsHint.isPositiveEV) {
        borderColor = '#2e7d32'; // Green for favorable
      } else if (!oddsHint.isPositiveEV) {
        borderColor = '#d32f2f'; // Red for unfavorable
      } else {
        borderColor = '#f57c00'; // Orange for medium
      }
    }

    return (
      <Button
        key={key}
        variant="contained"
        color={color}
        size="large"
        onClick={onClick}
        disabled={loading}
        data-decision-type={key}
        style={{
          minHeight: '80px',
          fontSize: '18px',
          fontWeight: 'bold',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          padding: '16px',
          textTransform: 'none',
          ...(borderColor && {
            border: `${borderWidth} solid ${borderColor}`,
            boxShadow: `0 0 8px ${borderColor}40`
          })
        }}
      >
        <span style={{ fontSize: '24px' }}>{icon}</span>
        <span>{label}</span>
        {description && (
          <span style={{ fontSize: '14px', opacity: 0.8, fontWeight: 'normal' }}>
            {description}
          </span>
        )}
        {oddsHint && (
          <span style={{
            fontSize: '12px',
            marginTop: '4px',
            padding: '4px 8px',
            borderRadius: '4px',
            background: 'rgba(255, 255, 255, 0.2)',
            fontWeight: 'bold'
          }}>
            {Math.round(oddsHint.probability * 100)}% • EV: {oddsHint.ev} pts
          </span>
        )}
      </Button>
    );
  };

  // No action available
  if (!interactionNeeded && !hasNextShot) {
    return (
      <div style={{
        padding: '32px',
        textAlign: 'center',
        color: '#666',
        fontSize: '16px'
      }}>
        Waiting for simulation...
      </div>
    );
  }

  // Continue button (no interaction needed, shots available)
  if (!interactionNeeded && hasNextShot) {
    return (
      <div style={{
        display: 'grid',
        gap: '16px',
        padding: '16px'
      }}>
        {renderButton(
          'continue',
          '▶️',
          'Play Next Shot',
          'Continue simulation',
          onNextShot,
          'success'
        )}
      </div>
    );
  }

  const buttons = [];

  // Partnership decisions
  if (interactionNeeded.type === 'captain_chooses_partner') {
    const availablePartners = interactionNeeded.available_partners || [];
    const players = gameState?.players || [];

    // Partner request buttons
    availablePartners.forEach(partnerId => {
      const partner = players.find(p => p.id === partnerId);
      if (partner) {
        buttons.push(renderButton(
          `partner-${partnerId}`,
          '🤝',
          `Partner: ${partner.name}`,
          'Form team',
          () => onDecision({
            action: 'request_partner',
            requested_partner: partnerId
          }),
          'primary'
        ));
      }
    });

    // Go solo button
    buttons.push(renderButton(
      'go-solo',
      '🚀',
      'Go Solo',
      'Double and play alone',
      () => onDecision({ action: 'go_solo' }),
      'primary'
    ));

    // Keep watching button
    buttons.push(renderButton(
      'keep-watching',
      '👀',
      'Keep Watching',
      'See more tee shots',
      () => onDecision({ action: 'keep_watching' }),
      'primary'
    ));
  }

  // Partnership response
  if (interactionNeeded.type === 'partnership_request') {
    buttons.push(renderButton(
      'accept-partnership',
      '✅',
      'Accept Partnership',
      'Team up',
      () => onDecision({ accept_partnership: true }),
      'primary'
    ));

    buttons.push(renderButton(
      'decline-partnership',
      '❌',
      'Decline Partnership',
      'Play alone',
      () => onDecision({ accept_partnership: false }),
      'primary'
    ));
  }

  // Betting/Doubling decisions
  if (interactionNeeded.type === 'double_offer') {
    const acceptOddsHint = getOddsHint('accept-double');

    buttons.push(renderButton(
      'accept-double',
      '💰',
      'Accept Double',
      'Raise the stakes',
      () => onDecision({ accept_double: true }),
      'warning',
      acceptOddsHint
    ));

    buttons.push(renderButton(
      'decline-double',
      '❌',
      'Decline Double',
      'Keep current wager',
      () => onDecision({ accept_double: false }),
      'warning'
    ));
  }

  if (interactionNeeded.type === 'offer_double') {
    const offerOddsHint = getOddsHint('offer-double');

    buttons.push(renderButton(
      'offer-double',
      '💰',
      'Offer Double',
      'Double the wager',
      () => onDecision({ offer_double: true }),
      'warning',
      offerOddsHint
    ));

    buttons.push(renderButton(
      'decline-offer',
      '❌',
      'Decline',
      'Keep current wager',
      () => onDecision({ offer_double: false }),
      'warning'
    ));
  }

  // Render buttons in grid
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: buttons.length === 1
        ? '1fr'
        : buttons.length === 2
        ? 'repeat(2, 1fr)'
        : 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: '16px',
      padding: '16px'
    }}>
      {buttons}
    </div>
  );
};

DecisionButtons.propTypes = {
  interactionNeeded: PropTypes.shape({
    type: PropTypes.string.isRequired,
    available_partners: PropTypes.arrayOf(PropTypes.string)
  }),
  hasNextShot: PropTypes.bool,
  onDecision: PropTypes.func,
  onNextShot: PropTypes.func,
  loading: PropTypes.bool,
  gameState: PropTypes.shape({
    players: PropTypes.array
  }),
  shotProbabilities: PropTypes.shape({
    betting_analysis: PropTypes.shape({
      offer_double: PropTypes.number,
      accept_double: PropTypes.number,
      expected_value: PropTypes.number,
      risk_level: PropTypes.string,
      error: PropTypes.string
    })
  })
};

export default DecisionButtons;
