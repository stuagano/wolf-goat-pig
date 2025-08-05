import React from 'react';
import { useTheme } from '../theme/Provider';
import { Card } from './ui';

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
  hoepfinger: '#9c27b0',
  vinnie: '#795548'
};

// Shot Result Panel
const ShotResultPanel = ({ shotResult }) => {
  const getShotQualityColor = (quality) => {
    switch (quality) {
      case 'excellent': return COLORS.success;
      case 'good': return '#4caf50';
      case 'average': return COLORS.warning;
      case 'poor': return '#ff5722';
      case 'terrible': return COLORS.error;
      default: return COLORS.muted;
    }
  };

  const getShotQualityIcon = (quality) => {
    switch (quality) {
      case 'excellent': return '🏆';
      case 'good': return '👍';
      case 'average': return '👌';
      case 'poor': return '👎';
      case 'terrible': return '💥';
      default: return '⚪';
    }
  };

  if (!shotResult) return null;

  return (
    <div style={{ marginBottom: 16 }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: 16, color: COLORS.text }}>
        🎯 Shot Analysis
      </h3>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
        gap: 12
      }}>
        <div style={{
          padding: 12,
          background: getShotQualityColor(shotResult.quality),
          color: '#fff',
          borderRadius: 8,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: 20, marginBottom: 4 }}>
            {getShotQualityIcon(shotResult.quality)}
          </div>
          <div style={{ fontSize: 12, textTransform: 'capitalize' }}>
            {shotResult.quality || 'Unknown'}
          </div>
        </div>
        <div style={{
          padding: 12,
          background: COLORS.card,
          border: `1px solid ${COLORS.border}`,
          borderRadius: 8,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: 18, fontWeight: 600, color: COLORS.primary }}>
            {shotResult.distance || 0}y
          </div>
          <div style={{ fontSize: 12, color: COLORS.muted }}>Distance</div>
        </div>
        <div style={{
          padding: 12,
          background: COLORS.card,
          border: `1px solid ${COLORS.border}`,
          borderRadius: 8,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: 18, fontWeight: 600, color: COLORS.accent }}>
            {shotResult.accuracy || 0}%
          </div>
          <div style={{ fontSize: 12, color: COLORS.muted }}>Accuracy</div>
        </div>
      </div>
    </div>
  );
};

