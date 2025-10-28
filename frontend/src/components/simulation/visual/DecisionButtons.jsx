// frontend/src/components/simulation/visual/DecisionButtons.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { Button } from '../../ui';

const DecisionButtons = ({
  interactionNeeded = null,
  hasNextShot = false,
  onDecision = () => {},
  onNextShot = () => {},
  loading = false,
  gameState = {}
}) => {
  // Helper to render large decision button
  const renderButton = (key, icon, label, description, onClick, color = 'primary') => (
    <Button
      key={key}
      variant="contained"
      color={color}
      size="large"
      onClick={onClick}
      disabled={loading}
      style={{
        minHeight: '80px',
        fontSize: '18px',
        fontWeight: 'bold',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        padding: '16px',
        textTransform: 'none'
      }}
    >
      <span style={{ fontSize: '24px' }}>{icon}</span>
      <span>{label}</span>
      {description && (
        <span style={{ fontSize: '14px', opacity: 0.8, fontWeight: 'normal' }}>
          {description}
        </span>
      )}
    </Button>
  );

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
    buttons.push(renderButton(
      'accept-double',
      '💰',
      'Accept Double',
      'Raise the stakes',
      () => onDecision({ accept_double: true }),
      'warning'
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
    buttons.push(renderButton(
      'offer-double',
      '💰',
      'Offer Double',
      'Double the wager',
      () => onDecision({ offer_double: true }),
      'warning'
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
  })
};

export default DecisionButtons;
