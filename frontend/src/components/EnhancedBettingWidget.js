import React, { useState, useEffect } from 'react';
import { useTheme } from '../theme/Provider';
import {
  getRiskColor,
  getRiskIcon,
  getActionIcon,
  getActionDescription,
  calculateExpectedValue
} from '../utils';

const EnhancedBettingWidget = ({ gameState, bettingOpportunity, onBettingAction }) => {
  const theme = useTheme();
  const [selectedAction, setSelectedAction] = useState(null);
  const [showRecommendation, setShowRecommendation] = useState(true);
  const [animatingAction, setAnimatingAction] = useState(null);

  // Reset selection when new betting opportunity appears
  useEffect(() => {
    setSelectedAction(null);
    setShowRecommendation(true);
  }, [bettingOpportunity]);

  if (!bettingOpportunity && !gameState?.betting_opportunity) {
    return (
      <div style={{
        background: theme.colors.card,
        borderRadius: 16,
        padding: 24,
        margin: '12px 0',
        boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
        textAlign: 'center',
        border: `2px solid ${theme.colors.border}`
      }}>
        <div style={{
          fontSize: 48,
          marginBottom: 12,
          opacity: 0.5
        }}>
          ⏳
        </div>
        <h3 style={{ 
          margin: '0 0 8px 0', 
          color: theme.colors.textSecondary,
          fontSize: 18
        }}>
          Waiting for Betting Opportunity
        </h3>
        <p style={{ 
          margin: 0, 
          color: theme.colors.textSecondary,
          fontSize: 14
        }}>
          Teams will form and betting opportunities will appear here
        </p>
      </div>
    );
  }

  const opportunity = bettingOpportunity || gameState.betting_opportunity;
  
  const handleActionClick = async (action) => {
    setSelectedAction(action);
    setAnimatingAction(action);
    
    // Add a brief delay for visual feedback
    setTimeout(async () => {
      if (onBettingAction) {
        await onBettingAction(action);
      }
      setAnimatingAction(null);
    }, 200);
  };

  // Imported helper functions now used from ../utils/bettingHelpers

  return (
    <div style={{
      background: 'linear-gradient(135deg, #ffffff, #f8f9fa)',
      borderRadius: 16,
      padding: 24,
      margin: '12px 0',
      boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
      border: `3px solid ${getRiskColor(opportunity.risk_assessment)}`,
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Risk indicator background */}
      <div style={{
        position: 'absolute',
        top: 0,
        right: 0,
        width: 80,
        height: 80,
        background: `linear-gradient(135deg, ${getRiskColor(opportunity.risk_assessment)}20, ${getRiskColor(opportunity.risk_assessment)}10)`,
        borderRadius: '0 16px 0 80px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 24
      }}>
        {getRiskIcon(opportunity.risk_assessment)}
      </div>

      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: 20
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
            <div style={{
              background: 'linear-gradient(135deg, #FF6B35, #F7931E)',
              color: 'white',
              width: 48,
              height: 48,
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 24,
              boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
            }}>
              💰
            </div>
            <div>
              <h2 style={{ 
                margin: 0, 
                color: theme.colors.primary,
                fontSize: 22,
                fontWeight: 700
              }}>
                Betting Decision
              </h2>
              <div style={{ 
                fontSize: 14, 
                color: theme.colors.textSecondary 
              }}>
                Current Wager: {gameState?.holeState?.betting?.current_wager || 1} quarters
              </div>
            </div>
          </div>
        </div>
        
        <div style={{
          background: getRiskColor(opportunity.risk_assessment),
          color: 'white',
          borderRadius: 20,
          padding: '6px 12px',
          fontSize: 12,
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          marginRight: 60 // Space for risk icon
        }}>
          {opportunity.risk_assessment} Risk
        </div>
      </div>

      {/* Situation Message */}
      <div style={{
        background: 'linear-gradient(135deg, #e3f2fd, #f3e5f5)',
        borderRadius: 12,
        padding: 16,
        marginBottom: 20,
        border: '1px solid rgba(33, 150, 243, 0.2)'
      }}>
        <div style={{
          fontSize: 16,
          lineHeight: 1.5,
          color: theme.colors.textPrimary,
          fontWeight: 500
        }}>
          {opportunity.message}
        </div>
      </div>

      {/* Probability Analysis */}
      {opportunity.probability_analysis && (
        <div style={{ marginBottom: 20 }}>
          <h4 style={{ 
            margin: '0 0 12px 0', 
            color: theme.colors.primary,
            fontSize: 16,
            fontWeight: 600
          }}>
            📊 Situation Analysis
          </h4>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
            gap: 12
          }}>
            {Object.entries(opportunity.probability_analysis).map(([key, value]) => (
              <div key={key} style={{
                background: '#f8f9fa',
                borderRadius: 8,
                padding: 12,
                textAlign: 'center',
                border: '1px solid rgba(0,0,0,0.08)'
              }}>
                <div style={{ 
                  fontSize: 11, 
                  color: theme.colors.textSecondary, 
                  marginBottom: 4,
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}>
                  {key.replace(/_/g, ' ')}
                </div>
                <div style={{ 
                  fontSize: 18, 
                  fontWeight: 700, 
                  color: theme.colors.primary 
                }}>
                  {typeof value === 'number' ? 
                    (value < 1 ? `${(value * 100).toFixed(0)}%` : value.toFixed(1)) : 
                    value}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Action */}
      {showRecommendation && opportunity.recommended_action && (
        <div style={{
          background: 'linear-gradient(135deg, #4CAF50, #45a049)',
          color: 'white',
          borderRadius: 12,
          padding: 16,
          marginBottom: 20,
          position: 'relative',
          overflow: 'hidden'
        }}>
          <div style={{
            position: 'absolute',
            top: -10,
            right: -10,
            width: 40,
            height: 40,
            background: 'rgba(255,255,255,0.2)',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            💡
          </div>
          
          <div style={{ fontSize: 12, opacity: 0.9, marginBottom: 4 }}>
            AI RECOMMENDATION
          </div>
          <div style={{ 
            fontSize: 16, 
            fontWeight: 700,
            marginBottom: 8
          }}>
            {getActionIcon(opportunity.recommended_action)} {opportunity.recommended_action.replace(/_/g, ' ').toUpperCase()}
          </div>
          <div style={{ 
            fontSize: 14, 
            opacity: 0.9,
            lineHeight: 1.3
          }}>
            {getActionDescription(opportunity.recommended_action)}
          </div>
          
          {/* Expected Value */}
          {opportunity.probability_analysis && (
            <div style={{ 
              fontSize: 12, 
              opacity: 0.8, 
              marginTop: 8,
              fontStyle: 'italic'
            }}>
              Expected Value: {calculateExpectedValue(opportunity.recommended_action, opportunity.probability_analysis, gameState)?.toFixed(1) || 'N/A'} quarters
            </div>
          )}
          
          <button
            onClick={() => setShowRecommendation(false)}
            style={{
              position: 'absolute',
              top: 8,
              right: 8,
              background: 'rgba(255,255,255,0.2)',
              border: 'none',
              color: 'white',
              borderRadius: '50%',
              width: 24,
              height: 24,
              cursor: 'pointer',
              fontSize: 12
            }}
          >
            ×
          </button>
        </div>
      )}

      {/* Action Buttons */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: opportunity.options?.length > 2 ? 'repeat(auto-fit, minmax(140px, 1fr))' : 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: 12
      }}>
        {opportunity.options?.map((action) => {
          const isRecommended = action === opportunity.recommended_action;
          const isSelected = selectedAction === action;
          const isAnimating = animatingAction === action;
          const expectedValue = calculateExpectedValue(action, opportunity.probability_analysis, gameState);
          
          return (
            <button
              key={action}
              onClick={() => handleActionClick(action)}
              disabled={isAnimating}
              style={{
                background: isRecommended ? 
                  'linear-gradient(135deg, #4CAF50, #45a049)' : 
                  isSelected ?
                  'linear-gradient(135deg, #2196F3, #1976D2)' :
                  'linear-gradient(135deg, #fff, #f5f5f5)',
                color: isRecommended || isSelected ? 'white' : theme.colors.textPrimary,
                border: `2px solid ${isRecommended ? '#4CAF50' : isSelected ? '#2196F3' : theme.colors.border}`,
                borderRadius: 12,
                padding: '16px 12px',
                fontWeight: 700,
                fontSize: 14,
                cursor: isAnimating ? 'not-allowed' : 'pointer',
                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                position: 'relative',
                overflow: 'hidden',
                transform: isAnimating ? 'scale(0.95)' : isSelected ? 'scale(1.02)' : 'scale(1)',
                boxShadow: isRecommended ? 
                  '0 8px 24px rgba(76, 175, 80, 0.3)' : 
                  isSelected ? 
                  '0 8px 24px rgba(33, 150, 243, 0.3)' : 
                  '0 2px 8px rgba(0,0,0,0.1)',
                opacity: isAnimating ? 0.7 : 1
              }}
              onMouseOver={(e) => {
                if (!isAnimating) {
                  e.target.style.transform = 'scale(1.05) translateY(-2px)';
                  e.target.style.boxShadow = '0 12px 32px rgba(0,0,0,0.2)';
                }
              }}
              onMouseOut={(e) => {
                if (!isAnimating) {
                  e.target.style.transform = isSelected ? 'scale(1.02)' : 'scale(1)';
                  e.target.style.boxShadow = isRecommended ? 
                    '0 8px 24px rgba(76, 175, 80, 0.3)' : 
                    isSelected ? 
                    '0 8px 24px rgba(33, 150, 243, 0.3)' : 
                    '0 2px 8px rgba(0,0,0,0.1)';
                }
              }}
            >
              {/* Loading animation */}
              {isAnimating && (
                <div style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  background: 'rgba(255,255,255,0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <div style={{
                    width: 20,
                    height: 20,
                    border: '2px solid rgba(255,255,255,0.3)',
                    borderTop: '2px solid white',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }} />
                </div>
              )}
              
              <div style={{ marginBottom: 4 }}>
                <span style={{ fontSize: 18, marginRight: 6 }}>
                  {getActionIcon(action)}
                </span>
                {action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </div>
              
              <div style={{ 
                fontSize: 11, 
                opacity: 0.8,
                lineHeight: 1.2
              }}>
                {getActionDescription(action)}
              </div>
              
              {expectedValue !== null && (
                <div style={{ 
                  fontSize: 10, 
                  opacity: 0.7,
                  marginTop: 4,
                  fontStyle: 'italic'
                }}>
                  EV: {expectedValue > 0 ? '+' : ''}{expectedValue.toFixed(1)}q
                </div>
              )}
              
              {isRecommended && (
                <div style={{
                  position: 'absolute',
                  top: 4,
                  right: 4,
                  background: 'rgba(255,255,255,0.3)',
                  borderRadius: '50%',
                  width: 20,
                  height: 20,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 10
                }}>
                  ⭐
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Reasoning */}
      {opportunity.reasoning && (
        <div style={{
          marginTop: 16,
          padding: 12,
          background: 'rgba(33, 150, 243, 0.08)',
          borderRadius: 8,
          borderLeft: `4px solid ${theme.colors.accent}`,
          fontSize: 14,
          color: theme.colors.textSecondary,
          fontStyle: 'italic'
        }}>
          <strong>AI Reasoning:</strong> {opportunity.reasoning}
        </div>
      )}

      {/* Animation styles injected into head */}
      <style dangerouslySetInnerHTML={{
        __html: `
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `
      }} />
    </div>
  );
};

export default EnhancedBettingWidget;