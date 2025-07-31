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

const StrategicAnalysisWidget = ({ bettingAnalysis }) => {
  if (!bettingAnalysis) return null;

  const {
    shot_assessment,
    team_position,
    strategic_recommendations,
    computer_tendencies
  } = bettingAnalysis;

  const getQualityColor = (quality) => {
    switch (quality) {
      case 'excellent': return COLORS.success;
      case 'good': return '#4caf50';
      case 'average': return COLORS.warning;
      case 'poor': return '#ff5722';
      case 'terrible': return COLORS.error;
      default: return COLORS.muted;
    }
  };

  const getMomentumColor = (momentum) => {
    switch (momentum) {
      case 'positive': return COLORS.success;
      case 'neutral': return COLORS.warning;
      case 'negative': return COLORS.error;
      default: return COLORS.muted;
    }
  };

  return (
    <div style={{
      background: COLORS.card,
      borderRadius: 16,
      boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
      padding: 20,
      margin: '12px 0'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        marginBottom: 20
      }}>
        <div style={{
          background: COLORS.primary,
          color: 'white',
          width: 48,
          height: 48,
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 24
        }}>
          🧠
        </div>
        <div>
          <h3 style={{ margin: 0, color: COLORS.text }}>
            Strategic Analysis
          </h3>
          <div style={{ color: COLORS.muted, fontSize: 14 }}>
            AI-powered insights and recommendations
          </div>
        </div>
      </div>

      {/* Shot Assessment */}
      {shot_assessment && (
        <div style={{ marginBottom: 20 }}>
          <h4 style={{ margin: '0 0 12px 0', color: COLORS.text }}>
            🎯 Shot Assessment
          </h4>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: 12
          }}>
            <div style={{
              background: '#f8f9fa',
              padding: 12,
              borderRadius: 8,
              textAlign: 'center'
            }}>
              <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>
                Quality Rating
              </div>
              <div style={{
                fontSize: 16,
                fontWeight: 600,
                color: getQualityColor(shot_assessment.quality_rating)
              }}>
                {shot_assessment.quality_rating.toUpperCase()}
              </div>
            </div>

            <div style={{
              background: '#f8f9fa',
              padding: 12,
              borderRadius: 8,
              textAlign: 'center'
            }}>
              <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>
                Distance Remaining
              </div>
              <div style={{ fontSize: 16, fontWeight: 600, color: COLORS.text }}>
                {Math.round(shot_assessment.distance_remaining)} yds
              </div>
            </div>

            <div style={{
              background: '#f8f9fa',
              padding: 12,
              borderRadius: 8,
              textAlign: 'center'
            }}>
              <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>
                Strategic Value
              </div>
              <div style={{ fontSize: 16, fontWeight: 600, color: COLORS.text }}>
                {shot_assessment.strategic_value.toUpperCase()}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Team Position */}
      {team_position && (
        <div style={{ marginBottom: 20 }}>
          <h4 style={{ margin: '0 0 12px 0', color: COLORS.text }}>
            🏆 Team Position
          </h4>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: 12
          }}>
            <div style={{
              background: '#f8f9fa',
              padding: 12,
              borderRadius: 8,
              textAlign: 'center'
            }}>
              <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>
                Current Wager
              </div>
              <div style={{ fontSize: 16, fontWeight: 600, color: COLORS.text }}>
                {team_position.current_wager} quarters
              </div>
            </div>

            <div style={{
              background: '#f8f9fa',
              padding: 12,
              borderRadius: 8,
              textAlign: 'center'
            }}>
              <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>
                Potential Double
              </div>
              <div style={{ fontSize: 16, fontWeight: 600, color: COLORS.warning }}>
                {team_position.potential_double} quarters
              </div>
            </div>

            <div style={{
              background: '#f8f9fa',
              padding: 12,
              borderRadius: 8,
              textAlign: 'center'
            }}>
              <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>
                Momentum
              </div>
              <div style={{
                fontSize: 16,
                fontWeight: 600,
                color: getMomentumColor(team_position.momentum)
              }}>
                {team_position.momentum.toUpperCase()}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Strategic Recommendations */}
      {strategic_recommendations && strategic_recommendations.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <h4 style={{ margin: '0 0 12px 0', color: COLORS.text }}>
            💡 Strategic Recommendations
          </h4>
          <div style={{
            background: '#e3f2fd',
            border: `1px solid ${COLORS.primary}`,
            borderRadius: 8,
            padding: 16
          }}>
            {strategic_recommendations.map((recommendation, index) => (
              <div key={index} style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 8,
                marginBottom: index < strategic_recommendations.length - 1 ? 8 : 0
              }}>
                <span style={{ fontSize: 16, marginTop: 2 }}>•</span>
                <div style={{ fontSize: 14, lineHeight: 1.5, color: COLORS.text }}>
                  {recommendation}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Computer Tendencies */}
      {computer_tendencies && Object.keys(computer_tendencies).length > 0 && (
        <div>
          <h4 style={{ margin: '0 0 12px 0', color: COLORS.text }}>
            🤖 Computer Player Tendencies
          </h4>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: 12
          }}>
            {Object.entries(computer_tendencies).map(([playerId, tendencies]) => (
              <div key={playerId} style={{
                background: '#f8f9fa',
                padding: 12,
                borderRadius: 8,
                border: `1px solid ${COLORS.border}`
              }}>
                <div style={{ fontWeight: 600, color: COLORS.text, marginBottom: 8 }}>
                  {playerId}
                </div>
                
                <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>
                  <strong>Personality:</strong> {tendencies.personality}
                </div>
                
                <div style={{ fontSize: 12, color: COLORS.muted, marginBottom: 4 }}>
                  <strong>Betting Style:</strong> {tendencies.betting_style}
                </div>
                
                <div style={{ fontSize: 12, color: COLORS.muted }}>
                  <strong>Double Acceptance:</strong> {tendencies.double_acceptance}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Summary */}
      <div style={{
        marginTop: 20,
        padding: 16,
        background: '#f8f9fa',
        borderRadius: 8,
        border: `1px solid ${COLORS.border}`
      }}>
        <div style={{ fontSize: 14, color: COLORS.muted, marginBottom: 8 }}>
          <strong>💭 Analysis Summary:</strong>
        </div>
        <div style={{ fontSize: 14, color: COLORS.text, lineHeight: 1.5 }}>
          {shot_assessment?.quality_rating === 'terrible' && 
            "Opponent's poor shot creates a prime opportunity for aggressive betting."}
          {shot_assessment?.quality_rating === 'excellent' && 
            "Strong shot by opponent - consider conservative approach unless you have a clear advantage."}
          {shot_assessment?.quality_rating === 'average' && 
            "Standard situation - evaluate team strength and position before making betting decisions."}
          {!shot_assessment?.quality_rating && 
            "Analyze the current game state and player positions to make informed decisions."}
        </div>
      </div>
    </div>
  );
};

export default StrategicAnalysisWidget; 