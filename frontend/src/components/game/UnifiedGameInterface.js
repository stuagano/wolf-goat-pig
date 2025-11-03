import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useTheme } from '../../theme/Provider';
import { useGame } from '../../context';
import { Button, Card, Select } from '../ui';
import useOddsCalculation from '../../hooks/useOddsCalculation';
// Import existing widgets
import ShotResultWidget from '../ShotResultWidget';
import BettingOpportunityWidget from '../BettingOpportunityWidget';
import BettingOddsPanel from '../BettingOddsPanel';
import GameStateWidget from '../GameStateWidget';
import StrategicAnalysisWidget from '../StrategicAnalysisWidget';
import AnalyticsDashboard from '../AnalyticsDashboard';
import HoleStrategyDisplay from '../HoleStrategyDisplay';

// Import enhanced components
import EnhancedBettingWidget from '../EnhancedBettingWidget';
import EnhancedScoringWidget from '../EnhancedScoringWidget';
import InteractivePlayerCard from '../InteractivePlayerCard';

// Import shot analysis components
import ShotAnalysisWidget from '../ShotAnalysisWidget';
import ShotVisualizationOverlay from '../ShotVisualizationOverlay';

// Import game history component
import GameHistory from '../GameHistory';

// Import simulation components
import { GameSetup as SimulationSetup, GamePlay as SimulationPlay } from '../simulation';

// Import game setup components
import GameSetupForm from './GameSetupForm';
import LargeScoringButtons from './LargeScoringButtons';
import MobileScorecard from './MobileScorecard';

const API_URL = process.env.REACT_APP_API_URL || "";

