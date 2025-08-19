import React, { useState } from 'react';
import { useTutorial } from '../../../context/TutorialContext';
import { useTheme } from '../../../theme/Provider';
import TutorialModule from '../TutorialModule';
import { TutorialQuiz, TutorialDragDrop, TutorialSimulation } from '../InteractiveElement';

const TeamFormationModule = ({ onStepComplete, onModuleComplete, currentStep, goToStep }) => {
  const tutorial = useTutorial();
  const theme = useTheme();

  const steps = [
    {
      id: 'partnership-basics',
      title: 'Partnership Formation Rules',
      hints: 'Understanding how teams form is crucial for strategic play.',
      content: 'partnership-basics'
    },
    {
      id: 'role-selection-order',
      title: 'Role Selection & Turn Order',
      hints: 'The order of selection creates strategic advantages and disadvantages.',
      content: 'role-selection-order'
    },
    {
      id: 'team-dynamics',
      title: 'Team Dynamics & Communication',
      hints: 'Good partnerships require understanding and sometimes sacrifice.',
      content: 'team-dynamics'
    },
    {
      id: 'formation-simulation',
      title: 'Interactive Formation Practice',
      hints: 'Practice forming teams in different scenarios to understand the dynamics.',
      content: 'formation-simulation'
    },
    {
      id: 'advanced-strategies',
      title: 'Advanced Partnership Strategies',
      hints: 'Learn when to form alliances and when to break them.',
      content: 'advanced-strategies'
    }
  ];

  const moduleProps = {
    moduleId: 'team-formation',
    title: 'Team Formation & Partnership Rules',
    description: 'Master the art of forming strategic partnerships, understanding team dynamics, and making optimal role selection decisions.',
    estimatedTime: 15,
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
      case 'partnership-basics':
        return <PartnershipBasicsStep />;
      case 'role-selection-order':
        return <RoleSelectionOrderStep />;
      case 'team-dynamics':
        return <TeamDynamicsStep />;
      case 'formation-simulation':
        return <FormationSimulationStep />;
      case 'advanced-strategies':
        return <AdvancedStrategiesStep />;
      default:
        return <div>Step content not found</div>;
    }
  };

  const PartnershipBasicsStep = () => {
    const styles = {
      container: {
        maxWidth: 900,
        margin: '0 auto'
      },
      
      ruleCard: {
        ...theme.cardStyle,
        padding: theme.spacing[5],
        marginBottom: theme.spacing[4]
      },
      
      ruleTitle: {
        fontSize: theme.typography.lg,
        fontWeight: theme.typography.semibold,
        color: theme.colors.primary,
        marginBottom: theme.spacing[3]
      },
      
      formationGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: theme.spacing[4],
        marginTop: theme.spacing[4]
      },
      
      formationType: {
        padding: theme.spacing[4],
        borderRadius: theme.borderRadius.base,
        border: `2px solid ${theme.colors.border}`,
        textAlign: 'center'
      },
      
      typeIcon: {
        fontSize: '3rem',
        marginBottom: theme.spacing[3]
      },
      
      exampleFormation: {
        ...theme.cardStyle,
        padding: theme.spacing[5],
        marginTop: theme.spacing[6]
      },
      
      playerGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: theme.spacing[3],
        marginBottom: theme.spacing[4]
      },
      
      player: {
        padding: theme.spacing[3],
        borderRadius: theme.borderRadius.base,
        textAlign: 'center',
        fontSize: theme.typography.sm,
        fontWeight: theme.typography.medium
      },
      
      wolf: {
        backgroundColor: theme.colors.errorLight + '30',
        border: `2px solid ${theme.colors.error}`,
        color: theme.colors.errorDark
      },
      
      goat: {
        backgroundColor: theme.colors.warningLight + '30',
        border: `2px solid ${theme.colors.warning}`,
        color: theme.colors.warningDark
      },
      
      pig: {
        backgroundColor: theme.colors.successLight + '30',
        border: `2px solid ${theme.colors.success}`,
        color: theme.colors.successDark
      }
    };

    return (
      <div style={styles.container} className="team-formation-demo">
        <div style={styles.ruleCard}>
          <h3 style={styles.ruleTitle}>Core Partnership Rules</h3>
          <p style={{fontSize: theme.typography.base, lineHeight: 1.6, marginBottom: theme.spacing[4]}}>
            Wolf Goat Pig uses a dynamic partnership system where teams change every hole based on 
            player choices. Understanding these rules is essential for strategic success.
          </p>
          
          <div style={styles.formationGrid}>
            <div style={styles.formationType}>
              <div style={styles.typeIcon}>🐺</div>
              <h4>Wolf Formation</h4>
              <p>One player goes alone against the other three players</p>
              <ul style={{textAlign: 'left', marginTop: theme.spacing[3]}}>
                <li>Wolf vs. Goat1 + Goat2 + Pig</li>
                <li>Wolf needs best individual score</li>
                <li>High risk, high reward</li>
              </ul>
            </div>
            
            <div style={styles.formationType}>
              <div style={styles.typeIcon}>🤝</div>
              <h4>Partnership Formation</h4>
              <p>Players form two teams of two</p>
              <ul style={{textAlign: 'left', marginTop: theme.spacing[3]}}>
                <li>Goat1 + Goat2 vs. Pig1 + Pig2</li>
                <li>Teams use best-ball scoring</li>
                <li>Balanced risk and reward</li>
              </ul>
            </div>
            
            <div style={styles.formationType}>
              <div style={styles.typeIcon}>🎯</div>
              <h4>Mixed Formation</h4>
              <p>Various combinations possible</p>
              <ul style={{textAlign: 'left', marginTop: theme.spacing[3]}}>
                <li>Wolf + Goat vs. Pig1 + Pig2</li>
                <li>Depends on selection order</li>
                <li>Creates unique dynamics</li>
              </ul>
            </div>
          </div>
        </div>

        <div style={styles.exampleFormation}>
          <h3 style={styles.ruleTitle}>Example: Formation in Action</h3>
          
          <div style={{marginBottom: theme.spacing[4]}}>
            <strong>Hole #3 Setup:</strong> Amy has first choice, followed by Ben, then Carlos, then Diana.
          </div>
          
          <div style={styles.playerGrid}>
            <div style={{...styles.player, ...styles.wolf}}>
              <div>Amy</div>
              <div>🐺 Wolf</div>
            </div>
            <div style={{...styles.player, ...styles.goat}}>
              <div>Ben</div>
              <div>🐐 Goat</div>
            </div>
            <div style={{...styles.player, ...styles.goat}}>
              <div>Carlos</div>
              <div>🐐 Goat</div>
            </div>
            <div style={{...styles.player, ...styles.pig}}>
              <div>Diana</div>
              <div>🐷 Pig</div>
            </div>
          </div>
          
          <div style={{
            padding: theme.spacing[4],
            backgroundColor: theme.colors.gray50,
            borderRadius: theme.borderRadius.base,
            marginBottom: theme.spacing[4]
          }}>
            <strong>Formation Process:</strong>
            <ol style={{marginTop: theme.spacing[2], lineHeight: 1.8}}>
              <li>Amy (1st choice): Selects Wolf - goes alone</li>
              <li>Ben (2nd choice): Selects Goat - will partner with next Goat</li>
              <li>Carlos (3rd choice): Selects Goat - automatically partners with Ben</li>
              <li>Diana (4th choice): Becomes Pig by default</li>
            </ol>
          </div>
          
          <div style={{
            padding: theme.spacing[3],
            backgroundColor: theme.colors.primaryLight + '20',
            borderRadius: theme.borderRadius.base,
            borderLeft: `4px solid ${theme.colors.primary}`
          }}>
            <strong>Final Teams:</strong> Amy (Wolf) vs. Ben & Carlos (Goat Partners) vs. Diana (Pig)<br/>
            <strong>Scoring:</strong> Amy needs best individual score to win. Ben & Carlos use their best ball. Diana plays individually.
          </div>
        </div>

        <div style={{marginTop: theme.spacing[6]}}>
          <TutorialQuiz
            questionId="partnership-basic"
            question="In the example above, what does Ben and Carlos need to do to beat Amy?"
            options={[
              "Both need to beat Amy's individual score",
              "Their best ball score needs to beat Amy's score",
              "They need to beat Amy and Diana individually",
              "They automatically win as partners"
            ]}
            correctAnswer={1}
            explanation="As Goat partners, Ben and Carlos use best-ball scoring - they take the better of their two scores to compare against Amy (Wolf) and Diana (Pig)."
          />
        </div>
      </div>
    );
  };

  const RoleSelectionOrderStep = () => {
    const [currentHole, setCurrentHole] = useState(1);
    
    const selectionOrder = [
      ['Amy', 'Ben', 'Carlos', 'Diana'],    // Hole 1
      ['Ben', 'Carlos', 'Diana', 'Amy'],    // Hole 2  
      ['Carlos', 'Diana', 'Amy', 'Ben'],    // Hole 3
      ['Diana', 'Amy', 'Ben', 'Carlos']     // Hole 4
    ];

    const styles = {
      container: {
        maxWidth: 900,
        margin: '0 auto'
      },
      
      orderCard: {
        ...theme.cardStyle,
        padding: theme.spacing[5],
        marginBottom: theme.spacing[4]
      },
      
      holeSelector: {
        display: 'flex',
        justifyContent: 'center',
        gap: theme.spacing[2],
        marginBottom: theme.spacing[6]
      },
      
      holeButton: {
        padding: `${theme.spacing[2]} ${theme.spacing[4]}`,
        borderRadius: theme.borderRadius.base,
        border: `2px solid ${theme.colors.border}`,
        background: theme.colors.paper,
        cursor: 'pointer',
        fontSize: theme.typography.sm,
        fontWeight: theme.typography.medium
      },
      
      holeButtonActive: {
        borderColor: theme.colors.primary,
        backgroundColor: theme.colors.primary,
        color: '#ffffff'
      },
      
      orderDisplay: {
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: theme.spacing[3],
        marginBottom: theme.spacing[6]
      },
      
      orderPosition: {
        padding: theme.spacing[4],
        borderRadius: theme.borderRadius.base,
        textAlign: 'center',
        border: `2px solid ${theme.colors.border}`
      },
      
      positionNumber: {
        fontSize: theme.typography.lg,
        fontWeight: theme.typography.bold,
        color: theme.colors.primary,
        marginBottom: theme.spacing[2]
      },
      
      playerName: {
        fontSize: theme.typography.base,
        fontWeight: theme.typography.semibold,
        marginBottom: theme.spacing[2]
      },
      
      advantage: {
        fontSize: theme.typography.sm,
        color: theme.colors.textSecondary,
        fontStyle: 'italic'
      },
      
      strategyCard: {
        ...theme.cardStyle,
        padding: theme.spacing[5]
      }
    };

    return (
      <div style={styles.container}>
        <div style={styles.orderCard}>
          <h3 style={{
            fontSize: theme.typography.lg,
            fontWeight: theme.typography.semibold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[3],
            textAlign: 'center'
          }}>
            Selection Order Rotation
          </h3>
          
          <p style={{fontSize: theme.typography.base, lineHeight: 1.6, marginBottom: theme.spacing[4]}}>
            The selection order rotates each hole to ensure fairness. The first player to choose 
            has the most options, while the last player often has their role determined by others' choices.
          </p>
          
          <div style={styles.holeSelector}>
            {[1, 2, 3, 4].map(hole => (
              <button
                key={hole}
                style={{
                  ...styles.holeButton,
                  ...(currentHole === hole ? styles.holeButtonActive : {})
                }}
                onClick={() => setCurrentHole(hole)}
              >
                Hole {hole}
              </button>
            ))}
          </div>
          
          <div style={styles.orderDisplay}>
            {selectionOrder[currentHole - 1].map((player, index) => {
              const advantages = [
                'Most options',
                'Good flexibility',
                'Limited options',
                'Usually determined'
              ];
              
              return (
                <div key={index} style={styles.orderPosition}>
                  <div style={styles.positionNumber}>{index + 1}st Choice</div>
                  <div style={styles.playerName}>{player}</div>
                  <div style={styles.advantage}>{advantages[index]}</div>
                </div>
              );
            })}
          </div>
          
          <div style={{
            padding: theme.spacing[4],
            backgroundColor: theme.colors.gray50,
            borderRadius: theme.borderRadius.base
          }}>
            <strong>Selection Pattern:</strong> Each player gets first choice every 4 holes, 
            ensuring everyone has equal opportunities to drive strategy throughout the round.
          </div>
        </div>

        <div style={styles.strategyCard}>
          <h3 style={{
            fontSize: theme.typography.lg,
            fontWeight: theme.typography.semibold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[4]
          }}>
            Strategic Implications of Selection Order
          </h3>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: theme.spacing[4]
          }}>
            <div>
              <h4 style={{color: theme.colors.success, marginBottom: theme.spacing[2]}}>
                1st Choice Advantages
              </h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Can choose Wolf on favorable holes</li>
                <li>Sets the tone for team formation</li>
                <li>Most strategic flexibility</li>
                <li>Can respond to course conditions</li>
              </ul>
            </div>
            
            <div>
              <h4 style={{color: theme.colors.warning, marginBottom: theme.spacing[2]}}>
                Middle Choice Strategy
              </h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>React to first player's choice</li>
                <li>Can form or break partnerships</li>
                <li>Good for Goat selection</li>
                <li>Balance risk and safety</li>
              </ul>
            </div>
            
            <div>
              <h4 style={{color: theme.colors.error, marginBottom: theme.spacing[2]}}>
                Last Choice Reality
              </h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Role often predetermined</li>
                <li>Must adapt to others' choices</li>
                <li>Can end up as unwilling Pig</li>
                <li>Requires mental flexibility</li>
              </ul>
            </div>
          </div>
        </div>

        <div style={{marginTop: theme.spacing[6]}}>
          <TutorialQuiz
            questionId="selection-order"
            question="If you have first choice on a hole you feel very confident about, what should you strongly consider?"
            options={[
              "Choose Goat to find a good partner",
              "Choose Wolf to maximize your advantage",
              "Wait to see what others choose",
              "Always choose Pig to be safe"
            ]}
            correctAnswer={1}
            explanation="With first choice on a hole you're confident about, choosing Wolf maximizes your opportunity since you set the terms and others must react to your decision."
          />
        </div>
      </div>
    );
  };

  const TeamDynamicsStep = () => {
    const styles = {
      container: {
        maxWidth: 900,
        margin: '0 auto'
      },
      
      dynamicsCard: {
        ...theme.cardStyle,
        padding: theme.spacing[5],
        marginBottom: theme.spacing[4]
      },
      
      dynamicsGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: theme.spacing[4],
        marginTop: theme.spacing[4]
      },
      
      dynamicType: {
        padding: theme.spacing[4],
        borderRadius: theme.borderRadius.base,
        border: `2px solid ${theme.colors.border}`
      },
      
      scenarioCard: {
        ...theme.cardStyle,
        padding: theme.spacing[5],
        marginTop: theme.spacing[6]
      }
    };

    return (
      <div style={styles.container} className="partnership-rules">
        <div style={styles.dynamicsCard}>
          <h3 style={{
            fontSize: theme.typography.lg,
            fontWeight: theme.typography.semibold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[3]
          }}>
            Partnership Communication & Dynamics
          </h3>
          
          <p style={{fontSize: theme.typography.base, lineHeight: 1.6, marginBottom: theme.spacing[4]}}>
            Successful partnerships in Wolf Goat Pig require understanding, communication, and 
            sometimes personal sacrifice for team success. Here's how to be an effective partner.
          </p>
          
          <div style={styles.dynamicsGrid}>
            <div style={styles.dynamicType}>
              <h4 style={{color: theme.colors.primary, marginBottom: theme.spacing[3]}}>
                🗣️ Communication
              </h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Share your confidence level</li>
                <li>Discuss course strategy</li>
                <li>Coordinate shot selection</li>
                <li>Be honest about struggles</li>
              </ul>
            </div>
            
            <div style={styles.dynamicType}>
              <h4 style={{color: theme.colors.success, marginBottom: theme.spacing[3]}}>
                🤝 Cooperation
              </h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Play complementary strategies</li>
                <li>Support partner's decisions</li>
                <li>Share risk appropriately</li>
                <li>Celebrate team success</li>
              </ul>
            </div>
            
            <div style={styles.dynamicType}>
              <h4 style={{color: theme.colors.warning, marginBottom: theme.spacing[3]}}>
                🎯 Strategic Thinking
              </h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>One safe, one aggressive</li>
                <li>Plan for different outcomes</li>
                <li>Consider opponents' strategies</li>
                <li>Adapt during the hole</li>
              </ul>
            </div>
          </div>
        </div>

        <div style={styles.scenarioCard}>
          <h3 style={{
            fontSize: theme.typography.lg,
            fontWeight: theme.typography.semibold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[4]
          }}>
            Partnership Scenario: The Safe/Aggressive Strategy
          </h3>
          
          <div style={{
            padding: theme.spacing[4],
            backgroundColor: theme.colors.gray50,
            borderRadius: theme.borderRadius.base,
            marginBottom: theme.spacing[4]
          }}>
            <strong>Situation:</strong> You and your partner are on a risky par 4 with water near the green. 
            You're playing against a Wolf who's having a great day.
          </div>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: theme.spacing[4],
            marginBottom: theme.spacing[4]
          }}>
            <div style={{
              padding: theme.spacing[4],
              borderRadius: theme.borderRadius.base,
              backgroundColor: theme.colors.successLight + '20',
              border: `2px solid ${theme.colors.success}`
            }}>
              <h4>Partner A: Safe Strategy</h4>
              <p>• Aim for middle of green</p>
              <p>• Accept bogey if necessary</p>
              <p>• Ensure team has a backup score</p>
              <p>• Minimize disaster risk</p>
            </div>
            
            <div style={{
              padding: theme.spacing[4],
              borderRadius: theme.borderRadius.base,
              backgroundColor: theme.colors.warningLight + '20',
              border: `2px solid ${theme.colors.warning}`
            }}>
              <h4>Partner B: Aggressive Strategy</h4>
              <p>• Go for pin position</p>
              <p>• Risk water for birdie chance</p>
              <p>• Try to match Wolf's likely good score</p>
              <p>• Accept higher risk for higher reward</p>
            </div>
          </div>
          
          <div style={{
            padding: theme.spacing[3],
            backgroundColor: theme.colors.primaryLight + '20',
            borderRadius: theme.borderRadius.base,
            borderLeft: `4px solid ${theme.colors.primary}`
          }}>
            <strong>Result:</strong> This strategy gives your team the best of both worlds - 
            a safe backup score and a chance for a great score. If Partner B's aggressive play 
            fails, Partner A's safe play keeps you competitive.
          </div>
        </div>

        <div style={{marginTop: theme.spacing[6]}}>
          <TutorialQuiz
            questionId="team-dynamics"
            question="Your partner just hit into a water hazard and is likely to make double bogey or worse. What should your strategy be?"
            options={[
              "Play aggressively to try to save the team",
              "Play it safe since your partner is already in trouble",
              "Give up on the hole since your partner failed",
              "Copy your partner's aggressive strategy"
            ]}
            correctAnswer={1}
            explanation="When your partner is in trouble, you become the team's safety net. Play conservatively to ensure your team has at least one decent score to work with."
          />
        </div>
      </div>
    );
  };

  const FormationSimulationStep = () => {
    const [selectedFormation, setSelectedFormation] = useState(null);
    
    const dragDropData = {
      items: [
        { id: 'amy', label: 'Amy (Confident)', correctCategory: 'wolf' },
        { id: 'ben', label: 'Ben (Struggling)', correctCategory: 'pig' },
        { id: 'carlos', label: 'Carlos (Steady)', correctCategory: 'goat' },
        { id: 'diana', label: 'Diana (Steady)', correctCategory: 'goat' }
      ],
      categories: [
        { id: 'wolf', name: 'Wolf (Solo)' },
        { id: 'goat', name: 'Goat Partners' },
        { id: 'pig', name: 'Pig (Remaining)' }
      ]
    };

    return (
      <div style={{maxWidth: 900, margin: '0 auto'}}>
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
            Team Formation Practice
          </h3>
          <p style={{fontSize: theme.typography.base, lineHeight: 1.6}}>
            Practice forming optimal teams based on player conditions and hole characteristics.
          </p>
        </div>

        <div style={{
          ...theme.cardStyle,
          padding: theme.spacing[5],
          marginBottom: theme.spacing[4]
        }}>
          <h4 style={{marginBottom: theme.spacing[3]}}>
            Scenario: Difficult Par 5 with Water Hazards
          </h4>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: theme.spacing[3],
            marginBottom: theme.spacing[4]
          }}>
            <div style={{textAlign: 'center'}}>
              <strong>Amy</strong><br/>
              Playing well today<br/>
              Confident on long holes<br/>
              Good driver
            </div>
            <div style={{textAlign: 'center'}}>
              <strong>Ben</strong><br/>
              Struggling with accuracy<br/>
              Made 3 bogeys already<br/>
              Avoiding risks
            </div>
            <div style={{textAlign: 'center'}}>
              <strong>Carlos</strong><br/>
              Steady, consistent player<br/>
              Good course management<br/>
              Reliable partner
            </div>
            <div style={{textAlign: 'center'}}>
              <strong>Diana</strong><br/>
              Solid iron play<br/>
              Conservative strategy<br/>
              Good under pressure
            </div>
          </div>
        </div>

        <TutorialDragDrop
          items={dragDropData.items}
          categories={dragDropData.categories}
          instructions="Based on the player conditions and hole difficulty, drag each player to their optimal role. Consider who should take risks and who should play it safe."
          onComplete={(success) => {
            if (success) {
              tutorial.addFeedback('Excellent! Amy should Wolf given her confidence, Carlos and Diana make a solid Goat partnership, and Ben should avoid risk as Pig.');
            }
          }}
        />

        <div style={{
          ...theme.cardStyle,
          padding: theme.spacing[4],
          marginTop: theme.spacing[6],
          backgroundColor: theme.colors.primaryLight + '20'
        }}>
          <h4 style={{marginBottom: theme.spacing[3]}}>Formation Analysis:</h4>
          <ul style={{lineHeight: 1.8}}>
            <li><strong>Amy as Wolf:</strong> Her confidence and driving skill suit the challenging hole</li>
            <li><strong>Carlos & Diana as Goats:</strong> Two steady players make a reliable partnership</li>
            <li><strong>Ben as Pig:</strong> His struggles suggest avoiding additional pressure</li>
            <li><strong>Strategy:</strong> Amy risks big for big reward, others play steady team golf</li>
          </ul>
        </div>
      </div>
    );
  };

  const AdvancedStrategiesStep = () => {
    const styles = {
      container: {
        maxWidth: 900,
        margin: '0 auto'
      },
      
      strategyCard: {
        ...theme.cardStyle,
        padding: theme.spacing[5],
        marginBottom: theme.spacing[4]
      },
      
      strategyGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: theme.spacing[4]
      },
      
      strategyType: {
        padding: theme.spacing[4],
        borderRadius: theme.borderRadius.base,
        border: `2px solid ${theme.colors.border}`
      }
    };

    return (
      <div style={styles.container}>
        <div style={styles.strategyCard}>
          <h3 style={{
            fontSize: theme.typography.lg,
            fontWeight: theme.typography.semibold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[3],
            textAlign: 'center'
          }}>
            Advanced Partnership Strategies
          </h3>
          
          <p style={{fontSize: theme.typography.base, lineHeight: 1.6, marginBottom: theme.spacing[6], textAlign: 'center'}}>
            Master-level players understand these advanced concepts for team formation and partnership management.
          </p>
          
          <div style={styles.strategyGrid}>
            <div style={styles.strategyType}>
              <h4 style={{color: theme.colors.primary, marginBottom: theme.spacing[3]}}>
                🎭 Strategic Deception
              </h4>
              <p style={{fontSize: theme.typography.sm, marginBottom: theme.spacing[3]}}>
                Influence others' role selection through verbal misdirection or body language.
              </p>
              <ul style={{fontSize: theme.typography.xs, lineHeight: 1.6}}>
                <li>Express fake confidence or doubt</li>
                <li>Influence partnership formation</li>
                <li>Force others into unfavorable roles</li>
              </ul>
            </div>
            
            <div style={styles.strategyType}>
              <h4 style={{color: theme.colors.success, marginBottom: theme.spacing[3]}}>
                🎯 Counter-Strategy
              </h4>
              <p style={{fontSize: theme.typography.sm, marginBottom: theme.spacing[3]}}>
                Adjust your role selection based on others' tendencies and patterns.
              </p>
              <ul style={{fontSize: theme.typography.xs, lineHeight: 1.6}}>
                <li>Counter aggressive players</li>
                <li>Exploit conservative players</li>
                <li>Break up strong partnerships</li>
              </ul>
            </div>
            
            <div style={styles.strategyType}>
              <h4 style={{color: theme.colors.warning, marginBottom: theme.spacing[3]}}>
                📊 Statistical Advantage
              </h4>
              <p style={{fontSize: theme.typography.sm, marginBottom: theme.spacing[3]}}>
                Use knowledge of course history and player statistics to inform decisions.
              </p>
              <ul style={{fontSize: theme.typography.xs, lineHeight: 1.6}}>
                <li>Track hole-specific performance</li>
                <li>Identify player weakness patterns</li>
                <li>Optimize risk/reward ratios</li>
              </ul>
            </div>
            
            <div style={styles.strategyType}>
              <h4 style={{color: theme.colors.error, marginBottom: theme.spacing[3]}}>
                ⚡ Pressure Management
              </h4>
              <p style={{fontSize: theme.typography.sm, marginBottom: theme.spacing[3]}}>
                Create or relieve pressure through strategic role selection and team dynamics.
              </p>
              <ul style={{fontSize: theme.typography.xs, lineHeight: 1.6}}>
                <li>Put pressure on opponents</li>
                <li>Relieve pressure on partners</li>
                <li>Manage late-round dynamics</li>
              </ul>
            </div>
          </div>
        </div>

        <div style={styles.strategyCard}>
          <h3 style={{
            fontSize: theme.typography.lg,
            fontWeight: theme.typography.semibold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[4]
          }}>
            Round Management Strategy
          </h3>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr 1fr',
            gap: theme.spacing[4]
          }}>
            <div>
              <h4 style={{color: theme.colors.success, marginBottom: theme.spacing[2]}}>
                Early Holes (1-6)
              </h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Build momentum</li>
                <li>Establish partnerships</li>
                <li>Test opponents' strategies</li>
                <li>Take calculated risks</li>
              </ul>
            </div>
            
            <div>
              <h4 style={{color: theme.colors.warning, marginBottom: theme.spacing[2]}}>
                Middle Holes (7-12)
              </h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Maintain or change momentum</li>
                <li>Adapt to course conditions</li>
                <li>Exploit opponent weaknesses</li>
                <li>Strategic alliance building</li>
              </ul>
            </div>
            
            <div>
              <h4 style={{color: theme.colors.error, marginBottom: theme.spacing[2]}}>
                Late Holes (13-18)
              </h4>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.8}}>
                <li>Protect leads or catch up</li>
                <li>Manage risk carefully</li>
                <li>Pressure or support as needed</li>
                <li>Execute closing strategy</li>
              </ul>
            </div>
          </div>
        </div>

        <div style={{marginTop: theme.spacing[6]}}>
          <TutorialQuiz
            questionId="advanced-strategy"
            question="You're leading by $50 going into hole 16. Your biggest rival is pushing to catch up and choosing roles aggressively. What's your best strategy?"
            options={[
              "Match their aggression with Wolf choices",
              "Form partnerships to share risk and protect your lead",
              "Always choose Pig to minimize losses",
              "Let them choose first and then counter"
            ]}
            correctAnswer={1}
            explanation="When you have a lead late in the round, sharing risk through partnerships helps protect your advantage while still giving you chances to win holes. Pure defense (always Pig) can backfire if they get hot."
          />
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

export default TeamFormationModule;