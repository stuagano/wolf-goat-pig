import React, { useState, useEffect } from 'react';
import { useTutorial } from '../../../context/TutorialContext';
import { useTheme } from '../../../theme/Provider';
import TutorialModule from '../TutorialModule';
import { TutorialSimulation } from '../InteractiveElement';

const PracticeGameModule = ({ onStepComplete, onModuleComplete, currentStep, goToStep }) => {
  const tutorial = useTutorial();
  const theme = useTheme();
  const [gameState, setGameState] = useState({
    hole: 1,
    scores: { player: 0, ai1: 0, ai2: 0, ai3: 0 },
    money: { player: 0, ai1: 0, ai2: 0, ai3: 0 },
    currentHoleScores: { player: null, ai1: null, ai2: null, ai3: null },
    selectionOrder: ['player', 'ai1', 'ai2', 'ai3'],
    roles: {}
  });

  const steps = [
    {
      id: 'game-setup',
      title: 'Practice Game Setup',
      hints: 'Get familiar with the practice environment and AI opponents.',
      content: 'game-setup'
    },
    {
      id: 'guided-play',
      title: 'Guided Hole-by-Hole Play',
      hints: 'Play through several holes with contextual guidance and strategy tips.',
      content: 'guided-play'
    },
    {
      id: 'independent-practice',
      title: 'Independent Practice Rounds',
      hints: 'Practice on your own with minimal guidance to build confidence.',
      content: 'independent-practice'
    }
  ];

  const moduleProps = {
    moduleId: 'practice-game',
    title: 'Practice Game with Guidance',
    description: 'Apply everything you\'ve learned in a guided practice round against AI opponents with real-time coaching.',
    estimatedTime: 30,
    steps,
    currentStep,
    onStepComplete,
    onModuleComplete,
    allowSkip: true,
    requiredCompletion: false
  };

  const renderStepContent = () => {
    const currentStepData = steps[currentStep];
    if (!currentStepData) return null;

    switch (currentStepData.content) {
      case 'game-setup':
        return <GameSetupStep />;
      case 'guided-play':
        return <GuidedPlayStep gameState={gameState} setGameState={setGameState} />;
      case 'independent-practice':
        return <IndependentPracticeStep />;
      default:
        return <div>Step content not found</div>;
    }
  };

  const GameSetupStep = () => (
    <div style={{maxWidth: 900, margin: '0 auto'}}>
      <div style={{...theme.cardStyle, padding: theme.spacing[5], marginBottom: theme.spacing[4], textAlign: 'center'}}>
        <h3 style={{
          fontSize: theme.typography.xl,
          fontWeight: theme.typography.bold,
          color: theme.colors.primary,
          marginBottom: theme.spacing[4]
        }}>
          Welcome to Wolf Goat Pig Practice!
        </h3>
        
        <p style={{fontSize: theme.typography.lg, lineHeight: 1.6, marginBottom: theme.spacing[6]}}>
          You're about to play your first guided round of Wolf Goat Pig. Don't worry - 
          you'll receive real-time coaching and strategy tips throughout the game.
        </p>
        
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: theme.spacing[4]}}>
          <div style={{textAlign: 'center'}}>
            <div style={{fontSize: '3rem', marginBottom: theme.spacing[2]}}>🤖</div>
            <h4>AI Opponents</h4>
            <p style={{fontSize: theme.typography.sm}}>Play against three AI players with different strategies and skill levels</p>
          </div>
          <div style={{textAlign: 'center'}}>
            <div style={{fontSize: '3rem', marginBottom: theme.spacing[2]}}>💡</div>
            <h4>Real-time Coaching</h4>
            <p style={{fontSize: theme.typography.sm}}>Get strategic advice and explanations for every decision</p>
          </div>
          <div style={{textAlign: 'center'}}>
            <div style={{fontSize: '3rem', marginBottom: theme.spacing[2]}}>📊</div>
            <h4>Performance Tracking</h4>
            <p style={{fontSize: theme.typography.sm}}>See how your decisions affect your winnings and strategy</p>
          </div>
        </div>
      </div>

      <div style={{...theme.cardStyle, padding: theme.spacing[5]}}>
        <h3 style={{color: theme.colors.primary, marginBottom: theme.spacing[4]}}>Meet Your Opponents</h3>
        
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: theme.spacing[4]}}>
          <div style={{padding: theme.spacing[4], border: `2px solid ${theme.colors.success}`, borderRadius: theme.borderRadius.base}}>
            <h4 style={{color: theme.colors.success, marginBottom: theme.spacing[2]}}>🤖 Steady Eddie</h4>
            <ul style={{fontSize: theme.typography.sm, lineHeight: 1.6}}>
              <li>Conservative player</li>
              <li>Rarely goes Wolf</li>
              <li>Consistent scoring</li>
              <li>Good partner choice</li>
            </ul>
          </div>
          
          <div style={{padding: theme.spacing[4], border: `2px solid ${theme.colors.warning}`, borderRadius: theme.borderRadius.base}}>
            <h4 style={{color: theme.colors.warning, marginBottom: theme.spacing[2]}}>🤖 Aggressive Annie</h4>
            <ul style={{fontSize: theme.typography.sm, lineHeight: 1.6}}>
              <li>High-risk, high-reward</li>
              <li>Loves going Wolf</li>
              <li>Variable scoring</li>
              <li>Exciting to play against</li>
            </ul>
          </div>
          
          <div style={{padding: theme.spacing[4], border: `2px solid ${theme.colors.error}`, borderRadius: theme.borderRadius.base}}>
            <h4 style={{color: theme.colors.error, marginBottom: theme.spacing[2]}}>🤖 Strategic Sam</h4>
            <ul style={{fontSize: theme.typography.sm, lineHeight: 1.6}}>
              <li>Adapts to situations</li>
              <li>Studies your patterns</li>
              <li>Makes smart partnerships</li>
              <li>Your biggest challenge</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );

  const GuidedPlayStep = ({ gameState, setGameState }) => {
    const [currentDecision, setCurrentDecision] = useState(null);
    
    const holes = [
      {
        number: 1,
        par: 4,
        distance: 380,
        difficulty: 'Medium',
        description: 'Straight par 4 with bunkers guarding the green',
        strategy: 'Good hole to start conservatively and observe opponents'
      },
      {
        number: 2,
        par: 3,
        distance: 165,
        difficulty: 'Easy',
        description: 'Short par 3 to large green, most players make par',
        strategy: 'Be cautious about going Wolf - everyone plays well here'
      },
      {
        number: 3,
        par: 5,
        distance: 520,
        difficulty: 'Hard',
        description: 'Long par 5 with water hazard on approach',
        strategy: 'Good Wolf opportunity if you\'re confident driving'
      }
    ];

    const currentHole = holes[Math.min(gameState.hole - 1, holes.length - 1)];

    const handleRoleSelection = (role) => {
      const newRoles = { ...gameState.roles, player: role };
      
      // Simulate AI role selections
      const availableRoles = ['wolf', 'goat', 'pig'];
      ['ai1', 'ai2', 'ai3'].forEach(ai => {
        if (!newRoles[ai]) {
          // Simple AI logic
          let selectedRole;
          if (ai === 'ai2' && Math.random() > 0.7) { // Aggressive Annie
            selectedRole = 'wolf';
          } else if (availableRoles.includes('goat') && Math.random() > 0.5) {
            selectedRole = 'goat';
          } else {
            selectedRole = availableRoles[0] || 'pig';
          }
          newRoles[ai] = selectedRole;
        }
      });

      setGameState(prev => ({ ...prev, roles: newRoles }));
      
      // Simulate hole play
      setTimeout(() => {
        simulateHoleOutcome(newRoles);
      }, 2000);
    };

    const simulateHoleOutcome = (roles) => {
      // Simple simulation of hole results
      const scores = {
        player: Math.floor(Math.random() * 3) + currentHole.par - 1,
        ai1: Math.floor(Math.random() * 3) + currentHole.par - 1,
        ai2: Math.floor(Math.random() * 4) + currentHole.par - 2,
        ai3: Math.floor(Math.random() * 3) + currentHole.par - 1
      };

      // Calculate money exchange (simplified)
      const moneyChange = { player: 0, ai1: 0, ai2: 0, ai3: 0 };
      
      // Determine winners based on roles and scores
      // (This would be more complex in a real implementation)
      if (roles.player === 'wolf') {
        if (scores.player <= Math.min(scores.ai1, scores.ai2, scores.ai3)) {
          moneyChange.player = 15; // Win $5 from each
          moneyChange.ai1 = moneyChange.ai2 = moneyChange.ai3 = -5;
        } else {
          moneyChange.player = -15; // Lose $5 to each
          moneyChange.ai1 = moneyChange.ai2 = moneyChange.ai3 = 5;
        }
      }

      setGameState(prev => ({
        ...prev,
        hole: prev.hole + 1,
        currentHoleScores: scores,
        money: {
          player: prev.money.player + moneyChange.player,
          ai1: prev.money.ai1 + moneyChange.ai1,
          ai2: prev.money.ai2 + moneyChange.ai2,
          ai3: prev.money.ai3 + moneyChange.ai3
        },
        roles: {}
      }));
    };

    return (
      <div style={{maxWidth: 900, margin: '0 auto'}}>
        <div style={{...theme.cardStyle, padding: theme.spacing[5], marginBottom: theme.spacing[4]}}>
          <h3 style={{color: theme.colors.primary, marginBottom: theme.spacing[3]}}>
            Hole {currentHole.number} - Par {currentHole.par}
          </h3>
          
          <div style={{display: 'grid', gridTemplateColumns: '2fr 1fr', gap: theme.spacing[4], marginBottom: theme.spacing[4]}}>
            <div>
              <h4>Hole Description</h4>
              <p style={{marginBottom: theme.spacing[3]}}>{currentHole.description}</p>
              
              <div style={{
                padding: theme.spacing[3],
                backgroundColor: theme.colors.primaryLight + '20',
                borderRadius: theme.borderRadius.base,
                borderLeft: `4px solid ${theme.colors.primary}`
              }}>
                <strong>💡 Strategy Tip:</strong> {currentHole.strategy}
              </div>
            </div>
            
            <div>
              <h4>Hole Stats</h4>
              <div style={{fontSize: theme.typography.sm}}>
                <div>Distance: {currentHole.distance} yards</div>
                <div>Difficulty: {currentHole.difficulty}</div>
                <div style={{marginTop: theme.spacing[2]}}>
                  <strong>Current Standings:</strong><br/>
                  You: ${gameState.money.player}<br/>
                  Eddie: ${gameState.money.ai1}<br/>
                  Annie: ${gameState.money.ai2}<br/>
                  Sam: ${gameState.money.ai3}
                </div>
              </div>
            </div>
          </div>
        </div>

        <TutorialSimulation
          title={`Role Selection - Hole ${currentHole.number}`}
          scenario={`You have first choice on this ${currentHole.difficulty.toLowerCase()} ${currentHole.description.toLowerCase()}. What role do you want to play?`}
          options={[
            {
              title: "🐺 Wolf",
              description: "Go alone against all three opponents for maximum risk/reward"
            },
            {
              title: "🐐 Goat",
              description: "Choose to partner up with another player"
            },
            {
              title: "🐷 Pig",
              description: "Accept whatever role is left after others choose"
            }
          ]}
          onDecision={(option) => {
            let role;
            if (option.title.includes('Wolf')) role = 'wolf';
            else if (option.title.includes('Goat')) role = 'goat';
            else role = 'pig';
            
            handleRoleSelection(role);
            
            const feedback = role === 'wolf' && currentHole.difficulty === 'Hard'
              ? "Great choice! Difficult holes are often good Wolf opportunities."
              : role === 'goat' 
              ? "Solid strategic thinking! Partnerships can be very effective."
              : "Playing it safe - sometimes the best strategy!";
              
            tutorial.addFeedback(feedback);
          }}
        />

        {gameState.currentHoleScores && (
          <div style={{
            ...theme.cardStyle,
            padding: theme.spacing[4],
            marginTop: theme.spacing[4],
            backgroundColor: theme.colors.successLight + '20'
          }}>
            <h4>Hole {gameState.hole - 1} Results</h4>
            <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: theme.spacing[3], marginTop: theme.spacing[3]}}>
              <div>You: {gameState.currentHoleScores.player}</div>
              <div>Eddie: {gameState.currentHoleScores.ai1}</div>
              <div>Annie: {gameState.currentHoleScores.ai2}</div>
              <div>Sam: {gameState.currentHoleScores.ai3}</div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const IndependentPracticeStep = () => (
    <div style={{maxWidth: 900, margin: '0 auto'}}>
      <div style={{...theme.cardStyle, padding: theme.spacing[5], marginBottom: theme.spacing[4], textAlign: 'center'}}>
        <h3 style={{
          fontSize: theme.typography.xl,
          fontWeight: theme.typography.bold,
          color: theme.colors.primary,
          marginBottom: theme.spacing[4]
        }}>
          Ready for Independent Practice!
        </h3>
        
        <p style={{fontSize: theme.typography.lg, lineHeight: 1.6, marginBottom: theme.spacing[6]}}>
          You've completed the guided tutorial. Now you can practice on your own with 
          the full Wolf Goat Pig game interface. Good luck!
        </p>
        
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: theme.spacing[6]}}>
          <div>
            <h4 style={{color: theme.colors.success, marginBottom: theme.spacing[3]}}>
              What You've Learned
            </h4>
            <ul style={{textAlign: 'left', lineHeight: 1.8}}>
              <li>Golf basics and terminology</li>
              <li>Wolf Goat Pig rules and roles</li>
              <li>Team formation strategies</li>
              <li>Betting systems and risk management</li>
              <li>Advanced strategies and analysis tools</li>
            </ul>
          </div>
          
          <div>
            <h4 style={{color: theme.colors.primary, marginBottom: theme.spacing[3]}}>
              Next Steps
            </h4>
            <ul style={{textAlign: 'left', lineHeight: 1.8}}>
              <li>Play practice rounds to build confidence</li>
              <li>Experiment with different strategies</li>
              <li>Track your performance over time</li>
              <li>Join real games when you feel ready</li>
              <li>Continue learning and improving</li>
            </ul>
          </div>
        </div>
        
        <div style={{
          marginTop: theme.spacing[6],
          padding: theme.spacing[4],
          backgroundColor: theme.colors.primaryLight + '20',
          borderRadius: theme.borderRadius.base
        }}>
          <strong>🎉 Congratulations!</strong> You've completed the Wolf Goat Pig tutorial. 
          You're now ready to enjoy this exciting golf betting game with confidence and strategic thinking!
        </div>
      </div>
    </div>
  );

  return (
    <TutorialModule {...moduleProps}>
      {renderStepContent()}
    </TutorialModule>
  );
};

export default PracticeGameModule;