const UnifiedGameInterface = ({ mode = 'regular' }) => {
  const theme = useTheme();
  const { gameId } = useParams(); // Get gameId from URL for multiplayer games
  const {
    gameState: contextGameState,
    setGameState: contextSetGameState,
    loading: contextLoading,
    setLoading: contextSetLoading,
    error: contextError,
    clearError: contextClearError,
    fetchGameState: contextFetchGameState,
    makeGameAction: contextMakeGameAction,
    isGameActive: contextIsGameActive,
    startGame: contextStartGame,
    endGame: contextEndGame
  } = useGame();

  // Local state management for multiplayer games
  const [localGameState, setLocalGameState] = useState(null);
  const [localLoading, setLocalLoading] = useState(false);
  const [localError, setLocalError] = useState(null);

  // Use local state for multiplayer, context state for single-player
  const gameState = gameId ? localGameState : contextGameState;
  const setGameState = gameId ? setLocalGameState : contextSetGameState;
  const loading = gameId ? localLoading : contextLoading;
  const setLoading = gameId ? setLocalLoading : contextSetLoading;
  const error = gameId ? localError : contextError;
  const clearError = gameId ? (() => setLocalError(null)) : contextClearError;
  const isGameActive = gameId ? (gameState && gameState.game_status === 'in_progress') : contextIsGameActive;
  const startGame = contextStartGame;
  const endGame = contextEndGame;

  // Fetch game state for multiplayer games
  const fetchGameState = async () => {
    if (!gameId) {
      return contextFetchGameState();
    }

    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/games/${gameId}/state`);
      if (!response.ok) {
        throw new Error('Failed to fetch game state');
      }
      const data = await response.json();
      setGameState(data);
      return data;
    } catch (err) {
      console.error('Error fetching game state:', err);
      setLocalError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Make game action for multiplayer games
  const makeGameAction = async (actionType, payload = {}) => {
    if (!gameId) {
      return contextMakeGameAction(actionType, payload);
    }

    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/games/${gameId}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action_type: actionType,
          payload
        })
      });

      if (!response.ok) {
        throw new Error('Action failed');
      }

      const data = await response.json();
      setGameState(data.game_state);
      return data;
    } catch (err) {
      console.error('Error performing action:', err);
      setLocalError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Interface state
  const [currentView, setCurrentView] = useState('game');
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [showOddsPanel, setShowOddsPanel] = useState(true);
  
  // Shot analysis state
  const [showShotAnalysis, setShowShotAnalysis] = useState(false);
  const [shotAnalysisData, setShotAnalysisData] = useState(null);
  const [currentPlayerForAnalysis, setCurrentPlayerForAnalysis] = useState(null);

  // Odds calculation hook
  const {
    loading: oddsLoading,
    error: oddsError,
    performanceMetrics,
    refreshOdds,
    clearError: clearOddsError,
    isCalculationStale,
    canCalculate
  } = useOddsCalculation({
    gameState,
    autoUpdate: true,
    updateInterval: 7000, // Update every 7 seconds
    onOddsUpdate: (newOddsData) => {
      // Add timeline event when odds update
      if (mode === 'enhanced') {
        setTimelineEvents(prev => [...prev, {
          id: Date.now(),
          type: 'odds_update',
          timestamp: new Date(),
          description: `Odds updated: ${newOddsData.optimal_strategy.replace(/_/g, ' ')}`,
          payload: { 
            confidence: newOddsData.confidence_level,
            calculation_time: newOddsData.calculation_time_ms 
          }
        }]);
      }
    },
    onError: (error) => {
      console.error('Odds calculation error:', error);
    }
  });

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
  }, [mode, gameId]); // Include gameId to refetch when it changes

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

  // Handle betting actions from odds panel
  const handleBettingAction = async (scenario) => {
    if (!scenario) return;

    try {
      // Map scenario types to game actions
      const actionMap = {
        'offer_double': 'OFFER_DOUBLE',
        'accept_double': 'ACCEPT_DOUBLE',
        'decline_double': 'DECLINE_DOUBLE',
        'go_solo': 'DECLARE_SOLO',
        'accept_partnership': 'RESPOND_PARTNERSHIP',
        'decline_partnership': 'RESPOND_PARTNERSHIP'
      };

      const actionType = actionMap[scenario.scenario_type];
      if (!actionType) {
        console.warn('Unknown betting scenario type:', scenario.scenario_type);
        return;
      }

      // Prepare payload based on scenario type
      let payload = {};
      if (scenario.scenario_type === 'accept_partnership' || scenario.scenario_type === 'decline_partnership') {
        payload.accepted = scenario.scenario_type === 'accept_partnership';
      } else if (scenario.scenario_type === 'offer_double') {
        // Find a player who can offer the double (simplified)
        const currentPlayer = gameState.players?.[0];
        if (currentPlayer) {
          payload.player_id = currentPlayer.id;
        }
      }

      // Execute the action
      await sendAction(actionType, payload);

      // Add timeline event
      if (mode === 'enhanced') {
        setTimelineEvents(prev => [...prev, {
          id: Date.now(),
          type: 'betting_action',
          timestamp: new Date(),
          description: `Betting action: ${scenario.scenario_type.replace(/_/g, ' ')}`,
          payload: { scenario: scenario.scenario_type, reasoning: scenario.reasoning }
        }]);
      }

    } catch (error) {
      console.error('Error executing betting action:', error);
    }
  };

  // Handle shot analysis toggle and recommendations
  const handleShotAnalysisToggle = () => {
    setShowShotAnalysis(!showShotAnalysis);
  };

  const handleShotRecommendation = (recommendation) => {
    setShotAnalysisData(recommendation);
    
    // Add timeline event for enhanced mode
    if (mode === 'enhanced') {
      setTimelineEvents(prev => [...prev, {
        id: Date.now(),
        type: 'shot_analysis',
        timestamp: new Date(),
        description: `Shot recommendation: ${recommendation.type?.replace('_', ' ').toUpperCase()}`,
        payload: recommendation
      }]);
    }
  };

  // Determine current player for shot analysis
  React.useEffect(() => {
    if (gameState && gameState.players) {
      // Try to find the current player to hit
      const nextPlayer = gameState.players.find(p => 
        p.id === (gameState.next_player_to_hit || gameState.current_player)
      );
      
      // If no specific next player, use first player as default
      setCurrentPlayerForAnalysis(nextPlayer || gameState.players[0]);
    }
  }, [gameState]);

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

  // For regular mode, show game setup if no game is active
  if (mode === 'regular' && !isGameActive && !gameState) {
    return (
      <div style={{ maxWidth: 800, margin: '0 auto', padding: theme.spacing[4] }}>
        <Card>
          <div style={{ textAlign: 'center', marginBottom: theme.spacing[6] }}>
            <h1 style={{ color: theme.colors.primary, marginBottom: theme.spacing[2] }}>
              🎯 Start New Wolf Goat Pig Game
            </h1>
            <p style={{ color: theme.colors.textSecondary, fontSize: theme.typography.lg }}>
              Set up players, course, and game settings
            </p>
          </div>
          
          <GameSetupForm 
            onSetup={(newGameState) => {
              setGameState(newGameState);
              startGame(newGameState);
            }}
          />
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
            
            <div style={{ display: 'flex', gap: theme.spacing[2], alignItems: 'center' }}>
              <Button
                onClick={handleShotAnalysisToggle}
                variant={showShotAnalysis ? "primary" : "secondary"}
                size="small"
              >
                {showShotAnalysis ? '🎯 Analysis ON' : '🎯 Shot Analysis'}
              </Button>
              
              <Button
                onClick={() => setShowOddsPanel(!showOddsPanel)}
                variant={showOddsPanel ? "primary" : "secondary"}
                size="small"
              >
                {showOddsPanel ? '📊 Odds ON' : '📊 Betting Odds'}
              </Button>
              
              <Select
                value={currentView}
                onChange={(e) => handleViewChange(e.target.value)}
                options={[
                  { value: 'game', label: '🎮 Game View' },
                  { value: 'analytics', label: '📊 Analytics' },
                  { value: 'history', label: '📋 History' },
                  { value: 'timeline', label: '🕒 Timeline' },
                  { value: 'visualization', label: '🗺️ Course View' },
                  { value: 'odds', label: '🎲 Odds Analysis' }
                ]}
              />
            </div>
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
            gridTemplateColumns: window.innerWidth < 768 ? '1fr' : 
              showShotAnalysis && showOddsPanel ? '2fr 1fr 1fr 1fr' :
              showShotAnalysis || showOddsPanel ? '2fr 1fr 1fr' : '2fr 1fr', 
            gap: theme.spacing[4] 
          }}>
            <div>
              <GameStateWidget gameState={gameState} holeState={gameState?.hole_state} onAction={sendAction} />
              {mode === 'enhanced' ? (
                <EnhancedScoringWidget gameState={gameState} />
              ) : (
                <ShotResultWidget gameState={gameState} />
              )}
            </div>
            <div>
              {mode === 'enhanced' ? (
                <>
                  <EnhancedBettingWidget gameState={gameState} onAction={sendAction} />
                  {gameState?.players && gameState.players.map(player => (
                    <InteractivePlayerCard 
                      key={player.id}
                      player={player} 
                      gameState={gameState}
                      onAction={sendAction}
                    />
                  ))}
                </>
              ) : (
                <>
                  <BettingOpportunityWidget gameState={gameState} onAction={sendAction} />
                  <StrategicAnalysisWidget gameState={gameState} />
                </>
              )}
            </div>
            {showOddsPanel && (
              <div>
                <BettingOddsPanel
                  gameState={gameState}
                  onBettingAction={handleBettingAction}
                  autoUpdate={true}
                  refreshInterval={7000}
                  showEducationalTooltips={true}
                />
              </div>
            )}
            {showShotAnalysis && (
              <div>
                <ShotAnalysisWidget
                  gameState={gameState}
                  holeState={gameState?.hole_state}
                  currentPlayer={currentPlayerForAnalysis}
                  visible={showShotAnalysis}
                  onShotRecommendation={handleShotRecommendation}
                />
              </div>
            )}
          </div>
        )}

        {/* New dedicated odds view */}
        {currentView === 'odds' && (
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: '1fr',
            gap: theme.spacing[4] 
          }}>
            <BettingOddsPanel
              gameState={gameState}
              onBettingAction={handleBettingAction}
              autoUpdate={true}
              refreshInterval={5000}
              showEducationalTooltips={true}
            />
            
            {/* Performance metrics card */}
            {canCalculate && performanceMetrics && (
              <Card>
                <h3 style={{ color: theme.colors.primary, marginBottom: theme.spacing[4] }}>
                  🔧 Odds Calculation Performance
                </h3>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: theme.spacing[4]
                }}>
                  <div>
                    <div style={{ fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
                      Average Calculation Time
                    </div>
                    <div style={{ 
                      fontSize: theme.typography.xl, 
                      fontWeight: theme.typography.bold,
                      color: performanceMetrics.averageCalculationTime < 50 ? theme.colors.success : theme.colors.warning
                    }}>
                      {performanceMetrics.averageCalculationTime.toFixed(1)}ms
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
                      Success Rate
                    </div>
                    <div style={{ 
                      fontSize: theme.typography.xl, 
                      fontWeight: theme.typography.bold,
                      color: theme.colors.success
                    }}>
                      {(performanceMetrics.successRate * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
                      Cache Efficiency
                    </div>
                    <div style={{ 
                      fontSize: theme.typography.xl, 
                      fontWeight: theme.typography.bold,
                      color: theme.colors.primary
                    }}>
                      {(performanceMetrics.cacheHitRate * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
                      Data Freshness
                    </div>
                    <div style={{ 
                      fontSize: theme.typography.base, 
                      fontWeight: theme.typography.medium,
                      color: isCalculationStale ? theme.colors.warning : theme.colors.success
                    }}>
                      {isCalculationStale ? 'Stale' : 'Fresh'}
                    </div>
                  </div>
                </div>
                
                {/* Manual refresh button */}
                <div style={{ marginTop: theme.spacing[4] }}>
                  <Button
                    onClick={refreshOdds}
                    disabled={oddsLoading}
                    variant="secondary"
                    size="small"
                  >
                    {oddsLoading ? '⟳ Calculating...' : '🔄 Refresh Odds'}
                  </Button>
                  
                  {oddsError && (
                    <Button
                      onClick={clearOddsError}
                      variant="error"
                      size="small"
                      style={{ marginLeft: theme.spacing[2] }}
                    >
                      ✕ Clear Error
                    </Button>
                  )}
                </div>
              </Card>
            )}
          </div>
        )}

        {currentView === 'analytics' && (
          <AnalyticsDashboard gameState={gameState} timelineEvents={timelineEvents} />
        )}

        {currentView === 'history' && (
          <GameHistory 
            gameData={gameState} 
            timelineEvents={timelineEvents}
          />
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
          <div>
            <HoleStrategyDisplay 
              gameState={gameState} 
              holeState={gameState?.hole_state}
              players={gameState?.players}
            />
            {showShotAnalysis && shotAnalysisData && (
              <Card style={{ marginTop: theme.spacing[4] }}>
                <h4 style={{ 
                  margin: `0 0 ${theme.spacing[3]} 0`,
                  color: theme.colors.primary 
                }}>
                  🎯 Shot Analysis Overlay
                </h4>
                <ShotVisualizationOverlay
                  analysis={shotAnalysisData}
                  holeState={gameState?.hole_state}
                  currentPlayer={currentPlayerForAnalysis}
                  showTargetZones={true}
                  showRiskAreas={true}
                  showOptimalPath={true}
                />
              </Card>
            )}
          </div>
        )}
      </div>
    );
  }

  // Regular mode - simple widget layout
  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: theme.spacing[4] }}>
      {/* Multiplayer Player Identity Banner */}
      {gameId && gameState && (
        <Card variant="info" style={{ marginBottom: theme.spacing[4] }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: theme.spacing[2]
          }}>
            <div>
              <div style={{ fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
                Multiplayer Game
              </div>
              <div style={{
                fontSize: theme.typography.lg,
                fontWeight: theme.typography.bold,
                color: theme.colors.primary
              }}>
                Game ID: {gameId.substring(0, 8)}...
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
                Players: {gameState.players?.length || 0}
              </div>
              <div style={{ fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
                Hole {gameState.current_hole || 1} of 18
              </div>
            </div>
          </div>
        </Card>
      )}

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
            textAlign: 'center',
            flex: 1
          }}>
            🎯 Wolf Goat Pig Game
          </h1>

          <Button
            onClick={handleShotAnalysisToggle}
            variant={showShotAnalysis ? "primary" : "secondary"}
            size="small"
          >
            {showShotAnalysis ? '🎯 Analysis ON' : '🎯 Shot Analysis'}
          </Button>
        </div>
      </Card>

      {/* Mobile Scorecard - replaces paper scorecard */}
      <div style={{ marginBottom: theme.spacing[4] }}>
        <MobileScorecard gameState={gameState} />
      </div>

      {/* Large Scoring Buttons - glove-friendly score entry */}
      <LargeScoringButtons
        gameState={gameState}
        onSaveScores={async (scores) => {
          // Save scores without calculating points
          try {
            for (const playerId of Object.keys(scores)) {
              await sendAction('record_net_score', {
                player_id: playerId,
                score: Number(scores[playerId])
              });
            }
          } catch (error) {
            console.error('Error saving scores:', error);
          }
        }}
        onScoreSubmit={async (scores) => {
          // Submit all scores and calculate points
          try {
            for (const playerId of Object.keys(scores)) {
              await sendAction('record_net_score', {
                player_id: playerId,
                score: Number(scores[playerId])
              });
            }
            await sendAction('calculate_hole_points');
          } catch (error) {
            console.error('Error submitting scores:', error);
          }
        }}
        onAction={sendAction}
        loading={loading}
      />

      {/* Additional widgets in collapsible/secondary section */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: showShotAnalysis ?
          'repeat(auto-fit, minmax(350px, 1fr))' :
          'repeat(auto-fit, minmax(400px, 1fr))',
        gap: theme.spacing[4],
        marginTop: theme.spacing[4]
      }}>
        <GameStateWidget gameState={gameState} holeState={gameState?.hole_state} onAction={sendAction} />
        <BettingOpportunityWidget gameState={gameState} onAction={sendAction} />
        <ShotResultWidget gameState={gameState} />
        <StrategicAnalysisWidget gameState={gameState} />

        {showShotAnalysis && (
          <ShotAnalysisWidget
            gameState={gameState}
            holeState={gameState?.hole_state}
            currentPlayer={currentPlayerForAnalysis}
            visible={showShotAnalysis}
            onShotRecommendation={handleShotRecommendation}
          />
        )}
      </div>
    </div>
  );
};

export default UnifiedGameInterface;