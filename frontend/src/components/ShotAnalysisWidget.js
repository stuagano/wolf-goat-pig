import React, { useState, useEffect, useCallback } from 'react';
import { useTheme } from '../theme/Provider';
import { useGame } from '../context';
import { Button, Card } from './ui';
import { apiPost, useApiCall } from '../utils/api';

/**
 * Enhanced Shot Analysis Widget for game integration
 * Provides real-time shot recommendations during gameplay
 */
const ShotAnalysisWidget = ({ 
  gameState, 
  holeState, 
  currentPlayer,
  visible = true,
  onShotRecommendation 
}) => {
  const theme = useTheme();
  const { setError } = useGame();
  const { makeApiCall, loading: apiLoading, error: apiError, isColdStart } = useApiCall();
  
  // Component state
  const [analysis, setAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [autoAnalyze, setAutoAnalyze] = useState(true);
  const [retryCount, setRetryCount] = useState(0);
  
  // Analysis parameters derived from game state
  const [analysisParams, setAnalysisParams] = useState({
    lie_type: 'fairway',
    distance_to_pin: 150,
    player_handicap: 10.0,
    hole_number: 1,
    team_situation: 'solo',
    score_differential: 0,
    opponent_styles: []
  });

  // Extract analysis parameters from current game state
  const updateAnalysisParams = useCallback(() => {
    if (!gameState || !holeState || !currentPlayer) return;

    const ballPosition = holeState.ball_positions[currentPlayer.id];
    const teamType = holeState.teams.type;
    
    // Determine score differential (simplified)
    const currentScore = currentPlayer.points || 0;
    const avgOpponentScore = gameState.players
      .filter(p => p.id !== currentPlayer.id)
      .reduce((sum, p) => sum + (p.points || 0), 0) / Math.max(1, gameState.players.length - 1);
    
    const newParams = {
      lie_type: ballPosition?.lie_type || 'fairway',
      distance_to_pin: ballPosition?.distance_to_pin || 150,
      player_handicap: currentPlayer.handicap || 18,
      hole_number: gameState.current_hole || 1,
      team_situation: teamType === 'partners' ? 'partners' : 'solo',
      score_differential: Math.round(currentScore - avgOpponentScore),
      opponent_styles: [] // Could be enhanced with player style data
    };

    setAnalysisParams(newParams);
  }, [gameState, holeState, currentPlayer]);

  // Perform shot analysis with enhanced error handling
  const performAnalysis = useCallback(async (params = analysisParams) => {
    if (!params.distance_to_pin || analysisLoading || apiLoading) return;

    setAnalysisLoading(true);
    try {
      const response = await makeApiCall(apiPost, '/wgp/shot-range-analysis', params);
      setAnalysis(response.analysis);
      setRetryCount(0); // Reset retry count on success
      
      // Notify parent component of recommendation
      if (onShotRecommendation && response.analysis?.recommended_shot) {
        onShotRecommendation(response.analysis.recommended_shot);
      }
    } catch (error) {
      console.error('Shot analysis failed:', error);
      setRetryCount(prev => prev + 1);
      
      // More descriptive error messages
      let errorMessage = 'Failed to analyze shot.';
      if (isColdStart) {
        errorMessage = 'The analysis service is starting up. This may take up to 30 seconds.';
      } else if (retryCount >= 2) {
        errorMessage = 'Shot analysis is temporarily unavailable. Please try again later.';
      }
      
      setError(errorMessage);
    } finally {
      setAnalysisLoading(false);
    }
  }, [analysisParams, analysisLoading, apiLoading, onShotRecommendation, setError, makeApiCall, isColdStart, retryCount]);

  // Auto-analyze when game state changes
  useEffect(() => {
    updateAnalysisParams();
  }, [updateAnalysisParams]);

  useEffect(() => {
    if (autoAnalyze && analysisParams.distance_to_pin && visible) {
      // Add a small delay to avoid rapid-fire API calls
      const timer = setTimeout(() => {
        performAnalysis();
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [analysisParams, autoAnalyze, visible, performAnalysis]);

  // Color coding for risk levels
  const getRiskColor = (risk) => {
    const riskNum = parseInt(risk);
    if (riskNum <= 30) return theme.colors.success;
    if (riskNum <= 60) return theme.colors.warning;
    return theme.colors.error;
  };


  if (!visible || !currentPlayer) {
    return null;
  }

  // Mobile breakpoint detection
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
  
  return (
    <Card style={{ 
      fontSize: isMobile ? theme.typography.sm : theme.typography.base 
    }}>
      <div style={{ marginBottom: theme.spacing[4] }}>
        {/* Header with toggle controls */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: isMobile ? 'flex-start' : 'center',
          flexDirection: isMobile ? 'column' : 'row',
          gap: isMobile ? theme.spacing[3] : 0,
          marginBottom: theme.spacing[4]
        }}>
          <h3 style={{ 
            margin: 0,
            color: theme.colors.primary,
            fontSize: theme.typography.lg,
            fontWeight: theme.typography.bold
          }}>
            🎯 Shot Analysis
          </h3>
          
          <div style={{ 
            display: 'flex', 
            gap: theme.spacing[2], 
            alignItems: 'center',
            flexWrap: isMobile ? 'wrap' : 'nowrap',
            width: isMobile ? '100%' : 'auto'
          }}>
            <label style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: theme.spacing[1],
              fontSize: theme.typography.sm,
              color: theme.colors.textSecondary
            }}>
              <input
                type="checkbox"
                checked={autoAnalyze}
                onChange={(e) => setAutoAnalyze(e.target.checked)}
              />
              Auto-analyze
            </label>
            
            <Button
              size="small"
              variant="secondary"
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              {showAdvanced ? 'Basic' : 'Advanced'} View
            </Button>
            
            <Button
              size="small"
              variant="primary"
              onClick={() => performAnalysis()}
              disabled={analysisLoading || apiLoading}
            >
              {analysisLoading || apiLoading ? 
                (isColdStart ? 'Starting up...' : 'Analyzing...') : 
                'Analyze Shot'}
            </Button>
          </div>
        </div>

        {/* Current situation summary */}
        <div style={{
          background: theme.colors.surface,
          padding: theme.spacing[3],
          borderRadius: theme.borderRadius.base,
          marginBottom: theme.spacing[4],
          border: `1px solid ${theme.colors.border}`
        }}>
          <div style={{ 
            display: 'grid',
            gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(auto-fit, minmax(100px, 1fr))',
            gap: theme.spacing[2],
            fontSize: theme.typography.sm
          }}>
            <div>
              <div style={{ color: theme.colors.textSecondary }}>Player</div>
              <div style={{ fontWeight: theme.typography.medium }}>
                {currentPlayer.name} (HC: {currentPlayer.handicap})
              </div>
            </div>
            <div>
              <div style={{ color: theme.colors.textSecondary }}>Distance</div>
              <div style={{ fontWeight: theme.typography.medium }}>
                {Math.round(analysisParams.distance_to_pin)} yards
              </div>
            </div>
            <div>
              <div style={{ color: theme.colors.textSecondary }}>Lie</div>
              <div style={{ fontWeight: theme.typography.medium }}>
                {analysisParams.lie_type.charAt(0).toUpperCase() + analysisParams.lie_type.slice(1)}
              </div>
            </div>
            <div>
              <div style={{ color: theme.colors.textSecondary }}>Hole</div>
              <div style={{ fontWeight: theme.typography.medium }}>
                #{analysisParams.hole_number}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Analysis Results */}
      {analysis && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: theme.spacing[4] }}>
          {/* Primary Recommendation */}
          <div style={{
            background: `linear-gradient(135deg, ${theme.colors.primary}15, ${theme.colors.accent}15)`,
            padding: theme.spacing[4],
            borderRadius: theme.borderRadius.base,
            border: `2px solid ${theme.colors.primary}`
          }}>
            <h4 style={{ 
              margin: `0 0 ${theme.spacing[3]} 0`,
              color: theme.colors.primary,
              fontSize: theme.typography.base,
              fontWeight: theme.typography.bold
            }}>
              🎯 Recommended Shot
            </h4>
            
            <div style={{
              display: 'grid',
              gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(auto-fit, minmax(80px, 1fr))',
              gap: theme.spacing[2]
            }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ 
                  fontSize: theme.typography.xl,
                  fontWeight: theme.typography.bold,
                  color: theme.colors.primary,
                  marginBottom: theme.spacing[1]
                }}>
                  {analysis.recommended_shot.type?.replace('_', ' ').toUpperCase()}
                </div>
                <div style={{ fontSize: theme.typography.xs, color: theme.colors.textSecondary }}>
                  Shot Type
                </div>
              </div>
              
              <div style={{ textAlign: 'center' }}>
                <div style={{ 
                  fontSize: theme.typography.lg,
                  fontWeight: theme.typography.bold,
                  color: theme.colors.success,
                  marginBottom: theme.spacing[1]
                }}>
                  {analysis.recommended_shot.success_rate}
                </div>
                <div style={{ fontSize: theme.typography.xs, color: theme.colors.textSecondary }}>
                  Success Rate
                </div>
              </div>
              
              <div style={{ textAlign: 'center' }}>
                <div style={{ 
                  fontSize: theme.typography.lg,
                  fontWeight: theme.typography.bold,
                  color: getRiskColor(analysis.recommended_shot.risk_level),
                  marginBottom: theme.spacing[1]
                }}>
                  {analysis.recommended_shot.risk_level}
                </div>
                <div style={{ fontSize: theme.typography.xs, color: theme.colors.textSecondary }}>
                  Risk Level
                </div>
              </div>
              
              <div style={{ textAlign: 'center' }}>
                <div style={{ 
                  fontSize: theme.typography.lg,
                  fontWeight: theme.typography.bold,
                  color: theme.colors.accent,
                  marginBottom: theme.spacing[1]
                }}>
                  {analysis.recommended_shot.equity_vs_field}
                </div>
                <div style={{ fontSize: theme.typography.xs, color: theme.colors.textSecondary }}>
                  vs Field
                </div>
              </div>
            </div>
          </div>

          {/* Player Style & Quick Tips */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: showAdvanced ? '1fr' : 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: theme.spacing[3]
          }}>
            {/* Player Style */}
            <div style={{
              background: theme.colors.surface,
              padding: theme.spacing[3],
              borderRadius: theme.borderRadius.base,
              border: `1px solid ${theme.colors.border}`
            }}>
              <h5 style={{ 
                margin: `0 0 ${theme.spacing[2]} 0`,
                color: theme.colors.textPrimary,
                fontSize: theme.typography.sm,
                fontWeight: theme.typography.medium
              }}>
                👤 Your Play Style
              </h5>
              <div style={{ 
                fontSize: theme.typography.base,
                fontWeight: theme.typography.bold,
                color: theme.colors.accent,
                marginBottom: theme.spacing[1]
              }}>
                {analysis.player_style?.profile?.toUpperCase() || 'BALANCED'}
              </div>
              <div style={{ 
                fontSize: theme.typography.sm,
                color: theme.colors.textSecondary
              }}>
                {analysis.player_style?.description || 'Balanced approach to shot selection'}
              </div>
            </div>

            {/* Quick Strategy Tips */}
            {analysis.strategic_advice && analysis.strategic_advice.length > 0 && (
              <div style={{
                background: theme.colors.surface,
                padding: theme.spacing[3],
                borderRadius: theme.borderRadius.base,
                border: `1px solid ${theme.colors.border}`
              }}>
                <h5 style={{ 
                  margin: `0 0 ${theme.spacing[2]} 0`,
                  color: theme.colors.textPrimary,
                  fontSize: theme.typography.sm,
                  fontWeight: theme.typography.medium
                }}>
                  💡 Quick Tips
                </h5>
                <div style={{ fontSize: theme.typography.sm }}>
                  {analysis.strategic_advice.slice(0, 2).map((tip, index) => (
                    <div key={index} style={{ 
                      marginBottom: theme.spacing[1],
                      color: theme.colors.textSecondary
                    }}>
                      • {tip}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Advanced Analysis (when toggled) */}
          {showAdvanced && (
            <>
              {/* All Shot Options */}
              <div>
                <h5 style={{ 
                  margin: `0 0 ${theme.spacing[3]} 0`,
                  color: theme.colors.textPrimary,
                  fontSize: theme.typography.base,
                  fontWeight: theme.typography.medium
                }}>
                  📊 All Shot Options
                </h5>
                <div style={{ 
                  overflowX: 'auto',
                  WebkitOverflowScrolling: 'touch' // Smooth scrolling on iOS
                }}>
                  <table style={{ 
                    width: '100%',
                    fontSize: isMobile ? theme.typography.xs : theme.typography.sm,
                    borderCollapse: 'collapse',
                    minWidth: isMobile ? '400px' : 'auto' // Ensure table doesn't shrink too much on mobile
                  }}>
                    <thead>
                      <tr style={{ background: theme.colors.surface }}>
                        <th style={{ padding: theme.spacing[2], textAlign: 'left', border: `1px solid ${theme.colors.border}` }}>
                          Shot Type
                        </th>
                        <th style={{ padding: theme.spacing[2], textAlign: 'center', border: `1px solid ${theme.colors.border}` }}>
                          Success Rate
                        </th>
                        <th style={{ padding: theme.spacing[2], textAlign: 'center', border: `1px solid ${theme.colors.border}` }}>
                          Risk
                        </th>
                        <th style={{ padding: theme.spacing[2], textAlign: 'center', border: `1px solid ${theme.colors.border}` }}>
                          Expected Value
                        </th>
                        <th style={{ padding: theme.spacing[2], textAlign: 'center', border: `1px solid ${theme.colors.border}` }}>
                          Equity
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {analysis.all_ranges?.slice(0, 5).map((range, index) => (
                        <tr key={index} style={{ 
                          background: index % 2 === 0 ? theme.colors.background : 'transparent'
                        }}>
                          <td style={{ 
                            padding: theme.spacing[2], 
                            fontWeight: theme.typography.medium,
                            border: `1px solid ${theme.colors.border}`
                          }}>
                            {range.type?.replace('_', ' ').toUpperCase()}
                          </td>
                          <td style={{ 
                            padding: theme.spacing[2], 
                            textAlign: 'center',
                            color: theme.colors.success,
                            border: `1px solid ${theme.colors.border}`
                          }}>
                            {range.success_rate}
                          </td>
                          <td style={{ 
                            padding: theme.spacing[2], 
                            textAlign: 'center',
                            color: getRiskColor(range.risk),
                            border: `1px solid ${theme.colors.border}`
                          }}>
                            {range.risk}
                          </td>
                          <td style={{ 
                            padding: theme.spacing[2], 
                            textAlign: 'center',
                            fontFamily: 'monospace',
                            border: `1px solid ${theme.colors.border}`
                          }}>
                            {range.ev}
                          </td>
                          <td style={{ 
                            padding: theme.spacing[2], 
                            textAlign: 'center',
                            color: theme.colors.accent,
                            border: `1px solid ${theme.colors.border}`
                          }}>
                            {range.equity}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* GTO vs Exploitative */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: theme.spacing[3]
              }}>
                <div style={{
                  background: `${theme.colors.success}15`,
                  padding: theme.spacing[3],
                  borderRadius: theme.borderRadius.base,
                  border: `2px solid ${theme.colors.success}`
                }}>
                  <h5 style={{ 
                    margin: `0 0 ${theme.spacing[2]} 0`,
                    color: theme.colors.success,
                    fontSize: theme.typography.sm,
                    fontWeight: theme.typography.bold
                  }}>
                    🧠 Optimal Strategy (GTO)
                  </h5>
                  <div style={{ 
                    fontSize: theme.typography.base,
                    fontWeight: theme.typography.bold,
                    color: theme.colors.success,
                    marginBottom: theme.spacing[1]
                  }}>
                    {analysis.gto_recommendation?.type?.replace('_', ' ').toUpperCase()}
                  </div>
                  <div style={{ 
                    fontSize: theme.typography.sm,
                    color: theme.colors.textSecondary
                  }}>
                    {analysis.gto_recommendation?.reasoning}
                  </div>
                </div>
                
                <div style={{
                  background: `${theme.colors.warning}15`,
                  padding: theme.spacing[3],
                  borderRadius: theme.borderRadius.base,
                  border: `2px solid ${theme.colors.warning}`
                }}>
                  <h5 style={{ 
                    margin: `0 0 ${theme.spacing[2]} 0`,
                    color: theme.colors.warning,
                    fontSize: theme.typography.sm,
                    fontWeight: theme.typography.bold
                  }}>
                    🎭 Situational Play
                  </h5>
                  <div style={{ 
                    fontSize: theme.typography.base,
                    fontWeight: theme.typography.bold,
                    color: theme.colors.warning,
                    marginBottom: theme.spacing[1]
                  }}>
                    {analysis.exploitative_play?.type?.replace('_', ' ').toUpperCase()}
                  </div>
                  <div style={{ 
                    fontSize: theme.typography.sm,
                    color: theme.colors.textSecondary
                  }}>
                    {analysis.exploitative_play?.reasoning}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Loading State */}
      {(analysisLoading || apiLoading) && (
        <div style={{
          textAlign: 'center',
          padding: theme.spacing[6],
          color: theme.colors.textSecondary
        }}>
          <div style={{ marginBottom: theme.spacing[2] }}>
            {isColdStart ? '❄️' : '🎲'}
          </div>
          <div>
            {isColdStart ? 
              'Starting analysis service... This may take up to 30 seconds.' : 
              'Analyzing shot options...'}
          </div>
          {retryCount > 0 && (
            <div style={{ 
              marginTop: theme.spacing[2], 
              fontSize: theme.typography.sm,
              color: theme.colors.warning 
            }}>
              Retry attempt {retryCount}
            </div>
          )}
        </div>
      )}

      {/* Error State */}
      {apiError && !analysisLoading && !apiLoading && (
        <div style={{
          textAlign: 'center',
          padding: theme.spacing[4],
          color: theme.colors.error,
          background: `${theme.colors.error}10`,
          borderRadius: theme.borderRadius.base,
          border: `1px solid ${theme.colors.error}30`,
          marginBottom: theme.spacing[4]
        }}>
          <div style={{ marginBottom: theme.spacing[2] }}>⚠️</div>
          <div style={{ marginBottom: theme.spacing[2] }}>{apiError}</div>
          <Button
            size="small"
            variant="secondary"
            onClick={() => performAnalysis()}
          >
            Retry Analysis
          </Button>
        </div>
      )}

      {/* No Analysis Yet */}
      {!analysis && !analysisLoading && !apiLoading && !apiError && (
        <div style={{
          textAlign: 'center',
          padding: theme.spacing[6],
          color: theme.colors.textSecondary
        }}>
          <div style={{ marginBottom: theme.spacing[2] }}>🎯</div>
          <div>
            {autoAnalyze ? 
              'Automatic analysis will start when player data is available' : 
              'Click "Analyze Shot" for recommendations'}
          </div>
        </div>
      )}
    </Card>
  );
};

export default ShotAnalysisWidget;