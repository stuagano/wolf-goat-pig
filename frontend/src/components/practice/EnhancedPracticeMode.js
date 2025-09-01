import React, { useState, useEffect, useCallback } from 'react';
import Card from '../ui/Card';
import './EnhancedPracticeMode.css';

// AI Opponent Personalities with Enhanced Behaviors
const AI_OPPONENTS = {
  steady_eddie: {
    name: "Steady Eddie",
    avatar: "🎯",
    personality: "conservative",
    description: "Plays it safe, rarely doubles, partners when ahead",
    traits: {
      aggression: 0.2,
      partnership: 0.7,
      doubling: 0.15,
      riskTolerance: 0.3
    },
    decisionPatterns: {
      whenBehind: { partner: 0.8, solo: 0.2, double: 0.1 },
      whenAhead: { partner: 0.5, solo: 0.5, double: 0.05 },
      difficultHole: { partner: 0.9, solo: 0.1, double: 0.05 },
      easyHole: { partner: 0.4, solo: 0.6, double: 0.2 }
    }
  },
  aggressive_annie: {
    name: "Aggressive Annie",
    avatar: "🔥",
    personality: "aggressive",
    description: "High risk, high reward. Loves to double and go solo",
    traits: {
      aggression: 0.85,
      partnership: 0.3,
      doubling: 0.7,
      riskTolerance: 0.9
    },
    decisionPatterns: {
      whenBehind: { partner: 0.2, solo: 0.3, double: 0.5 },
      whenAhead: { partner: 0.1, solo: 0.4, double: 0.5 },
      difficultHole: { partner: 0.3, solo: 0.2, double: 0.5 },
      easyHole: { partner: 0.1, solo: 0.3, double: 0.6 }
    }
  },
  strategic_sam: {
    name: "Strategic Sam",
    avatar: "🧠",
    personality: "strategic",
    description: "Analyzes every situation, adapts to game flow",
    traits: {
      aggression: 0.5,
      partnership: 0.5,
      doubling: 0.35,
      riskTolerance: 0.6
    },
    decisionPatterns: {
      whenBehind: { partner: 0.5, solo: 0.2, double: 0.3 },
      whenAhead: { partner: 0.4, solo: 0.4, double: 0.2 },
      difficultHole: { partner: 0.6, solo: 0.1, double: 0.3 },
      easyHole: { partner: 0.3, solo: 0.5, double: 0.2 }
    }
  }
};

// Decision Types
const DECISION_TYPES = {
  CAPTAIN_CHOICE: 'captain_choice',
  PARTNERSHIP_RESPONSE: 'partnership_response',
  DOUBLING_DECISION: 'doubling_decision',
  STRATEGIC_PLAY: 'strategic_play'
};

