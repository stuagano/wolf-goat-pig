import React, { useState } from 'react';

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
  tooltip: '#2c2c2c'
};

const EducationalTooltip = ({ 
  children, 
  content, 
  title, 
  position = 'top',
  maxWidth = 300,
  showIcon = true,
  type = 'info' // info, tip, warning, concept
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const handleMouseEnter = (e) => {
    setMousePosition({ x: e.clientX, y: e.clientY });
    setIsVisible(true);
  };

  const handleMouseMove = (e) => {
    setMousePosition({ x: e.clientX, y: e.clientY });
  };

  const handleMouseLeave = () => {
    setIsVisible(false);
  };

  const getTypeIcon = () => {
    switch (type) {
      case 'tip': return '💡';
      case 'warning': return '⚠️';
      case 'concept': return '🎓';
      default: return 'ℹ️';
    }
  };

  const getTypeColor = () => {
    switch (type) {
      case 'tip': return COLORS.warning;
      case 'warning': return COLORS.error;
      case 'concept': return COLORS.success;
      default: return COLORS.primary;
    }
  };

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <div
        onMouseEnter={handleMouseEnter}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={{ 
          cursor: 'help',
          borderBottom: `1px dashed ${getTypeColor()}`,
          display: 'inline-block'
        }}
      >
        {children}
        {showIcon && (
          <span style={{ 
            marginLeft: 4, 
            fontSize: 12,
            opacity: 0.7
          }}>
            {getTypeIcon()}
          </span>
        )}
      </div>

      {isVisible && (
        <div
          style={{
            position: 'fixed',
            left: mousePosition.x + 10,
            top: mousePosition.y - 10,
            maxWidth,
            background: COLORS.tooltip,
            color: 'white',
            padding: 12,
            borderRadius: 8,
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            zIndex: 10000,
            fontSize: 14,
            lineHeight: 1.4,
            pointerEvents: 'none'
          }}
        >
          {title && (
            <div style={{
              fontWeight: 600,
              marginBottom: 8,
              color: getTypeColor(),
              display: 'flex',
              alignItems: 'center',
              gap: 6
            }}>
              <span>{getTypeIcon()}</span>
              {title}
            </div>
          )}
          <div>{content}</div>
        </div>
      )}
    </div>
  );
};

// Pre-defined educational content for common betting terms and concepts
export const BettingConcepts = {
  expectedValue: {
    title: "Expected Value (EV)",
    content: "The average amount you can expect to win or lose on a bet over time. Positive EV means the bet is mathematically favorable.",
    type: "concept"
  },
  
  winProbability: {
    title: "Win Probability",
    content: "The calculated chance of winning based on current positions, handicaps, and course conditions. This updates in real-time as the hole progresses.",
    type: "info"
  },
  
  confidenceInterval: {
    title: "Confidence Interval",
    content: "A range showing the uncertainty in our probability calculation. Wider intervals indicate more uncertainty in the prediction.",
    type: "concept"
  },
  
  monteCarloSimulation: {
    title: "Monte Carlo Simulation",
    content: "A method that runs thousands of virtual games to calculate accurate probabilities. Used for complex scenarios with multiple variables.",
    type: "concept"
  },
  
  riskLevel: {
    title: "Risk Assessment",
    content: "Low risk: High probability of success. Medium risk: Uncertain outcome. High risk: Low probability of success with potential high reward.",
    type: "tip"
  },
  
  handicapAdjustment: {
    title: "Handicap Factors",
    content: "Lower handicap players have better odds on difficult shots. The system accounts for skill differences in probability calculations.",
    type: "info"
  },
  
  teamFormation: {
    title: "Partnership Strategy",
    content: "Choosing the right partner depends on handicaps, current positions, and hole difficulty. Consider complementary skills.",
    type: "tip"
  },
  
  soloPlay: {
    title: "Going Solo",
    content: "Playing alone against three opponents doubles the wager automatically. You need to beat the best ball of the other three players.",
    type: "warning"
  },
  
  doublingStrategy: {
    title: "Doubling the Wager",
    content: "Offer a double when you have favorable position or good odds. The other team can accept (doubling stakes) or decline (giving you the hole).",
    type: "tip"
  },
  
  lineOfScrimmage: {
    title: "Line of Scrimmage",
    content: "The point closest to the pin after all players have hit. Affects betting opportunities and partnership formation deadlines.",
    type: "info"
  },
  
  karlMarxRule: {
    title: "Karl Marx Rule",
    content: "When quarters can't be divided evenly among winners, the player with the fewest points gets the extra quarter(s). Helps the poor get richer!",
    type: "concept"
  },
  
  bigDickChallenge: {
    title: "Big Dick Challenge",
    content: "A high-stakes individual challenge on hole 18. All previous team results are ignored - it's every player for themselves.",
    type: "warning"
  },
  
  aardvarkSituation: {
    title: "Aardvark Rules",
    content: "When a player is significantly behind in points, special rules may apply to help them catch up. Includes team joining options and tossing mechanisms.",
    type: "concept"
  }
};

