import React, { useState } from 'react';
import { useTutorial } from '../../../context/TutorialContext';
import { useTheme } from '../../../theme/Provider';
import TutorialModule from '../TutorialModule';
import { TutorialQuiz, TutorialSimulation } from '../InteractiveElement';

const BettingSystemModule = ({ onStepComplete, onModuleComplete, currentStep, goToStep }) => {
  const tutorial = useTutorial();
  const theme = useTheme();

  const steps = [
    {
      id: 'betting-basics',
      title: 'Basic Betting Mechanics',
      hints: 'Understanding the money flow is crucial to strategic success.',
      content: 'betting-basics'
    },
    {
      id: 'odds-calculation',
      title: 'Odds Calculation & Payouts',
      hints: 'Learn to calculate expected value and make smart betting decisions.',
      content: 'odds-calculation'
    },
    {
      id: 'wager-types',
      title: 'Different Wager Types',
      hints: 'Various betting options add complexity and opportunity.',
      content: 'wager-types'
    },
    {
      id: 'risk-management',
      title: 'Risk Management Strategies',
      hints: 'Smart bankroll management separates winners from losers.',
      content: 'risk-management'
    },
    {
      id: 'betting-simulation',
      title: 'Interactive Betting Scenarios',
      hints: 'Practice making betting decisions in realistic game situations.',
      content: 'betting-simulation'
    }
  ];

  const moduleProps = {
    moduleId: 'betting-system',
    title: 'Betting System & Wager Types',
    description: 'Master the financial mechanics of Wolf Goat Pig, from basic betting to advanced wagering strategies and risk management.',
    estimatedTime: 20,
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
      case 'betting-basics':
        return <BettingBasicsStep />;
      case 'odds-calculation':
        return <OddsCalculationStep />;
      case 'wager-types':
        return <WagerTypesStep />;
      case 'risk-management':
        return <RiskManagementStep />;
      case 'betting-simulation':
        return <BettingSimulationStep />;
      default:
        return <div>Step content not found</div>;
    }
  };

  const BettingBasicsStep = () => {
    const [selectedBet, setSelectedBet] = useState(5);
    
    const calculatePayouts = (betAmount) => {
      return {
        wolfWins: betAmount * 3,
        wolfLoses: -betAmount * 3,
        goatWins: betAmount * 2,
        goatLoses: -betAmount,
        pigWins: betAmount,
        pigLoses: -betAmount * 2
      };
    };

    const payouts = calculatePayouts(selectedBet);

    const styles = {
      container: {
        maxWidth: 900,
        margin: '0 auto'
      },
      
      basicCard: {
        ...theme.cardStyle,
        padding: theme.spacing[5],
        marginBottom: theme.spacing[4]
      },
      
      calculator: {
        ...theme.cardStyle,
        padding: theme.spacing[5],
        marginBottom: theme.spacing[4],
        backgroundColor: theme.colors.gray50
      },
      
      betSlider: {
        width: '100%',
        marginBottom: theme.spacing[4]
      },
      
      payoutGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: theme.spacing[4],
        marginTop: theme.spacing[4]
      },
      
      payoutCard: {
        padding: theme.spacing[4],
        borderRadius: theme.borderRadius.base,
        textAlign: 'center'
      },
      
      wolfPayout: {
        backgroundColor: theme.colors.errorLight + '20',
        border: `2px solid ${theme.colors.error}`
      },
      
      goatPayout: {
        backgroundColor: theme.colors.warningLight + '20',
        border: `2px solid ${theme.colors.warning}`
      },
      
      pigPayout: {
        backgroundColor: theme.colors.successLight + '20',
        border: `2px solid ${theme.colors.success}`
      },
      
      exampleGame: {
        ...theme.cardStyle,
        padding: theme.spacing[5],
        marginTop: theme.spacing[6]
      }
    };

    return (
      <div style={styles.container} className="betting-calculator">
        <div style={styles.basicCard}>
          <h3 style={{
            fontSize: theme.typography.lg,
            fontWeight: theme.typography.semibold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[3]
          }}>
            How Wolf Goat Pig Betting Works
          </h3>
          
          <p style={{fontSize: theme.typography.base, lineHeight: 1.6, marginBottom: theme.spacing[4]}}>
            Wolf Goat Pig uses a simple but strategic betting system where your potential winnings 
            and losses depend on the role you choose and how well you perform.
          </p>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: theme.spacing[4]
          }}>
            <div>
              <h4 style={{color: theme.colors.error, marginBottom: theme.spacing[2]}}>🐺 Wolf</h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Goes alone against 3 players</li>
                <li><strong>Win:</strong> Collects from all 3 opponents</li>
                <li><strong>Lose:</strong> Pays all 3 opponents</li>
                <li>Highest risk, highest reward</li>
              </ul>
            </div>
            
            <div>
              <h4 style={{color: theme.colors.warning, marginBottom: theme.spacing[2]}}>🐐 Goat</h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Partners with another Goat</li>
                <li><strong>Win:</strong> Collect from losing teams</li>
                <li><strong>Lose:</strong> Pay winning teams</li>
                <li>Moderate risk, shared rewards</li>
              </ul>
            </div>
            
            <div>
              <h4 style={{color: theme.colors.success, marginBottom: theme.spacing[2]}}>🐷 Pig</h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Individual or paired with other Pigs</li>
                <li><strong>Win:</strong> Collect from losing players</li>
                <li><strong>Lose:</strong> Pay winning players</li>
                <li>Lower risk, lower rewards</li>
              </ul>
            </div>
          </div>
        </div>

        <div style={styles.calculator}>
          <h3 style={{
            fontSize: theme.typography.lg,
            fontWeight: theme.typography.semibold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[4],
            textAlign: 'center'
          }}>
            Interactive Betting Calculator
          </h3>
          
          <div style={{textAlign: 'center', marginBottom: theme.spacing[4]}}>
            <label style={{fontSize: theme.typography.base, fontWeight: theme.typography.medium}}>
              Bet Amount: ${selectedBet}
            </label>
            <input
              type="range"
              min="1"
              max="20"
              value={selectedBet}
              onChange={(e) => setSelectedBet(parseInt(e.target.value))}
              style={styles.betSlider}
            />
          </div>
          
          <div style={styles.payoutGrid}>
            <div style={{...styles.payoutCard, ...styles.wolfPayout}}>
              <div style={{fontSize: '2rem', marginBottom: theme.spacing[2]}}>🐺</div>
              <h4>Wolf</h4>
              <div style={{color: theme.colors.success, fontWeight: theme.typography.bold}}>
                Win: +${payouts.wolfWins}
              </div>
              <div style={{color: theme.colors.error, fontWeight: theme.typography.bold}}>
                Lose: ${payouts.wolfLoses}
              </div>
            </div>
            
            <div style={{...styles.payoutCard, ...styles.goatPayout}}>
              <div style={{fontSize: '2rem', marginBottom: theme.spacing[2]}}>🐐</div>
              <h4>Goat Partner</h4>
              <div style={{color: theme.colors.success, fontWeight: theme.typography.bold}}>
                Win: +${payouts.goatWins}
              </div>
              <div style={{color: theme.colors.error, fontWeight: theme.typography.bold}}>
                Lose: ${payouts.goatLoses}
              </div>
            </div>
            
            <div style={{...styles.payoutCard, ...styles.pigPayout}}>
              <div style={{fontSize: '2rem', marginBottom: theme.spacing[2]}}>🐷</div>
              <h4>Pig</h4>
              <div style={{color: theme.colors.success, fontWeight: theme.typography.bold}}>
                Win: +${payouts.pigWins}
              </div>
              <div style={{color: theme.colors.error, fontWeight: theme.typography.bold}}>
                Lose: ${payouts.pigLoses}
              </div>
            </div>
          </div>
        </div>

        <div style={styles.exampleGame}>
          <h3 style={{
            fontSize: theme.typography.lg,
            fontWeight: theme.typography.semibold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[4]
          }}>
            Example: $5 Bet, Wolf vs Goat Partners vs Pig
          </h3>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: theme.spacing[3],
            marginBottom: theme.spacing[4]
          }}>
            <div style={{textAlign: 'center'}}>
              <strong>Alice (Wolf)</strong><br/>
              Score: 4
            </div>
            <div style={{textAlign: 'center'}}>
              <strong>Bob (Goat)</strong><br/>
              Score: 5
            </div>
            <div style={{textAlign: 'center'}}>
              <strong>Carol (Goat)</strong><br/>
              Score: 4
            </div>
            <div style={{textAlign: 'center'}}>
              <strong>Dave (Pig)</strong><br/>
              Score: 6
            </div>
          </div>
          
          <div style={{
            padding: theme.spacing[4],
            backgroundColor: theme.colors.primaryLight + '20',
            borderRadius: theme.borderRadius.base,
            borderLeft: `4px solid ${theme.colors.primary}`,
            fontSize: theme.typography.sm
          }}>
            <strong>Results:</strong><br/>
            • Alice (Wolf): 4<br/>
            • Bob & Carol (Goat team): Best ball = 4<br/>
            • Dave (Pig): 6<br/>
            <br/>
            <strong>Outcome:</strong> Alice and Goat team tie with 4, Dave loses with 6<br/>
            <strong>Money Flow:</strong><br/>
            • Dave pays $10 ($5 to Alice, $5 split between Bob & Carol)<br/>
            • Alice wins $5<br/>
            • Bob & Carol each win $2.50
          </div>
        </div>

        <div style={{marginTop: theme.spacing[6]}}>
          <TutorialQuiz
            questionId="betting-basic"
            question="In a $10 bet, if you choose Wolf and lose, how much do you pay out?"
            options={[
              "$10",
              "$20", 
              "$30",
              "$40"
            ]}
            correctAnswer={2}
            explanation="As Wolf, you're playing against 3 other players. If you lose, you pay each of them $10, for a total loss of $30."
          />
        </div>
      </div>
    );
  };

  const OddsCalculationStep = () => {
    const [scenario, setScenario] = useState(0);
    
    const scenarios = [
      {
        title: "Easy Par 3 Hole",
        description: "Short hole, everyone typically makes par or better",
        probabilities: {
          wolf: { win: 25, lose: 75 },
          goat: { win: 45, lose: 55 },
          pig: { win: 30, lose: 70 }
        }
      },
      {
        title: "Difficult Par 5 Hole", 
        description: "Long hole with hazards, scores vary widely",
        probabilities: {
          wolf: { win: 40, lose: 60 },
          goat: { win: 35, lose: 65 },
          pig: { win: 25, lose: 75 }
        }
      }
    ];

    const calculateExpectedValue = (role, betAmount, probs) => {
      const multipliers = {
        wolf: { win: 3, lose: -3 },
        goat: { win: 2, lose: -1 },
        pig: { win: 1, lose: -2 }
      };
      
      const winEV = (probs.win / 100) * betAmount * multipliers[role].win;
      const loseEV = (probs.lose / 100) * betAmount * multipliers[role].lose;
      
      return winEV + loseEV;
    };

    const styles = {
      container: {
        maxWidth: 900,
        margin: '0 auto'
      },
      
      scenarioCard: {
        ...theme.cardStyle,
        padding: theme.spacing[5],
        marginBottom: theme.spacing[4]
      },
      
      scenarioSelector: {
        display: 'flex',
        gap: theme.spacing[3],
        marginBottom: theme.spacing[6],
        justifyContent: 'center'
      },
      
      scenarioButton: {
        padding: `${theme.spacing[3]} ${theme.spacing[5]}`,
        borderRadius: theme.borderRadius.base,
        border: `2px solid ${theme.colors.border}`,
        background: theme.colors.paper,
        cursor: 'pointer',
        fontSize: theme.typography.base
      },
      
      scenarioButtonActive: {
        borderColor: theme.colors.primary,
        backgroundColor: theme.colors.primary,
        color: '#ffffff'
      },
      
      oddsGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: theme.spacing[4],
        marginTop: theme.spacing[4]
      },
      
      oddsCard: {
        padding: theme.spacing[4],
        borderRadius: theme.borderRadius.base,
        border: `2px solid ${theme.colors.border}`,
        textAlign: 'center'
      },
      
      expectedValue: {
        fontSize: theme.typography.lg,
        fontWeight: theme.typography.bold,
        marginTop: theme.spacing[3]
      },
      
      positive: {
        color: theme.colors.success
      },
      
      negative: {
        color: theme.colors.error
      }
    };

    const currentScenario = scenarios[scenario];

    return (
      <div style={styles.container}>
        <div style={styles.scenarioCard}>
          <h3 style={{
            fontSize: theme.typography.lg,
            fontWeight: theme.typography.semibold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[3],
            textAlign: 'center'
          }}>
            Understanding Odds & Expected Value
          </h3>
          
          <p style={{fontSize: theme.typography.base, lineHeight: 1.6, marginBottom: theme.spacing[4]}}>
            Smart betting requires understanding the probability of success for each role 
            and calculating the expected value of your decisions.
          </p>
          
          <div style={styles.scenarioSelector}>
            {scenarios.map((s, index) => (
              <button
                key={index}
                style={{
                  ...styles.scenarioButton,
                  ...(scenario === index ? styles.scenarioButtonActive : {})
                }}
                onClick={() => setScenario(index)}
              >
                {s.title}
              </button>
            ))}
          </div>
          
          <div style={{
            padding: theme.spacing[4],
            backgroundColor: theme.colors.gray50,
            borderRadius: theme.borderRadius.base,
            textAlign: 'center',
            marginBottom: theme.spacing[4]
          }}>
            <h4>{currentScenario.title}</h4>
            <p>{currentScenario.description}</p>
          </div>
        </div>

        <div style={styles.scenarioCard}>
          <h3 style={{
            fontSize: theme.typography.lg,
            fontWeight: theme.typography.semibold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[4],
            textAlign: 'center'
          }}>
            Expected Value Analysis ($10 Bet)
          </h3>
          
          <div style={styles.oddsGrid}>
            {Object.entries(currentScenario.probabilities).map(([role, probs]) => {
              const ev = calculateExpectedValue(role, 10, probs);
              const roleLabels = { wolf: '🐺 Wolf', goat: '🐐 Goat', pig: '🐷 Pig' };
              
              return (
                <div key={role} style={styles.oddsCard}>
                  <h4>{roleLabels[role]}</h4>
                  <div>Win: {probs.win}%</div>
                  <div>Lose: {probs.lose}%</div>
                  <div style={{
                    ...styles.expectedValue,
                    ...(ev >= 0 ? styles.positive : styles.negative)
                  }}>
                    Expected Value: ${ev.toFixed(2)}
                  </div>
                </div>
              );
            })}
          </div>
          
          <div style={{
            padding: theme.spacing[4],
            backgroundColor: theme.colors.primaryLight + '20',
            borderRadius: theme.borderRadius.base,
            borderLeft: `4px solid ${theme.colors.primary}`,
            marginTop: theme.spacing[4]
          }}>
            <strong>Interpretation:</strong>
            <ul style={{marginTop: theme.spacing[2], lineHeight: 1.8}}>
              <li>Positive expected value = profitable over time</li>
              <li>Negative expected value = loses money over time</li>
              <li>Higher expected value = better choice mathematically</li>
              <li>Consider your actual skill vs. assumed probabilities</li>
            </ul>
          </div>
        </div>

        <div style={{marginTop: theme.spacing[6]}}>
          <TutorialQuiz
            questionId="odds-calculation"
            question="Based on the difficult par 5 scenario above, which role has the best expected value?"
            options={[
              "Wolf - highest potential payout",
              "Goat - balanced risk/reward", 
              "Pig - safest option",
              "They're all roughly equal"
            ]}
            correctAnswer={0}
            explanation="On difficult holes where the Wolf has a better chance of winning (40% vs others struggling), the Wolf role has the highest expected value despite the higher risk."
          />
        </div>
      </div>
    );
  };

  const WagerTypesStep = () => {
    const styles = {
      container: {
        maxWidth: 900,
        margin: '0 auto'
      },
      
      wagerCard: {
        ...theme.cardStyle,
        padding: theme.spacing[5],
        marginBottom: theme.spacing[4]
      },
      
      wagerGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: theme.spacing[4]
      },
      
      wagerType: {
        padding: theme.spacing[4],
        borderRadius: theme.borderRadius.base,
        border: `2px solid ${theme.colors.border}`
      }
    };

    return (
      <div style={styles.container}>
        <div style={styles.wagerCard}>
          <h3 style={{
            fontSize: theme.typography.lg,
            fontWeight: theme.typography.semibold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[3],
            textAlign: 'center'
          }}>
            Advanced Wager Types
          </h3>
          
          <p style={{fontSize: theme.typography.base, lineHeight: 1.6, marginBottom: theme.spacing[6], textAlign: 'center'}}>
            Beyond basic role betting, Wolf Goat Pig offers various specialized wagers that add 
            excitement and strategic depth to each hole.
          </p>
          
          <div style={styles.wagerGrid}>
            <div style={styles.wagerType}>
              <h4 style={{color: theme.colors.primary, marginBottom: theme.spacing[3]}}>
                💰 Progressive Betting
              </h4>
              <p style={{fontSize: theme.typography.sm, marginBottom: theme.spacing[3]}}>
                Bet amounts increase throughout the round, creating higher stakes on later holes.
              </p>
              <ul style={{fontSize: theme.typography.xs, lineHeight: 1.6}}>
                <li>Holes 1-6: $5 base bet</li>
                <li>Holes 7-12: $10 base bet</li>
                <li>Holes 13-18: $15 base bet</li>
                <li>Creates dramatic late-round excitement</li>
              </ul>
            </div>
            
            <div style={styles.wagerType}>
              <h4 style={{color: theme.colors.success, marginBottom: theme.spacing[3]}}>
                🎯 Performance Bonuses
              </h4>
              <p style={{fontSize: theme.typography.sm, marginBottom: theme.spacing[3]}}>
                Extra payouts for exceptional play, regardless of hole winner.
              </p>
              <ul style={{fontSize: theme.typography.xs, lineHeight: 1.6}}>
                <li>Eagle: +$10 bonus</li>
                <li>Hole-in-one: +$50 bonus</li>
                <li>Birdie from wolf: +$5 bonus</li>
                <li>Paid by all other players</li>
              </ul>
            </div>
            
            <div style={styles.wagerType}>
              <h4 style={{color: theme.colors.warning, marginBottom: theme.spacing[3]}}>
                🔥 Side Bets
              </h4>
              <p style={{fontSize: theme.typography.sm, marginBottom: theme.spacing[3]}}>
                Additional wagers between specific players on hole outcomes.
              </p>
              <ul style={{fontSize: theme.typography.xs, lineHeight: 1.6}}>
                <li>Closest to pin contests</li>
                <li>Longest drive competitions</li>
                <li>Head-to-head score bets</li>
                <li>Negotiated between players</li>
              </ul>
            </div>
            
            <div style={styles.wagerType}>
              <h4 style={{color: theme.colors.error, marginBottom: theme.spacing[3]}}>
                ⚡ Press Bets
              </h4>
              <p style={{fontSize: theme.typography.sm, marginBottom: theme.spacing[3]}}>
                Double down on current hole bet when trailing or confident.
              </p>
              <ul style={{fontSize: theme.typography.xs, lineHeight: 1.6}}>
                <li>Automatic press when down 2+ holes</li>
                <li>Voluntary press anytime</li>
                <li>Creates catch-up opportunities</li>
                <li>Can lead to big swings</li>
              </ul>
            </div>
            
            <div style={styles.wagerType}>
              <h4 style={{color: theme.colors.accent, marginBottom: theme.spacing[3]}}>
                🎲 Carnies
              </h4>
              <p style={{fontSize: theme.typography.sm, marginBottom: theme.spacing[3]}}>
                Fun novelty bets that add variety to the round.
              </p>
              <ul style={{fontSize: theme.typography.xs, lineHeight: 1.6}}>
                <li>Sand saves: $2 bonus</li>
                <li>Up and downs: $3 bonus</li>
                <li>Disaster avoidance: $5 bonus</li>
                <li>Keeps non-competitive players engaged</li>
              </ul>
            </div>
            
            <div style={styles.wagerType}>
              <h4 style={{color: theme.colors.purple, marginBottom: theme.spacing[3]}}>
                🏆 Overall Game Bets
              </h4>
              <p style={{fontSize: theme.typography.sm, marginBottom: theme.spacing[3]}}>
                Wagers on overall round performance and final standings.
              </p>
              <ul style={{fontSize: theme.typography.xs, lineHeight: 1.6}}>
                <li>Low round winner: $20</li>
                <li>Most birdies: $10</li>
                <li>Fewest penalty strokes: $5</li>
                <li>Settled at round completion</li>
              </ul>
            </div>
          </div>
        </div>

        <div style={styles.wagerCard}>
          <h3 style={{
            fontSize: theme.typography.lg,
            fontWeight: theme.typography.semibold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[4]
          }}>
            Wager Selection Strategy
          </h3>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: theme.spacing[6]
          }}>
            <div>
              <h4 style={{color: theme.colors.success, marginBottom: theme.spacing[3]}}>
                When You're Playing Well
              </h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Add performance bonuses</li>
                <li>Increase base bet amounts</li>
                <li>Take press bets when offered</li>
                <li>Be confident with side bets</li>
              </ul>
            </div>
            
            <div>
              <h4 style={{color: theme.colors.warning, marginBottom: theme.spacing[3]}}>
                When You're Struggling
              </h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Focus on basic hole bets</li>
                <li>Avoid performance bonuses</li>
                <li>Consider defensive carnies</li>
                <li>Press only when desperate</li>
              </ul>
            </div>
          </div>
        </div>

        <div style={{marginTop: theme.spacing[6]}}>
          <TutorialQuiz
            questionId="wager-types"
            question="You're playing well and confident. The group offers to add eagle bonuses (+$10 each). What should you consider?"
            options={[
              "Accept immediately - easy money",
              "Decline - too risky",
              "Consider your eagle frequency and others' likely performance",
              "Only accept if you're already winning"
            ]}
            correctAnswer={2}
            explanation="Smart betting requires evaluating your actual eagle frequency vs. the group's. If you make more eagles than average, it's profitable. If not, you're essentially paying others' bonuses."
          />
        </div>
      </div>
    );
  };

  const RiskManagementStep = () => {
    const styles = {
      container: {
        maxWidth: 900,
        margin: '0 auto'
      },
      
      riskCard: {
        ...theme.cardStyle,
        padding: theme.spacing[5],
        marginBottom: theme.spacing[4]
      },
      
      principleGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minMax(250px, 1fr))',
        gap: theme.spacing[4]
      },
      
      principle: {
        padding: theme.spacing[4],
        borderRadius: theme.borderRadius.base,
        border: `2px solid ${theme.colors.border}`
      }
    };

    return (
      <div style={styles.container} className="risk-management">
        <div style={styles.riskCard}>
          <h3 style={{
            fontSize: theme.typography.lg,
            fontWeight: theme.typography.semibold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[3],
            textAlign: 'center'
          }}>
            Smart Bankroll Management
          </h3>
          
          <p style={{fontSize: theme.typography.base, lineHeight: 1.6, marginBottom: theme.spacing[6], textAlign: 'center'}}>
            The difference between winning and losing players often comes down to smart money management 
            and understanding when to take risks vs. when to play it safe.
          </p>
          
          <div style={styles.principleGrid}>
            <div style={styles.principle}>
              <h4 style={{color: theme.colors.primary, marginBottom: theme.spacing[3]}}>
                💰 Set Loss Limits
              </h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Decide maximum loss before playing</li>
                <li>Stop playing when limit is reached</li>
                <li>Prevents chasing losses</li>
                <li>Protects long-term bankroll</li>
              </ul>
            </div>
            
            <div style={styles.principle}>
              <h4 style={{color: theme.colors.success, marginBottom: theme.spacing[3]}}>
                📊 Track Your Performance
              </h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Record wins/losses by role</li>
                <li>Identify your strengths</li>
                <li>Note hole-specific patterns</li>
                <li>Adjust strategy based on data</li>
              </ul>
            </div>
            
            <div style={styles.principle}>
              <h4 style={{color: theme.colors.warning, marginBottom: theme.spacing[3]}}>
                ⚖️ Risk-Reward Balance
              </h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Higher bets require higher confidence</li>
                <li>Diversify your role selections</li>
                <li>Don't always play the same way</li>
                <li>Adjust to opponents' strategies</li>
              </ul>
            </div>
            
            <div style={styles.principle}>
              <h4 style={{color: theme.colors.error, marginBottom: theme.spacing[3]}}>
                🚨 Tilt Control
              </h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Recognize emotional decision-making</li>
                <li>Take breaks when frustrated</li>
                <li>Don't increase bets when angry</li>
                <li>Stick to your planned strategy</li>
              </ul>
            </div>
          </div>
        </div>

        <div style={styles.riskCard}>
          <h3 style={{
            fontSize: theme.typography.lg,
            fontWeight: theme.typography.semibold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[4]
          }}>
            Situational Risk Management
          </h3>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr 1fr',
            gap: theme.spacing[4]
          }}>
            <div>
              <h4 style={{color: theme.colors.success, marginBottom: theme.spacing[2]}}>
                When Ahead
              </h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Protect your lead</li>
                <li>Take fewer Wolf risks</li>
                <li>Let others make mistakes</li>
                <li>Consider smaller bets</li>
              </ul>
            </div>
            
            <div>
              <h4 style={{color: theme.colors.warning, marginBottom: theme.spacing[2]}}>
                When Behind
              </h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Take calculated risks</li>
                <li>Look for Wolf opportunities</li>
                <li>Consider press bets</li>
                <li>Don't panic - stay strategic</li>
              </ul>
            </div>
            
            <div>
              <h4 style={{color: theme.colors.error, marginBottom: theme.spacing[2]}}>
                When Tilted
              </h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Play more conservatively</li>
                <li>Stick to basic bets</li>
                <li>Focus on your golf game</li>
                <li>Avoid complex strategies</li>
              </ul>
            </div>
          </div>
        </div>

        <div style={{marginTop: theme.spacing[6]}}>
          <TutorialQuiz
            questionId="risk-management"
            question="You've lost $80 in the first 12 holes and are feeling frustrated. What's the best approach for the remaining holes?"
            options={[
              "Increase bets to try to break even",
              "Go Wolf on every hole to catch up quickly", 
              "Stick to your original strategy and betting limits",
              "Quit the round to avoid further losses"
            ]}
            correctAnswer={2}
            explanation="When behind and tilted, the most important thing is to stick to your original plan. Chasing losses with bigger bets or riskier plays usually leads to even bigger losses."
          />
        </div>
      </div>
    );
  };

  const BettingSimulationStep = () => {
    const [currentRound, setCurrentRound] = useState(0);
    const [bankroll, setBankroll] = useState(0);
    
    const scenarios = [
      {
        title: "Early Round Decision",
        setup: "Hole 4, par 3. You're down $15. Easy hole where everyone typically scores well.",
        situation: "You have first choice. Current bankroll: $85 of $100 starting.",
        options: [
          {
            title: "Wolf for $10",
            description: "Go alone, try to catch up quickly with big win"
          },
          {
            title: "Goat for $5", 
            description: "Find a partner, moderate risk approach"
          },
          {
            title: "Accept Pig",
            description: "Play it safe, minimize further losses"
          }
        ]
      },
      {
        title: "Mid-Round Pressure",
        setup: "Hole 12, difficult par 5. You're up $25 but opponents are pressing.",
        situation: "Others want to double the bet to $20. You're playing well today.",
        options: [
          {
            title: "Accept press, go Wolf",
            description: "Take advantage of difficult hole and your good play"
          },
          {
            title: "Accept press, choose Goat",
            description: "Share the risk but still capitalize on press"
          },
          {
            title: "Decline press",
            description: "Protect your lead, avoid high-risk situation"
          }
        ]
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
            Betting Strategy Simulation
          </h3>
          <p style={{fontSize: theme.typography.base, lineHeight: 1.6}}>
            Practice making smart betting decisions under pressure. Your choices affect your bankroll 
            and position in the game.
          </p>
        </div>

        {scenarios.map((scenario, index) => (
          <div key={index} style={{marginBottom: theme.spacing[6]}}>
            <TutorialSimulation
              title={scenario.title}
              scenario={`${scenario.setup}\n\n${scenario.situation}`}
              options={scenario.options}
              onDecision={(option, history) => {
                // Simulate bankroll changes based on decisions
                let change = 0;
                if (option.title.includes('Wolf')) {
                  change = Math.random() > 0.6 ? 30 : -30; // Wolf outcome
                } else if (option.title.includes('Goat')) {
                  change = Math.random() > 0.5 ? 15 : -10; // Goat outcome  
                } else {
                  change = Math.random() > 0.4 ? 5 : -10; // Pig outcome
                }
                
                setBankroll(prev => prev + change);
                
                const feedback = change > 0 
                  ? `Good choice! You won $${Math.abs(change)}.`
                  : `Tough luck. You lost $${Math.abs(change)}.`;
                
                tutorial.addFeedback(feedback);
              }}
            />
          </div>
        ))}

        <div style={{
          ...theme.cardStyle,
          padding: theme.spacing[4],
          marginTop: theme.spacing[6],
          backgroundColor: theme.colors.primaryLight + '20'
        }}>
          <h4 style={{marginBottom: theme.spacing[3]}}>Betting Strategy Recap:</h4>
          <ul style={{lineHeight: 1.8}}>
            <li><strong>Know your odds:</strong> Calculate expected value before big decisions</li>
            <li><strong>Manage your bankroll:</strong> Don't bet more than you can afford to lose</li>
            <li><strong>Play the situation:</strong> Adjust risk based on your position</li>
            <li><strong>Stay disciplined:</strong> Don't chase losses or get over-confident</li>
            <li><strong>Track performance:</strong> Learn from your wins and losses</li>
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

export default BettingSystemModule;