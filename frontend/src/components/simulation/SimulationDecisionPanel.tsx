import React, { useMemo, useCallback } from 'react';
import { useTheme } from '../../theme/Provider';
import { Button, Card } from '../ui';

const HUMAN_PLAYER_ID = 'human';

interface Player {
  id: string;
  name: string;
  handicap?: number | string;
  is_human?: boolean;
  points?: number;
}

interface BettingState {
  current_wager?: number;
}

interface HoleState {
  hole_complete?: boolean;
  current_shot_number?: number;
}

interface GameState {
  players?: Player[];
  captain_id?: string;
  base_wager?: number;
  betting?: BettingState;
  hole_state?: HoleState;
  current_hole?: number;
  interactionNeeded?: InteractionNeeded | null;
  hasNextShot?: boolean;
}

interface InteractionNeeded {
  type: string;
  captain_id?: string;
  captain_name?: string;
  requested_partner?: string;
  available_partners?: string[];
  options?: Array<{
    action: string;
    label?: string;
    description?: string;
  }>;
  message?: string;
  // Allow additional properties from API while maintaining type safety
  [key: string]: unknown;
}

interface SimulationDecisionPanelProps {
  gameState?: GameState | null;
  interactionNeeded?: InteractionNeeded | null;
  onDecision?: (payload: Record<string, unknown>) => void;
  onNextShot?: () => void;
  onNextHole?: () => void;
  hasNextShot?: boolean | null;
  style?: React.CSSProperties;
}