// Betting Opportunities Panel
const BettingPanel = ({ opportunities = [] }) => {
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

  return (
    <div style={{ marginBottom: 16 }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: 16, color: COLORS.text }}>
        💰 Betting Opportunities
      </h3>
      {opportunities.length === 0 ? (
        <div style={{
          padding: 16,
          background: COLORS.card,
          border: `1px solid ${COLORS.border}`,
          borderRadius: 8,
          textAlign: 'center',
          color: COLORS.muted
        }}>
          No current betting opportunities
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {opportunities.map((opp, index) => (
            <div key={index} style={{
              padding: 12,
              background: COLORS.card,
              border: `1px solid ${COLORS.border}`,
              borderRadius: 8,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>
                  {opp.type || 'Side Bet'}
                </div>
                <div style={{ fontSize: 12, color: COLORS.muted }}>
                  {opp.description || 'Betting opportunity available'}
                </div>
              </div>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}>
                <span style={{ color: getRiskColor(opp.risk) }}>
                  {getRiskIcon(opp.risk)}
                </span>
                <span style={{ fontWeight: 600 }}>
                  ${opp.amount || 0}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Game State Panel
const GameStatePanel = ({ gameState, holeState }) => {
  if (!gameState || !holeState) return null;

  const getPhaseColor = (phase) => {
    switch (phase) {
      case 'regular': return COLORS.primary;
      case 'vinnie_variation': return COLORS.vinnie;
      case 'hoepfinger': return COLORS.hoepfinger;
      default: return COLORS.muted;
    }
  };

  const getPhaseIcon = (phase) => {
    switch (phase) {
      case 'regular': return '⛳';
      case 'vinnie_variation': return '🐺';
      case 'hoepfinger': return '🎯';
      default: return '🏌️';
    }
  };

  return (
    <div style={{ marginBottom: 16 }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: 16, color: COLORS.text }}>
        🎮 Game State
      </h3>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
        gap: 12
      }}>
        <div style={{
          padding: 12,
          background: getPhaseColor(holeState.phase),
          color: '#fff',
          borderRadius: 8,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: 20, marginBottom: 4 }}>
            {getPhaseIcon(holeState.phase)}
          </div>
          <div style={{ fontSize: 12, textTransform: 'capitalize' }}>
            {holeState.phase?.replace('_', ' ') || 'Regular'}
          </div>
        </div>
        <div style={{
          padding: 12,
          background: COLORS.card,
          border: `1px solid ${COLORS.border}`,
          borderRadius: 8,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: 18, fontWeight: 600, color: COLORS.primary }}>
            {holeState.hole_number || 1}
          </div>
          <div style={{ fontSize: 12, color: COLORS.muted }}>Hole</div>
        </div>
        <div style={{
          padding: 12,
          background: COLORS.card,
          border: `1px solid ${COLORS.border}`,
          borderRadius: 8,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: 18, fontWeight: 600, color: COLORS.accent }}>
            ${gameState.total_pot || 0}
          </div>
          <div style={{ fontSize: 12, color: COLORS.muted }}>Total Pot</div>
        </div>
      </div>
    </div>
  );
};

// Strategic Analysis Panel
const StrategyPanel = ({ analysis }) => {
  if (!analysis) return null;

  return (
    <div style={{ marginBottom: 16 }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: 16, color: COLORS.text }}>
        🧠 Strategic Analysis
      </h3>
      <div style={{
        padding: 16,
        background: COLORS.card,
        border: `1px solid ${COLORS.border}`,
        borderRadius: 8
      }}>
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>Recommended Play:</div>
          <div style={{ color: COLORS.primary }}>
            {analysis.recommendation || 'Play conservatively'}
          </div>
        </div>
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>Key Factors:</div>
          <div style={{ fontSize: 14, color: COLORS.muted }}>
            {analysis.factors?.join(', ') || 'Position, risk tolerance, pot odds'}
          </div>
        </div>
        {analysis.confidence && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}>
            <span style={{ fontSize: 14, fontWeight: 600 }}>Confidence:</span>
            <div style={{
              flex: 1,
              height: 8,
              background: COLORS.border,
              borderRadius: 4,
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${analysis.confidence}%`,
                height: '100%',
                background: analysis.confidence > 70 ? COLORS.success : 
                          analysis.confidence > 40 ? COLORS.warning : COLORS.error
              }} />
            </div>
            <span style={{ fontSize: 14 }}>{analysis.confidence}%</span>
          </div>
        )}
      </div>
    </div>
  );
};

// Main Dashboard Component
const GameDashboard = ({ 
  gameState, 
  holeState, 
  shotResult, 
  bettingOpportunities, 
  strategicAnalysis 
}) => {
  const theme = useTheme();

  return (
    <Card style={{ padding: 0 }}>
      <div style={{
        padding: 20,
        background: theme.colors.background,
        borderRadius: 12
      }}>
        <h2 style={{
          margin: '0 0 20px 0',
          fontSize: 20,
          color: theme.colors.primary,
          textAlign: 'center'
        }}>
          🎮 Game Dashboard
        </h2>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: window.innerWidth > 768 ? 'repeat(2, 1fr)' : '1fr',
          gap: 20
        }}>
          <div>
            <GameStatePanel gameState={gameState} holeState={holeState} />
            <ShotResultPanel shotResult={shotResult} />
          </div>
          
          <div>
            <BettingPanel opportunities={bettingOpportunities} />
            <StrategyPanel analysis={strategicAnalysis} />
          </div>
        </div>
      </div>
    </Card>
  );
};

export default GameDashboard;