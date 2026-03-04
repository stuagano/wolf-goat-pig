import React, { useState } from 'react';
import { useTheme } from '../theme/Provider';
import { Button, Card, Input, Select } from './ui';

const ShotRangeAnalyzer = () => {
  const theme = useTheme();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    lie_type: 'fairway',
    distance_to_pin: 150,
    player_handicap: 10.0,
    hole_number: 10,
    team_situation: 'solo',
    score_differential: 0,
    opponent_styles: []
  });

  const handleInputChange = (e) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) : value
    }));
  };

  const analyzeShot = async () => {
    setLoading(true);
    try {
      const response = await fetch('/wgp/shot-range-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });
      
      const data = await response.json();
      setAnalysis(data.analysis);
    } catch (error) {
      console.error('Error analyzing shot:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (risk) => {
    const riskNum = parseInt(risk);
    if (riskNum <= 30) return 'text-green-600';
    if (riskNum <= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getPlayerStyleIcon = (style) => {
    switch (style) {
      case 'nit': return '🛡️';
      case 'tag': return '⚖️';
      case 'lag': return '⚡';
      case 'maniac': return '🔥';
      default: return '🎯';
    }
  };

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: theme.spacing[6] }}>
      <Card>
        <h2 style={{ 
          fontSize: theme.typography['3xl'], 
          fontWeight: theme.typography.bold, 
          textAlign: 'center', 
          marginBottom: theme.spacing[6],
          color: theme.colors.textPrimary 
        }}>
          🎰 Shot Range Analysis - Poker Style
        </h2>
        
        {/* Input Form */}
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
          gap: theme.spacing[4], 
          marginBottom: theme.spacing[6] 
        }}>
          <Select
            label="Lie Type"
            name="lie_type"
            value={formData.lie_type}
            onChange={handleInputChange}
            options={[
              { value: 'fairway', label: 'Fairway' },
              { value: 'rough', label: 'Rough' },
              { value: 'bunker', label: 'Bunker' },
              { value: 'trees', label: 'Trees' },
              { value: 'first cut', label: 'First Cut' },
              { value: 'hazard', label: 'Hazard' }
            ]}
          />
          
          <Input
            label="Distance to Pin (yards)"
            type="number"
            name="distance_to_pin"
            value={formData.distance_to_pin}
            onChange={handleInputChange}
          />
          
          <Input
            label="Player Handicap"
            type="number"
            name="player_handicap"
            value={formData.player_handicap}
            onChange={handleInputChange}
            step="0.1"
          />
          
          <Input
            label="Hole Number"
            type="number"
            name="hole_number"
            value={formData.hole_number}
            onChange={handleInputChange}
            min="1"
            max="18"
          />
        </div>

        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
          gap: theme.spacing[4], 
          marginBottom: theme.spacing[6] 
        }}>
          <Select
            label="Team Situation"
            name="team_situation"
            value={formData.team_situation}
            onChange={handleInputChange}
            options={[
              { value: 'solo', label: 'Solo' },
              { value: 'partners', label: 'Partners' }
            ]}
          />
          
          <Input
            label="Score Differential"
            type="number"
            name="score_differential"
            value={formData.score_differential}
            onChange={handleInputChange}
          />
          
          <div style={{ display: 'flex', alignItems: 'end' }}>
            <Button
              onClick={analyzeShot}
              disabled={loading}
              variant="primary"
              size="large"
              style={{ width: '100%' }}
            >
              {loading ? '🎲 Analyzing...' : '🎯 Analyze Shot'}
            </Button>
          </div>
        </div>
      </Card>

      {/* Analysis Results */}
      {analysis && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: theme.spacing[6] }}>
          {/* Recommended Shot */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-lg border-l-4 border-blue-500">
            <h3 className="text-xl font-bold text-gray-800 mb-4">
              🎯 Recommended Shot
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {analysis.recommended_shot.type?.replace('_', ' ').toUpperCase()}
                </div>
                <div className="text-sm text-gray-600">Shot Type</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {analysis.recommended_shot.success_rate}
                </div>
                <div className="text-sm text-gray-600">Success Rate</div>
              </div>
              <div className="text-center">
                <div className={`text-2xl font-bold ${getRiskColor(analysis.recommended_shot.risk_level)}`}>
                  {analysis.recommended_shot.risk_level}
                </div>
                <div className="text-sm text-gray-600">Risk Level</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {analysis.recommended_shot.equity_vs_field}
                </div>
                <div className="text-sm text-gray-600">Equity vs Field</div>
              </div>
            </div>
          </div>

          {/* Player Style */}
          <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-6 rounded-lg border-l-4 border-purple-500">
            <h3 className="text-xl font-bold text-gray-800 mb-4">
              {getPlayerStyleIcon(analysis.player_style.profile)} Player Style
            </h3>
            <div className="flex items-center space-x-4">
              <div className="text-lg font-semibold text-purple-600">
                {analysis.player_style.profile.toUpperCase()}
              </div>
              <div className="text-gray-600">
                {analysis.player_style.description}
              </div>
            </div>
          </div>

          {/* All Shot Ranges */}
          <div className="bg-gray-50 p-6 rounded-lg">
            <h3 className="text-xl font-bold text-gray-800 mb-4">
              📊 Available Shot Ranges
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-200">
                  <tr>
                    <th className="px-4 py-2 text-left">Shot Type</th>
                    <th className="px-4 py-2 text-center">Success Rate</th>
                    <th className="px-4 py-2 text-center">Risk Level</th>
                    <th className="px-4 py-2 text-center">Expected Value</th>
                    <th className="px-4 py-2 text-center">Equity</th>
                    <th className="px-4 py-2 text-center">Pot Odds Needed</th>
                  </tr>
                </thead>
                <tbody>
                  {analysis.all_ranges.map((range, index) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-4 py-2 font-semibold">
                        {range.type.replace('_', ' ').toUpperCase()}
                      </td>
                      <td className="px-4 py-2 text-center text-green-600">
                        {range.success_rate}
                      </td>
                      <td className={`px-4 py-2 text-center ${getRiskColor(range.risk)}`}>
                        {range.risk}
                      </td>
                      <td className="px-4 py-2 text-center font-mono">
                        {range.ev}
                      </td>
                      <td className="px-4 py-2 text-center text-purple-600">
                        {range.equity}
                      </td>
                      <td className="px-4 py-2 text-center text-orange-600">
                        {range.pot_odds_needed}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* GTO vs Exploitative */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-green-50 p-4 rounded-lg border-l-4 border-green-500">
              <h4 className="font-bold text-green-800 mb-2">🧠 GTO Recommendation</h4>
              <div className="text-lg font-semibold text-green-600">
                {analysis.gto_recommendation.type?.replace('_', ' ').toUpperCase()}
              </div>
              <div className="text-sm text-green-700 mt-1">
                {analysis.gto_recommendation.reasoning}
              </div>
            </div>
            
            <div className="bg-orange-50 p-4 rounded-lg border-l-4 border-orange-500">
              <h4 className="font-bold text-orange-800 mb-2">🎭 Exploitative Play</h4>
              <div className="text-lg font-semibold text-orange-600">
                {analysis.exploitative_play.type?.replace('_', ' ').toUpperCase()}
              </div>
              <div className="text-sm text-orange-700 mt-1">
                {analysis.exploitative_play.reasoning}
              </div>
            </div>
          </div>

          {/* Strategic Advice */}
          {analysis.strategic_advice && analysis.strategic_advice.length > 0 && (
            <div className="bg-yellow-50 p-6 rounded-lg border-l-4 border-yellow-500">
              <h3 className="text-xl font-bold text-gray-800 mb-4">
                💡 Strategic Advice
              </h3>
              <ul className="space-y-2">
                {analysis.strategic_advice.map((advice, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <span className="text-yellow-600 font-bold">•</span>
                    <span className="text-gray-700">{advice}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 3-Bet Ranges */}
          {analysis['3bet_ranges'] && analysis['3bet_ranges'].length > 0 && (
            <div className="bg-red-50 p-6 rounded-lg border-l-4 border-red-500">
              <h3 className="text-xl font-bold text-gray-800 mb-4">
                🔥 Ultra-Aggressive (3-Bet) Ranges
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {analysis['3bet_ranges'].map((range, index) => (
                  <div key={index} className="bg-white p-3 rounded border">
                    <div className="font-semibold text-red-600">
                      {range.type.replace('_', ' ').toUpperCase()}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">
                      Fold Equity: {range.fold_equity}
                    </div>
                    <div className="text-sm text-gray-600">
                      Bluff Frequency: {range.bluff_frequency}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ShotRangeAnalyzer;