const SimulationDecisionPanel: React.FC<SimulationDecisionPanelProps> = ({
  gameState,
  interactionNeeded,
  onDecision,
  onNextShot,
  onNextHole,
  hasNextShot,
  style
}) => {
  const theme = useTheme();

  const effectiveInteraction = interactionNeeded ?? gameState?.interactionNeeded ?? null;
  const shotAvailable = hasNextShot ?? gameState?.hasNextShot ?? false;

  const players: Player[] = useMemo(() => gameState?.players ?? [], [gameState?.players]);

  const humanPlayerId = useMemo(() => {
    if (!players || players.length === 0) {
      return HUMAN_PLAYER_ID;
    }
    const explicitHuman = players.find(player => player.is_human);
    if (explicitHuman) {
      return explicitHuman.id;
    }
    const fallbackHuman = players.find(player => player.id === HUMAN_PLAYER_ID);
    return fallbackHuman?.id ?? HUMAN_PLAYER_ID;
  }, [players]);

  const captainId = effectiveInteraction?.captain_id || gameState?.captain_id || humanPlayerId;

  const availablePartners = useMemo(() => {
    if (!players || players.length === 0) {
      return [] as Player[];
    }

    const fromInteraction = effectiveInteraction?.available_partners;
    if (fromInteraction && Array.isArray(fromInteraction) && fromInteraction.length > 0) {
      return fromInteraction
        .map(partnerId => players.find(player => player.id === partnerId))
        .filter(Boolean) as Player[];
    }

    return players.filter(player => {
      if (player.id === humanPlayerId) {
        return false;
      }
      if (player.id === captainId) {
        return false;
      }
      return !player.is_human;
    });
  }, [players, effectiveInteraction, humanPlayerId, captainId]);

  const currentWager = useMemo(() => {
    if (gameState?.betting?.current_wager) {
      return gameState.betting.current_wager;
    }
    if (typeof gameState?.base_wager === 'number') {
      return gameState.base_wager;
    }
    return 1;
  }, [gameState]);

  const handleDecision = useCallback((payload: Record<string, unknown>) => {
    if (onDecision) {
      onDecision(payload);
    }
  }, [onDecision]);

  const handlePartnerInvite = useCallback((partnerId: string) => {
    handleDecision({
      action: 'request_partner',
      requested_partner: partnerId,
      player_id: captainId,
      captain_id: captainId,
    });
  }, [handleDecision, captainId]);

  const handleGoSolo = useCallback(() => {
    handleDecision({
      action: 'go_solo',
      player_id: captainId,
      captain_id: captainId,
    });
  }, [handleDecision, captainId]);

  const handleKeepWatching = useCallback(() => {
    handleDecision({
      action: 'keep_watching',
      player_id: captainId,
    });
  }, [handleDecision, captainId]);

  const handlePartnershipResponse = useCallback((accepted: boolean) => {
    handleDecision({
      accept_partnership: accepted,
      partner_id: effectiveInteraction?.captain_id ?? captainId,
    });
  }, [handleDecision, effectiveInteraction?.captain_id, captainId]);

  const handleDoubleResponse = useCallback((accepted: boolean) => {
    handleDecision({
      accept_double: accepted,
    });
  }, [handleDecision]);

  const handleDoubleDecision = useCallback((offer: boolean) => {
    handleDecision({
      offer_double: offer,
      player_id: captainId,
    });
  }, [handleDecision, captainId]);

  const renderCaptainDecision = () => {
    const captainName = players.find(player => player.id === captainId)?.name || 'You';

    return (
      <Card
        variant="warning"
        style={{
          border: `4px solid ${theme.colors.primary}`,
          backgroundColor: '#f0f8ff',
          maxWidth: '800px',
          margin: '0 auto',
          wordBreak: 'break-word',
          overflowWrap: 'break-word'
        }}
      >
        <h3 style={{ color: theme.colors.primary, marginBottom: theme.spacing[3] }}>🤔 Your Decision</h3>
        <p style={{ marginBottom: theme.spacing[3], fontSize: theme.typography.base }}>
          <strong>{captainName}</strong> is captain for this hole. Choose how you want to play it.
        </p>

        {availablePartners.length > 0 && (
          <div style={{ marginBottom: theme.spacing[4] }}>
            <h4 style={{ marginBottom: theme.spacing[2] }}>Invite a partner:</h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: theme.spacing[2] }}>
              {availablePartners.map(partner => (
                <Button
                  key={partner.id}
                  variant="primary"
                  onClick={() => handlePartnerInvite(partner.id)}
                >
                  🤝 Team with {partner.name}
                </Button>
              ))}
            </div>
          </div>
        )}

        <div style={{ textAlign: 'center', marginBottom: theme.spacing[3] }}>
          <strong>— OR —</strong>
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: theme.spacing[2], flexWrap: 'wrap' }}>
          <Button
            variant="warning"
            size="large"
            onClick={handleGoSolo}
          >
            🚀 Go Solo (Double the wager)
          </Button>

          <Button
            variant="secondary"
            onClick={handleKeepWatching}
          >
            👀 Keep Watching Tee Shots
          </Button>
        </div>

        <p style={{ marginTop: theme.spacing[3], fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
          Current wager: <strong>{currentWager} quarter{currentWager !== 1 ? 's' : ''}</strong>
        </p>
      </Card>
    );
  };

  const renderPartnershipResponse = () => {
    const captainName = effectiveInteraction?.captain_name || players.find(player => player.id === effectiveInteraction?.captain_id)?.name || 'Your teammate';

    return (
      <Card
        variant="warning"
        style={{
          border: `4px solid ${theme.colors.warning}`,
          backgroundColor: '#fff8e1',
          maxWidth: '800px',
          margin: '0 auto',
          wordBreak: 'break-word',
          overflowWrap: 'break-word'
        }}
      >
        <h3 style={{ color: theme.colors.warning, marginBottom: theme.spacing[3] }}>🤝 Partnership Invitation</h3>
        <p style={{ fontSize: theme.typography.base, marginBottom: theme.spacing[4] }}>
          <strong>{captainName}</strong> has invited you to partner up.
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: theme.spacing[3], flexWrap: 'wrap' }}>
          <Button
            variant="success"
            onClick={() => handlePartnershipResponse(true)}
          >
            ✅ Accept Partnership
          </Button>
          <Button
            variant="error"
            onClick={() => handlePartnershipResponse(false)}
          >
            ❌ Decline (Make them go solo)
          </Button>
        </div>
        <p style={{ marginTop: theme.spacing[3], fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
          Declining forces the captain to play solo and doubles the wager.
        </p>
      </Card>
    );
  };

  const renderDoubleOffer = () => (
    <Card
      variant="warning"
      style={{
        border: `4px solid ${theme.colors.warning}`,
        backgroundColor: '#fff8e1',
        maxWidth: '800px',
        margin: '0 auto',
        wordBreak: 'break-word',
        overflowWrap: 'break-word'
      }}
    >
      <h3 style={{ color: theme.colors.warning, marginBottom: theme.spacing[3] }}>💰 Double Opportunity</h3>
      <p style={{ fontSize: theme.typography.base, marginBottom: theme.spacing[4] }}>
        A double has been offered. Accepting will increase the stakes for this hole.
      </p>
      <div style={{ display: 'flex', justifyContent: 'center', gap: theme.spacing[3], flexWrap: 'wrap' }}>
        <Button
          variant="success"
          onClick={() => handleDoubleResponse(true)}
        >
          ✅ Accept Double
        </Button>
        <Button
          variant="error"
          onClick={() => handleDoubleResponse(false)}
        >
          ❌ Decline Double
        </Button>
      </div>
      <p style={{ marginTop: theme.spacing[3], fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
        Current wager: <strong>{currentWager} quarter{currentWager !== 1 ? 's' : ''}</strong>
      </p>
    </Card>
  );

  const renderDoubleDecision = () => (
    <Card
      variant="warning"
      style={{
        border: `4px solid ${theme.colors.primary}`,
        backgroundColor: '#f0f8ff',
        maxWidth: '800px',
        margin: '0 auto',
        wordBreak: 'break-word',
        overflowWrap: 'break-word'
      }}
    >
      <h3 style={{ color: theme.colors.primary, marginBottom: theme.spacing[3] }}>🎲 Offer a Double?</h3>
      <p style={{ fontSize: theme.typography.base, marginBottom: theme.spacing[4] }}>
        Your side can press the bet. Should we send the double back to our opponents?
      </p>
      <div style={{ display: 'flex', justifyContent: 'center', gap: theme.spacing[3], flexWrap: 'wrap' }}>
        <Button
          variant="warning"
          onClick={() => handleDoubleDecision(true)}
        >
          💥 Offer Double
        </Button>
        <Button
          variant="secondary"
          onClick={() => handleDoubleDecision(false)}
        >
          ⛳ Keep Playing This Wager
        </Button>
      </div>
    </Card>
  );

  const renderGenericDecision = () => (
    <Card variant="info" style={{
      maxWidth: '800px',
      margin: '0 auto',
      wordBreak: 'break-word',
      overflowWrap: 'break-word'
    }}>
      <h3 style={{ color: theme.colors.primary, marginBottom: theme.spacing[3] }}>🎮 Game in Progress</h3>
      {effectiveInteraction?.message && (
        <p style={{ marginBottom: theme.spacing[3], fontSize: theme.typography.base }}>{effectiveInteraction.message}</p>
      )}
      {!effectiveInteraction?.message && (
        <p style={{ fontSize: theme.typography.base, color: theme.colors.textSecondary }}>
          The game is progressing. Your next decision will appear when it's ready.
        </p>
      )}
    </Card>
  );

  const renderInteractionCard = () => {
    if (!effectiveInteraction) {
      return null;
    }

    // Normalize decision type to handle multiple naming conventions
    const decisionType = effectiveInteraction.type;

    // Captain choosing partner
    if (decisionType === 'captain_decision' || decisionType === 'captain_chooses_partner') {
      return renderCaptainDecision();
    }

    // Partnership response
    if (decisionType === 'partnership_response' || decisionType === 'partnership_request') {
      return renderPartnershipResponse();
    }

    // Double offer/response
    if (decisionType === 'double_offer') {
      return renderDoubleOffer();
    }

    if (decisionType === 'double_response' || decisionType === 'offer_double') {
      return renderDoubleDecision();
    }

    // Unknown decision type - show friendly fallback
    return renderGenericDecision();
  };

  const renderNextShotCard = () => {
    if (!shotAvailable) {
      return null;
    }

    if (effectiveInteraction) {
      return null;
    }

    return (
      <Card
        variant="success"
        style={{
          backgroundColor: '#f0fff4',
          border: `2px solid ${theme.colors.success}`,
          maxWidth: '800px',
          margin: '0 auto',
          wordBreak: 'break-word',
          overflowWrap: 'break-word'
        }}
      >
        <h3 style={{ marginBottom: theme.spacing[2] }}>⛳ Ready to Play</h3>
        <p style={{ marginBottom: theme.spacing[4] }}>
          Advance the simulation to see the next shot result and updated betting options.
        </p>
        <div style={{ textAlign: 'center' }}>
          <Button
            variant="primary"
            size="large"
            onClick={onNextShot}
          >
            ⛳ Play Next Shot
          </Button>
        </div>
      </Card>
    );
  };

  const renderHoleCompleteCard = () => {
    // Check if hole is complete
    const holeComplete = gameState?.hole_state?.hole_complete;

    if (!holeComplete) {
      return null;
    }

    // Don't show if there are interactions pending
    if (effectiveInteraction) {
      return null;
    }

    const currentHole = gameState?.current_hole || 1;
    const isLastHole = currentHole >= 18;

    return (
      <Card
        variant="success"
        style={{
          backgroundColor: '#fff8e1',
          border: `4px solid ${theme.colors.success}`,
          maxWidth: '800px',
          margin: '0 auto',
          wordBreak: 'break-word',
          overflowWrap: 'break-word'
        }}
      >
        <h3 style={{ color: theme.colors.success, marginBottom: theme.spacing[3] }}>
          🏁 Hole {currentHole} Complete!
        </h3>
        <p style={{ marginBottom: theme.spacing[4], fontSize: theme.typography.base }}>
          {isLastHole
            ? "That's the final hole! Ready to see the final results?"
            : `Great round on hole ${currentHole}! Ready to move to the next hole?`
          }
        </p>
        <div style={{ textAlign: 'center' }}>
          <Button
            variant="primary"
            size="large"
            onClick={onNextHole}
          >
            {isLastHole ? '🏆 View Final Results' : `⛳ Continue to Hole ${currentHole + 1}`}
          </Button>
        </div>
      </Card>
    );
  };

  const renderIdleCard = () => {
    return (
      <Card style={{
        maxWidth: '800px',
        margin: '0 auto',
        wordBreak: 'break-word',
        overflowWrap: 'break-word'
      }}>
        <h3 style={{ marginBottom: theme.spacing[2] }}>Waiting on the Field</h3>
        <p style={{ margin: 0, color: theme.colors.textSecondary }}>
          The robots are completing their swings. We'll surface your next decision as soon as it's available.
        </p>
      </Card>
    );
  };

  const interactionCard = renderInteractionCard();
  const holeCompleteCard = renderHoleCompleteCard();
  const nextShotCard = renderNextShotCard();

  // Show idle card only if no other cards are being displayed
  const idleCard = (!interactionCard && !holeCompleteCard && !nextShotCard) ? renderIdleCard() : null;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: theme.spacing[4],
        ...style,
      }}
    >
      {interactionCard}
      {holeCompleteCard}
      {nextShotCard}
      {idleCard}
    </div>
  );
};

export default SimulationDecisionPanel;
