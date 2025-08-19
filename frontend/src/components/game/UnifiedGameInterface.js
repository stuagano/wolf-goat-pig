import React, { useState, useEffect } from 'react';
import { useTheme } from '../../theme/Provider';
import { useGame } from '../../context';
import { Button, Card, Select } from '../ui';

// Import existing widgets
import ShotResultWidget from '../ShotResultWidget';
import BettingOpportunityWidget from '../BettingOpportunityWidget';
import GameStateWidget from '../GameStateWidget';
import StrategicAnalysisWidget from '../StrategicAnalysisWidget';
import AnalyticsDashboard from '../AnalyticsDashboard';
import HoleVisualization from '../HoleVisualization';

// Import simulation components
import { GameSetup as SimulationSetup, GamePlay as SimulationPlay } from '../simulation';

const UnifiedGameInterface = ({ mode = 'regular' }) => {
  const theme = useTheme();
  const { 
    gameState,
    setGameState,
    loading,
    setLoading,
    error,
    clearError,
    fetchGameState,
    makeGameAction,
    isGameActive,
    startGame,
    endGame
  } = useGame();

  // Interface state
  const [currentView, setCurrentView] = useState('game');
  const [timelineEvents, setTimelineEvents] = useState([]);

  // Simulation-specific state (only used in simulation mode)
  const [humanPlayer, setHumanPlayer] = useState({
    id: "human",
    name: "",
    handicap: 18,
    strength: "Average",
    is_human: true
  });
  const [computerPlayers, setComputerPlayers] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState("");
  const [courses, setCourses] = useState({});
  const [personalities, setPersonalities] = useState([]);
  const [suggestedOpponents, setSuggestedOpponents] = useState([]);
  const [feedback] = useState([]); // Passed to SimulationPlay component

  useEffect(() => {
    if (mode === 'regular' || mode === 'enhanced') {
      fetchGameState();
    }
  }, [mode, fetchGameState]);

  const sendAction = async (actionType, payload = {}) => {
    setLoading(true);
    try {
      const response = await makeGameAction(actionType, payload);
      setGameState(response);
      
      // Add timeline event for enhanced mode
      if (mode === 'enhanced') {
        setTimelineEvents(prev => [...prev, {
          id: Date.now(),
          type: actionType,
          timestamp: new Date(),
          description: `Action: ${actionType}`,
          payload
        }]);
      }
      
      return response;
    } catch (error) {
      console.error('Action failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const handleViewChange = (view) => {
    setCurrentView(view);
  };

  // For simulation mode, delegate to simulation components
  if (mode === 'simulation') {
    if (!isGameActive) {
      return (
        <SimulationSetup
          humanPlayer={humanPlayer}
          setHumanPlayer={setHumanPlayer}
          computerPlayers={computerPlayers}
          setComputerPlayers={setComputerPlayers}
          selectedCourse={selectedCourse}
          setSelectedCourse={setSelectedCourse}
          courses={courses}
          setCourses={setCourses}
          personalities={personalities}
          setPersonalities={setPersonalities}
          suggestedOpponents={suggestedOpponents}
          setSuggestedOpponents={setSuggestedOpponents}
          onStartGame={startGame}
        />
      );
    }

    return (
      <SimulationPlay
        gameState={gameState}
        onEndSimulation={endGame}
        feedback={feedback}
        // Add other simulation-specific props as needed
      />
    );
  }

  // Loading state
  if (loading && !gameState) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '50vh' 
      }}>
        <Card>
          <div style={{ textAlign: 'center', padding: theme.spacing[6] }}>
            <h2 style={{ color: theme.colors.primary, marginBottom: theme.spacing[4] }}>
              Loading Wolf Goat Pig...
            </h2>
            <div style={{ color: theme.colors.textSecondary }}>
              Please wait while we prepare your game
            </div>
          </div>
        </Card>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '50vh' 
      }}>
        <Card variant="error">
          <div style={{ textAlign: 'center', padding: theme.spacing[6] }}>
            <h2 style={{ color: theme.colors.error, marginBottom: theme.spacing[4] }}>
              Game Error
            </h2>
            <div style={{ color: theme.colors.textPrimary, marginBottom: theme.spacing[4] }}>
              {error}
            </div>
            <Button onClick={clearError} variant="primary">
              Try Again
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // No game state
  if (!gameState) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '50vh' 
      }}>
        <Card>
          <div style={{ textAlign: 'center', padding: theme.spacing[6] }}>
            <h2 style={{ color: theme.colors.primary, marginBottom: theme.spacing[4] }}>
              No Active Game
            </h2>
            <div style={{ color: theme.colors.textSecondary, marginBottom: theme.spacing[4] }}>
              Start a new game or join an existing one to continue.
            </div>
            <Button onClick={() => window.location.href = '/setup'} variant="primary">
              Start New Game
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // Enhanced mode - render with view switcher
  if (mode === 'enhanced') {
    return (
      <div style={{ maxWidth: 1400, margin: '0 auto', padding: theme.spacing[4] }}>
        {/* Header with view switcher */}
        <Card>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: theme.spacing[4]
          }}>
            <h1 style={{ 
              color: theme.colors.primary, 
              margin: 0,
              fontSize: theme.typography['2xl'],
              fontWeight: theme.typography.bold
            }}>
              🚀 Enhanced Wolf Goat Pig
            </h1>
            
            <Select
              value={currentView}
              onChange={(e) => handleViewChange(e.target.value)}
              options={[
                { value: 'game', label: '🎮 Game View' },
                { value: 'analytics', label: '📊 Analytics' },
                { value: 'timeline', label: '📋 Timeline' },
                { value: 'visualization', label: '🗺️ Course View' }
              ]}
            />
          </div>

          {/* Game status */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: theme.spacing[4],
            marginBottom: theme.spacing[4]
          }}>
            <div>
              <div style={{ fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
                Current Hole
              </div>
              <div style={{ 
                fontSize: theme.typography.xl, 
                fontWeight: theme.typography.bold,
                color: theme.colors.primary 
              }}>
                {gameState.current_hole || 1}
              </div>
            </div>
            <div>
              <div style={{ fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
                Game Phase
              </div>
              <div style={{ 
                fontSize: theme.typography.base, 
                fontWeight: theme.typography.medium,
                color: theme.colors.textPrimary 
              }}>
                {gameState.game_phase || 'Active'}
              </div>
            </div>
            <div>
              <div style={{ fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
                Base Wager
              </div>
              <div style={{ 
                fontSize: theme.typography.lg, 
                fontWeight: theme.typography.bold,
                color: theme.colors.warning 
              }}>
                ${gameState.base_wager || 0}
              </div>
            </div>
          </div>
        </Card>

        {/* View content */}
        {currentView === 'game' && (
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: '2fr 1fr', 
            gap: theme.spacing[4] 
          }}>
            <div>
              <GameStateWidget gameState={gameState} onAction={sendAction} />
              <ShotResultWidget gameState={gameState} />
            </div>
            <div>
              <BettingOpportunityWidget gameState={gameState} onAction={sendAction} />
              <StrategicAnalysisWidget gameState={gameState} />
            </div>
          </div>
        )}

        {currentView === 'analytics' && (
          <AnalyticsDashboard gameState={gameState} timelineEvents={timelineEvents} />
        )}

        {currentView === 'timeline' && (
          <Card>
            <h3 style={{ color: theme.colors.primary, marginBottom: theme.spacing[4] }}>
              📋 Game Timeline
            </h3>
            <div style={{ maxHeight: 600, overflowY: 'auto' }}>
              {timelineEvents.length === 0 ? (
                <div style={{ 
                  textAlign: 'center', 
                  color: theme.colors.textSecondary,
                  padding: theme.spacing[6]
                }}>
                  No timeline events yet. Actions will appear here as you play.
                </div>
              ) : (
                timelineEvents.map(event => (
                  <div 
                    key={event.id}
                    style={{
                      padding: theme.spacing[3],
                      marginBottom: theme.spacing[2],
                      border: `1px solid ${theme.colors.border}`,
                      borderRadius: theme.borderRadius.base,
                      backgroundColor: theme.colors.background
                    }}
                  >
                    <div style={{ 
                      fontWeight: theme.typography.medium,
                      color: theme.colors.primary 
                    }}>
                      {event.description}
                    </div>
                    <div style={{ 
                      fontSize: theme.typography.sm,
                      color: theme.colors.textSecondary,
                      marginTop: theme.spacing[1]
                    }}>
                      {event.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        )}

        {currentView === 'visualization' && (
          <HoleVisualization gameState={gameState} />
        )}
      </div>
    );
  }

  // Regular mode - simple widget layout
  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: theme.spacing[4] }}>
      <Card>
        <h1 style={{ 
          color: theme.colors.primary, 
          marginBottom: theme.spacing[4],
          textAlign: 'center'
        }}>
          🎯 Wolf Goat Pig Game
        </h1>
      </Card>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', 
        gap: theme.spacing[4] 
      }}>
        <GameStateWidget gameState={gameState} onAction={sendAction} />
        <BettingOpportunityWidget gameState={gameState} onAction={sendAction} />
        <ShotResultWidget gameState={gameState} />
        <StrategicAnalysisWidget gameState={gameState} />
      </div>
    </div>
  );
};

export default UnifiedGameInterface;