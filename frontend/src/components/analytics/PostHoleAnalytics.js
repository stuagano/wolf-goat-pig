import React, { useState, useEffect } from 'react';
import Card from '../ui/Card';

/**
 * Post-Hole Analytics Component
 * Displays comprehensive analysis and insights after completing a hole
 */
const PostHoleAnalytics = ({ analytics, onContinue, onReplay, onPracticeScenario }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [expandedSections, setExpandedSections] = useState({});

  if (!analytics) return null;

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Color scheme
  const colors = {
    excellent: '#10b981',
    good: '#3b82f6',
    neutral: '#6b7280',
    poor: '#f59e0b',
    terrible: '#ef4444',
    primary: '#3b82f6',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    dark: '#1f2937',
    light: '#f3f4f6'
  };

  // Performance indicators
  const getPerformanceColor = (score) => {
    if (score >= 80) return colors.excellent;
    if (score >= 60) return colors.good;
    if (score >= 40) return colors.neutral;
    if (score >= 20) return colors.poor;
    return colors.terrible;
  };

  const getPerformanceLabel = (score) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Average';
    if (score >= 20) return 'Poor';
    return 'Needs Work';
  };

  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Hole Result Summary */}
      <Card className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-2xl font-bold text-gray-800">
              Hole {analytics.hole_number} Complete
            </h3>
            <p className="text-gray-600 mt-1">
              Par {analytics.hole_par} • {analytics.hole_yardage} yards
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold" style={{ color: analytics.quarters_exchanged > 0 ? colors.success : colors.danger }}>
              {analytics.quarters_exchanged > 0 ? '+' : ''}{analytics.quarters_exchanged} Quarters
            </div>
            <p className="text-sm text-gray-600 mt-1">
              {analytics.winner === 'solo_player' ? 'Won Solo!' : 
               analytics.winner === 'team1' ? 'Team Victory' : 
               analytics.winner === 'tie' ? 'Tied' : 'Lost'}
            </p>
          </div>
        </div>
      </Card>

      {/* Performance Scores */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="p-4 text-center">
          <div className="text-3xl font-bold" style={{ color: getPerformanceColor(analytics.overall_performance) }}>
            {Math.round(analytics.overall_performance)}
          </div>
          <div className="text-sm text-gray-600 mt-1">Overall Performance</div>
          <div className="text-xs mt-2" style={{ color: getPerformanceColor(analytics.overall_performance) }}>
            {getPerformanceLabel(analytics.overall_performance)}
          </div>
        </Card>
        
        <Card className="p-4 text-center">
          <div className="text-3xl font-bold" style={{ color: getPerformanceColor(analytics.decision_making_score) }}>
            {Math.round(analytics.decision_making_score)}
          </div>
          <div className="text-sm text-gray-600 mt-1">Decision Making</div>
        </Card>
        
        <Card className="p-4 text-center">
          <div className="text-3xl font-bold" style={{ color: getPerformanceColor(analytics.risk_management_score) }}>
            {Math.round(analytics.risk_management_score)}
          </div>
          <div className="text-sm text-gray-600 mt-1">Risk Management</div>
        </Card>
      </div>

      {/* Key Insights */}
      <Card className="p-6">
        <h4 className="text-lg font-semibold mb-4 flex items-center">
          💡 Key Insights
        </h4>
        <div className="space-y-3">
          {analytics.best_decision && (
            <div className="flex items-start p-3 bg-green-50 rounded-lg">
              <span className="text-green-500 mr-3">✅</span>
              <div>
                <div className="font-medium text-green-800">Best Decision</div>
                <div className="text-sm text-green-700 mt-1">{analytics.best_decision}</div>
              </div>
            </div>
          )}
          
          {analytics.biggest_mistake && (
            <div className="flex items-start p-3 bg-red-50 rounded-lg">
              <span className="text-red-500 mr-3">❌</span>
              <div>
                <div className="font-medium text-red-800">Biggest Mistake</div>
                <div className="text-sm text-red-700 mt-1">{analytics.biggest_mistake}</div>
              </div>
            </div>
          )}
          
          {analytics.learning_points?.map((point, idx) => (
            <div key={idx} className="flex items-start p-3 bg-blue-50 rounded-lg">
              <span className="text-blue-500 mr-3">📝</span>
              <div className="text-sm text-blue-800">{point}</div>
            </div>
          ))}
        </div>
      </Card>

      {/* Quick Actions */}
      <div className="flex gap-3">
        <button
          onClick={onContinue}
          className="flex-1 py-3 px-6 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          Continue to Next Hole →
        </button>
        {onReplay && (
          <button
            onClick={onReplay}
            className="py-3 px-6 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
          >
            Replay Hole
          </button>
        )}
      </div>
    </div>
  );

  const renderDecisionsTab = () => (
    <div className="space-y-4">
      <h4 className="text-lg font-semibold mb-4">Decision Analysis</h4>
      
      {/* Partnership Decision */}
      {analytics.partnership_analysis && (
        <Card className="p-4">
          <div className="flex justify-between items-start mb-3">
            <h5 className="font-medium">Partnership Decision</h5>
            <span className={`px-2 py-1 rounded text-xs font-medium ${
              analytics.partnership_analysis.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}>
              {analytics.partnership_analysis.success ? 'Successful' : 'Failed'}
            </span>
          </div>
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-gray-600">Formation:</span>{' '}
              {analytics.partnership_analysis.partnership_formed ? 
                `Partnered with ${analytics.partnership_analysis.partner_id}` : 
                'Went Solo'}
            </div>
            <div>
              <span className="text-gray-600">Timing:</span>{' '}
              {analytics.partnership_analysis.timing}
            </div>
            <div>
              <span className="text-gray-600">Chemistry:</span>{' '}
              <div className="inline-flex items-center">
                <div className="w-24 h-2 bg-gray-200 rounded-full mr-2">
                  <div 
                    className="h-2 bg-blue-500 rounded-full" 
                    style={{ width: `${analytics.partnership_analysis.chemistry_rating * 100}%` }}
                  />
                </div>
                <span>{Math.round(analytics.partnership_analysis.chemistry_rating * 100)}%</span>
              </div>
            </div>
            {analytics.partnership_analysis.explanation && (
              <div className="mt-2 p-2 bg-gray-50 rounded text-gray-700">
                {analytics.partnership_analysis.explanation}
              </div>
            )}
          </div>
        </Card>
      )}
      
      {/* Individual Decision Points */}
      <div className="space-y-3">
        {analytics.decision_points?.map((decision, idx) => (
          <Card key={idx} className="p-4">
            <div className="flex justify-between items-start mb-2">
              <div className="font-medium capitalize">
                {decision.decision_type.replace(/_/g, ' ')}
              </div>
              <span 
                className="px-2 py-1 rounded text-xs font-medium"
                style={{ 
                  backgroundColor: colors[decision.quality] + '20',
                  color: colors[decision.quality]
                }}
              >
                {decision.quality}
              </span>
            </div>
            <div className="text-sm text-gray-600">
              <div>Decision: {decision.decision_made}</div>
              <div>Impact: {decision.quarters_impact > 0 ? '+' : ''}{decision.quarters_impact} quarters</div>
            </div>
            {decision.explanation && (
              <div className="mt-2 text-xs text-gray-500">
                {decision.explanation}
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  );

  const renderBettingTab = () => (
    <div className="space-y-4">
      <h4 className="text-lg font-semibold mb-4">Betting Analysis</h4>
      
      <Card className="p-4">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <div className="text-2xl font-bold text-blue-600">
              {analytics.betting_analysis?.doubles_offered || 0}
            </div>
            <div className="text-sm text-gray-600">Doubles Offered</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-600">
              {analytics.betting_analysis?.doubles_accepted || 0}
            </div>
            <div className="text-sm text-gray-600">Doubles Accepted</div>
          </div>
        </div>
        
        {/* Aggression Meter */}
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-1">
            <span>Betting Aggression</span>
            <span>{Math.round((analytics.betting_analysis?.aggressive_rating || 0) * 100)}%</span>
          </div>
          <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className="h-3 bg-gradient-to-r from-green-400 to-red-500 rounded-full transition-all duration-500"
              style={{ width: `${(analytics.betting_analysis?.aggressive_rating || 0) * 100}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Conservative</span>
            <span>Aggressive</span>
          </div>
        </div>
        
        {/* Timing Quality */}
        <div className="flex items-center justify-between py-2 border-t">
          <span className="text-sm text-gray-600">Timing Quality</span>
          <span className={`px-2 py-1 rounded text-xs font-medium ${
            analytics.betting_analysis?.timing_quality === 'perfect' ? 'bg-green-100 text-green-700' :
            analytics.betting_analysis?.timing_quality === 'good' ? 'bg-blue-100 text-blue-700' :
            'bg-yellow-100 text-yellow-700'
          }`}>
            {analytics.betting_analysis?.timing_quality || 'Unknown'}
          </span>
        </div>
        
        {/* Duncan Usage */}
        {analytics.betting_analysis?.duncan_used && (
          <div className="mt-3 p-3 bg-purple-50 rounded-lg">
            <div className="flex items-center">
              <span className="text-purple-600 mr-2">🎯</span>
              <span className="text-sm font-medium text-purple-800">Duncan Invoked!</span>
            </div>
          </div>
        )}
      </Card>
      
      {/* Missed Opportunities */}
      {analytics.betting_analysis?.missed_opportunities?.length > 0 && (
        <Card className="p-4 border-yellow-200 bg-yellow-50">
          <h5 className="font-medium text-yellow-800 mb-2">Missed Opportunities</h5>
          <ul className="space-y-1">
            {analytics.betting_analysis.missed_opportunities.map((opp, idx) => (
              <li key={idx} className="text-sm text-yellow-700 flex items-start">
                <span className="mr-2">•</span>
                <span>{opp}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );

  const renderShotsTab = () => (
    <div className="space-y-4">
      <h4 className="text-lg font-semibold mb-4">Shot Analysis</h4>
      
      {/* Shot Quality Distribution */}
      <Card className="p-4">
        <h5 className="font-medium mb-3">Shot Quality Distribution</h5>
        <div className="space-y-2">
          {Object.entries(analytics.shot_analysis?.shot_quality_distribution || {}).map(([quality, count]) => (
            <div key={quality} className="flex items-center">
              <span className="w-20 text-sm capitalize">{quality}</span>
              <div className="flex-1 mx-3">
                <div className="w-full h-6 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className="h-6 rounded-full flex items-center justify-end pr-2"
                    style={{ 
                      width: `${(count / analytics.shot_analysis.total_shots) * 100}%`,
                      backgroundColor: colors[quality]
                    }}
                  >
                    <span className="text-xs text-white font-medium">{count}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
      
      {/* Pressure Performance */}
      <Card className="p-4">
        <h5 className="font-medium mb-3">Pressure Performance</h5>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold" style={{ 
              color: analytics.shot_analysis?.pressure_performance > 0.7 ? colors.success : colors.warning 
            }}>
              {Math.round((analytics.shot_analysis?.pressure_performance || 0) * 100)}%
            </div>
            <div className="text-sm text-gray-600">Success rate in clutch moments</div>
          </div>
          <div className="text-right">
            <div className="text-lg font-semibold">
              {analytics.shot_analysis?.clutch_shots?.length || 0}
            </div>
            <div className="text-sm text-gray-600">Clutch shots</div>
          </div>
        </div>
      </Card>
      
      {/* Best and Worst Shots */}
      <div className="grid grid-cols-2 gap-4">
        {analytics.shot_analysis?.best_shot && (
          <Card className="p-3 bg-green-50">
            <div className="text-sm font-medium text-green-800 mb-1">Best Shot</div>
            <div className="text-xs text-green-700">
              {analytics.shot_analysis.best_shot.quality} shot
              {analytics.shot_analysis.best_shot.distance && 
                ` • ${analytics.shot_analysis.best_shot.distance}yd to pin`}
            </div>
          </Card>
        )}
        
        {analytics.shot_analysis?.worst_shot && (
          <Card className="p-3 bg-red-50">
            <div className="text-sm font-medium text-red-800 mb-1">Worst Shot</div>
            <div className="text-xs text-red-700">
              {analytics.shot_analysis.worst_shot.quality} shot
              {analytics.shot_analysis.worst_shot.distance && 
                ` • ${analytics.shot_analysis.worst_shot.distance}yd to pin`}
            </div>
          </Card>
        )}
      </div>
    </div>
  );

  const renderComparisonTab = () => (
    <div className="space-y-4">
      <h4 className="text-lg font-semibold mb-4">Comparisons & Recommendations</h4>
      
      {/* AI Comparison */}
      <Card className="p-4">
        <h5 className="font-medium mb-3 flex items-center">
          <span className="mr-2">🤖</span>
          AI Comparison
        </h5>
        <div className="space-y-2 text-sm">
          <div>
            <span className="text-gray-600">Different Decisions:</span>{' '}
            <span className="font-medium">{analytics.ai_comparison?.different_decisions || 0}</span>
          </div>
          <div>
            <span className="text-gray-600">AI Expected Outcome:</span>{' '}
            <span className="font-medium">{analytics.ai_comparison?.ai_expected_outcome}</span>
          </div>
          {analytics.ai_comparison?.key_difference && (
            <div className="mt-2 p-2 bg-blue-50 rounded text-blue-800">
              💡 {analytics.ai_comparison.key_difference}
            </div>
          )}
        </div>
      </Card>
      
      {/* Historical Comparison */}
      <Card className="p-4">
        <h5 className="font-medium mb-3 flex items-center">
          <span className="mr-2">📊</span>
          Historical Performance
        </h5>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Your average on this hole</span>
            <span className="font-medium">{analytics.historical_comparison?.avg_performance_this_hole || 0}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">This round</span>
            <span className="font-medium" style={{ 
              color: analytics.historical_comparison?.improvement ? colors.success : colors.warning 
            }}>
              {analytics.historical_comparison?.this_hole_performance || 0}
              {analytics.historical_comparison?.improvement ? ' ↑' : ' ↓'}
            </span>
          </div>
        </div>
      </Card>
      
      {/* Tips for Improvement */}
      {analytics.tips_for_improvement?.length > 0 && (
        <Card className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50">
          <h5 className="font-medium mb-3">Tips for Improvement</h5>
          <ul className="space-y-2">
            {analytics.tips_for_improvement.map((tip, idx) => (
              <li key={idx} className="flex items-start text-sm">
                <span className="text-blue-500 mr-2 mt-0.5">→</span>
                <span className="text-gray-700">{tip}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
      
      {/* Practice Recommendations */}
      {analytics.similar_scenarios_to_practice?.length > 0 && (
        <Card className="p-4">
          <h5 className="font-medium mb-3">Practice Recommendations</h5>
          <div className="space-y-2">
            {analytics.similar_scenarios_to_practice.map((scenario, idx) => (
              <button
                key={idx}
                onClick={() => onPracticeScenario && onPracticeScenario(scenario)}
                className="w-full text-left p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors text-sm"
              >
                <div className="flex justify-between items-center">
                  <span>{scenario}</span>
                  <span className="text-gray-400">→</span>
                </div>
              </button>
            ))}
          </div>
        </Card>
      )}
    </div>
  );

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'decisions', label: 'Decisions', icon: '🎯' },
    { id: 'betting', label: 'Betting', icon: '💰' },
    { id: 'shots', label: 'Shots', icon: '⛳' },
    { id: 'comparison', label: 'Compare', icon: '📈' }
  ];

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-gray-800 mb-2">
          Post-Hole Analysis
        </h2>
        <p className="text-gray-600">
          Review your performance and learn from this hole
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 overflow-x-auto">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <span className="mr-2">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'decisions' && renderDecisionsTab()}
        {activeTab === 'betting' && renderBettingTab()}
        {activeTab === 'shots' && renderShotsTab()}
        {activeTab === 'comparison' && renderComparisonTab()}
      </div>
    </div>
  );
};

export default PostHoleAnalytics;