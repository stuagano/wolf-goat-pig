import React, { useState, useEffect, useCallback } from 'react';
import { Card } from './ui';
import ProbabilityVisualization from './ProbabilityVisualization';
import EducationalTooltip, { BettingConcepts, generateStrategicInsight, ContextualHelp } from './EducationalTooltip';

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
  favorable: '#4caf50',
  unfavorable: '#f44336',
  neutral: '#757575'
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

const formatProbability = (prob) => {
  if (prob === null || prob === undefined) return 'N/A';
  return `${(prob * 100).toFixed(1)}%`;
};

const formatValue = (value) => {
  if (value === null || value === undefined) return 'N/A';
  return value >= 0 ? `+${value.toFixed(2)}` : value.toFixed(2);
};

const BettingOddsPanel = ({ 
  gameState, 
  onBettingAction,
  autoUpdate = true,
  refreshInterval = 5000,
  showEducationalTooltips = true 
}) => {
  const [oddsData, setOddsData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [selectedView, setSelectedView] = useState('overview'); // overview, scenarios, analysis
  const [expandedScenario, setExpandedScenario] = useState(null);
  const [calculationHistory, setCalculationHistory] = useState([]);

  // Fetch odds data from the API
  const fetchOddsData = useCallback(async () => {
    if (!gameState || !gameState.players || !gameState.active) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Prepare request data
      const requestData = {
        players: gameState.players.map(player => ({
          id: player.id,
          name: player.name,
          handicap: player.handicap,
          current_score: player.current_score || 0,
          shots_taken: player.shots_taken || 0,
          distance_to_pin: player.distance_to_pin || 0,
          lie_type: player.lie_type || 'fairway',
          is_captain: player.is_captain || false,
          team_id: player.team_id || null,
          confidence_factor: 1.0
        })),
        hole_state: {
          hole_number: gameState.current_hole || 1,
          par: gameState.current_hole_par || 4,
          difficulty_rating: gameState.hole_difficulty || 3.0,
          weather_factor: 1.0,
          pin_position: 'middle',
          course_conditions: 'normal',
          teams: gameState.teams?.type || 'pending',
          current_wager: gameState.current_wager || 1,
          is_doubled: gameState.is_doubled || false,
          line_of_scrimmage_passed: gameState.line_of_scrimmage_passed || false
        },
        use_monte_carlo: gameState.players.length > 4, // Auto-enable for complex scenarios
        simulation_params: {
          num_simulations: 5000,
          max_time_ms: 25.0
        }
      };

      const response = await fetch('/api/wgp/calculate-odds', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      setOddsData(data);
      setLastUpdate(new Date());
      
      // Add to calculation history for trends
      setCalculationHistory(prev => {
        const newHistory = [...prev, {
          timestamp: data.timestamp,
          calculation_time: data.calculation_time_ms,
          confidence: data.confidence_level,
          team_probabilities: data.team_probabilities
        }].slice(-20); // Keep last 20 calculations
        return newHistory;
      });

    } catch (err) {
      console.error('Error fetching odds data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [gameState]);

  // Auto-update effect
  useEffect(() => {
    if (autoUpdate && gameState?.active) {
      fetchOddsData();
      
      const interval = setInterval(fetchOddsData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoUpdate, refreshInterval, fetchOddsData, gameState?.active]);

  // Manual refresh
  const handleRefresh = () => {
    fetchOddsData();
  };

  // Handle betting action
  const handleBettingAction = (scenario) => {
    if (onBettingAction) {
      onBettingAction(scenario);
    }
  };

  // Render loading state
  if (loading && !oddsData) {
    return (
      <Card className="betting-odds-panel">
        <div style={{ padding: 20, textAlign: 'center' }}>
          <div style={{ fontSize: 24, marginBottom: 16 }}>🎯</div>
          <div>Calculating odds...</div>
          <div style={{ fontSize: 12, color: COLORS.muted, marginTop: 8 }}>
            Running probability analysis
          </div>
        </div>
      </Card>
    );
  }

  // Render error state
  if (error && !oddsData) {
    return (
      <Card className="betting-odds-panel">
        <div style={{ padding: 20, textAlign: 'center' }}>
          <div style={{ fontSize: 24, marginBottom: 16, color: COLORS.error }}>⚠️</div>
          <div style={{ color: COLORS.error, marginBottom: 16 }}>
            Error calculating odds: {error}
          </div>
          <button 
            onClick={handleRefresh}
            style={{
              background: COLORS.primary,
              color: 'white',
              border: 'none',
              borderRadius: 8,
              padding: '8px 16px',
              cursor: 'pointer'
            }}
          >
            Retry
          </button>
        </div>
      </Card>
    );
  }

  if (!oddsData) {
    return null;
  }

  return (
    <div className="betting-odds-panel" style={{ 
      background: COLORS.card,
      borderRadius: 16,
      boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #1976d2, #00bcd4)',
        color: 'white',
        padding: 20,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 28 }}>🎯</span>
          <div>
            <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>
              Real-Time Betting Odds
            </h2>
            <div style={{ fontSize: 14, opacity: 0.9 }}>
              Hole {gameState.current_hole} • Updated {lastUpdate?.toLocaleTimeString()}
            </div>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {/* Confidence indicator */}
          <div style={{
            background: 'rgba(255,255,255,0.2)',
            borderRadius: 20,
            padding: '4px 12px',
            fontSize: 12
          }}>
            {Math.round(oddsData.confidence_level * 100)}% Confidence
          </div>
          
          {/* Calculation time */}
          <div style={{
            background: 'rgba(255,255,255,0.2)',
            borderRadius: 20,
            padding: '4px 12px',
            fontSize: 12
          }}>
            {oddsData.calculation_time_ms.toFixed(0)}ms
          </div>
          
          {/* Refresh button */}
          <button
            onClick={handleRefresh}
            disabled={loading}
            style={{
              background: 'rgba(255,255,255,0.2)',
              border: 'none',
              borderRadius: 8,
              color: 'white',
              padding: '6px 12px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: 12
            }}
          >
            {loading ? '⟳' : '↻'}
          </button>
        </div>
      </div>

      {/* View selector */}
      <div style={{
        padding: '16px 20px 0',
        borderBottom: `1px solid ${COLORS.border}`
      }}>
        <div style={{ display: 'flex', gap: 4 }}>
          {[
            { id: 'overview', label: 'Overview', icon: '📊' },
            { id: 'scenarios', label: 'Betting Scenarios', icon: '💰' },
            { id: 'analysis', label: 'Analysis', icon: '🔍' }
          ].map(view => (
            <button
              key={view.id}
              onClick={() => setSelectedView(view.id)}
              style={{
                background: selectedView === view.id ? COLORS.primary : 'transparent',
                color: selectedView === view.id ? 'white' : COLORS.text,
                border: 'none',
                borderRadius: '8px 8px 0 0',
                padding: '8px 16px',
                cursor: 'pointer',
                fontSize: 14,
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}
            >
              <span>{view.icon}</span>
              {view.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content area */}
      <div style={{ padding: 20 }}>
        {selectedView === 'overview' && (
          <OverviewView 
            oddsData={oddsData} 
            gameState={gameState}
            onBettingAction={handleBettingAction}
          />
        )}
        
        {selectedView === 'scenarios' && (
          <ScenariosView 
            oddsData={oddsData}
            gameState={gameState}
            onBettingAction={handleBettingAction}
            expandedScenario={expandedScenario}
            setExpandedScenario={setExpandedScenario}
          />
        )}
        
        {selectedView === 'analysis' && (
          <AnalysisView 
            oddsData={oddsData}
            gameState={gameState}
            calculationHistory={calculationHistory}
          />
        )}
      </div>

      {/* Educational insights footer */}
      {showEducationalTooltips && (
        <div style={{
          background: '#f8f9fa',
          padding: 16,
          borderTop: `1px solid ${COLORS.border}`
        }}>
          {/* Contextual help */}
          <ContextualHelp 
            gamePhase={gameState.teams?.type === 'pending' ? 'partnership_formation' : 'betting_window'}
            playerPosition={gameState.current_leader === gameState.human_player ? 'leading' : 'behind'}
            bettingScenario={oddsData.betting_scenarios?.[0]?.scenario_type}
          />
          
          {/* Strategic insights */}
          {oddsData.educational_insights?.length > 0 && (
            <>
              <div style={{ 
                fontSize: 14, 
                fontWeight: 600, 
                marginBottom: 8,
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}>
                <span>💡</span>
                Strategic Insights
              </div>
              {oddsData.educational_insights.map((insight, index) => (
                <div key={index} style={{ 
                  fontSize: 13, 
                  lineHeight: 1.4, 
                  color: COLORS.text,
                  marginBottom: 8
                }}>
                  • {insight}
                </div>
              ))}
            </>
          )}
          
          {/* Dynamic strategic insights based on current scenario */}
          {oddsData.betting_scenarios?.length > 0 && (
            <div style={{ marginTop: 12 }}>
              {generateStrategicInsight(oddsData.betting_scenarios[0], gameState).map((insight, index) => (
                <EducationalTooltip key={index} title={insight.title} content={insight.content} type={insight.type}>
                  <div style={{
                    display: 'inline-block',
                    background: insight.type === 'warning' ? '#fff3e0' : '#e8f5e8',
                    border: `1px solid ${insight.type === 'warning' ? COLORS.warning : COLORS.success}`,
                    borderRadius: 6,
                    padding: '6px 10px',
                    fontSize: 12,
                    margin: '4px 8px 4px 0',
                    cursor: 'help'
                  }}>
                    {insight.title}
                  </div>
                </EducationalTooltip>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Overview view component
const OverviewView = ({ oddsData, gameState, onBettingAction }) => {
  const playerProbs = oddsData.player_probabilities || {};
  const teamProbs = oddsData.team_probabilities || {};

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Player probabilities */}
      <div>
        <h3 style={{ margin: '0 0 16px 0', color: COLORS.text }}>
          Individual{' '}
          <EducationalTooltip {...BettingConcepts.winProbability}>
            Win Probabilities
          </EducationalTooltip>
        </h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 12
        }}>
          {Object.entries(playerProbs).map(([playerId, data]) => (
            <div key={playerId} style={{
              background: '#f8f9fa',
              borderRadius: 12,
              padding: 16,
              position: 'relative'
            }}>
              <div style={{ 
                fontSize: 16, 
                fontWeight: 600, 
                marginBottom: 8,
                color: COLORS.text
              }}>
                {data.name || playerId}
              </div>
              
              <div style={{
                fontSize: 24,
                fontWeight: 'bold',
                color: COLORS.primary,
                marginBottom: 8
              }}>
                {formatProbability(data.win_probability)}
              </div>
              
              <div style={{ fontSize: 12, color: COLORS.muted }}>
                Expected Score: {data.expected_score?.toFixed(1) || 'N/A'}
              </div>
              
              {/* Probability bar */}
              <div style={{
                width: '100%',
                height: 4,
                background: '#e0e0e0',
                borderRadius: 2,
                marginTop: 8,
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${(data.win_probability || 0) * 100}%`,
                  height: '100%',
                  background: COLORS.primary,
                  borderRadius: 2
                }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Team probabilities */}
      {Object.keys(teamProbs).length > 0 && (
        <div>
          <h3 style={{ margin: '0 0 16px 0', color: COLORS.text }}>
            Team Win Probabilities
          </h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: 12
          }}>
            {Object.entries(teamProbs).map(([teamId, probability]) => (
              <div key={teamId} style={{
                background: probability > 0.5 ? COLORS.favorable : COLORS.unfavorable,
                color: 'white',
                borderRadius: 12,
                padding: 16,
                textAlign: 'center'
              }}>
                <div style={{ fontSize: 14, opacity: 0.9, marginBottom: 4 }}>
                  {teamId.charAt(0).toUpperCase() + teamId.slice(1)}
                </div>
                <div style={{ fontSize: 20, fontWeight: 'bold' }}>
                  {formatProbability(probability)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick actions */}
      {oddsData.betting_scenarios?.length > 0 && (
        <div>
          <h3 style={{ margin: '0 0 16px 0', color: COLORS.text }}>
            Recommended Action
          </h3>
          <div style={{
            background: COLORS.primary,
            color: 'white',
            borderRadius: 12,
            padding: 16,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>
                {oddsData.optimal_strategy.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </div>
              <div style={{ fontSize: 14, opacity: 0.9 }}>
                {oddsData.betting_scenarios[0]?.reasoning}
              </div>
            </div>
            <button
              onClick={() => onBettingAction(oddsData.betting_scenarios[0])}
              style={{
                background: 'rgba(255,255,255,0.2)',
                color: 'white',
                border: 'none',
                borderRadius: 8,
                padding: '8px 16px',
                cursor: 'pointer',
                fontWeight: 600
              }}
            >
              Take Action
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Scenarios view component
const ScenariosView = ({ 
  oddsData, 
  gameState, 
  onBettingAction, 
  expandedScenario, 
  setExpandedScenario 
}) => {
  const scenarios = oddsData.betting_scenarios || [];

  if (scenarios.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: 40, color: COLORS.muted }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>🎯</div>
        <div style={{ fontSize: 16, marginBottom: 8 }}>No Betting Scenarios Available</div>
        <div style={{ fontSize: 14 }}>
          Betting opportunities will appear based on game state and timing.
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {scenarios.map((scenario, index) => {
        const isExpanded = expandedScenario === index;
        const riskColor = getRiskColor(scenario.risk_level);
        const riskIcon = getRiskIcon(scenario.risk_level);

        return (
          <div
            key={index}
            style={{
              border: `2px solid ${riskColor}`,
              borderRadius: 12,
              overflow: 'hidden'
            }}
          >
            {/* Scenario header */}
            <div
              onClick={() => setExpandedScenario(isExpanded ? null : index)}
              style={{
                background: riskColor,
                color: 'white',
                padding: 16,
                cursor: 'pointer',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}
            >
              <div>
                <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>
                  {scenario.scenario_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </div>
                <div style={{ fontSize: 14, opacity: 0.9 }}>
                  <EducationalTooltip {...BettingConcepts.winProbability}>
                    {formatProbability(scenario.win_probability)} win probability
                  </EducationalTooltip>
                  {' • '}
                  <EducationalTooltip {...BettingConcepts.expectedValue}>
                    EV: {formatValue(scenario.expected_value)}
                  </EducationalTooltip>
                </div>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{
                  background: 'rgba(255,255,255,0.2)',
                  borderRadius: 20,
                  padding: '4px 8px',
                  fontSize: 12,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4
                }}>
                  {riskIcon} {scenario.risk_level.toUpperCase()}
                </div>
                <span style={{ fontSize: 18 }}>
                  {isExpanded ? '⌄' : '›'}
                </span>
              </div>
            </div>

            {/* Expanded content */}
            {isExpanded && (
              <div style={{ padding: 20 }}>
                {/* Reasoning */}
                <div style={{ marginBottom: 16 }}>
                  <h4 style={{ margin: '0 0 8px 0', color: COLORS.text }}>
                    Analysis
                  </h4>
                  <div style={{ 
                    background: '#f8f9fa', 
                    padding: 12, 
                    borderRadius: 8,
                    fontSize: 14,
                    lineHeight: 1.4,
                    color: COLORS.text
                  }}>
                    {scenario.reasoning}
                  </div>
                </div>

                {/* Payout matrix */}
                <div style={{ marginBottom: 16 }}>
                  <h4 style={{ margin: '0 0 8px 0', color: COLORS.text }}>
                    Potential Outcomes
                  </h4>
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                    gap: 8
                  }}>
                    {Object.entries(scenario.payout_matrix).map(([outcome, value]) => (
                      <div key={outcome} style={{
                        background: value > 0 ? COLORS.favorable : value < 0 ? COLORS.unfavorable : COLORS.neutral,
                        color: 'white',
                        padding: 12,
                        borderRadius: 8,
                        textAlign: 'center'
                      }}>
                        <div style={{ fontSize: 12, opacity: 0.9, marginBottom: 4 }}>
                          {outcome.charAt(0).toUpperCase() + outcome.slice(1)}
                        </div>
                        <div style={{ fontSize: 16, fontWeight: 'bold' }}>
                          {formatValue(value)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Confidence interval */}
                <div style={{ marginBottom: 16 }}>
                  <h4 style={{ margin: '0 0 8px 0', color: COLORS.text }}>
                    <EducationalTooltip {...BettingConcepts.confidenceInterval}>
                      Confidence Range
                    </EducationalTooltip>
                  </h4>
                  <div style={{ fontSize: 14, color: COLORS.muted }}>
                    {formatProbability(scenario.confidence_interval[0])} - {formatProbability(scenario.confidence_interval[1])}
                  </div>
                </div>

                {/* Action button */}
                <button
                  onClick={() => onBettingAction(scenario)}
                  style={{
                    background: scenario.recommendation.includes('recommend') ? COLORS.success : COLORS.primary,
                    color: 'white',
                    border: 'none',
                    borderRadius: 8,
                    padding: '12px 24px',
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: 'pointer',
                    width: '100%'
                  }}
                >
                  {scenario.recommendation === 'offer' ? '💰 Offer' : 
                   scenario.recommendation === 'accept' ? '✅ Accept' :
                   scenario.recommendation === 'decline' ? '❌ Decline' :
                   '🎯 Execute'}
                </button>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

// Analysis view component
const AnalysisView = ({ oddsData, gameState, calculationHistory }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Performance metrics */}
      <div>
        <h3 style={{ margin: '0 0 16px 0', color: COLORS.text }}>
          Calculation Performance
        </h3>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: 12
        }}>
          <div style={{
            background: '#f8f9fa',
            borderRadius: 12,
            padding: 16,
            textAlign: 'center'
          }}>
            <div style={{ fontSize: 20, fontWeight: 'bold', color: COLORS.primary }}>
              {oddsData.calculation_time_ms.toFixed(0)}ms
            </div>
            <div style={{ fontSize: 12, color: COLORS.muted }}>
              Calculation Time
            </div>
          </div>
          
          <div style={{
            background: '#f8f9fa',
            borderRadius: 12,
            padding: 16,
            textAlign: 'center'
          }}>
            <div style={{ fontSize: 20, fontWeight: 'bold', color: COLORS.primary }}>
              {Math.round(oddsData.confidence_level * 100)}%
            </div>
            <div style={{ fontSize: 12, color: COLORS.muted }}>
              Confidence Level
            </div>
          </div>
          
          {oddsData.monte_carlo_used && (
            <div style={{
              background: '#f8f9fa',
              borderRadius: 12,
              padding: 16,
              textAlign: 'center'
            }}>
              <div style={{ fontSize: 20, fontWeight: 'bold', color: COLORS.primary }}>
                {oddsData.simulation_details?.num_simulations_run?.toLocaleString() || 'N/A'}
              </div>
              <div style={{ fontSize: 12, color: COLORS.muted }}>
                Simulations Run
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Risk assessment */}
      <div>
        <h3 style={{ margin: '0 0 16px 0', color: COLORS.text }}>
          Risk Assessment
        </h3>
        <div style={{
          background: '#f8f9fa',
          borderRadius: 12,
          padding: 16
        }}>
          {Object.entries(oddsData.risk_assessment).map(([key, value]) => (
            <div key={key} style={{
              display: 'flex',
              justifyContent: 'space-between',
              marginBottom: 8,
              fontSize: 14
            }}>
              <span style={{ color: COLORS.text }}>
                {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
              </span>
              <span style={{ color: COLORS.muted }}>
                {Array.isArray(value) ? value.join(', ') : 
                 typeof value === 'number' ? value.toFixed(2) :
                 value?.toString() || 'N/A'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Probability visualization */}
      <div>
        <h3 style={{ margin: '0 0 16px 0', color: COLORS.text }}>
          Probability Trends
        </h3>
        <ProbabilityVisualization 
          data={calculationHistory}
          currentOdds={oddsData}
        />
      </div>

      {/* Educational insights */}
      {oddsData.educational_insights?.length > 0 && (
        <div>
          <h3 style={{ margin: '0 0 16px 0', color: COLORS.text }}>
            Educational Insights
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {oddsData.educational_insights.map((insight, index) => (
              <div key={index} style={{
                background: '#f8f9fa',
                borderRadius: 8,
                padding: 12,
                fontSize: 14,
                lineHeight: 1.4,
                color: COLORS.text,
                borderLeft: `4px solid ${COLORS.primary}`
              }}>
                {insight}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default BettingOddsPanel;