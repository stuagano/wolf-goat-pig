import React, { useState } from 'react';
import AnalyticsDashboard from './AnalyticsDashboard';
import HoleStrategyDisplay from './HoleStrategyDisplay';

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

const EnhancedWGPInterface = () => {
  const [gameState, setGameState] = useState(null);
  const [availableActions, setAvailableActions] = useState([]);
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [currentView, setCurrentView] = useState('game'); // 'game', 'analysis', 'timeline', 'analytics'
  const [postHoleAnalysis, setPostHoleAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [gameId] = useState('enhanced-wgp-123');

  const sendAction = async (actionType, payload = null) => {
    setLoading(true);
    try {
      const response = await fetch(`/wgp/${gameId}/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action_type: actionType,
          payload: payload
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        setGameState(data.game_state);
        setAvailableActions(data.available_actions);
        
        if (data.timeline_event) {
          setTimelineEvents(prev => [...prev, data.timeline_event]);
          
          // If this is a post-hole analysis event, extract the analysis
          if (data.timeline_event.type === 'post_hole_analysis') {
            setPostHoleAnalysis(data.timeline_event.details);
            setCurrentView('analysis');
          }
        }
        if (process.env.NODE_ENV !== 'production') {
          console.debug('Action response:', data);
        }
      } else {
        const errorText = await response.text();
        console.error('Action error:', errorText);
      }
    } catch (error) {
      console.error('Network error:', error);
    } finally {
      setLoading(false);
    }
  };

  const initializeGame = (playerCount = 4) => {
    const playerConfigs = {
      4: [
        { name: 'Scott', handicap: 10.5 },
        { name: 'Bob', handicap: 15.0 },
        { name: 'Tim', handicap: 8.0 },
        { name: 'Steve', handicap: 20.5 }
      ],
      5: [
        { name: 'Scott', handicap: 10.5 },
        { name: 'Bob', handicap: 15.0 },
        { name: 'Tim', handicap: 8.0 },
        { name: 'Steve', handicap: 20.5 },
        { name: 'Alex', handicap: 12.0 }
      ],
      6: [
        { name: 'Scott', handicap: 10.5 },
        { name: 'Bob', handicap: 15.0 },
        { name: 'Tim', handicap: 8.0 },
        { name: 'Steve', handicap: 20.5 },
        { name: 'Alex', handicap: 12.0 },
        { name: 'Mike', handicap: 18.0 }
      ]
    };
    
    sendAction('INITIALIZE_GAME', {
      players: playerConfigs[playerCount]
    });
  };

  const renderHoleStateCard = () => {
    if (!gameState || !gameState.hole_state) return null;

    const holeState = gameState.hole_state;
    const teams = holeState.teams;
    const betting = holeState.betting;

    // Get difficulty color
    const getDifficultyColor = (difficulty) => {
      switch (difficulty) {
        case 'Easy': return COLORS.success;
        case 'Medium': return COLORS.warning;
        case 'Hard': return COLORS.danger;
        case 'Very Hard': return COLORS.dark;
        default: return COLORS.secondary;
      }
    };

    return (
      <div style={{
        backgroundColor: COLORS.light,
        border: `3px solid ${COLORS.accent}`,
        borderRadius: '12px',
        padding: '24px',
        marginBottom: '24px',
        boxShadow: '0 4px 8px rgba(0,0,0,0.1)'
      }}>
        {/* Hole Information Header */}
        <div style={{ 
          backgroundColor: 'white',
          padding: '16px',
          borderRadius: '8px',
          marginBottom: '20px',
          border: `2px solid ${COLORS.accent}`
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h2 style={{ color: COLORS.primary, fontSize: '28px', margin: 0 }}>
                Hole {gameState.current_hole} - Par {holeState.hole_par || 4}
              </h2>
              <div style={{ display: 'flex', gap: '20px', alignItems: 'center', marginTop: '8px' }}>
                <span style={{ fontSize: '16px', color: COLORS.secondary }}>
                  📏 {holeState.hole_yardage || 400} yards
                </span>
                <span style={{ 
                  fontSize: '14px', 
                  color: getDifficultyColor(holeState.hole_difficulty),
                  fontWeight: 'bold',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  backgroundColor: getDifficultyColor(holeState.hole_difficulty) + '20'
                }}>
                  {holeState.hole_difficulty || 'Medium'} (HCP #{holeState.stroke_index || 10})
                </span>
                <span style={{ fontSize: '16px', color: COLORS.primary }}>
                  {gameState.game_phase}
                </span>
              </div>
            </div>
            <div style={{
              backgroundColor: COLORS.warning,
              color: 'white',
              padding: '8px 16px',
              borderRadius: '20px',
              fontSize: '18px',
              fontWeight: 'bold'
            }}>
              {betting?.current_wager || 1} Quarters
            </div>
          </div>
        </div>

        {/* Hole Progression Visual */}
        {renderHoleProgression()}

        {/* Hole Strategy Display */}
        <HoleStrategyDisplay 
          holeState={holeState} 
          players={gameState.players || []} 
          gameState={gameState} 
        />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px' }}>
          {/* Team Formation */}
          <div style={{
            backgroundColor: 'white',
            padding: '16px',
            borderRadius: '8px',
            border: `2px solid ${COLORS.secondary}`
          }}>
            <h3 style={{ color: COLORS.primary, marginTop: 0 }}>Team Formation</h3>
            <p><strong>Captain:</strong> {teams?.captain_name || 'Unknown'}</p>
            <p><strong>Format:</strong> {teams?.type || 'Pending'}</p>
            {teams?.type === 'partners' && teams.team1 && (
              <>
                <p><strong>Team 1:</strong> {teams.team1.join(', ')}</p>
                <p><strong>Team 2:</strong> {teams.team2?.join(', ') || 'TBD'}</p>
              </>
            )}
            {teams?.type === 'solo' && (
              <>
                <p><strong>Solo Player:</strong> {teams.solo_player_name || 'Unknown'}</p>
                <p><strong>Risk Level:</strong> <span style={{ color: COLORS.danger }}>HIGH</span></p>
              </>
            )}
          </div>

          {/* Betting Status */}
          <div style={{
            backgroundColor: 'white',
            padding: '16px',
            borderRadius: '8px',
            border: `2px solid ${COLORS.gold}`
          }}>
            <h3 style={{ color: COLORS.primary, marginTop: 0 }}>Betting Status</h3>
            <p><strong>Base Wager:</strong> {betting?.base_wager || 1}</p>
            <p><strong>Current Wager:</strong> {betting?.current_wager || 1}</p>
            <p><strong>Multiplier:</strong> {betting?.base_wager ? (betting.current_wager / betting.base_wager).toFixed(1) : '1.0'}x</p>
            {betting?.special_rules && betting.special_rules.length > 0 && (
              <p><strong>Special Rules:</strong> {betting.special_rules.join(', ')}</p>
            )}
          </div>

          {/* Player Standings */}
          <div style={{
            backgroundColor: 'white',
            padding: '16px',
            borderRadius: '8px',
            border: `2px solid ${COLORS.success}`
          }}>
            <h3 style={{ color: COLORS.primary, marginTop: 0 }}>Current Standings</h3>
            {gameState.players && gameState.players
              .sort((a, b) => b.points - a.points)
              .map((player, index) => (
                <div key={player.id} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: '4px',
                  color: index === 0 ? COLORS.success : (player.points < 0 ? COLORS.danger : COLORS.dark)
                }}>
                  <span>{player.name}</span>
                  <span style={{ fontWeight: 'bold' }}>{player.points > 0 ? '+' : ''}{player.points}</span>
                </div>
              ))}
          </div>
        </div>
      </div>
    );
  };

  const renderDecisionButtons = () => {
    if (!availableActions || availableActions.length === 0) return null;

    return (
      <div style={{
        backgroundColor: COLORS.secondary,
        padding: '24px',
        borderRadius: '12px',
        marginBottom: '24px'
      }}>
        <h3 style={{ color: 'white', marginTop: 0, fontSize: '24px', textAlign: 'center' }}>
          Available Decisions
        </h3>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '16px',
          marginTop: '20px'
        }}>
          {availableActions.map((action, index) => {
            const buttonColor = getActionButtonColor(action.action_type);
            const actionDescription = getActionDescription(action.action_type);
            
            return (
              <button
                key={index}
                onClick={() => handleActionClick(action)}
                disabled={loading}
                style={{
                  backgroundColor: buttonColor,
                  color: 'white',
                  border: 'none',
                  padding: '20px',
                  borderRadius: '10px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.6 : 1,
                  minHeight: '120px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                  textAlign: 'center',
                  transition: 'all 0.3s ease',
                  boxShadow: '0 4px 8px rgba(0,0,0,0.2)'
                }}
                onMouseEnter={(e) => {
                  if (!loading) {
                    e.target.style.transform = 'translateY(-2px)';
                    e.target.style.boxShadow = '0 6px 12px rgba(0,0,0,0.3)';
                  }
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
                }}
              >
                <div style={{ fontSize: '18px', marginBottom: '8px' }}>
                  {action.prompt}
                </div>
                {action.player_turn && (
                  <div style={{ fontSize: '14px', opacity: 0.9 }}>
                    {action.player_turn}'s turn
                  </div>
                )}
                <div style={{ fontSize: '12px', marginTop: '8px', opacity: 0.8 }}>
                  {actionDescription}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    );
  };

  const getActionButtonColor = (actionType) => {
    switch (actionType) {
      case 'REQUEST_PARTNERSHIP': return COLORS.accent;
      case 'RESPOND_PARTNERSHIP': return COLORS.success;
      case 'DECLARE_SOLO': return COLORS.danger;
      case 'OFFER_DOUBLE': return COLORS.warning;
      case 'ACCEPT_DOUBLE': return COLORS.gold;
      case 'AARDVARK_JOIN_REQUEST': return COLORS.purple;
      case 'AARDVARK_TOSS': return COLORS.danger;
      case 'AARDVARK_GO_SOLO': return COLORS.warning;
      case 'PING_PONG_AARDVARK': return COLORS.gold;
      case 'PLAY_SHOT': return COLORS.primary;
      case 'ADVANCE_HOLE': return COLORS.success;
      case 'GET_POST_HOLE_ANALYSIS': return COLORS.purple;
      case 'ENTER_HOLE_SCORES': return COLORS.accent;
      default: return COLORS.primary;
    }
  };

  const getActionDescription = (actionType) => {
    switch (actionType) {
      case 'REQUEST_PARTNERSHIP': return 'Ask another player to be your partner';
      case 'RESPOND_PARTNERSHIP': return 'Accept or decline partnership request';
      case 'DECLARE_SOLO': return 'Go solo against the field - high risk, high reward';
      case 'OFFER_DOUBLE': return 'Double the wager - increase the stakes';
      case 'ACCEPT_DOUBLE': return 'Accept or decline the double offer';
      case 'AARDVARK_JOIN_REQUEST': return 'Aardvark asks to join a team';
      case 'AARDVARK_TOSS': return 'Accept or toss the Aardvark (doubles wager if tossed)';
      case 'AARDVARK_GO_SOLO': return 'Aardvark goes solo - 3 for 2 odds';
      case 'PING_PONG_AARDVARK': return 'Re-toss the Aardvark (doubles wager again)';
      case 'PLAY_SHOT': return 'Hit your shot and advance the hole';
      case 'ADVANCE_HOLE': return 'Move to the next hole';
      case 'GET_POST_HOLE_ANALYSIS': return 'View detailed analysis of the completed hole';
      case 'ENTER_HOLE_SCORES': return 'Enter scores to calculate points';
      default: return 'Perform this action';
    }
  };

  const handleActionClick = (action) => {
    if (action.action_type === 'ENTER_HOLE_SCORES') {
      // Show score entry modal
      showScoreEntryModal();
    } else if (action.action_type === 'GET_POST_HOLE_ANALYSIS') {
      sendAction(action.action_type, action.payload);
    } else {
      sendAction(action.action_type, action.payload);
    }
  };

  const showScoreEntryModal = () => {
    const scores = {};
    if (gameState && gameState.players) {
      gameState.players.forEach(player => {
        const score = prompt(`Enter score for ${player.name}:`);
        if (score !== null && !isNaN(score)) {
          scores[player.id] = parseInt(score);
        }
      });
      
      if (Object.keys(scores).length === gameState.players.length) {
        sendAction('ENTER_HOLE_SCORES', { scores });
      }
    }
  };

  const renderEnhancedTimeline = () => {
    if (timelineEvents.length === 0) return null;

    return (
      <div style={{
        backgroundColor: 'white',
        padding: '24px',
        borderRadius: '12px',
        marginBottom: '24px',
        border: `2px solid ${COLORS.accent}`
      }}>
        <h3 style={{ color: COLORS.primary, marginTop: 0, fontSize: '24px' }}>
          Game Timeline
        </h3>
        
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {timelineEvents.map((event, index) => (
            <div
              key={event.id || index}
              style={{
                marginBottom: '16px',
                padding: '16px',
                backgroundColor: COLORS.light,
                borderRadius: '8px',
                borderLeft: `6px solid ${getEventColor(event.type)}`,
                position: 'relative'
              }}
            >
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: '8px'
              }}>
                <div style={{
                  fontWeight: 'bold',
                  color: getEventColor(event.type),
                  fontSize: '16px'
                }}>
                  {getEventIcon(event.type)} {event.type.replace('_', ' ').toUpperCase()}
                </div>
                <div style={{
                  fontSize: '12px',
                  color: COLORS.secondary,
                  opacity: 0.8
                }}>
                  {new Date(event.timestamp).toLocaleTimeString()}
                </div>
              </div>
              
              <div style={{ fontSize: '14px', lineHeight: '1.4', marginBottom: '8px' }}>
                {event.description}
              </div>
              
              {event.player_name && (
                <div style={{
                  fontSize: '12px',
                  color: COLORS.primary,
                  fontWeight: 'bold'
                }}>
                  Player: {event.player_name}
                </div>
              )}
              
              {event.details && (
                <div style={{
                  marginTop: '12px',
                  padding: '8px',
                  backgroundColor: 'white',
                  borderRadius: '4px',
                  fontSize: '12px',
                  color: COLORS.secondary
                }}>
                  <strong>Details:</strong> {JSON.stringify(event.details, null, 2)}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderPostHoleAnalysis = () => {
    if (!postHoleAnalysis) return null;

    return (
      <div style={{
        backgroundColor: 'white',
        padding: '24px',
        borderRadius: '12px',
        marginBottom: '24px',
        border: `2px solid ${COLORS.purple}`
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2 style={{ color: COLORS.purple, margin: 0 }}>
            Hole {postHoleAnalysis.hole_number} Analysis
          </h2>
          <button
            onClick={() => setCurrentView('game')}
            style={{
              backgroundColor: COLORS.accent,
              color: 'white',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            Back to Game
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          {/* Final Teams */}
          <div style={{
            backgroundColor: COLORS.light,
            padding: '16px',
            borderRadius: '8px'
          }}>
            <h3 style={{ color: COLORS.primary, marginTop: 0 }}>Final Teams</h3>
            <p><strong>Formation:</strong> {postHoleAnalysis.final_teams.formation_type}</p>
            <p><strong>Captain:</strong> {postHoleAnalysis.final_teams.captain}</p>
            {postHoleAnalysis.final_teams.team1 && (
              <>
                <p><strong>Team 1:</strong> {postHoleAnalysis.final_teams.team1.join(', ')}</p>
                <p><strong>Team 2:</strong> {postHoleAnalysis.final_teams.team2.join(', ')}</p>
              </>
            )}
          </div>

          {/* Betting Summary */}
          <div style={{
            backgroundColor: COLORS.light,
            padding: '16px',
            borderRadius: '8px'
          }}>
            <h3 style={{ color: COLORS.primary, marginTop: 0 }}>Betting Summary</h3>
            <p><strong>Starting Wager:</strong> {postHoleAnalysis.betting_summary.starting_wager}</p>
            <p><strong>Final Wager:</strong> {postHoleAnalysis.betting_summary.final_wager}</p>
            <p><strong>Multiplier:</strong> {postHoleAnalysis.betting_summary.wager_multiplier.toFixed(1)}x</p>
            {postHoleAnalysis.betting_summary.special_rules_invoked.length > 0 && (
              <div>
                <strong>Special Rules:</strong>
                <ul>
                  {postHoleAnalysis.betting_summary.special_rules_invoked.map((rule, index) => (
                    <li key={index}>{rule}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Strategic Insights */}
        {postHoleAnalysis.strategic_insights && postHoleAnalysis.strategic_insights.length > 0 && (
          <div style={{
            backgroundColor: COLORS.light,
            padding: '16px',
            borderRadius: '8px',
            marginTop: '20px'
          }}>
            <h3 style={{ color: COLORS.primary, marginTop: 0 }}>Strategic Insights</h3>
            <ul>
              {postHoleAnalysis.strategic_insights.map((insight, index) => (
                <li key={index} style={{ marginBottom: '8px', lineHeight: '1.4' }}>{insight}</li>
              ))}
            </ul>
          </div>
        )}

        {/* What-If Scenarios */}
        {postHoleAnalysis.what_if_scenarios && postHoleAnalysis.what_if_scenarios.length > 0 && (
          <div style={{
            backgroundColor: COLORS.warning,
            color: 'white',
            padding: '16px',
            borderRadius: '8px',
            marginTop: '20px'
          }}>
            <h3 style={{ marginTop: 0 }}>What-If Scenarios</h3>
            <ul>
              {postHoleAnalysis.what_if_scenarios.map((scenario, index) => (
                <li key={index} style={{ marginBottom: '8px', lineHeight: '1.4' }}>{scenario}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const getEventIcon = (type) => {
    switch (type) {
      case 'game_start': return '🎯';
      case 'hole_start': return '🏁';
      case 'shot': return '🏌️';
      case 'partnership_request': return '🤝';
      case 'partnership_response': return '✅';
      case 'partnership_decision': return '👤';
      case 'double_offer': return '💎';
      case 'double_response': return '💎';
      case 'aardvark_request': return '🦫';
      case 'aardvark_toss': return '🎯';
      case 'aardvark_solo': return '🦫';
      case 'ping_pong_aardvark': return '🏓';
      case 'scores_entered': return '📊';
      case 'post_hole_analysis': return '📈';
      default: return '📝';
    }
  };

  const getEventColor = (type) => {
    switch (type) {
      case 'game_start': return COLORS.success;
      case 'hole_start': return COLORS.primary;
      case 'shot': return COLORS.accent;
      case 'partnership_request': return COLORS.warning;
      case 'partnership_response': return COLORS.success;
      case 'partnership_decision': return COLORS.gold;
      case 'double_offer': return COLORS.danger;
      case 'double_response': return COLORS.danger;
      case 'aardvark_request': return COLORS.purple;
      case 'aardvark_toss': return COLORS.danger;
      case 'aardvark_solo': return COLORS.warning;
      case 'ping_pong_aardvark': return COLORS.gold;
      case 'scores_entered': return COLORS.purple;
      case 'post_hole_analysis': return COLORS.purple;
      default: return COLORS.secondary;
    }
  };

  const renderHoleProgression = () => {
    if (!gameState || !gameState.hole_state) return null;

    const holeState = gameState.hole_state;
    const players = gameState.players || [];

    // Check ball positions for progression stages
    const ballPositions = holeState.ball_positions || {};
    const playersOnGreen = Object.values(ballPositions).filter(pos => pos && pos.lie_type === 'green').length;
    const playersFinished = Object.values(ballPositions).filter(pos => pos && (pos.holed || pos.conceded)).length;
    
    // Calculate progression stages
    const stages = [
      { id: 'tee', name: 'Tee Shots', icon: '🏌️', completed: (holeState.tee_shots_complete || 0) >= players.length },
      { id: 'partnership', name: 'Partnerships', icon: '🤝', completed: holeState.teams?.type !== 'pending' },
      { id: 'approach', name: 'Approach Shots', icon: '🎯', completed: playersOnGreen > 0 || playersFinished > 0 },
      { id: 'green', name: 'On Green', icon: '⛳', completed: playersOnGreen >= players.length || playersFinished > 0 },
      { id: 'scoring', name: 'Scoring', icon: '📊', completed: holeState.hole_complete || false }
    ];

    // Determine current stage
    let currentStage = 0;
    for (let i = 0; i < stages.length; i++) {
      if (!stages[i].completed) {
        currentStage = i;
        break;
      }
      if (i === stages.length - 1) currentStage = stages.length - 1;
    }

    return (
      <div style={{
        backgroundColor: 'white',
        padding: '16px',
        borderRadius: '8px',
        marginBottom: '20px',
        border: `2px solid ${COLORS.secondary}`
      }}>
        <h3 style={{ color: COLORS.primary, marginTop: 0, marginBottom: '16px' }}>Hole Progression</h3>
        
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          {stages.map((stage, index) => (
            <div key={stage.id} style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
              {/* Stage Circle */}
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                backgroundColor: stage.completed ? COLORS.success : 
                                (index === currentStage ? COLORS.warning : COLORS.light),
                color: stage.completed || index === currentStage ? 'white' : COLORS.secondary,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '18px',
                fontWeight: 'bold',
                border: `2px solid ${stage.completed ? COLORS.success : 
                                   (index === currentStage ? COLORS.warning : COLORS.secondary)}`
              }}>
                {stage.completed ? '✓' : stage.icon}
              </div>
              
              {/* Stage Label */}
              <div style={{ 
                marginLeft: '8px', 
                fontSize: '12px', 
                fontWeight: 'bold',
                color: stage.completed ? COLORS.success : 
                       (index === currentStage ? COLORS.warning : COLORS.secondary)
              }}>
                {stage.name}
              </div>
              
              {/* Connecting Line */}
              {index < stages.length - 1 && (
                <div style={{
                  flex: 1,
                  height: '2px',
                  backgroundColor: stage.completed ? COLORS.success : COLORS.light,
                  marginLeft: '8px',
                  marginRight: '8px'
                }} />
              )}
            </div>
          ))}
        </div>

        {/* Player Positions */}
        {Object.keys(ballPositions).length > 0 && (
          <div style={{ marginTop: '12px' }}>
            <div style={{ fontSize: '12px', fontWeight: 'bold', color: COLORS.primary, marginBottom: '8px' }}>
              Ball Positions:
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {Object.entries(ballPositions).map(([playerId, position]) => {
                const player = players.find(p => p.id === playerId);
                if (!player || !position) return null;
                
                const getLieIcon = (lieType) => {
                  switch (lieType) {
                    case 'tee': return '🏌️';
                    case 'fairway': return '🌱';
                    case 'rough': return '🌿';
                    case 'bunker': return '🏖️';
                    case 'green': return '⛳';
                    case 'in_hole': return '🕳️';
                    default: return '⚫';
                  }
                };
                
                const lieType = position.lie_type || 'unknown';
                const isHoled = position.holed || false;
                const distance = position.distance_to_pin;
                
                return (
                  <div key={playerId} style={{
                    backgroundColor: isHoled ? COLORS.success : COLORS.light,
                    color: isHoled ? 'white' : COLORS.dark,
                    padding: '4px 8px',
                    borderRadius: '12px',
                    fontSize: '11px',
                    fontWeight: 'bold'
                  }}>
                    {getLieIcon(lieType)} {player.name}: {isHoled ? 'HOLED' : `${distance ? distance.toFixed(0) : '?'}yd`}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Progress Actions */}
        {!holeState.hole_complete && (
          <div style={{ marginTop: '16px', textAlign: 'center' }}>
            <button
              onClick={() => sendAction('PLAY_SHOT')}
              disabled={loading}
              style={{
                backgroundColor: COLORS.accent,
                color: 'white',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: 'bold',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.6 : 1
              }}
            >
              {loading ? 'Processing...' : `Continue to ${stages[currentStage]?.name || 'Next Stage'}`}
            </button>
          </div>
        )}
      </div>
    );
  };

  const renderViewTabs = () => {
    return (
      <div style={{
        display: 'flex',
        marginBottom: '20px',
        backgroundColor: COLORS.light,
        borderRadius: '8px',
        padding: '4px'
      }}>
        {['game', 'timeline', 'analysis', 'analytics'].map(view => (
          <button
            key={view}
            onClick={() => setCurrentView(view)}
            style={{
              flex: 1,
              padding: '12px',
              border: 'none',
              borderRadius: '6px',
              backgroundColor: currentView === view ? COLORS.accent : 'transparent',
              color: currentView === view ? 'white' : COLORS.primary,
              fontWeight: 'bold',
              cursor: 'pointer',
              textTransform: 'capitalize'
            }}
          >
            {view === 'analysis' ? 'Hole Analysis' : 
             view === 'analytics' ? 'Advanced Analytics' : 
             view.charAt(0).toUpperCase() + view.slice(1)}
          </button>
        ))}
      </div>
    );
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      <h1 style={{ color: COLORS.primary, textAlign: 'center', marginBottom: '30px', fontSize: '32px' }}>
        Wolf Goat Pig - Enhanced Interface
      </h1>

      {!gameState ? (
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <h2 style={{ color: COLORS.primary, marginBottom: '20px' }}>Select Game Type</h2>
          <div style={{ display: 'flex', gap: '20px', justifyContent: 'center', flexWrap: 'wrap' }}>
            {[4, 5, 6].map(playerCount => (
              <button
                key={playerCount}
                onClick={() => initializeGame(playerCount)}
                disabled={loading}
                style={{
                  backgroundColor: COLORS.success,
                  color: 'white',
                  border: 'none',
                  padding: '20px 30px',
                  borderRadius: '10px',
                  fontSize: '16px',
                  fontWeight: 'bold',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.6 : 1,
                  minWidth: '140px'
                }}
              >
                {loading ? 'Starting...' : `${playerCount}-Man Game`}
              </button>
            ))}
          </div>
          <div style={{ marginTop: '15px', fontSize: '14px', color: COLORS.secondary }}>
            <p>4-Man: Classic game with Invisible Aardvark</p>
            <p>5-Man: Adds real Aardvark (5th player)</p>
            <p>6-Man: Two Aardvarks with complex team dynamics</p>
          </div>
        </div>
      ) : (
        <>
          {renderViewTabs()}
          
          {currentView === 'game' && (
            <>
              {renderHoleStateCard()}
              {renderDecisionButtons()}
            </>
          )}
          
          {currentView === 'timeline' && renderEnhancedTimeline()}
          
          {currentView === 'analysis' && postHoleAnalysis && renderPostHoleAnalysis()}
          
          {currentView === 'analytics' && (
            <AnalyticsDashboard 
              gameId={gameId} 
              onBack={() => setCurrentView('game')} 
            />
          )}

          {loading && (
            <div style={{
              textAlign: 'center',
              padding: '20px',
              color: COLORS.accent,
              fontSize: '18px',
              fontWeight: 'bold'
            }}>
              Processing action...
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default EnhancedWGPInterface;
