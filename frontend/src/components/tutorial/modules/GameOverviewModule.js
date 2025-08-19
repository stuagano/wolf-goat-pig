import React, { useState } from 'react';
import { useTutorial } from '../../../context/TutorialContext';
import { useTheme } from '../../../theme/Provider';
import TutorialModule from '../TutorialModule';
import { TutorialQuiz, TutorialSimulation } from '../InteractiveElement';

const GameOverviewModule = ({ onStepComplete, onModuleComplete, currentStep, goToStep }) => {
  const tutorial = useTutorial();
  const theme = useTheme();

  const steps = [
    {
      id: 'wgp-introduction',
      title: 'What is Wolf Goat Pig?',
      hints: 'Wolf Goat Pig adds strategy and excitement to regular golf through dynamic partnerships.',
      content: 'wgp-introduction'
    },
    {
      id: 'game-objectives',
      title: 'Game Objectives & Winning',
      hints: 'The goal is to win money through strategic partnerships and good play.',
      content: 'game-objectives'
    },
    {
      id: 'role-explanation',
      title: 'Understanding Roles: Wolf, Goat, Pig',
      hints: 'Each role has different strategies and risk/reward profiles.',
      content: 'role-explanation'
    },
    {
      id: 'game-flow',
      title: 'How a Round Progresses',
      hints: 'Understanding the flow helps you plan your strategy across all 18 holes.',
      content: 'game-flow'
    },
    {
      id: 'strategy-simulation',
      title: 'Basic Strategy Simulation',
      hints: 'Practice making strategic decisions in different scenarios.',
      content: 'strategy-simulation'
    }
  ];

  const moduleProps = {
    moduleId: 'game-overview',
    title: 'Wolf Goat Pig Overview & Objectives',
    description: 'Understand the core mechanics, roles, and strategic elements that make Wolf Goat Pig an exciting golf betting game.',
    estimatedTime: 10,
    steps,
    currentStep,
    onStepComplete,
    onModuleComplete,
    allowSkip: false,
    requiredCompletion: true
  };

  const renderStepContent = () => {
    const currentStepData = steps[currentStep];
    if (!currentStepData) return null;

    switch (currentStepData.content) {
      case 'wgp-introduction':
        return <WGPIntroductionStep />;
      case 'game-objectives':
        return <GameObjectivesStep />;
      case 'role-explanation':
        return <RoleExplanationStep />;
      case 'game-flow':
        return <GameFlowStep />;
      case 'strategy-simulation':
        return <StrategySimulationStep />;
      default:
        return <div>Step content not found</div>;
    }
  };

  const WGPIntroductionStep = () => {
    const styles = {
      container: {
        maxWidth: 900,
        margin: '0 auto'
      },
      
      heroCard: {
        ...theme.cardStyle,
        padding: theme.spacing[8],
        marginBottom: theme.spacing[6],
        textAlign: 'center',
        background: `linear-gradient(135deg, ${theme.colors.primary} 0%, ${theme.colors.accent} 100%)`,
        color: '#ffffff',
        border: 'none'
      },
      
      heroTitle: {
        fontSize: theme.typography['3xl'],
        fontWeight: theme.typography.bold,
        marginBottom: theme.spacing[4]
      },
      
      heroSubtitle: {
        fontSize: theme.typography.lg,
        opacity: 0.9,
        lineHeight: 1.6
      },
      
      featuresGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: theme.spacing[4],
        marginBottom: theme.spacing[6]
      },
      
      featureCard: {
        ...theme.cardStyle,
        padding: theme.spacing[5],
        textAlign: 'center',
        transition: tutorial.reducedMotion ? 'none' : 'transform 0.2s ease'
      },
      
      featureIcon: {
        fontSize: '3rem',
        marginBottom: theme.spacing[3]
      },
      
      featureTitle: {
        fontSize: theme.typography.lg,
        fontWeight: theme.typography.semibold,
        color: theme.colors.primary,
        marginBottom: theme.spacing[2]
      },
      
      comparisonCard: {
        ...theme.cardStyle,
        padding: theme.spacing[5]
      },
      
      comparisonGrid: {
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: theme.spacing[6],
        marginTop: theme.spacing[4]
      },
      
      comparisonSide: {
        textAlign: 'center'
      },
      
      comparisonTitle: {
        fontSize: theme.typography.lg,
        fontWeight: theme.typography.semibold,
        marginBottom: theme.spacing[3]
      }
    };

    return (
      <div style={styles.container}>
        <div style={styles.heroCard}>
          <h2 style={styles.heroTitle}>🐺🐐🐷 Wolf Goat Pig</h2>
          <p style={styles.heroSubtitle}>
            A dynamic golf betting game that transforms ordinary rounds into strategic battles 
            through changing partnerships, calculated risks, and exciting wagering opportunities.
          </p>
        </div>

        <div style={styles.featuresGrid}>
          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>🤝</div>
            <h3 style={styles.featureTitle}>Dynamic Partnerships</h3>
            <p>Team up with different players throughout the round, creating ever-changing alliances and strategies.</p>
          </div>
          
          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>💰</div>
            <h3 style={styles.featureTitle}>Strategic Betting</h3>
            <p>Make calculated wagers based on hole difficulty, player performance, and risk tolerance.</p>
          </div>
          
          <div style={styles.featureCard}>
            <div style={styles.featureIcon}>🎯</div>
            <h3 style={styles.featureTitle}>Skill & Strategy</h3>
            <p>Success depends on both golf skills and strategic decision-making throughout the round.</p>
          </div>
        </div>

        <div style={styles.comparisonCard}>
          <h3 style={{
            fontSize: theme.typography.xl,
            fontWeight: theme.typography.bold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[4],
            textAlign: 'center'
          }}>
            Wolf Goat Pig vs. Regular Golf
          </h3>
          
          <div style={styles.comparisonGrid}>
            <div style={styles.comparisonSide}>
              <h4 style={{...styles.comparisonTitle, color: theme.colors.textSecondary}}>
                Regular Golf
              </h4>
              <ul style={{textAlign: 'left', lineHeight: 2}}>
                <li>Individual competition</li>
                <li>Fixed scoring system</li>
                <li>Static partnerships (if any)</li>
                <li>Limited betting opportunities</li>
                <li>Predictable strategy</li>
              </ul>
            </div>
            
            <div style={styles.comparisonSide}>
              <h4 style={{...styles.comparisonTitle, color: theme.colors.primary}}>
                Wolf Goat Pig
              </h4>
              <ul style={{textAlign: 'left', lineHeight: 2}}>
                <li>Dynamic team competition</li>
                <li>Multiple scoring scenarios</li>
                <li>Changing partnerships each hole</li>
                <li>Strategic betting decisions</li>
                <li>Adaptive strategy required</li>
              </ul>
            </div>
          </div>
          
          <div style={{
            marginTop: theme.spacing[6],
            padding: theme.spacing[4],
            backgroundColor: theme.colors.successLight + '20',
            borderRadius: theme.borderRadius.base,
            borderLeft: `4px solid ${theme.colors.success}`,
            textAlign: 'center'
          }}>
            <strong>The Result:</strong> Every hole becomes a mini-game with its own strategy, 
            partnerships, and opportunities for both big wins and calculated risks.
          </div>
        </div>
      </div>
    );
  };

  const GameObjectivesStep = () => {
    const styles = {
      container: {
        maxWidth: 800,
        margin: '0 auto'
      },
      
      objectiveCard: {
        ...theme.cardStyle,
        padding: theme.spacing[5],
        marginBottom: theme.spacing[4]
      },
      
      objectiveTitle: {
        fontSize: theme.typography.lg,
        fontWeight: theme.typography.semibold,
        color: theme.colors.primary,
        marginBottom: theme.spacing[3]
      },
      
      winConditions: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: theme.spacing[4],
        marginTop: theme.spacing[4]
      },
      
      winCondition: {
        padding: theme.spacing[4],
        borderRadius: theme.borderRadius.base,
        border: `2px solid ${theme.colors.border}`,
        textAlign: 'center'
      },
      
      exampleGame: {
        ...theme.cardStyle,
        padding: theme.spacing[5],
        marginTop: theme.spacing[6]
      }
    };

    return (
      <div style={styles.container}>
        <div style={styles.objectiveCard}>
          <h3 style={styles.objectiveTitle}>Primary Objective: Maximize Your Winnings</h3>
          <p style={{fontSize: theme.typography.base, lineHeight: 1.6, marginBottom: theme.spacing[4]}}>
            Unlike regular golf where the goal is simply to shoot the lowest score, Wolf Goat Pig 
            focuses on <strong>winning money</strong> through strategic partnerships and smart betting decisions.
          </p>
          
          <div style={{
            padding: theme.spacing[4],
            backgroundColor: theme.colors.primaryLight + '20',
            borderRadius: theme.borderRadius.base,
            borderLeft: `4px solid ${theme.colors.primary}`
          }}>
            <strong>Key Insight:</strong> The player with the lowest golf score doesn't always win 
            the most money. Strategic thinking and partnership choices often matter more than pure golf skill.
          </div>
        </div>

        <div style={styles.objectiveCard}>
          <h3 style={styles.objectiveTitle}>Ways to Win Money</h3>
          
          <div style={styles.winConditions}>
            <div style={styles.winCondition}>
              <div style={{fontSize: '2rem', marginBottom: theme.spacing[2]}}>🤝</div>
              <h4>Partnership Wins</h4>
              <p style={{fontSize: theme.typography.sm}}>
                Team up with another player to beat the remaining pair on each hole
              </p>
            </div>
            
            <div style={styles.winCondition}>
              <div style={{fontSize: '2rem', marginBottom: theme.spacing[2]}}>🐺</div>
              <h4>Wolf Wins</h4>
              <p style={{fontSize: theme.typography.sm}}>
                Go solo against the other three players for bigger rewards (and bigger risks)
              </p>
            </div>
            
            <div style={styles.winCondition}>
              <div style={{fontSize: '2rem', marginBottom: theme.spacing[2]}}>💎</div>
              <h4>Special Bets</h4>
              <p style={{fontSize: theme.typography.sm}}>
                Side bets and bonuses for exceptional performance or risky plays
              </p>
            </div>
          </div>
        </div>

        <div style={styles.exampleGame}>
          <h3 style={styles.objectiveTitle}>Example: How Winning Works</h3>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: theme.spacing[3],
            marginBottom: theme.spacing[4]
          }}>
            <div style={{textAlign: 'center'}}>
              <strong>Player A</strong><br/>
              <div style={{color: theme.colors.success}}>Score: 4</div>
              <div>Role: Wolf</div>
            </div>
            <div style={{textAlign: 'center'}}>
              <strong>Player B</strong><br/>
              <div>Score: 5</div>
              <div>Role: Goat</div>
            </div>
            <div style={{textAlign: 'center'}}>
              <strong>Player C</strong><br/>
              <div>Score: 6</div>
              <div>Role: Goat</div>
            </div>
            <div style={{textAlign: 'center'}}>
              <strong>Player D</strong><br/>
              <div>Score: 7</div>
              <div>Role: Pig</div>
            </div>
          </div>
          
          <div style={{
            padding: theme.spacing[3],
            backgroundColor: theme.colors.gray50,
            borderRadius: theme.borderRadius.base,
            fontFamily: theme.typography.fontMono,
            fontSize: theme.typography.sm
          }}>
            <strong>Hole Result:</strong><br/>
            • Player A (Wolf) had the best score (4)<br/>
            • As the Wolf, Player A beats all three other players<br/>
            • Player A wins 3x the bet amount<br/>
            • Players B, C, D each lose 1x the bet amount<br/>
            <br/>
            <strong>Lesson:</strong> Player A won money despite everyone playing reasonably well, 
            because they made a strategic Wolf decision and executed with good play.
          </div>
        </div>

        <div style={{marginTop: theme.spacing[6]}}>
          <TutorialQuiz
            questionId="objectives-basic"
            question="What is the primary objective in Wolf Goat Pig?"
            options={[
              "Shoot the lowest golf score",
              "Make the most birdies",
              "Win the most money",
              "Play the most consistent round"
            ]}
            correctAnswer={2}
            explanation="While good golf scores help, the primary objective is to win money through strategic partnerships and betting decisions."
          />
        </div>
      </div>
    );
  };

  const RoleExplanationStep = () => {
    const [selectedRole, setSelectedRole] = useState('wolf');
    
    const roles = {
      wolf: {
        icon: '🐺',
        title: 'The Wolf',
        description: 'Goes alone against the other three players',
        risk: 'High Risk, High Reward',
        strategy: 'Choose when you feel confident about your shot',
        payout: 'Win 3x bet, lose 3x bet',
        color: theme.colors.error
      },
      goat: {
        icon: '🐐',
        title: 'The Goat',
        description: 'Teams up with another player to compete as partners',
        risk: 'Medium Risk, Medium Reward',
        strategy: 'Strategic partnership selection is key',
        payout: 'Win 2x bet, lose 1x bet (split with partner)',
        color: theme.colors.warning
      },
      pig: {
        icon: '🐷',
        title: 'The Pig',
        description: 'The remaining players who team up together',
        risk: 'Low Risk, Lower Reward',
        strategy: 'Solid, consistent play wins',
        payout: 'Win 1x bet, lose 2x bet (split losses)',
        color: theme.colors.success
      }
    };

    const styles = {
      container: {
        maxWidth: 900,
        margin: '0 auto'
      },
      
      roleSelector: {
        display: 'flex',
        justifyContent: 'center',
        gap: theme.spacing[3],
        marginBottom: theme.spacing[6]
      },
      
      roleTab: {
        padding: `${theme.spacing[3]} ${theme.spacing[5]}`,
        borderRadius: theme.borderRadius.base,
        border: `2px solid ${theme.colors.border}`,
        background: theme.colors.paper,
        cursor: 'pointer',
        transition: tutorial.reducedMotion ? 'none' : 'all 0.2s ease',
        fontSize: theme.typography.base,
        fontWeight: theme.typography.medium
      },
      
      roleTabActive: {
        borderColor: roles[selectedRole].color,
        backgroundColor: roles[selectedRole].color + '20',
        color: roles[selectedRole].color
      },
      
      roleDisplay: {
        ...theme.cardStyle,
        padding: theme.spacing[8],
        textAlign: 'center',
        marginBottom: theme.spacing[6]
      },
      
      roleIcon: {
        fontSize: '4rem',
        marginBottom: theme.spacing[4]
      },
      
      roleTitle: {
        fontSize: theme.typography['2xl'],
        fontWeight: theme.typography.bold,
        color: roles[selectedRole].color,
        marginBottom: theme.spacing[3]
      },
      
      roleDescription: {
        fontSize: theme.typography.lg,
        color: theme.colors.textPrimary,
        marginBottom: theme.spacing[6],
        lineHeight: 1.6
      },
      
      roleDetails: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: theme.spacing[4]
      },
      
      roleDetail: {
        padding: theme.spacing[4],
        borderRadius: theme.borderRadius.base,
        border: `1px solid ${theme.colors.border}`,
        textAlign: 'left'
      },
      
      detailTitle: {
        fontWeight: theme.typography.semibold,
        marginBottom: theme.spacing[2],
        color: roles[selectedRole].color
      },
      
      scenarioCard: {
        ...theme.cardStyle,
        padding: theme.spacing[5]
      }
    };

    return (
      <div style={styles.container}>
        <div style={styles.roleSelector}>
          {Object.entries(roles).map(([key, role]) => (
            <button
              key={key}
              style={{
                ...styles.roleTab,
                ...(selectedRole === key ? styles.roleTabActive : {})
              }}
              onClick={() => setSelectedRole(key)}
            >
              {role.icon} {role.title}
            </button>
          ))}
        </div>

        <div style={styles.roleDisplay}>
          <div style={styles.roleIcon}>{roles[selectedRole].icon}</div>
          <h3 style={styles.roleTitle}>{roles[selectedRole].title}</h3>
          <p style={styles.roleDescription}>{roles[selectedRole].description}</p>
          
          <div style={styles.roleDetails}>
            <div style={styles.roleDetail}>
              <div style={styles.detailTitle}>Risk Level</div>
              <div>{roles[selectedRole].risk}</div>
            </div>
            
            <div style={styles.roleDetail}>
              <div style={styles.detailTitle}>Strategy</div>
              <div>{roles[selectedRole].strategy}</div>
            </div>
            
            <div style={styles.roleDetail}>
              <div style={styles.detailTitle}>Payout</div>
              <div>{roles[selectedRole].payout}</div>
            </div>
          </div>
        </div>

        <div style={styles.scenarioCard}>
          <h3 style={{
            fontSize: theme.typography.xl,
            fontWeight: theme.typography.bold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[4],
            textAlign: 'center'
          }}>
            Role Selection Strategy
          </h3>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: theme.spacing[4]
          }}>
            <div>
              <h4 style={{color: theme.colors.error}}>Choose Wolf When:</h4>
              <ul style={{lineHeight: 1.8}}>
                <li>You're playing your favorite hole</li>
                <li>You're feeling confident</li>
                <li>Others are struggling</li>
                <li>You need to catch up quickly</li>
              </ul>
            </div>
            
            <div>
              <h4 style={{color: theme.colors.warning}}>Choose Goat When:</h4>
              <ul style={{lineHeight: 1.8}}>
                <li>You want a strategic partnership</li>
                <li>The hole suits your playing style</li>
                <li>You want moderate risk</li>
                <li>Someone strong is available to partner with</li>
              </ul>
            </div>
            
            <div>
              <h4 style={{color: theme.colors.success}}>Be Pig When:</h4>
              <ul style={{lineHeight: 1.8}}>
                <li>You're having an off day</li>
                <li>The hole is very difficult</li>
                <li>You want to minimize losses</li>
                <li>Others are taking big risks</li>
              </ul>
            </div>
          </div>
        </div>

        <div style={{marginTop: theme.spacing[6]}}>
          <TutorialQuiz
            questionId="roles-understanding"
            question="If you're feeling very confident about a difficult par-4 hole, which role should you consider?"
            options={[
              "Wolf - go alone for maximum reward",
              "Goat - find a strong partner",
              "Pig - play it safe",
              "It doesn't matter which role you choose"
            ]}
            correctAnswer={0}
            explanation="When you're confident and on a difficult hole, going Wolf maximizes your potential reward since others are likely to struggle."
          />
        </div>
      </div>
    );
  };

  const GameFlowStep = () => {
    const styles = {
      container: {
        maxWidth: 1000,
        margin: '0 auto'
      },
      
      flowDiagram: {
        ...theme.cardStyle,
        padding: theme.spacing[6],
        marginBottom: theme.spacing[6]
      },
      
      flowTitle: {
        fontSize: theme.typography.xl,
        fontWeight: theme.typography.bold,
        color: theme.colors.primary,
        marginBottom: theme.spacing[6],
        textAlign: 'center'
      },
      
      flowSteps: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: theme.spacing[4],
        marginBottom: theme.spacing[6]
      },
      
      flowStep: {
        padding: theme.spacing[4],
        borderRadius: theme.borderRadius.base,
        border: `2px solid ${theme.colors.border}`,
        textAlign: 'center',
        position: 'relative'
      },
      
      stepNumber: {
        position: 'absolute',
        top: -10,
        left: '50%',
        transform: 'translateX(-50%)',
        width: 24,
        height: 24,
        borderRadius: '50%',
        backgroundColor: theme.colors.primary,
        color: '#ffffff',
        fontSize: theme.typography.sm,
        fontWeight: theme.typography.bold,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      },
      
      stepTitle: {
        fontSize: theme.typography.base,
        fontWeight: theme.typography.semibold,
        marginTop: theme.spacing[3],
        marginBottom: theme.spacing[2]
      },
      
      exampleRound: {
        ...theme.cardStyle,
        padding: theme.spacing[5]
      },
      
      holeExample: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: theme.spacing[3],
        padding: theme.spacing[4],
        backgroundColor: theme.colors.gray50,
        borderRadius: theme.borderRadius.base,
        marginBottom: theme.spacing[4]
      }
    };

    return (
      <div style={styles.container}>
        <div style={styles.flowDiagram}>
          <h3 style={styles.flowTitle}>How Each Hole Plays Out</h3>
          
          <div style={styles.flowSteps}>
            <div style={styles.flowStep}>
              <div style={styles.stepNumber}>1</div>
              <div style={styles.stepTitle}>Tee Selection</div>
              <p>Players rotate who gets to choose their role first (Wolf, Goat, or Pig)</p>
            </div>
            
            <div style={styles.flowStep}>
              <div style={styles.stepNumber}>2</div>
              <div style={styles.stepTitle}>Team Formation</div>
              <p>Based on role choices, partnerships are formed for the hole</p>
            </div>
            
            <div style={styles.flowStep}>
              <div style={styles.stepNumber}>3</div>
              <div style={styles.stepTitle}>Play the Hole</div>
              <p>All players complete the hole, tracking scores</p>
            </div>
            
            <div style={styles.flowStep}>
              <div style={styles.stepNumber}>4</div>
              <div style={styles.stepTitle}>Determine Winner</div>
              <p>Compare team scores to determine hole winners</p>
            </div>
            
            <div style={styles.flowStep}>
              <div style={styles.stepNumber}>5</div>
              <div style={styles.stepTitle}>Money Exchange</div>
              <p>Winners collect money from losers based on bet amounts</p>
            </div>
            
            <div style={styles.flowStep}>
              <div style={styles.stepNumber}>6</div>
              <div style={styles.stepTitle}>Next Hole</div>
              <p>Rotate and repeat for all 18 holes</p>
            </div>
          </div>
        </div>

        <div style={styles.exampleRound}>
          <h3 style={{
            fontSize: theme.typography.lg,
            fontWeight: theme.typography.semibold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[4],
            textAlign: 'center'
          }}>
            Example: Hole #7 Walkthrough
          </h3>
          
          <div style={{marginBottom: theme.spacing[4]}}>
            <strong>Setup:</strong> Par 4, 380 yards. Sarah has first choice this hole.
          </div>
          
          <div style={styles.holeExample}>
            <div><strong>Sarah</strong><br/>Chooses: Wolf<br/>Score: 4 (par)</div>
            <div><strong>Mike</strong><br/>Chooses: Goat<br/>Score: 5 (bogey)</div>
            <div><strong>Lisa</strong><br/>Chooses: Goat<br/>Score: 4 (par)</div>
            <div><strong>Tom</strong><br/>Becomes: Pig<br/>Score: 6 (double bogey)</div>
          </div>
          
          <div style={{marginBottom: theme.spacing[4]}}>
            <strong>Teams:</strong> Sarah (Wolf) vs Mike & Lisa (Goat partnership) vs Tom (Pig)
          </div>
          
          <div style={{marginBottom: theme.spacing[4]}}>
            <strong>Team Scores:</strong>
            <ul style={{marginTop: theme.spacing[2]}}>
              <li>Sarah (Wolf): 4</li>
              <li>Mike & Lisa (Goat partners): Best ball = 4</li>
              <li>Tom (Pig): 6</li>
            </ul>
          </div>
          
          <div style={{
            padding: theme.spacing[3],
            backgroundColor: theme.colors.successLight + '20',
            borderRadius: theme.borderRadius.base,
            borderLeft: `4px solid ${theme.colors.success}`
          }}>
            <strong>Result:</strong> Sarah and the Goat team tie with score of 4. Tom loses as Pig.<br/>
            <strong>Money:</strong> Tom pays out, Sarah and Mike & Lisa split the winnings.
          </div>
        </div>

        <div style={{marginTop: theme.spacing[6]}}>
          <TutorialQuiz
            questionId="game-flow"
            question="In the example above, what happens when the Wolf and Goat team tie?"
            options={[
              "The Wolf always wins ties",
              "They split the winnings from the Pig",
              "The hole is replayed",
              "Nobody wins money on that hole"
            ]}
            correctAnswer={1}
            explanation="When teams tie, they split the winnings from the losing team(s). This encourages both solid play and strategic thinking."
          />
        </div>
      </div>
    );
  };

  const StrategySimulationStep = () => {
    const [currentScenario, setCurrentScenario] = useState(0);
    
    const scenarios = [
      {
        title: "Scenario 1: Easy Par 3",
        scenario: "You're on a short par 3 (140 yards) with a large green. Everyone typically makes par or better on this hole. You're currently down $20 for the round. What's your strategy?",
        options: [
          {
            title: "Choose Wolf",
            description: "Go alone for a chance to win big and catch up quickly"
          },
          {
            title: "Choose Goat",
            description: "Partner up for a safer, moderate gain opportunity"
          },
          {
            title: "Accept Pig role",
            description: "Play it safe and avoid falling further behind"
          }
        ],
        feedback: {
          0: "Risky choice! On an easy hole where everyone plays well, going Wolf is dangerous.",
          1: "Good strategic thinking! Partnering gives you a solid chance without huge risk.",
          2: "Very safe, but you might miss an opportunity to catch up."
        }
      },
      {
        title: "Scenario 2: Difficult Par 5",
        scenario: "You're on a long, difficult par 5 with water hazards. Wind is strong today and several players have already made double bogey or worse. You're feeling confident about your driving today.",
        options: [
          {
            title: "Choose Wolf",
            description: "Take advantage of difficult conditions and others' struggles"
          },
          {
            title: "Choose Goat",
            description: "Find a reliable partner to split the risk"
          },
          {
            title: "Accept Pig role",
            description: "Let others take the big risks on this tough hole"
          }
        ],
        feedback: {
          0: "Excellent choice! Difficult holes where others struggle are perfect Wolf opportunities.",
          1: "Reasonable, but you might be missing a golden Wolf opportunity.",
          2: "Too conservative given the conditions favor you over other players."
        }
      }
    ];

    return (
      <div style={{maxWidth: 800, margin: '0 auto'}}>
        <div style={{
          ...theme.cardStyle,
          padding: theme.spacing[5],
          marginBottom: theme.spacing[6],
          textAlign: 'center'
        }}>
          <h3 style={{
            fontSize: theme.typography.xl,
            fontWeight: theme.typography.bold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[3]
          }}>
            Strategic Decision Making
          </h3>
          <p style={{fontSize: theme.typography.base, lineHeight: 1.6}}>
            Practice making strategic decisions in different game situations. 
            Good decision-making often matters more than perfect golf shots.
          </p>
        </div>

        <TutorialSimulation
          title={scenarios[currentScenario].title}
          scenario={scenarios[currentScenario].scenario}
          options={scenarios[currentScenario].options}
          onDecision={(option, history) => {
            const optionIndex = scenarios[currentScenario].options.indexOf(option);
            const feedback = scenarios[currentScenario].feedback[optionIndex];
            tutorial.addFeedback(feedback);
            
            // Move to next scenario after a delay
            if (currentScenario < scenarios.length - 1) {
              setTimeout(() => setCurrentScenario(currentScenario + 1), 3000);
            }
          }}
        />

        <div style={{
          ...theme.cardStyle,
          padding: theme.spacing[4],
          marginTop: theme.spacing[6],
          backgroundColor: theme.colors.primaryLight + '20'
        }}>
          <h4 style={{marginBottom: theme.spacing[3]}}>Key Strategic Principles:</h4>
          <ul style={{lineHeight: 1.8}}>
            <li><strong>Easy holes:</strong> Be cautious about going Wolf - everyone plays well</li>
            <li><strong>Difficult holes:</strong> Consider Wolf if you're confident - others likely to struggle</li>
            <li><strong>Behind in money:</strong> Take calculated risks to catch up</li>
            <li><strong>Ahead in money:</strong> Play more conservatively to protect your lead</li>
            <li><strong>Know your strengths:</strong> Go Wolf on holes that suit your game</li>
          </ul>
        </div>
      </div>
    );
  };

  return (
    <TutorialModule {...moduleProps}>
      {renderStepContent()}
    </TutorialModule>
  );
};

export default GameOverviewModule;