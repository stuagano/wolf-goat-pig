import React, { useState, useEffect, useCallback } from 'react';

const COLORS = {
  primary: '#2c3e50',
  secondary: '#34495e',
  accent: '#3498db',
  success: '#27ae60',
  warning: '#f39c12',
  danger: '#e74c3c',
  light: '#ecf0f1',
  dark: '#2c3e50',
  gold: '#f1c40f',
  purple: '#9b59b6'
};

const AnalyticsDashboard = ({ gameId, onBack }) => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('performance');

  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`/wgp/${gameId}/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action_type: 'GET_ADVANCED_ANALYTICS',
          payload: {}
        })
      });

      if (response.ok) {
        const data = await response.json();
        // Analytics data should be in the timeline event details or game state
        if (data.timeline_event && data.timeline_event.details) {
          setAnalytics(data.timeline_event.details);
        } else if (data.game_state && data.game_state.analytics) {
          setAnalytics(data.game_state.analytics);
        }
      } else {
        console.error('Failed to fetch analytics');
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
    }
  }, [gameId]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const renderPerformanceTrends = () => {
    if (!analytics || !analytics.performance_trends) return null;

    return (
      <div style={{ display: 'grid', gap: '20px' }}>
        <h3 style={{ color: COLORS.primary, marginBottom: '20px' }}>Performance Trends</h3>
        
        {Object.values(analytics.performance_trends).map((player, index) => (
          <div
            key={player.name}
            style={{
              backgroundColor: 'white',
              padding: '20px',
              borderRadius: '12px',
              border: `2px solid ${COLORS.accent}`,
              boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
              <h4 style={{ color: COLORS.primary, margin: 0 }}>{player.name}</h4>
              <div style={{
                backgroundColor: player.trend_direction === 'improving' ? COLORS.success : 
                              player.trend_direction === 'declining' ? COLORS.danger : COLORS.secondary,
                color: 'white',
                padding: '4px 12px',
                borderRadius: '20px',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>
                {player.trend_direction.replace('_', ' ').toUpperCase()}
              </div>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '10px' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: COLORS.primary }}>
                  {player.current_points}
                </div>
                <div style={{ fontSize: '12px', color: COLORS.secondary }}>Current Points</div>
              </div>
              
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: COLORS.accent }}>
                  {player.average_per_hole.toFixed(1)}
                </div>
                <div style={{ fontSize: '12px', color: COLORS.secondary }}>Avg Per Hole</div>
              </div>
              
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: COLORS.success }}>
                  {player.best_hole}
                </div>
                <div style={{ fontSize: '12px', color: COLORS.secondary }}>Best Hole</div>
              </div>
              
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: COLORS.danger }}>
                  {player.worst_hole}
                </div>
                <div style={{ fontSize: '12px', color: COLORS.secondary }}>Worst Hole</div>
              </div>
              
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: COLORS.gold }}>
                  {(player.consistency * 100).toFixed(0)}%
                </div>
                <div style={{ fontSize: '12px', color: COLORS.secondary }}>Consistency</div>
              </div>
            </div>
            
            {/* Hole-by-hole mini chart */}
            <div style={{ marginTop: '15px' }}>
              <div style={{ fontSize: '14px', color: COLORS.secondary, marginBottom: '5px' }}>
                Hole Performance:
              </div>
              <div style={{ display: 'flex', gap: '2px', height: '30px', alignItems: 'flex-end' }}>
                {player.hole_by_hole.slice(-10).map((hole, i) => (
                  <div
                    key={i}
                    style={{
                      width: '20px',
                      height: `${Math.max(5, Math.abs(hole.points) * 10)}px`,
                      backgroundColor: hole.points > 0 ? COLORS.success : hole.points < 0 ? COLORS.danger : COLORS.secondary,
                      opacity: 0.7,
                      borderRadius: '2px',
                      position: 'relative'
                    }}
                    title={`Hole ${hole.hole}: ${hole.points > 0 ? '+' : ''}${hole.points}`}
                  />
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderBettingAnalysis = () => {
    if (!analytics || !analytics.betting_analysis) return null;

    const betting = analytics.betting_analysis;

    return (
      <div style={{ display: 'grid', gap: '20px' }}>
        <h3 style={{ color: COLORS.primary, marginBottom: '20px' }}>Betting Analysis</h3>
        
        {/* Overall Betting Stats */}
        <div style={{
          backgroundColor: 'white',
          padding: '20px',
          borderRadius: '12px',
          border: `2px solid ${COLORS.warning}`,
          boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
        }}>
          <h4 style={{ color: COLORS.primary, marginTop: 0 }}>Overall Wagering</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '15px' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: COLORS.warning }}>
                {betting.average_wager?.toFixed(1) || 0}
              </div>
              <div style={{ fontSize: '12px', color: COLORS.secondary }}>Average Wager</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: COLORS.danger }}>
                {betting.max_wager || 0}
              </div>
              <div style={{ fontSize: '12px', color: COLORS.secondary }}>Max Wager</div>
            </div>
          </div>
          
          {/* Wager Escalation Chart */}
          <div style={{ marginTop: '20px' }}>
            <div style={{ fontSize: '14px', color: COLORS.secondary, marginBottom: '10px' }}>
              Wager Escalation by Hole:
            </div>
            <div style={{ display: 'flex', gap: '3px', height: '40px', alignItems: 'flex-end' }}>
              {(betting.wager_escalation || []).map((wager, i) => (
                <div
                  key={i}
                  style={{
                    width: '15px',
                    height: `${Math.max(5, wager * 5)}px`,
                    backgroundColor: wager >= 4 ? COLORS.danger : wager >= 2 ? COLORS.warning : COLORS.accent,
                    borderRadius: '2px',
                    opacity: 0.8
                  }}
                  title={`Hole ${i + 1}: ${wager} quarters`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Special Rules Frequency */}
        <div style={{
          backgroundColor: 'white',
          padding: '20px',
          borderRadius: '12px',
          border: `2px solid ${COLORS.purple}`,
          boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
        }}>
          <h4 style={{ color: COLORS.primary, marginTop: 0 }}>Special Rules Invoked</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '15px' }}>
            {Object.entries(betting.special_rules_frequency || {}).map(([rule, count]) => (
              <div key={rule} style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: COLORS.purple }}>
                  {count}
                </div>
                <div style={{ fontSize: '12px', color: COLORS.secondary, textTransform: 'capitalize' }}>
                  {rule.replace('_', ' ')}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Success Rates by Strategy */}
        <div style={{
          backgroundColor: 'white',
          padding: '20px',
          borderRadius: '12px',
          border: `2px solid ${COLORS.success}`,
          boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
        }}>
          <h4 style={{ color: COLORS.primary, marginTop: 0 }}>Strategy Success Rates</h4>
          {Object.values(betting.success_rates || {}).map(player => (
            <div key={player.name} style={{ marginBottom: '15px', padding: '10px', backgroundColor: COLORS.light, borderRadius: '8px' }}>
              <div style={{ fontWeight: 'bold', marginBottom: '8px' }}>{player.name}</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '14px' }}>
                <div>
                  <span style={{ color: COLORS.danger }}>Solo Success: </span>
                  <strong>{(player.solo_success_rate * 100).toFixed(1)}%</strong>
                  <span style={{ color: COLORS.secondary }}> ({player.solo_attempts} attempts)</span>
                </div>
                <div>
                  <span style={{ color: COLORS.success }}>Partnership Success: </span>
                  <strong>{(player.partnership_success_rate * 100).toFixed(1)}%</strong>
                  <span style={{ color: COLORS.secondary }}> ({player.partnership_attempts} attempts)</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderPartnershipChemistry = () => {
    if (!analytics || !analytics.partnership_chemistry) return null;

    return (
      <div style={{ display: 'grid', gap: '20px' }}>
        <h3 style={{ color: COLORS.primary, marginBottom: '20px' }}>Partnership Chemistry</h3>
        
        {Object.entries(analytics.partnership_chemistry).map(([partnership, stats]) => (
          <div
            key={partnership}
            style={{
              backgroundColor: 'white',
              padding: '20px',
              borderRadius: '12px',
              border: `2px solid ${
                stats.chemistry_rating === 'Excellent' ? COLORS.success :
                stats.chemistry_rating === 'Good' ? COLORS.accent :
                stats.chemistry_rating === 'Average' ? COLORS.warning : COLORS.danger
              }`,
              boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
              <h4 style={{ color: COLORS.primary, margin: 0 }}>{partnership}</h4>
              <div style={{
                backgroundColor: 
                  stats.chemistry_rating === 'Excellent' ? COLORS.success :
                  stats.chemistry_rating === 'Good' ? COLORS.accent :
                  stats.chemistry_rating === 'Average' ? COLORS.warning : COLORS.danger,
                color: 'white',
                padding: '4px 12px',
                borderRadius: '20px',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>
                {stats.chemistry_rating}
              </div>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '15px' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: COLORS.primary }}>
                  {stats.attempts}
                </div>
                <div style={{ fontSize: '12px', color: COLORS.secondary }}>Attempts</div>
              </div>
              
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: COLORS.success }}>
                  {stats.wins}
                </div>
                <div style={{ fontSize: '12px', color: COLORS.secondary }}>Wins</div>
              </div>
              
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: COLORS.accent }}>
                  {(stats.success_rate * 100).toFixed(1)}%
                </div>
                <div style={{ fontSize: '12px', color: COLORS.secondary }}>Success Rate</div>
              </div>
              
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: COLORS.gold }}>
                  {stats.average_points.toFixed(1)}
                </div>
                <div style={{ fontSize: '12px', color: COLORS.secondary }}>Avg Points</div>
              </div>
            </div>
          </div>
        ))}
        
        {Object.keys(analytics.partnership_chemistry).length === 0 && (
          <div style={{
            backgroundColor: COLORS.light,
            padding: '40px',
            borderRadius: '12px',
            textAlign: 'center',
            color: COLORS.secondary
          }}>
            No partnership data available yet. Play some holes with partnerships to see chemistry analysis.
          </div>
        )}
      </div>
    );
  };

  const renderPredictions = () => {
    if (!analytics || !analytics.prediction_models) return null;

    return (
      <div style={{ display: 'grid', gap: '20px' }}>
        <h3 style={{ color: COLORS.primary, marginBottom: '20px' }}>Win Predictions</h3>
        
        {Object.values(analytics.prediction_models).map((prediction, index) => (
          <div
            key={prediction.name}
            style={{
              backgroundColor: 'white',
              padding: '20px',
              borderRadius: '12px',
              border: `2px solid ${index === 0 ? COLORS.gold : COLORS.accent}`,
              boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
              position: 'relative'
            }}
          >
            {index === 0 && (
              <div style={{
                position: 'absolute',
                top: '-10px',
                right: '20px',
                backgroundColor: COLORS.gold,
                color: 'white',
                padding: '4px 12px',
                borderRadius: '20px',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>
                FAVORITE
              </div>
            )}
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
              <h4 style={{ color: COLORS.primary, margin: 0 }}>{prediction.name}</h4>
              <div style={{
                backgroundColor: COLORS.accent,
                color: 'white',
                padding: '4px 12px',
                borderRadius: '20px',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>
                #{prediction.current_position}
              </div>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '15px' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: COLORS.primary }}>
                  {prediction.current_points}
                </div>
                <div style={{ fontSize: '12px', color: COLORS.secondary }}>Current Points</div>
              </div>
              
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: COLORS.success }}>
                  {prediction.win_probability.toFixed(1)}%
                </div>
                <div style={{ fontSize: '12px', color: COLORS.secondary }}>Win Probability</div>
              </div>
              
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: COLORS.accent }}>
                  {prediction.projected_final_points.toFixed(1)}
                </div>
                <div style={{ fontSize: '12px', color: COLORS.secondary }}>Projected Final</div>
              </div>
            </div>
            
            {/* Key Factors */}
            <div style={{ marginTop: '15px' }}>
              <div style={{ fontSize: '14px', color: COLORS.secondary, marginBottom: '8px' }}>
                Key Factors:
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                {prediction.key_factors.map((factor, i) => (
                  <span
                    key={i}
                    style={{
                      backgroundColor: COLORS.light,
                      padding: '3px 8px',
                      borderRadius: '12px',
                      fontSize: '11px',
                      color: COLORS.secondary
                    }}
                  >
                    {factor}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'performance':
        return renderPerformanceTrends();
      case 'betting':
        return renderBettingAnalysis();
      case 'chemistry':
        return renderPartnershipChemistry();
      case 'predictions':
        return renderPredictions();
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '400px',
        color: COLORS.accent,
        fontSize: '18px'
      }}>
        Loading analytics...
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <h1 style={{ color: COLORS.primary, margin: 0, fontSize: '32px' }}>
          Advanced Analytics Dashboard
        </h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={fetchAnalytics}
            disabled={loading}
            style={{
              backgroundColor: COLORS.accent,
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Refresh
          </button>
          <button
            onClick={onBack}
            style={{
              backgroundColor: COLORS.secondary,
              color: 'white',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Back to Game
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{
        display: 'flex',
        marginBottom: '30px',
        backgroundColor: COLORS.light,
        borderRadius: '8px',
        padding: '4px'
      }}>
        {[
          { id: 'performance', label: 'Performance Trends' },
          { id: 'betting', label: 'Betting Analysis' },
          { id: 'chemistry', label: 'Partnership Chemistry' },
          { id: 'predictions', label: 'Win Predictions' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              flex: 1,
              padding: '12px',
              border: 'none',
              borderRadius: '6px',
              backgroundColor: activeTab === tab.id ? COLORS.accent : 'transparent',
              color: activeTab === tab.id ? 'white' : COLORS.primary,
              fontWeight: 'bold',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div>
        {renderTabContent()}
      </div>
    </div>
  );
};

export default AnalyticsDashboard;