import React, { useState, useEffect } from 'react';
import {
  ShotResultWidget,
  BettingOpportunityWidget,
  GameStateWidget,
  StrategicAnalysisWidget
} from '../';
import { useTheme } from '../../theme/Provider';
import { useGame } from '../../context';

const WolfGoatPigGame = () => {
  const theme = useTheme();
  const { 
    gameState, 
    setGameState, 
    loading, 
    setLoading, 
    error, 
    clearError,
    fetchGameState,
    makeGameAction 
  } = useGame();
  
  const [availableActions, setAvailableActions] = useState([]);
  const [logMessages, setLogMessages] = useState([]);
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [gameId] = useState('wgp-game-123');
  const [playerCount, setPlayerCount] = useState(4);
  const [players, setPlayers] = useState([]);

  useEffect(() => {
    // Initialize default players based on count
    const defaultNames = ['Bob', 'Scott', 'Vince', 'Mike', 'Terry', 'Bill'];
    const defaultHandicaps = [10.5, 15, 8, 20.5, 12, 18];
    
    const newPlayers = Array.from({ length: playerCount }, (_, i) => ({
      name: defaultNames[i] || `Player ${i + 1}`,
      handicap: defaultHandicaps[i] || 15
    }));
    
    setPlayers(newPlayers);
  }, [playerCount]);

  const sendAction = async (actionType, payload = null) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/wgp/${gameId}/action`, {
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
      players: players
    });
  };

  const renderGameState = () => {
    if (!gameState) return null;

    return (
      <div style={theme.cardStyle}>
        <GameStateWidget 
          gameState={gameState}
          currentHole={gameState.current_hole}
          players={gameState.players}
          holeState={gameState.hole_state}
        />
      </div>
    );
  };

  const renderAvailableActions = () => {
    if (availableActions.length === 0) return null;

    return (
      <div style={theme.cardStyle}>
        <h3 style={{ color: theme.colors.primary, marginBottom: '15px' }}>Available Actions</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
          {availableActions.map((action, index) => (
            <button
              key={index}
              onClick={() => sendAction(action.action_type, action.payload)}
              disabled={loading}
              style={{
                ...theme.buttonStyle,
                opacity: loading ? 0.6 : 1,
                cursor: loading ? 'not-allowed' : 'pointer'
              }}
            >
              {action.prompt}
              {action.player_turn && ` (${action.player_turn})`}
            </button>
          ))}
        </div>
      </div>
    );
  };

  const renderLogMessages = () => {
    return (
      <div style={{ 
        ...theme.cardStyle,
        backgroundColor: theme.colors.accent, 
        color: 'white',
        maxHeight: '300px',
        overflowY: 'auto'
      }}>
        <h3 style={{ marginBottom: '15px' }}>Game Log</h3>
        {logMessages.map(log => (
          <div 
            key={log.id} 
            style={{ 
              marginBottom: '10px',
              padding: '10px',
              backgroundColor: log.isError ? theme.colors.error : theme.colors.primary,
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
        ...theme.cardStyle,
        backgroundColor: theme.colors.warning
      }}>
        <h3 style={{ marginBottom: '15px' }}>Timeline Events</h3>
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {timelineEvents.map((event, index) => (
            <div 
              key={event.id || index}
              style={{ 
                marginBottom: '10px',
                padding: '10px',
                backgroundColor: 'white',
                borderRadius: '5px',
                borderLeft: `4px solid ${getEventColor(event.type)}`
              }}
            >
              <div style={{ fontWeight: 'bold', color: getEventColor(event.type) }}>
                {getEventIcon(event.type)} {event.type.replace('_', ' ').toUpperCase()}
              </div>
              <div style={{ color: theme.colors.textPrimary }}>{event.description}</div>
              {event.player_name && (
                <div style={{ fontSize: '12px', opacity: 0.7, color: theme.colors.textPrimary }}>
                  Player: {event.player_name}
                </div>
              )}
              {event.details && (
                <div style={{ fontSize: '12px', opacity: 0.7, color: theme.colors.textPrimary, marginTop: '5px' }}>
                  {renderEventDetails(event.details)}
                </div>
              )}
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
      case 'hole_start': return theme.colors.primary;
      case 'shot': return theme.colors.success;
      case 'partnership_request': return theme.colors.accent;
      case 'partnership_response': return theme.colors.success;
      case 'partnership_decision': return theme.colors.warning;
      case 'double_offer': return theme.colors.error;
      case 'double_response': return theme.colors.error;
      case 'concession': return theme.colors.accent;
      default: return theme.colors.gray800;
    }
  };

  const renderEventDetails = (details) => {
    if (!details) return null;
    
    const detailStrings = [];
    if (details.distance_to_pin) {
      detailStrings.push(`${details.distance_to_pin.toFixed(0)} yards to pin`);
    }
    if (details.shot_quality) {
      detailStrings.push(`Quality: ${details.shot_quality}`);
    }
    if (details.current_wager && details.potential_wager) {
      detailStrings.push(`Wager: ${details.current_wager} → ${details.potential_wager} quarters`);
    }
    if (details.accepted !== undefined) {
      detailStrings.push(details.accepted ? 'Accepted' : 'Declined');
    }
    
    return detailStrings.join(' • ');
  };

  const renderGameSetup = () => (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <div style={theme.cardStyle}>
        <h2 style={{ color: theme.colors.primary, textAlign: 'center', marginBottom: '30px' }}>
          Wolf Goat Pig Setup
        </h2>
        
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '10px', fontWeight: 'bold' }}>
            Number of Players:
          </label>
          <select 
            value={playerCount} 
            onChange={(e) => setPlayerCount(parseInt(e.target.value))}
            style={{
              padding: '10px',
              borderRadius: '5px',
              border: `1px solid ${theme.colors.border}`,
              fontSize: '16px'
            }}
          >
            <option value={4}>4 Players</option>
            <option value={5}>5 Players</option>
            <option value={6}>6 Players</option>
          </select>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <h3 style={{ color: theme.colors.primary, marginBottom: '15px' }}>Players:</h3>
          {players.map((player, index) => (
            <div key={index} style={{ 
              display: 'grid', 
              gridTemplateColumns: '1fr 1fr', 
              gap: '10px', 
              marginBottom: '10px',
              padding: '10px',
              backgroundColor: theme.colors.background,
              borderRadius: '5px'
            }}>
              <div>
                <strong>{player.name}</strong>
              </div>
              <div>
                Handicap: {player.handicap}
              </div>
            </div>
          ))}
        </div>

        <div style={{ textAlign: 'center' }}>
          <button
            onClick={initializeGame}
            disabled={loading}
            style={{
              ...theme.buttonStyle,
              fontSize: '18px',
              padding: '15px 30px',
              opacity: loading ? 0.6 : 1,
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Starting Game...' : 'Start Game'}
          </button>
        </div>
      </div>
    </div>
  );

  const renderGame = () => {
    return (
      <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px' }}>
        <h1 style={{ color: theme.colors.primary, textAlign: 'center', marginBottom: '30px' }}>
          Wolf Goat Pig Game
        </h1>
        
        {renderGameState()}
        {renderAvailableActions()}
        {renderLogMessages()}
        {renderTimeline()}

        {loading && (
          <div style={{ 
            textAlign: 'center', 
            padding: '20px',
            color: theme.colors.accent,
            fontSize: '18px'
          }}>
            Processing action...
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{ backgroundColor: theme.colors.background, minHeight: '100vh' }}>
      {!gameState ? renderGameSetup() : renderGame()}
    </div>
  );
};

export default WolfGoatPigGame;