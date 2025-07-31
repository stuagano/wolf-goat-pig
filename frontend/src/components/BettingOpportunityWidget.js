import React from 'react';

const COLORS = {
  primary: '#1976d2',
  accent: '#00bcd4',
  warning: '#ff9800',
  error: '#d32f2f',
  success: '#388e3c',
  bg: '#f9fafe',
  card: '#fff',
  border: '#e0e0e0',
  text: '#222',
  muted: '#888',
};

const getRiskColor = (risk) => {
  switch (risk) {
    case 'low': return COLORS.success;
    case 'medium': return COLORS.warning;
    case 'high': return COLORS.error;
    default: return COLORS.muted;
  }
};

const getRiskIcon = (risk) => {
  switch (risk) {
    case 'low': return '🟢';
    case 'medium': return '🟡';
    case 'high': return '🔴';
    default: return '⚪';
  }
};

const BettingOpportunityWidget = ({ bettingOpportunity, onDecision }) => {
  if (!bettingOpportunity) return null;

  const {
    opportunity_type,
    message,
    options,
    probability_analysis,
    recommended_action,
    risk_assessment
  } = bettingOpportunity;

  const riskColor = getRiskColor(risk_assessment);
  const riskIcon = getRiskIcon(risk_assessment);

  return (
    <div style={{
      background: COLORS.card,
      borderRadius: 16,
      boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
      padding: 20,
      margin: '12px 0',
      border: `2px solid ${riskColor}`,
      position: 'relative'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 16
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 24 }}>💰</span>
          <h3 style={{ margin: 0, color: COLORS.text }}>
            Betting Opportunity
          </h3>
        </div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          background: riskColor,
          color: 'white',
          padding: '4px 12px',
          borderRadius: 20,
          fontSize: 14,
          fontWeight: 600
        }}>
          <span>{riskIcon}</span>
          {risk_assessment} Risk
        </div>
      </div>

      {/* Message */}
      <div style={{
        background: '#f8f9fa',
        padding: 16,
        borderRadius: 8,
        marginBottom: 16,
        fontSize: 16,
        lineHeight: 1.5,
        color: COLORS.text
      }}>
        {message}
      </div>

      {/* Probability Analysis */}
      {probability_analysis && (
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ margin: '0 0 12px 0', color: COLORS.text }}>
            📊 Probability Analysis
          </h4>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: 12
          }}>
            {Object.entries(probability_analysis).map(([key, value]) => (
              <div key={key} style={{
                background: '#f8f9fa',
                padding: 12,
                borderRadius: 8,
                textAlign: 'center'
              }}>
                <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>
                  {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </div>
                <div style={{ fontSize: 16, fontWeight: 600, color: COLORS.text }}>
                  {typeof value === 'number' ? (value * 100).toFixed(1) + '%' : value}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Action */}
      <div style={{
        background: COLORS.primary,
        color: 'white',
        padding: 12,
        borderRadius: 8,
        marginBottom: 16,
        display: 'flex',
        alignItems: 'center',
        gap: 8
      }}>
        <span style={{ fontSize: 18 }}>💡</span>
        <div>
          <div style={{ fontSize: 12, opacity: 0.9 }}>Recommended Action</div>
          <div style={{ fontSize: 16, fontWeight: 600 }}>
            {recommended_action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div style={{
        display: 'flex',
        gap: 12,
        flexWrap: 'wrap'
      }}>
        {options.map((option) => (
          <button
            key={option}
            onClick={() => onDecision(option)}
            style={{
              background: option === recommended_action ? COLORS.success : COLORS.primary,
              color: 'white',
              border: 'none',
              borderRadius: 8,
              padding: '12px 20px',
              fontWeight: 600,
              fontSize: 14,
              cursor: 'pointer',
              transition: 'all 0.2s',
              flex: 1,
              minWidth: 120
            }}
            onMouseOver={(e) => {
              e.target.style.transform = 'translateY(-2px)';
              e.target.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
            }}
            onMouseOut={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = 'none';
            }}
          >
            {option === 'offer_double' && '💰 Offer Double'}
            {option === 'pass' && '⏭️ Pass'}
            {option === 'accept' && '✅ Accept'}
            {option === 'decline' && '❌ Decline'}
            {!['offer_double', 'pass', 'accept', 'decline'].includes(option) && 
              option.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </button>
        ))}
      </div>

      {/* Risk Assessment Details */}
      <div style={{
        marginTop: 16,
        padding: 12,
        background: '#f8f9fa',
        borderRadius: 8,
        fontSize: 14,
        color: COLORS.muted
      }}>
        <strong>Risk Level:</strong> {risk_assessment.toUpperCase()} - 
        {risk_assessment === 'low' && ' Good opportunity with minimal risk'}
        {risk_assessment === 'medium' && ' Moderate risk, consider your position'}
        {risk_assessment === 'high' && ' High risk, proceed with caution'}
      </div>
    </div>
  );
};

export default BettingOpportunityWidget; 