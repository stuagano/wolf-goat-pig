import React from 'react';
import {
  ShotResultWidget,
  BettingOpportunityWidget,
  GameStateWidget,
  StrategicAnalysisWidget
} from './index';

// Example of how to integrate the new widgets into your existing WolfGoatPigGame.js
const IntegrationExample = () => {
  // This shows how to replace existing render methods with the new widgets
  
  // Instead of this in your existing component:
  /*
  const renderShotResult = () => (
    <div style={cardStyle}>
      <h3>Shot Result</h3>
      <p>Player: {shotResult.player}</p>
      <p>Distance: {shotResult.distance}</p>
      // ... more manual rendering
    </div>
  );
  */
  
  // You can now do this:
  const renderShotResult = (shotResult, playerName, isComputer) => (
    <ShotResultWidget 
      shotResult={shotResult}
      playerName={playerName}
      isComputer={isComputer}
    />
  );

  // Instead of manual betting UI:
  /*
  const renderBettingUI = () => (
    <div style={cardStyle}>
      <h3>Betting Decision</h3>
      <button onClick={() => makeDecision('accept')}>Accept</button>
      <button onClick={() => makeDecision('decline')}>Decline</button>
      // ... more manual buttons
    </div>
  );
  */
  
  // You can now do this:
  const renderBettingUI = (bettingOpportunity, onDecision) => (
    <BettingOpportunityWidget 
      bettingOpportunity={bettingOpportunity}
      onDecision={onDecision}
    />
  );

  // Instead of manual game state display:
  /*
  const renderGameState = () => (
    <div style={cardStyle}>
      <h3>Hole {gameState.current_hole}</h3>
      <p>Phase: {gameState.game_phase}</p>
      <p>Teams: {JSON.stringify(gameState.teams)}</p>
      // ... more manual state display
    </div>
  );
  */
  
  // You can now do this:
  const renderGameState = (gameState, holeState) => (
    <GameStateWidget 
      gameState={gameState}
      holeState={holeState}
    />
  );

  // Instead of manual analysis display:
  /*
  const renderAnalysis = () => (
    <div style={cardStyle}>
      <h3>Analysis</h3>
      <p>Recommendation: {analysis.recommendation}</p>
      <p>Risk: {analysis.risk}</p>
      // ... more manual analysis display
    </div>
  );
  */
  
  // You can now do this:
  const renderAnalysis = (bettingAnalysis) => (
    <StrategicAnalysisWidget 
      bettingAnalysis={bettingAnalysis}
    />
  );

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>🔧 Integration Example</h2>
      <p>Here's how to integrate the new widgets into your existing components:</p>
      
      <div style={{ background: '#f8f9fa', padding: '16px', borderRadius: '8px', margin: '16px 0' }}>
        <h3>1. Import the widgets:</h3>
        <pre style={{ background: '#fff', padding: '12px', borderRadius: '4px', overflow: 'auto' }}>
{`import {
  ShotResultWidget,
  BettingOpportunityWidget,
  GameStateWidget,
  StrategicAnalysisWidget
} from './components';`}
        </pre>
      </div>

      <div style={{ background: '#f8f9fa', padding: '16px', borderRadius: '8px', margin: '16px 0' }}>
        <h3>2. Replace manual rendering with widgets:</h3>
        <pre style={{ background: '#fff', padding: '12px', borderRadius: '4px', overflow: 'auto' }}>
{`// OLD: Manual rendering
const renderShotResult = () => (
  <div style={cardStyle}>
    <h3>Shot Result</h3>
    <p>Player: {shotResult.player}</p>
    <p>Distance: {shotResult.distance}</p>
  </div>
);

// NEW: Use widget
const renderShotResult = (shotResult, playerName, isComputer) => (
  <ShotResultWidget 
    shotResult={shotResult}
    playerName={playerName}
    isComputer={isComputer}
  />
);`}
        </pre>
      </div>

      <div style={{ background: '#f8f9fa', padding: '16px', borderRadius: '8px', margin: '16px 0' }}>
        <h3>3. Update your API response handling:</h3>
        <pre style={{ background: '#fff', padding: '12px', borderRadius: '4px', overflow: 'auto' }}>
{`// In your playNextShot function:
const playNextShot = async () => {
  const response = await fetch('/wgp/play-next-shot', {
    method: 'POST',
    body: JSON.stringify({})
  });
  
  const data = await response.json();
  
  // Update state with the rich data
  setGameState(data.game_state);
  setHoleState(data.hole_state);
  setShotResult(data.shot_result);
  setBettingOpportunity(data.betting_opportunity);
  setBettingAnalysis(data.betting_analysis);
};`}
        </pre>
      </div>

      <div style={{ background: '#f8f9fa', padding: '16px', borderRadius: '8px', margin: '16px 0' }}>
        <h3>4. Use in your render method:</h3>
        <pre style={{ background: '#fff', padding: '12px', borderRadius: '4px', overflow: 'auto' }}>
{`return (
  <div>
    {/* Game State */}
    <GameStateWidget 
      gameState={gameState}
      holeState={holeState}
    />
    
    {/* Shot Result */}
    {shotResult && (
      <ShotResultWidget 
        shotResult={shotResult}
        playerName={getPlayerName(shotResult.player_id)}
        isComputer={isComputerPlayer(shotResult.player_id)}
      />
    )}
    
    {/* Betting Opportunity */}
    {bettingOpportunity && (
      <BettingOpportunityWidget 
        bettingOpportunity={bettingOpportunity}
        onDecision={handleBettingDecision}
      />
    )}
    
    {/* Strategic Analysis */}
    {bettingAnalysis && (
      <StrategicAnalysisWidget 
        bettingAnalysis={bettingAnalysis}
      />
    )}
  </div>
);`}
        </pre>
      </div>

      <div style={{ background: '#e8f5e8', border: '1px solid #4caf50', padding: '16px', borderRadius: '8px', margin: '16px 0' }}>
        <h3>✅ Benefits:</h3>
        <ul>
          <li><strong>Consistent Design:</strong> All widgets use the same color scheme and styling</li>
          <li><strong>Rich Data Display:</strong> Beautiful visualizations of shot quality, risk levels, etc.</li>
          <li><strong>Interactive Elements:</strong> Built-in buttons and decision handling</li>
          <li><strong>Responsive Layout:</strong> Widgets adapt to different screen sizes</li>
          <li><strong>Easy Maintenance:</strong> Update widget logic in one place</li>
        </ul>
      </div>
    </div>
  );
};

export default IntegrationExample; 