// Higher-order component for easy tooltip integration
export const withTooltip = (Component, tooltipProps) => {
  return (props) => (
    <EducationalTooltip {...tooltipProps}>
      <Component {...props} />
    </EducationalTooltip>
  );
};

// Strategic insights generator
export const generateStrategicInsight = (scenario, gameState) => {
  const insights = [];
  
  if (scenario.scenario_type === 'offer_double') {
    if (scenario.win_probability > 0.6) {
      insights.push({
        title: "Strong Doubling Position",
        content: `With ${(scenario.win_probability * 100).toFixed(1)}% win probability, this is a favorable time to double. The expected value is ${scenario.expected_value.toFixed(2)} quarters.`,
        type: "tip"
      });
    } else if (scenario.win_probability < 0.4) {
      insights.push({
        title: "Risky Double",
        content: `Low win probability (${(scenario.win_probability * 100).toFixed(1)}%) makes this a high-risk double. Consider your overall position before offering.`,
        type: "warning"
      });
    }
  }
  
  if (scenario.scenario_type === 'go_solo') {
    insights.push({
      title: "Solo Strategy",
      content: `Going solo requires beating the best ball of three opponents. Success rate is typically 15-35% depending on skill differential. High risk, high reward.`,
      type: "concept"
    });
  }
  
  if (gameState?.current_hole >= 16) {
    insights.push({
      title: "Late Game Strategy",
      content: `On the final holes, consider your overall match position. Sometimes protecting a lead is better than aggressive betting.`,
      type: "tip"
    });
  }
  
  return insights;
};

// Context-aware help system
export const ContextualHelp = ({ gamePhase, playerPosition, bettingScenario }) => {
  const getHelpContent = () => {
    if (gamePhase === 'partnership_formation') {
      return {
        title: "Partnership Formation",
        content: "The captain must choose a partner or go solo. Consider handicaps, current positions, and hole difficulty when deciding.",
        type: "tip"
      };
    }
    
    if (gamePhase === 'betting_window') {
      return {
        title: "Betting Window Open",
        content: "This is an optimal time for doubles and side bets. Position advantage and hole difficulty affect the odds.",
        type: "info"
      };
    }
    
    if (playerPosition === 'behind') {
      return {
        title: "Catch-Up Strategy",
        content: "When behind in points, consider more aggressive betting strategies. Solo play and accepting doubles can help you catch up.",
        type: "tip"
      };
    }
    
    if (playerPosition === 'leading') {
      return {
        title: "Protect Your Lead",
        content: "With a point lead, consider conservative play. Offering doubles from strong positions can pressure opponents.",
        type: "tip"
      };
    }
    
    return null;
  };
  
  const helpContent = getHelpContent();
  
  if (!helpContent) return null;
  
  return (
    <div style={{
      background: '#e3f2fd',
      border: `1px solid ${COLORS.primary}`,
      borderRadius: 8,
      padding: 12,
      margin: '12px 0',
      fontSize: 14
    }}>
      <div style={{
        fontWeight: 600,
        color: COLORS.primary,
        marginBottom: 4,
        display: 'flex',
        alignItems: 'center',
        gap: 6
      }}>
        <span>💡</span>
        {helpContent.title}
      </div>
      <div style={{ color: COLORS.text }}>
        {helpContent.content}
      </div>
    </div>
  );
};

export default EducationalTooltip;