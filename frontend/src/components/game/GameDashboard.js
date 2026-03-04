import React from 'react';
import { useTheme } from '../theme/Provider';
import { Card } from './ui';
import {
  UI_COLORS,
  getShotQualityColor,
  getShotQualityIcon,
  getRiskColor,
  getRiskIcon,
  getPhaseColor,
  getPhaseIcon
} from '../constants/colors';

// Shot Result Panel
const ShotResultPanel = ({ shotResult }) => {

  if (!shotResult) return null;

  return (
    <div style={{ marginBottom: 16 }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: 16, color: UI_COLORS.text }}>
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
          background: UI_COLORS.card,
          border: `1px solid ${UI_COLORS.border}`,
          borderRadius: 8,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: 18, fontWeight: 600, color: UI_COLORS.primary }}>
            {shotResult.distance || 0}y
          </div>
          <div style={{ fontSize: 12, color: UI_COLORS.muted }}>Distance</div>
        </div>
        <div style={{
          padding: 12,
          background: UI_COLORS.card,
          border: `1px solid ${UI_COLORS.border}`,
          borderRadius: 8,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: 18, fontWeight: 600, color: UI_COLORS.accent }}>
            {shotResult.accuracy || 0}%
          </div>
          <div style={{ fontSize: 12, color: UI_COLORS.muted }}>Accuracy</div>
        </div>
      </div>
    </div>
  );
};

// Betting Opportunities Panel
const BettingPanel = ({ opportunities = [] }) => {
  return (
    <div style={{ marginBottom: 16 }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: 16, color: UI_COLORS.text }}>
        💰 Betting Opportunities
      </h3>
      {opportunities.length === 0 ? (
        <div style={{
          padding: 16,
          background: UI_COLORS.card,
          border: `1px solid ${UI_COLORS.border}`,
          borderRadius: 8,
          textAlign: 'center',
          color: UI_COLORS.muted
        }}>
          No current betting opportunities
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {opportunities.map((opp, index) => (
            <div key={index} style={{
              padding: 12,
              background: UI_COLORS.card,
              border: `1px solid ${UI_COLORS.border}`,
              borderRadius: 8,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                <div style={{ fontWeight: 600, marginBottom: 4 }}>
                  {opp.type || 'Side Bet'}
                </div>
                <div style={{ fontSize: 12, color: UI_COLORS.muted }}>
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

  return (
    <div style={{ marginBottom: 16 }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: 16, color: UI_COLORS.text }}>
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
          background: UI_COLORS.card,
          border: `1px solid ${UI_COLORS.border}`,
          borderRadius: 8,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: 18, fontWeight: 600, color: UI_COLORS.primary }}>
            {holeState.hole_number || 1}
          </div>
          <div style={{ fontSize: 12, color: UI_COLORS.muted }}>Hole</div>
        </div>
        <div style={{
          padding: 12,
          background: UI_COLORS.card,
          border: `1px solid ${UI_COLORS.border}`,
          borderRadius: 8,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: 18, fontWeight: 600, color: UI_COLORS.accent }}>
            ${gameState.total_pot || 0}
          </div>
          <div style={{ fontSize: 12, color: UI_COLORS.muted }}>Total Pot</div>
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
      <h3 style={{ margin: '0 0 12px 0', fontSize: 16, color: UI_COLORS.text }}>
        🧠 Strategic Analysis
      </h3>
      <div style={{
        padding: 16,
        background: UI_COLORS.card,
        border: `1px solid ${UI_COLORS.border}`,
        borderRadius: 8
      }}>
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>Recommended Play:</div>
          <div style={{ color: UI_COLORS.primary }}>
            {analysis.recommendation || 'Play conservatively'}
          </div>
        </div>
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>Key Factors:</div>
          <div style={{ fontSize: 14, color: UI_COLORS.muted }}>
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
              background: UI_COLORS.border,
              borderRadius: 4,
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${analysis.confidence}%`,
                height: '100%',
                background: analysis.confidence > 70 ? UI_COLORS.success :
                          analysis.confidence > 40 ? UI_COLORS.warning : UI_COLORS.error
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