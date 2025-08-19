import React, { useState } from 'react';
import {
  ShotResultWidget,
  BettingOpportunityWidget,
  GameStateWidget,
  StrategicAnalysisWidget
} from './index';

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

const API_URL = process.env.REACT_APP_API_URL || '';

const WolfGoatPigDashboard = () => {
  const [gameState, setGameState] = useState(null);
  const [holeState, setHoleState] = useState(null);
  const [shotResult, setShotResult] = useState(null);
  const [bettingOpportunity, setBettingOpportunity] = useState(null);
  const [bettingAnalysis, setBettingAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Demo data for showcasing widgets
  const demoShotResult = {
    shot_number: 2,
    lie_type: 'fairway',
    distance_to_pin: 145,
    shot_quality: 'good',
    made_shot: false,
    penalty_strokes: 0
  };

  const demoBettingOpportunity = {
    opportunity_type: 'double_opportunity',
    message: "Scott's approach shot landed 25 feet from the pin. This creates a good opportunity to double the bet if you're confident in your team's position.",
    options: ['offer_double', 'pass'],
    probability_analysis: {
      success_rate: 0.65,
      risk_level: 'medium',
      expected_value: 0.8
    },
    recommended_action: 'offer_double',
    risk_assessment: 'medium'
  };

  const demoBettingAnalysis = {
    shot_assessment: {
      quality_rating: 'good',
      distance_remaining: 145,
      strategic_value: 'high'
    },
    team_position: {
      current_wager: 4,
      potential_double: 8,
      momentum: 'positive'
    },
    strategic_recommendations: [
      "Consider doubling the bet given the favorable position",
      "Your team has a 2-stroke advantage on this hole",
      "Scott's conservative personality suggests he may decline a double"
    ],
    computer_tendencies: {
      'p2': {
        personality: 'conservative',
        betting_style: 'cautious',
        double_acceptance: 'rarely'
      },
      'p3': {
        personality: 'aggressive',
        betting_style: 'bold',
        double_acceptance: 'often'
      }
    }
  };

  const startDemoGame = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/wgp/start-game`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_count: 4,
          players: [
            { id: 'p1', name: 'Bob', handicap: 10.5, isComputer: false },
            { id: 'p2', name: 'Scott', handicap: 15, isComputer: true, personality: 'conservative' },
            { id: 'p3', name: 'Vince', handicap: 8, isComputer: true, personality: 'aggressive' },
            { id: 'p4', name: 'Mike', handicap: 20.5, isComputer: true, personality: 'strategic' }
          ],
          double_points_round: false,
          annual_banquet: false
        })
      });

      if (response.ok) {
        const data = await response.json();
        setGameState(data.game_state);
        setMessage('Demo game started! Check out the beautiful widgets below.');
      } else {
        setMessage('Error starting demo game');
      }
    } catch (error) {
      setMessage('Network error starting demo game');
    } finally {
      setLoading(false);
    }
  };

  const playNextShot = async () => {
    if (!gameState) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/wgp/play-next-shot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });

      if (response.ok) {
        const data = await response.json();
        
        // Update state with real data
        if (data.game_state) setGameState(data.game_state);
        if (data.hole_state) setHoleState(data.hole_state);
        if (data.shot_result) setShotResult(data.shot_result);
        if (data.betting_opportunity) setBettingOpportunity(data.betting_opportunity);
        if (data.betting_analysis) setBettingAnalysis(data.betting_analysis);
        
        setMessage('Shot played! Check the widgets for updated information.');
      } else {
        setMessage('Error playing shot');
      }
    } catch (error) {
      setMessage('Network error playing shot');
    } finally {
      setLoading(false);
    }
  };

  const handleBettingDecision = (decision) => {
    setMessage(`Betting decision made: ${decision}`);
    setBettingOpportunity(null); // Clear the opportunity after decision
  };

  return (
    <div style={{
      background: COLORS.bg,
      minHeight: '100vh',
      padding: '20px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      {/* Header */}
      <div style={{
        background: COLORS.card,
        borderRadius: 16,
        boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
        padding: 24,
        marginBottom: 24,
        textAlign: 'center'
      }}>
        <h1 style={{ margin: '0 0 8px 0', color: COLORS.text }}>
          🏌️ Wolf Goat Pig Dashboard
        </h1>
        <p style={{ margin: '0 0 20px 0', color: COLORS.muted }}>
          Beautiful widgets for displaying rich Wolf Goat Pig game data
        </p>
        
        <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={startDemoGame}
            disabled={loading}
            style={{
              background: COLORS.primary,
              color: 'white',
              border: 'none',
              borderRadius: 8,
              padding: '12px 24px',
              fontWeight: 600,
              fontSize: 16,
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1
            }}
          >
            {loading ? 'Starting...' : '🎮 Start Demo Game'}
          </button>
          
          <button
            onClick={playNextShot}
            disabled={loading || !gameState}
            style={{
              background: COLORS.success,
              color: 'white',
              border: 'none',
              borderRadius: 8,
              padding: '12px 24px',
              fontWeight: 600,
              fontSize: 16,
              cursor: (loading || !gameState) ? 'not-allowed' : 'pointer',
              opacity: (loading || !gameState) ? 0.6 : 1
            }}
          >
            {loading ? 'Playing...' : '⏭️ Play Next Shot'}
          </button>
        </div>
        
        {message && (
          <div style={{
            marginTop: 16,
            padding: 12,
            background: '#e8f5e8',
            border: `1px solid ${COLORS.success}`,
            borderRadius: 8,
            color: COLORS.success,
            fontWeight: 600
          }}>
            {message}
          </div>
        )}
      </div>

      {/* Widgets Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: 24,
        maxWidth: 1400,
        margin: '0 auto'
      }}>
        
        {/* Game State Widget */}
        <div>
          <h2 style={{ margin: '0 0 16px 0', color: COLORS.text }}>
            📊 Game State
          </h2>
          <GameStateWidget 
            gameState={gameState} 
            holeState={holeState} 
          />
        </div>

        {/* Shot Result Widget */}
        <div>
          <h2 style={{ margin: '0 0 16px 0', color: COLORS.text }}>
            🎯 Shot Result
          </h2>
          <ShotResultWidget 
            shotResult={shotResult || demoShotResult}
            playerName="Scott"
            isComputer={true}
          />
        </div>

        {/* Betting Opportunity Widget */}
        <div>
          <h2 style={{ margin: '0 0 16px 0', color: COLORS.text }}>
            💰 Betting Opportunity
          </h2>
          <BettingOpportunityWidget 
            bettingOpportunity={bettingOpportunity || demoBettingOpportunity}
            onDecision={handleBettingDecision}
          />
        </div>

        {/* Strategic Analysis Widget */}
        <div>
          <h2 style={{ margin: '0 0 16px 0', color: COLORS.text }}>
            🧠 Strategic Analysis
          </h2>
          <StrategicAnalysisWidget 
            bettingAnalysis={bettingAnalysis || demoBettingAnalysis}
          />
        </div>
      </div>

      {/* Instructions */}
      <div style={{
        background: COLORS.card,
        borderRadius: 16,
        boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
        padding: 24,
        marginTop: 32,
        maxWidth: 800,
        margin: '32px auto 0'
      }}>
        <h3 style={{ margin: '0 0 16px 0', color: COLORS.text }}>
          🎯 How to Use These Widgets
        </h3>
        <div style={{ fontSize: 14, lineHeight: 1.6, color: COLORS.text }}>
          <p><strong>1. Game State Widget:</strong> Shows current hole, team formations, betting state, and player positions.</p>
          <p><strong>2. Shot Result Widget:</strong> Displays detailed shot information with quality ratings and visual indicators.</p>
          <p><strong>3. Betting Opportunity Widget:</strong> Presents betting decisions with risk assessment and recommendations.</p>
          <p><strong>4. Strategic Analysis Widget:</strong> Provides AI-powered insights and computer player tendencies.</p>
          <p><strong>Integration:</strong> Import these widgets into your existing components and pass the API data to them.</p>
        </div>
      </div>
    </div>
  );
};

export default WolfGoatPigDashboard; 