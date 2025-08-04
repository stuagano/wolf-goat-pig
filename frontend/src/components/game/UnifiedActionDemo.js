import React, { useState, useEffect } from 'react';

const COLORS = {
  primary: '#2c3e50',
  secondary: '#34495e',
  accent: '#3498db',
  success: '#27ae60',
  warning: '#f39c12',
  danger: '#e74c3c',
  light: '#ecf0f1',
  dark: '#2c3e50'
};

const UnifiedActionDemo = () => {
  const [gameState, setGameState] = useState(null);
  const [availableActions, setAvailableActions] = useState([]);
  const [logMessages, setLogMessages] = useState([]);
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [gameId] = useState('demo-game-123');

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
        
        // Update state
        setGameState(data.game_state);
        setAvailableActions(data.available_actions);
        
        // Add log message
        setLogMessages(prev => [...prev, {
          id: Date.now(),
          message: data.log_message,
          timestamp: new Date().toISOString()
        }]);
        
        // Add timeline event if present
        if (data.timeline_event) {
          setTimelineEvents(prev => [...prev, data.timeline_event]);
        }
        
        console.log('Action response:', data);
      } else {
        const errorText = await response.text();
        console.error('Action error:', errorText);
        setLogMessages(prev => [...prev, {
          id: Date.now(),
          message: `Error: ${errorText}`,
          timestamp: new Date().toISOString(),
          isError: true
        }]);
      }
    } catch (error) {
      console.error('Network error:', error);
      setLogMessages(prev => [...prev, {
        id: Date.now(),
        message: `Network error: ${error.message}`,
        timestamp: new Date().toISOString(),
        isError: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  const initializeGame = () => {
    sendAction('INITIALIZE_GAME', {
      players: [
        { name: 'Scott', handicap: 10.5 },
        { name: 'Bob', handicap: 15.0 },
        { name: 'Tim', handicap: 8.0 },
        { name: 'Steve', handicap: 20.5 }
      ]
    });
  };

  const renderGameState = () => {
    if (!gameState) return null;

    return (
      <div style={{ 
        backgroundColor: COLORS.light, 
        padding: '20px', 
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h3>Game State</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
          <div>
            <h4>Current Hole: {gameState.current_hole}</h4>
            <p><strong>Captain:</strong> {gameState.hole_state?.teams?.captain}</p>
            <p><strong>Team Type:</strong> {gameState.hole_state?.teams?.type}</p>
            <p><strong>Current Wager:</strong> {gameState.hole_state?.betting?.current_wager} quarters</p>
          </div>
          <div>
            <h4>Players</h4>
            {gameState.players?.map(player => (
              <div key={player.id} style={{ marginBottom: '5px' }}>
                {player.name} (HCP: {player.handicap}) - {player.points} quarters
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderAvailableActions = () => {
    if (availableActions.length === 0) return null;

    return (
      <div style={{ 
        backgroundColor: COLORS.accent, 
        padding: '20px', 
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h3>Available Actions</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {availableActions.map((action, index) => (
            <div key={index} style={{ 
              backgroundColor: 'white', 
              padding: '15px', 
              borderRadius: '8px',
              border: '2px solid #e0e0e0'
            }}>
              {action.context && (
                <div style={{ 
                  fontSize: '14px', 
                  color: '#666', 
                  marginBottom: '8px',
                  fontStyle: 'italic'
                }}>
                  {action.context}
                </div>
              )}
              <button
                onClick={() => sendAction(action.action_type, action.payload)}
                disabled={loading}
                style={{
                  backgroundColor: action.action_type === 'DECLARE_SOLO' ? COLORS.danger : COLORS.success,
                  color: 'white',
                  border: 'none',
                  padding: '12px 20px',
                  borderRadius: '5px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.6 : 1,
                  fontSize: '16px',
                  fontWeight: 'bold',
                  width: '100%'
                }}
              >
                {action.prompt}
                {action.player_turn && (
                  <div style={{ fontSize: '12px', marginTop: '4px', opacity: 0.9 }}>
                    {action.player_turn}'s turn
                  </div>
                )}
              </button>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderLogMessages = () => {
    return (
      <div style={{ 
        backgroundColor: COLORS.secondary, 
        color: 'white',
        padding: '20px', 
        borderRadius: '8px',
        marginBottom: '20px',
        maxHeight: '300px',
        overflowY: 'auto'
      }}>
        <h3>Game Log</h3>
        {logMessages.map(log => (
          <div 
            key={log.id} 
            style={{ 
              marginBottom: '10px',
              padding: '10px',
              backgroundColor: log.isError ? COLORS.danger : COLORS.primary,
              borderRadius: '5px'
            }}
          >
            <div style={{ fontSize: '12px', opacity: 0.8 }}>
              {new Date(log.timestamp).toLocaleTimeString()}
            </div>
            <div>{log.message}</div>
          </div>
        ))}
      </div>
    );
  };

  const renderTimeline = () => {
    if (timelineEvents.length === 0) return null;

    return (
      <div style={{ 
        backgroundColor: COLORS.warning, 
        padding: '20px', 
        borderRadius: '8px',
        marginBottom: '20px'
      }}>
        <h3>Game Timeline</h3>
        <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
          {timelineEvents.map((event, index) => (
            <div 
              key={event.id || index}
              style={{ 
                marginBottom: '10px',
                padding: '15px',
                backgroundColor: 'white',
                borderRadius: '8px',
                borderLeft: `4px solid ${getEventColor(event.type)}`,
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ 
                  fontSize: '18px', 
                  marginRight: '8px',
                  color: getEventColor(event.type)
                }}>
                  {getEventIcon(event.type)}
                </span>
                <span style={{ 
                  fontWeight: 'bold', 
                  color: getEventColor(event.type),
                  textTransform: 'uppercase',
                  fontSize: '12px',
                  letterSpacing: '1px'
                }}>
                  {event.type.replace('_', ' ')}
                </span>
                {event.player_name && (
                  <span style={{ 
                    marginLeft: 'auto',
                    fontSize: '12px',
                    color: '#666',
                    backgroundColor: '#f0f0f0',
                    padding: '2px 8px',
                    borderRadius: '12px'
                  }}>
                    {event.player_name}
                  </span>
                )}
              </div>
              <div style={{ 
                fontSize: '14px', 
                color: '#333',
                marginBottom: '8px'
              }}>
                {event.description}
              </div>
              {event.details && (
                <div style={{ 
                  fontSize: '12px', 
                  color: '#666',
                  backgroundColor: '#f8f8f8',
                  padding: '8px',
                  borderRadius: '4px',
                  border: '1px solid #e0e0e0'
                }}>
                  <strong>Details:</strong> {JSON.stringify(event.details, null, 2)}
                </div>
              )}
              <div style={{ 
                fontSize: '11px', 
                color: '#999',
                marginTop: '8px',
                fontStyle: 'italic'
              }}>
                {new Date(event.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const getEventIcon = (type) => {
    switch (type) {
      case 'hole_start': return '🏁';
      case 'shot': return '🏌️';
      case 'partnership_request': return '🤝';
      case 'partnership_response': return '✅';
      case 'partnership_decision': return '👤';
      case 'double_offer': return '💎';
      case 'double_response': return '💎';
      case 'concession': return '🏌️';
      default: return '📝';
    }
  };

  const getEventColor = (type) => {
    switch (type) {
      case 'hole_start': return COLORS.primary;
      case 'shot': return COLORS.success;
      case 'partnership_request': return COLORS.accent;
      case 'partnership_response': return COLORS.success;
      case 'partnership_decision': return COLORS.warning;
      case 'double_offer': return COLORS.danger;
      case 'double_response': return COLORS.danger;
      case 'concession': return COLORS.secondary;
      default: return COLORS.dark;
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ color: COLORS.primary, textAlign: 'center', marginBottom: '30px' }}>
        Wolf Goat Pig - Unified Action API Demo
      </h1>
      
      <div style={{ textAlign: 'center', marginBottom: '30px' }}>
        <button
          onClick={initializeGame}
          disabled={loading || gameState}
          style={{
            backgroundColor: COLORS.success,
            color: 'white',
            border: 'none',
            padding: '15px 30px',
            borderRadius: '8px',
            fontSize: '16px',
            cursor: loading || gameState ? 'not-allowed' : 'pointer',
            opacity: loading || gameState ? 0.6 : 1
          }}
        >
          {gameState ? 'Game Already Started' : 'Initialize Game'}
        </button>
      </div>

      {renderGameState()}
      {renderAvailableActions()}
      {renderLogMessages()}
      {renderTimeline()}

      {loading && (
        <div style={{ 
          textAlign: 'center', 
          padding: '20px',
          color: COLORS.accent,
          fontSize: '18px'
        }}>
          Processing action...
        </div>
      )}
    </div>
  );
};

export default UnifiedActionDemo; 