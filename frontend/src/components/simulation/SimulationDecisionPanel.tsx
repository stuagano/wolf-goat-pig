// @ts-nocheck
import React, { useMemo } from 'react';
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

interface GameState {
  players?: Player[];
  captain_id?: string;
  base_wager?: number;
  betting?: BettingState;
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
  [key: string]: any;
}

interface SimulationDecisionPanelProps {
  gameState?: GameState | null;
  interactionNeeded?: InteractionNeeded | null;
  onDecision?: (payload: Record<string, unknown>) => void;
  onNextShot?: () => void;
  hasNextShot?: boolean | null;
  style?: React.CSSProperties;
}

const SimulationDecisionPanel: React.FC<SimulationDecisionPanelProps> = ({
  gameState,
  interactionNeeded,
  onDecision,
  onNextShot,
  hasNextShot,
  style
}) => {
  const theme = useTheme();

  const effectiveInteraction = interactionNeeded ?? (gameState as any)?.interactionNeeded ?? null;
  const shotAvailable = hasNextShot ?? (gameState as any)?.hasNextShot ?? false;

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

  const handleDecision = (payload: Record<string, unknown>) => {
    if (onDecision) {
      onDecision(payload);
    }
  };

  const handlePartnerInvite = (partnerId: string) => {
    handleDecision({
      action: 'request_partner',
      requested_partner: partnerId,
      player_id: captainId,
      captain_id: captainId,
    });
  };

  const handleGoSolo = () => {
    handleDecision({
      action: 'go_solo',
      player_id: captainId,
      captain_id: captainId,
    });
  };

  const handleKeepWatching = () => {
    handleDecision({
      action: 'keep_watching',
      player_id: captainId,
    });
  };

  const handlePartnershipResponse = (accepted: boolean) => {
    handleDecision({
      accept_partnership: accepted,
      partner_id: effectiveInteraction?.captain_id ?? captainId,
    });
  };

  const handleDoubleResponse = (accepted: boolean) => {
    handleDecision({
      accept_double: accepted,
    });
  };

  const handleDoubleDecision = (offer: boolean) => {
    handleDecision({
      offer_double: offer,
      player_id: captainId,
    });
  };

  const renderCaptainDecision = () => {
    const captainName = players.find(player => player.id === captainId)?.name || 'You';

    return (
      <Card
        variant="warning"
        style={{
          border: `4px solid ${theme.colors.primary}`,
          backgroundColor: '#f0f8ff',
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
    <Card variant="warning">
      <h3 style={{ color: theme.colors.warning, marginBottom: theme.spacing[3] }}>Decision Required</h3>
      {effectiveInteraction?.message && (
        <p style={{ marginBottom: theme.spacing[3] }}>{effectiveInteraction.message}</p>
      )}
      <pre
        style={{
          backgroundColor: theme.colors.background,
          padding: theme.spacing[3],
          borderRadius: theme.borderRadius.base,
          overflowX: 'auto',
          fontFamily: theme.typography.fontMono,
          fontSize: theme.typography.xs,
        }}
      >
        {JSON.stringify(effectiveInteraction, null, 2)}
      </pre>
    </Card>
  );

  const renderInteractionCard = () => {
    if (!effectiveInteraction) {
      return null;
    }

    switch (effectiveInteraction.type) {
      case 'captain_decision':
        return renderCaptainDecision();
      case 'partnership_response':
        return renderPartnershipResponse();
      case 'double_offer':
        return renderDoubleOffer();
      case 'double_response':
        return renderDoubleDecision();
      default:
        return renderGenericDecision();
    }
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
            🏌️ Play Next Shot
          </Button>
        </div>
      </Card>
    );
  };

  const renderIdleCard = () => {
    if (effectiveInteraction || shotAvailable) {
      return null;
    }

    return (
      <Card>
        <h3 style={{ marginBottom: theme.spacing[2] }}>Waiting on the Field</h3>
        <p style={{ margin: 0, color: theme.colors.textSecondary }}>
          The robots are completing their swings. We'll surface your next decision as soon as it's available.
        </p>
      </Card>
    );
  };

  const interactionCard = renderInteractionCard();
  const nextShotCard = renderNextShotCard();
  const idleCard = renderIdleCard();

  if (!interactionCard && !nextShotCard && !idleCard) {
    return null;
  }

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
      {nextShotCard}
      {idleCard}
    </div>
  );
};

export default SimulationDecisionPanel;
