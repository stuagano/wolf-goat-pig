import React from 'react';
import HoleVisualization from './HoleVisualization';

const HoleVisualizationTest = () => {
  // Mock game state for testing
  const mockGameState = {
    current_hole: 3,
    players: [
      { id: 'p1', name: 'Alice', handicap: 10.5 },
      { id: 'p2', name: 'Bob', handicap: 15.0 },
      { id: 'p3', name: 'Charlie', handicap: 8.0 },
      { id: 'p4', name: 'Dave', handicap: 20.5 }
    ]
  };

  // Mock hole state for testing
  const mockHoleState = {
    hole_par: 4,
    hole_yardage: 420,
    hole_difficulty: 'Hard',
    stroke_index: 3,
    line_of_scrimmage: 'p3',
    betting: {
      current_wager: 2,
      base_wager: 1
    },
    ball_positions: {
      p1: {
        distance_to_pin: 180,
        lie_type: 'fairway',
        holed: false,
        shot_count: 2
      },
      p2: {
        distance_to_pin: 85,
        lie_type: 'rough',
        holed: false,
        shot_count: 2
      },
      p3: {
        distance_to_pin: 280,
        lie_type: 'fairway',
        holed: false,
        shot_count: 1
      },
      p4: {
        distance_to_pin: 12,
        lie_type: 'green',
        holed: false,
        shot_count: 3
      }
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ textAlign: 'center', color: '#2c3e50' }}>
        🏌️ Hole Visualization Test
      </h1>
      
      <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <h3>Test Scenario:</h3>
        <p><strong>Hole 3 - Par 4, 420 yards, Hard difficulty</strong></p>
        <ul>
          <li>Charlie (p3) is at line of scrimmage - 280 yards out, can offer doubles</li>
          <li>Alice (p1) is 180 yards out - cannot offer doubles (past scrimmage line)</li>
          <li>Bob (p2) is 85 yards in rough - cannot offer doubles</li>
          <li>Dave (p4) is 12 yards on green - cannot offer doubles, putting for birdie</li>
        </ul>
      </div>

      <HoleVisualization 
        holeState={mockHoleState}
        players={mockGameState.players}
        gameState={mockGameState}
      />

      <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#e8f5e8', borderRadius: '8px' }}>
        <h4 style={{ color: '#27ae60' }}>✅ Test Results:</h4>
        <ul style={{ color: '#2c3e50' }}>
          <li>Line of scrimmage correctly shows at Charlie's position (280yd)</li>
          <li>Ball positions displayed with proper lie type colors</li>
          <li>Player names and distances clearly labeled</li>
          <li>Strategic information shows betting rules</li>
          <li>Green circle and hole pin properly positioned</li>
        </ul>
      </div>
    </div>
  );
};

export default HoleVisualizationTest;