const EnhancedPracticeMode = ({ onComplete, onExit }) => {
  const [gameState, setGameState] = useState({
    currentHole: 1,
    scores: {
      player: 0,
      steady_eddie: 0,
      aggressive_annie: 0,
      strategic_sam: 0
    },
    currentCaptain: 'player',
    currentDecision: null,
    gameHistory: [],
    playerStats: {
      decisionsWon: 0,
      decisionsLost: 0,
      partnershipSuccess: 0,
      soloSuccess: 0,
      doublingSuccess: 0
    }
  });

  const [pendingDecision, setPendingDecision] = useState(null);
  const [aiThoughts, setAiThoughts] = useState({});
  const [decisionAnalysis, setDecisionAnalysis] = useState(null);
  const [showCoaching, setShowCoaching] = useState(true);

  // Simulate hole difficulty
  const getHoleDifficulty = (holeNum) => {
    const difficulties = ['easy', 'medium', 'hard'];
    const index = (holeNum - 1) % 3;
    return difficulties[index];
  };

  // Get game situation
  const getGameSituation = () => {
    const { scores } = gameState;
    const playerScore = scores.player;
    const maxOpponentScore = Math.max(
      scores.steady_eddie,
      scores.aggressive_annie,
      scores.strategic_sam
    );
    
    if (playerScore > maxOpponentScore) return 'whenAhead';
    if (playerScore < maxOpponentScore) return 'whenBehind';
    return 'whenTied';
  };

  // AI Decision Making with Personality
  const makeAIDecision = (opponent, decisionType) => {
    const situation = getGameSituation();
    const holeDifficulty = getHoleDifficulty(gameState.currentHole);
    const patterns = AI_OPPONENTS[opponent].decisionPatterns;
    
    // Adjust patterns based on hole difficulty
    let adjustedPatterns = { ...patterns[situation] };
    if (holeDifficulty === 'hard') {
      adjustedPatterns = patterns.difficultHole;
    } else if (holeDifficulty === 'easy') {
      adjustedPatterns = patterns.easyHole;
    }

    // Generate decision based on weighted random
    const rand = Math.random();
    let cumulative = 0;
    
    for (const [decision, probability] of Object.entries(adjustedPatterns)) {
      cumulative += probability;
      if (rand < cumulative) {
        return decision;
      }
    }
    
    return 'partner'; // Default fallback
  };

  // Generate AI thought process
  const generateAIThought = (opponent, decision) => {
    const ai = AI_OPPONENTS[opponent];
    const situation = getGameSituation();
    const holeDifficulty = getHoleDifficulty(gameState.currentHole);
    
    const thoughts = {
      steady_eddie: {
        partner: `"Let's play it safe and team up. ${holeDifficulty === 'hard' ? 'This hole looks tough.' : 'Better to share the risk.'}"`,
        solo: `"I'm feeling confident enough to go alone here. The risk is manageable."`,
        double: `"The odds are in my favor here. Time for a calculated double."`
      },
      aggressive_annie: {
        partner: `"Ugh, fine. Partnership it is... but only because the risk is too high even for me!"`,
        solo: `"Watch this! I don't need anyone. Time to show what I can do!"`,
        double: `"DOUBLE DOWN! Let's make this interesting! 🔥"`
      },
      strategic_sam: {
        partner: `"Based on the ${situation} and ${holeDifficulty} difficulty, partnership offers the best expected value."`,
        solo: `"My analysis suggests going solo here. The risk-reward ratio is favorable."`,
        double: `"The probabilities favor doubling. Expected return: +${Math.floor(Math.random() * 30 + 20)}%"`
      }
    };
    
    return thoughts[opponent][decision] || `"Making a ${decision} decision..."`;
  };

  // Present Captain Decision to Player
  const presentCaptainDecision = () => {
    const holeDifficulty = getHoleDifficulty(gameState.currentHole);
    const situation = getGameSituation();
    
    setPendingDecision({
      type: DECISION_TYPES.CAPTAIN_CHOICE,
      title: `Hole ${gameState.currentHole} - You're the Captain!`,
      subtitle: `${holeDifficulty.toUpperCase()} difficulty • You're ${situation.replace('when', '').toLowerCase()}`,
      options: [
        {
          id: 'partner',
          label: 'Choose Partner',
          icon: '🤝',
          description: 'Team up with an opponent',
          riskLevel: 'low',
          expectedValue: calculateExpectedValue('partner', holeDifficulty, situation),
          coachAdvice: generateCoachAdvice('partner', holeDifficulty, situation)
        },
        {
          id: 'solo',
          label: 'Go Solo (Wolf)',
          icon: '🐺',
          description: 'Play alone for higher stakes',
          riskLevel: 'high',
          expectedValue: calculateExpectedValue('solo', holeDifficulty, situation),
          coachAdvice: generateCoachAdvice('solo', holeDifficulty, situation)
        }
      ],
      aiResponses: {}
    });

    // Generate AI responses
    const responses = {};
    Object.keys(AI_OPPONENTS).forEach(opponent => {
      const decision = makeAIDecision(opponent, DECISION_TYPES.CAPTAIN_CHOICE);
      responses[opponent] = {
        decision,
        thought: generateAIThought(opponent, decision)
      };
    });
    
    setAiThoughts(responses);
  };

  // Calculate expected value for decisions
  const calculateExpectedValue = (decision, difficulty, situation) => {
    const baseValues = {
      partner: { easy: 2, medium: 3, hard: 4 },
      solo: { easy: 4, medium: 6, hard: 8 }
    };
    
    const situationMultiplier = {
      whenAhead: 0.9,
      whenBehind: 1.1,
      whenTied: 1.0
    };
    
    const value = baseValues[decision][difficulty] * situationMultiplier[situation];
    const winProbability = decision === 'partner' ? 0.6 : 0.4;
    
    return {
      expectedPoints: (value * winProbability).toFixed(1),
      winProbability: (winProbability * 100).toFixed(0),
      riskRating: decision === 'partner' ? 'Low' : 'High'
    };
  };

  // Generate coaching advice
  const generateCoachAdvice = (decision, difficulty, situation) => {
    const advice = {
      partner: {
        easy: "Good choice for building steady points on an easy hole.",
        medium: "Smart play to share the risk on a moderate hole.",
        hard: "Wise decision! This hole is tough - partnership reduces risk."
      },
      solo: {
        easy: "Bold move! Easy holes are good for wolf attempts.",
        medium: "Risky but potentially rewarding on this moderate hole.",
        hard: "Very aggressive! Going solo on hard holes requires confidence."
      }
    };
    
    return advice[decision][difficulty];
  };

  // Handle player decision
  const handlePlayerDecision = (optionId) => {
    const decision = pendingDecision.options.find(opt => opt.id === optionId);
    
    // Show decision analysis
    setDecisionAnalysis({
      yourChoice: decision,
      aiChoices: aiThoughts,
      outcome: simulateHoleOutcome(decision.id),
      lesson: generateLessonFromDecision(decision.id, aiThoughts)
    });
    
    // Update game state
    setGameState(prev => ({
      ...prev,
      currentHole: prev.currentHole + 1,
      gameHistory: [...prev.gameHistory, {
        hole: prev.currentHole,
        playerDecision: decision.id,
        aiDecisions: aiThoughts,
        outcome: 'TBD'
      }]
    }));
    
    // Clear pending decision after delay
    setTimeout(() => {
      setPendingDecision(null);
      setDecisionAnalysis(null);
      if (gameState.currentHole < 18) {
        presentCaptainDecision();
      }
    }, 5000);
  };

  // Simulate hole outcome
  const simulateHoleOutcome = (playerDecision) => {
    const rand = Math.random();
    const success = playerDecision === 'partner' ? rand < 0.6 : rand < 0.4;
    
    return {
      success,
      points: success ? (playerDecision === 'partner' ? 3 : 6) : 0,
      message: success ? 
        `Great ${playerDecision === 'partner' ? 'partnership' : 'wolf'} play!` :
        `The ${playerDecision === 'partner' ? 'partnership' : 'wolf attempt'} didn't work out this time.`
    };
  };

  // Generate lesson from decision
  const generateLessonFromDecision = (playerDecision, aiDecisions) => {
    const aiDecisionCounts = Object.values(aiDecisions).reduce((acc, ai) => {
      acc[ai.decision] = (acc[ai.decision] || 0) + 1;
      return acc;
    }, {});
    
    const majorityDecision = Object.entries(aiDecisionCounts)
      .sort((a, b) => b[1] - a[1])[0][0];
    
    if (playerDecision === majorityDecision) {
      return "You aligned with the majority of AI players. This shows good situational awareness!";
    } else {
      return "You went against the grain! Sometimes unique decisions pay off big.";
    }
  };

  // Initialize game
  useEffect(() => {
    presentCaptainDecision();
  }, []);

  return (
    <div className="enhanced-practice-mode">
      {/* Game Header */}
      <div className="practice-header">
        <div className="hole-info">
          <h2>Hole {gameState.currentHole} of 18</h2>
          <span className={`difficulty-badge ${getHoleDifficulty(gameState.currentHole)}`}>
            {getHoleDifficulty(gameState.currentHole).toUpperCase()}
          </span>
        </div>
        
        <div className="score-summary">
          <div className="player-score">
            <span>You: {gameState.scores.player}</span>
          </div>
          <div className="ai-scores">
            {Object.entries(AI_OPPONENTS).map(([key, ai]) => (
              <span key={key}>
                {ai.avatar} {gameState.scores[key]}
              </span>
            ))}
          </div>
        </div>
        
        <button onClick={onExit} className="exit-button">
          Exit Practice
        </button>
      </div>

      {/* AI Opponents Display */}
      <div className="ai-opponents-row">
        {Object.entries(AI_OPPONENTS).map(([key, ai]) => (
          <Card key={key} className="ai-opponent-card">
            <div className="ai-avatar">{ai.avatar}</div>
            <h3>{ai.name}</h3>
            <p className="ai-description">{ai.description}</p>
            {aiThoughts[key] && (
              <div className="ai-thought-bubble">
                {aiThoughts[key].thought}
              </div>
            )}
            <div className="ai-stats">
              <span className="trait">Aggression: {(ai.traits.aggression * 100).toFixed(0)}%</span>
              <span className="trait">Risk: {(ai.traits.riskTolerance * 100).toFixed(0)}%</span>
            </div>
          </Card>
        ))}
      </div>

      {/* Decision Interface */}
      {pendingDecision && (
        <div className="decision-overlay">
          <Card className="decision-card">
            <h2>{pendingDecision.title}</h2>
            <p className="decision-subtitle">{pendingDecision.subtitle}</p>
            
            <div className="decision-options">
              {pendingDecision.options.map(option => (
                <div
                  key={option.id}
                  className={`decision-option ${option.riskLevel}-risk`}
                  onClick={() => handlePlayerDecision(option.id)}
                >
                  <div className="option-header">
                    <span className="option-icon">{option.icon}</span>
                    <h3>{option.label}</h3>
                  </div>
                  
                  <p className="option-description">{option.description}</p>
                  
                  <div className="option-analytics">
                    <div className="expected-value">
                      <span className="label">Expected Points:</span>
                      <span className="value">+{option.expectedValue.expectedPoints}</span>
                    </div>
                    <div className="win-probability">
                      <span className="label">Win Chance:</span>
                      <span className="value">{option.expectedValue.winProbability}%</span>
                    </div>
                    <div className="risk-rating">
                      <span className="label">Risk:</span>
                      <span className="value">{option.expectedValue.riskRating}</span>
                    </div>
                  </div>
                  
                  {showCoaching && (
                    <div className="coach-advice">
                      <span className="coach-icon">💡</span>
                      {option.coachAdvice}
                    </div>
                  )}
                </div>
              ))}
            </div>
            
            <div className="decision-timer">
              <span>Decision Time Remaining: 15s</span>
              <div className="timer-bar"></div>
            </div>
          </Card>
        </div>
      )}

      {/* Decision Analysis */}
      {decisionAnalysis && (
        <div className="analysis-overlay">
          <Card className="analysis-card">
            <h2>Decision Analysis</h2>
            
            <div className="your-decision">
              <h3>Your Choice: {decisionAnalysis.yourChoice.label}</h3>
              <p className={decisionAnalysis.outcome.success ? 'success' : 'failure'}>
                {decisionAnalysis.outcome.message}
              </p>
              <p>Points: {decisionAnalysis.outcome.success ? `+${decisionAnalysis.outcome.points}` : '0'}</p>
            </div>
            
            <div className="ai-decisions">
              <h3>What the AI Players Chose:</h3>
              {Object.entries(decisionAnalysis.aiChoices).map(([key, choice]) => (
                <div key={key} className="ai-choice">
                  <span>{AI_OPPONENTS[key].avatar} {AI_OPPONENTS[key].name}:</span>
                  <span>{choice.decision === 'partner' ? '🤝 Partner' : '🐺 Solo'}</span>
                </div>
              ))}
            </div>
            
            <div className="lesson">
              <h3>Lesson:</h3>
              <p>{decisionAnalysis.lesson}</p>
            </div>
          </Card>
        </div>
      )}

      {/* Coaching Toggle */}
      <div className="coaching-toggle">
        <label>
          <input
            type="checkbox"
            checked={showCoaching}
            onChange={(e) => setShowCoaching(e.target.checked)}
          />
          Show Coaching Tips
        </label>
      </div>

      {/* Player Stats Dashboard */}
      <div className="player-stats-dashboard">
        <Card className="stats-card">
          <h3>Your Decision Stats</h3>
          <div className="stat-grid">
            <div className="stat">
              <span className="stat-label">Decisions Won:</span>
              <span className="stat-value">{gameState.playerStats.decisionsWon}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Partnership Success:</span>
              <span className="stat-value">{gameState.playerStats.partnershipSuccess}%</span>
            </div>
            <div className="stat">
              <span className="stat-label">Solo Success:</span>
              <span className="stat-value">{gameState.playerStats.soloSuccess}%</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default EnhancedPracticeMode;