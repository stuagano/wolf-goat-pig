import React from 'react';
import { useTheme } from '../../theme/Provider';
import { Card, Button } from '../ui';

const PokerBettingPanel = ({
  pokerState = {},
  bettingOptions = [],
  onBettingAction,
  currentPlayer,
  disabled = false
}) => {
  const theme = useTheme();
  
  // Default poker state values
  const {
    pot_size = 0,
    base_bet = 1,
    current_bet = 1,
    betting_phase = 'pre-flop',
    doubled = false,
    players_in = 4,
    action_on = null,
    can_raise = true,
    can_fold = true
  } = pokerState;
  
  // Phase colors and descriptions
  const phaseInfo = {
    'pre-flop': { color: theme.colors.warning, desc: 'Before Tee Shots', icon: '🎯' },
    'flop': { color: theme.colors.info, desc: 'After Tee Shots', icon: '⛳' },
    'turn': { color: theme.colors.secondary, desc: 'Mid-Hole', icon: '🏌️' },
    'river': { color: theme.colors.success, desc: 'Near Completion', icon: '🏁' }
  };
  
  const currentPhase = phaseInfo[betting_phase] || phaseInfo['pre-flop'];
  
  return (
    <Card>
      {/* Poker Table Header */}
      <div style={{
        background: `linear-gradient(135deg, #1a4d2e 0%, #0d2818 100%)`,
        color: 'white',
        padding: 16,
        borderRadius: '8px 8px 0 0',
        marginBottom: 16
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: 20 }}>
              🎰 Texas Hold'em Style Betting
            </h3>
            <p style={{ margin: '4px 0 0 0', fontSize: 12, opacity: 0.9 }}>
              Wolf-Goat-Pig Poker Hybrid
            </p>
          </div>
          
          {/* Pot Size Display */}
          <div style={{
            background: 'rgba(255, 215, 0, 0.2)',
            border: '2px solid gold',
            borderRadius: 8,
            padding: '8px 16px',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: 12, opacity: 0.8 }}>POT</div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: 'gold' }}>
              ${pot_size}
            </div>
          </div>
        </div>
      </div>
      
      {/* Betting Phase Indicator */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        marginBottom: 16
      }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
          padding: '8px 16px',
          background: `${currentPhase.color}20`,
          border: `2px solid ${currentPhase.color}`,
          borderRadius: 20
        }}>
          <span style={{ fontSize: 20 }}>{currentPhase.icon}</span>
          <div>
            <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
              BETTING PHASE
            </div>
            <div style={{ fontWeight: 'bold', color: currentPhase.color }}>
              {betting_phase.toUpperCase()} - {currentPhase.desc}
            </div>
          </div>
        </div>
      </div>
      
      {/* Game Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: 12,
        marginBottom: 16
      }}>
        <div style={{
          textAlign: 'center',
          padding: 12,
          background: theme.colors.background,
          borderRadius: 8,
          border: `1px solid ${theme.colors.border}`
        }}>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
            Base Bet
          </div>
          <div style={{ fontSize: 18, fontWeight: 'bold' }}>
            ${base_bet}
          </div>
        </div>
        
        <div style={{
          textAlign: 'center',
          padding: 12,
          background: doubled ? `${theme.colors.error}10` : theme.colors.background,
          borderRadius: 8,
          border: `1px solid ${doubled ? theme.colors.error : theme.colors.border}`
        }}>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
            Current Bet
          </div>
          <div style={{ 
            fontSize: 18, 
            fontWeight: 'bold',
            color: doubled ? theme.colors.error : theme.colors.text
          }}>
            ${current_bet} {doubled && '(2x)'}
          </div>
        </div>
        
        <div style={{
          textAlign: 'center',
          padding: 12,
          background: theme.colors.background,
          borderRadius: 8,
          border: `1px solid ${theme.colors.border}`
        }}>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
            Players In
          </div>
          <div style={{ fontSize: 18, fontWeight: 'bold' }}>
            {players_in}
          </div>
        </div>
      </div>
      
      {/* Action Indicator */}
      {action_on && (
        <div style={{
          padding: 12,
          background: `${theme.colors.primary}10`,
          border: `1px solid ${theme.colors.primary}`,
          borderRadius: 8,
          textAlign: 'center',
          marginBottom: 16
        }}>
          <div style={{ fontSize: 14, color: theme.colors.primary }}>
            Action on: <strong>{action_on === currentPlayer ? 'YOU' : action_on}</strong>
          </div>
        </div>
      )}
      
      {/* Betting Options */}
      {bettingOptions.length > 0 && (
        <div>
          <h4 style={{ marginBottom: 12, fontSize: 14, color: theme.colors.textSecondary }}>
            YOUR OPTIONS:
          </h4>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12 }}>
            {bettingOptions.map((option, index) => {
              // Style different actions
              let buttonStyle = 'primary';
              if (option.action === 'fold' || option.action === 'concede') buttonStyle = 'error';
              if (option.action === 'check') buttonStyle = 'secondary';
              if (option.action === 'raise' || option.action === 'offer_double') buttonStyle = 'warning';
              if (option.action === 'go_solo' || option.action === 'all_in') buttonStyle = 'success';
              
              return (
                <Button
                  key={option.action}
                  variant={buttonStyle}
                  onClick={() => onBettingAction(option.action, option)}
                  disabled={disabled}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    padding: 12,
                    height: 'auto'
                  }}
                >
                  <div style={{ fontSize: 20, marginBottom: 4 }}>
                    {option.icon}
                  </div>
                  <div style={{ fontSize: 14, fontWeight: 'bold' }}>
                    {option.label}
                  </div>
                  {option.amount && (
                    <div style={{ fontSize: 12, opacity: 0.9, marginTop: 2 }}>
                      ${option.amount}
                    </div>
                  )}
                  {option.multiplier && (
                    <div style={{ fontSize: 11, opacity: 0.8, marginTop: 2 }}>
                      {option.multiplier}x stakes
                    </div>
                  )}
                  <div style={{ fontSize: 10, opacity: 0.7, marginTop: 4 }}>
                    {option.description}
                  </div>
                </Button>
              );
            })}
          </div>
        </div>
      )}
      
      {/* No actions available */}
      {bettingOptions.length === 0 && !disabled && (
        <div style={{
          padding: 20,
          textAlign: 'center',
          color: theme.colors.textSecondary
        }}>
          <p>Waiting for other players...</p>
        </div>
      )}
    </Card>
  );
};

export default PokerBettingPanel;