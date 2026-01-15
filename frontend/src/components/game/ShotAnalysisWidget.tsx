import React, { useState, useEffect, ChangeEvent } from 'react';
import { useTheme } from '../../theme/Provider';
import { useShotAnalysis } from '../../hooks';
import { Button, Input, Select } from '../ui';

interface Player {
  id: string;
  name: string;
  handicap: number | string;
  is_authenticated?: boolean;
}

interface PlayerStanding {
  quarters: number;
}

interface AnalysisData {
  recommended_shot: {
    type: string;
    success_rate: string;
    risk_level: string;
    expected_value: number;
  };
  player_style: {
    profile: string;
    description: string;
  };
  gto_recommendation: {
    type: string;
  };
  strategic_advice: string[];
}

interface ShotAnalysisWidgetProps {
  holeNumber: number;
  players: Player[];
  captainId: string | null;
  teamMode: string;
  playerStandings: Record<string, PlayerStanding>;
  initialDistance?: number;
}

/**
 * Integrated Shot Analysis Widget for decision support during gameplay
 */
const ShotAnalysisWidget: React.FC<ShotAnalysisWidgetProps> = ({ 
  holeNumber, 
  players, 
  captainId, 
  teamMode, 
  playerStandings,
  initialDistance = 150
}) => {
  const theme = useTheme();
  const { analysis, loading, error, analyzeShot } = useShotAnalysis();
  
  const [formData, setFormData] = useState({
    lie_type: 'fairway',
    distance_to_pin: initialDistance,
    player_handicap: 10.0,
    hole_number: holeNumber,
    team_situation: teamMode === 'solo' ? 'solo' : 'partners',
    score_differential: 0,
    opponent_styles: [] as string[]
  });

  // Update form data when props change
  useEffect(() => {
    // Determine captain's handicap for analysis
    const captain = players.find(p => p.id === captainId) || players[0];
    const handicap = captain ? (parseFloat(String(captain.handicap)) || 10.0) : 10.0;
    
    // Calculate score differential (simplified as captain's quarters)
    const diff = captainId && playerStandings[captainId] 
      ? playerStandings[captainId].quarters 
      : 0;

    setFormData(prev => ({
      ...prev,
      hole_number: holeNumber,
      player_handicap: handicap,
      team_situation: teamMode === 'solo' ? 'solo' : 'partners',
      score_differential: diff
    }));
  }, [holeNumber, players, captainId, teamMode, playerStandings]);

  const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) : value
    }));
  };

  const onAnalyze = () => {
    analyzeShot(formData);
  };

  const getRiskColor = (risk: string) => {
    const riskNum = parseInt(risk);
    if (riskNum <= 30) return '#4CAF50'; // Green
    if (riskNum <= 60) return '#FF9800'; // Orange
    return '#F44336'; // Red
  };

  const getPlayerStyleIcon = (style: string) => {
    switch (style?.toLowerCase()) {
      case 'nit': return '🛡️';
      case 'tag': return '⚖️';
      case 'lag': return '⚡';
      case 'maniac': return '🔥';
      default: return '🎯';
    }
  };

  const typedAnalysis = analysis as AnalysisData | null;

  return (
    <div style={{ marginBottom: '16px' }}>
      <div style={{ 
        padding: '12px', 
        background: 'rgba(255,255,255,0.05)', 
        borderRadius: '8px',
        border: `1px solid ${theme.colors.border}`
      }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '12px'
        }}>
          <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 'bold' }}>
            🎯 Strategic Shot Analysis
          </h4>
          <Button 
            onClick={onAnalyze} 
            disabled={loading}
            size="small"
            variant="primary"
          >
            {loading ? 'Analyzing...' : 'Analyze'}
          </Button>
        </div>

        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: '1fr 1fr', 
          gap: '10px',
          marginBottom: '12px'
        }}>
          <Select
            label="Lie"
            name="lie_type"
            value={formData.lie_type}
            onChange={handleInputChange}
            options={[
              { value: 'fairway', label: 'Fairway' },
              { value: 'rough', label: 'Rough' },
              { value: 'bunker', label: 'Bunker' },
              { value: 'trees', label: 'Trees' },
              { value: 'hazard', label: 'Hazard' }
            ]}
            style={{ fontSize: '12px' }}
          />
          <Input
            label="Distance"
            type="number"
            name="distance_to_pin"
            value={formData.distance_to_pin}
            onChange={handleInputChange}
            style={{ fontSize: '12px' }}
            placeholder="Distance"
            id="distance_to_pin"
          />
        </div>

        {error && (
          <div style={{ color: theme.colors.error, fontSize: '12px', marginBottom: '8px' }}>
            ⚠️ {error}
          </div>
        )}

        {typedAnalysis && (
          <div style={{ 
            marginTop: '12px', 
            padding: '12px', 
            background: 'white', 
            borderRadius: '8px',
            color: '#333',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
            {/* Recommended Shot */}
            <div style={{ marginBottom: '12px', borderBottom: '1px solid #eee', paddingBottom: '8px' }}>
              <div style={{ fontSize: '11px', textTransform: 'uppercase', color: '#666', fontWeight: 'bold' }}>
                Recommended Play
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
                <span style={{ fontSize: '16px', fontWeight: 'bold', color: theme.colors.primary }}>
                  {typedAnalysis.recommended_shot.type?.replace('_', ' ').toUpperCase()}
                </span>
                <span style={{ 
                  fontSize: '12px', 
                  fontWeight: 'bold', 
                  color: 'white', 
                  background: getRiskColor(typedAnalysis.recommended_shot.risk_level),
                  padding: '2px 8px',
                  borderRadius: '10px'
                }}>
                  Risk: {typedAnalysis.recommended_shot.risk_level}
                </span>
              </div>
              <div style={{ fontSize: '12px', color: '#4CAF50', fontWeight: 'bold', marginTop: '2px' }}>
                Success Rate: {typedAnalysis.recommended_shot.success_rate}
              </div>
            </div>

            {/* Style & GTO */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' }}>
              <div style={{ background: '#F3E5F5', padding: '6px', borderRadius: '4px' }}>
                <div style={{ fontSize: '9px', textTransform: 'uppercase', color: '#7B1FA2' }}>Your Style</div>
                <div style={{ fontSize: '12px', fontWeight: 'bold' }}>
                  {getPlayerStyleIcon(typedAnalysis.player_style.profile)} {typedAnalysis.player_style.profile.toUpperCase()}
                </div>
              </div>
              <div style={{ background: '#E8F5E9', padding: '6px', borderRadius: '4px' }}>
                <div style={{ fontSize: '9px', textTransform: 'uppercase', color: '#2E7D32' }}>GTO Play</div>
                <div style={{ fontSize: '12px', fontWeight: 'bold' }}>
                  {typedAnalysis.gto_recommendation.type?.replace('_', ' ').toUpperCase()}
                </div>
              </div>
            </div>

            {/* Strategic Advice */}
            {typedAnalysis.strategic_advice && typedAnalysis.strategic_advice.length > 0 && (
              <div style={{ background: '#FFF9C4', padding: '8px', borderRadius: '6px' }}>
                <div style={{ fontSize: '10px', fontWeight: 'bold', marginBottom: '4px', color: '#F57F17' }}>
                  💡 STRATEGIC ADVICE
                </div>
                {typedAnalysis.strategic_advice.map((advice: string, idx: number) => (
                  <div key={idx} style={{ fontSize: '11px', marginBottom: '2px', lineHeight: '1.3' }}>
                    • {advice}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ShotAnalysisWidget;
