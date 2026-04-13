import React from 'react'; // Removed unused useState
import { useTutorial } from '../../../context/TutorialContext';
import { useTheme } from '../../../theme/Provider';
import TutorialModule from '../TutorialModule';
import { TutorialQuiz, TutorialDragDrop } from '../InteractiveElement';

const GolfBasicsModule = ({ onStepComplete, onModuleComplete, currentStep, goToStep }) => {
  const tutorial = useTutorial();
  const theme = useTheme();

  const steps = [
    {
      id: 'scoring-basics',
      title: 'Golf Scoring Fundamentals',
      hints: 'Remember: in golf, lower scores are better! Par is the expected number of strokes.',
      content: 'scoring-basics'
    },
    {
      id: 'handicap-system',
      title: 'Understanding Handicaps',
      hints: 'Handicaps level the playing field between players of different skill levels.',
      content: 'handicap-system'
    },
    {
      id: 'course-knowledge',
      title: 'Course Layout & Holes',
      hints: 'Different hole types (par 3, 4, 5) require different strategies.',
      content: 'course-knowledge'
    },
    {
      id: 'terminology-quiz',
      title: 'Golf Terminology Quiz',
      hints: 'Take your time to understand each term - they\'ll be used throughout the tutorial.',
      content: 'terminology-quiz'
    }
  ];

  const moduleProps = {
    moduleId: 'golf-basics',
    title: 'Basic Golf Concepts & Scoring',
    description: 'Master the fundamental concepts of golf scoring, handicaps, and terminology that form the foundation of Wolf Goat Pig.',
    estimatedTime: 5,
    steps,
    currentStep,
    onStepComplete,
    onModuleComplete,
    allowSkip: tutorial.learningPreferences.skipBasics,
    requiredCompletion: !tutorial.learningPreferences.skipBasics
  };

  const renderStepContent = () => {
    const currentStepData = steps[currentStep];
    if (!currentStepData) return null;

    switch (currentStepData.content) {
      case 'scoring-basics':
        return <ScoringBasicsStep />;
      case 'handicap-system':
        return <HandicapSystemStep />;
      case 'course-knowledge':
        return <CourseKnowledgeStep />;
      case 'terminology-quiz':
        return <TerminologyQuizStep />;
      default:
        return <div>Step content not found</div>;
    }
  };

  const ScoringBasicsStep = () => {
    const styles = {
      container: {
        maxWidth: 800,
        margin: '0 auto'
      },
      
      conceptCard: {
        ...theme.cardStyle,
        marginBottom: theme.spacing[4],
        padding: theme.spacing[5]
      },
      
      conceptTitle: {
        fontSize: theme.typography.lg,
        fontWeight: theme.typography.semibold,
        color: theme.colors.primary,
        marginBottom: theme.spacing[3]
      },
      
      conceptDescription: {
        fontSize: theme.typography.base,
        lineHeight: 1.6,
        marginBottom: theme.spacing[4]
      },
      
      exampleGrid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: theme.spacing[3],
        marginBottom: theme.spacing[4]
      },
      
      example: {
        padding: theme.spacing[3],
        borderRadius: theme.borderRadius.base,
        textAlign: 'center',
        fontSize: theme.typography.sm
      },
      
      birdie: {
        backgroundColor: theme.colors.successLight + '30',
        border: `2px solid ${theme.colors.success}`
      },
      
      par: {
        backgroundColor: theme.colors.gray100,
        border: `2px solid ${theme.colors.gray400}`
      },
      
      bogey: {
        backgroundColor: theme.colors.warningLight + '30',
        border: `2px solid ${theme.colors.warning}`
      },
      
      doubleBogey: {
        backgroundColor: theme.colors.errorLight + '30',
        border: `2px solid ${theme.colors.error}`
      },
      
      practiceSection: {
        marginTop: theme.spacing[6]
      }
    };

    return (
      <div style={styles.container} className="golf-basics-scoring">
        <div style={styles.conceptCard}>
          <h3 style={styles.conceptTitle}>What is Golf Scoring?</h3>
          <p style={styles.conceptDescription}>
            Golf scoring is based on counting the number of strokes (hits) it takes to get the ball 
            into the hole. Unlike many sports, <strong>lower scores are better</strong> in golf.
          </p>
          
          <div style={styles.exampleGrid}>
            <div style={{ ...styles.example, ...styles.birdie }}>
              <div style={{ fontSize: '1.5rem', marginBottom: theme.spacing[2] }}>🐦</div>
              <strong>Birdie</strong>
              <div>1 under par</div>
            </div>
            
            <div style={{ ...styles.example, ...styles.par }}>
              <div style={{ fontSize: '1.5rem', marginBottom: theme.spacing[2] }}>🎯</div>
              <strong>Par</strong>
              <div>Expected score</div>
            </div>
            
            <div style={{ ...styles.example, ...styles.bogey }}>
              <div style={{ fontSize: '1.5rem', marginBottom: theme.spacing[2] }}>⚠️</div>
              <strong>Bogey</strong>
              <div>1 over par</div>
            </div>
            
            <div style={{ ...styles.example, ...styles.doubleBogey }}>
              <div style={{ fontSize: '1.5rem', marginBottom: theme.spacing[2] }}>❌</div>
              <strong>Double Bogey</strong>
              <div>2 over par</div>
            </div>
          </div>
        </div>

        <div style={styles.conceptCard}>
          <h3 style={styles.conceptTitle}>Par Values Explained</h3>
          <p style={styles.conceptDescription}>
            Each hole has a "par" value - the number of strokes an expert golfer is expected to need:
          </p>
          
          <ul style={{ lineHeight: 1.8, marginBottom: theme.spacing[4] }}>
            <li><strong>Par 3:</strong> Short holes, typically 100-250 yards</li>
            <li><strong>Par 4:</strong> Medium holes, typically 250-450 yards</li>
            <li><strong>Par 5:</strong> Long holes, typically 450+ yards</li>
          </ul>
          
          <div style={{
            padding: theme.spacing[4],
            backgroundColor: theme.colors.gray50,
            borderRadius: theme.borderRadius.base,
            borderLeft: `4px solid ${theme.colors.primary}`
          }}>
            <strong>Example:</strong> If you take 4 strokes on a par-3 hole, you scored a "bogey" 
            (1 over par). If you take 4 strokes on a par-5 hole, you scored an "eagle" (2 under par)!
          </div>
        </div>

        <div style={styles.practiceSection}>
          <TutorialQuiz
            questionId="scoring-basic-1"
            question="If a player takes 5 strokes on a par-4 hole, what did they score?"
            options={[
              "Birdie (1 under par)",
              "Par (even)",
              "Bogey (1 over par)",
              "Eagle (2 under par)"
            ]}
            correctAnswer={2}
            explanation="5 strokes on a par-4 hole is 1 stroke over par, which is called a bogey."
          />
        </div>
      </div>
    );
  };

  const HandicapSystemStep = () => {
    const styles = {
      container: {
        maxWidth: 800,
        margin: '0 auto'
      },
      
      conceptCard: {
        ...theme.cardStyle,
        marginBottom: theme.spacing[4],
        padding: theme.spacing[5]
      },
      
      conceptTitle: {
        fontSize: theme.typography.lg,
        fontWeight: theme.typography.semibold,
        color: theme.colors.primary,
        marginBottom: theme.spacing[3]
      },
      
      handicapExample: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: theme.spacing[4],
        marginTop: theme.spacing[4]
      },
      
      playerCard: {
        padding: theme.spacing[4],
        borderRadius: theme.borderRadius.base,
        border: `2px solid ${theme.colors.border}`,
        textAlign: 'center'
      },
      
      calculation: {
        backgroundColor: theme.colors.gray50,
        padding: theme.spacing[4],
        borderRadius: theme.borderRadius.base,
        marginTop: theme.spacing[4],
        fontFamily: theme.typography.fontMono
      }
    };

    return (
      <div style={styles.container} className="golf-basics-handicap">
        <div style={styles.conceptCard}>
          <h3 style={styles.conceptTitle}>What is a Golf Handicap?</h3>
          <p style={{ fontSize: theme.typography.base, lineHeight: 1.6, marginBottom: theme.spacing[4] }}>
            A handicap is a number that represents a player's skill level. It allows players of 
            different abilities to compete fairly against each other by adjusting their scores.
          </p>
          
          <div style={{
            padding: theme.spacing[4],
            backgroundColor: theme.colors.primaryLight + '20',
            borderRadius: theme.borderRadius.base,
            borderLeft: `4px solid ${theme.colors.primary}`,
            marginBottom: theme.spacing[4]
          }}>
            <strong>Key Point:</strong> Lower handicaps indicate better players. A handicap of 0 
            means you play at par level. Negative handicaps (rare) indicate you typically score under par.
          </div>

          <h4 style={{ marginTop: theme.spacing[5], marginBottom: theme.spacing[3] }}>
            How Handicaps Work in Competition
          </h4>
          
          <div style={styles.handicapExample}>
            <div style={styles.playerCard}>
              <h5>Player A</h5>
              <div>Handicap: 5</div>
              <div>Actual Score: 85</div>
              <div style={{ marginTop: theme.spacing[2], fontWeight: theme.typography.semibold, color: theme.colors.primary }}>
                Net Score: 80
              </div>
            </div>
            
            <div style={styles.playerCard}>
              <h5>Player B</h5>
              <div>Handicap: 15</div>
              <div>Actual Score: 95</div>
              <div style={{ marginTop: theme.spacing[2], fontWeight: theme.typography.semibold, color: theme.colors.primary }}>
                Net Score: 80
              </div>
            </div>
          </div>
          
          <div style={styles.calculation}>
            <div>Calculation:</div>
            <div>Net Score = Gross Score - Handicap</div>
            <div style={{ marginTop: theme.spacing[2] }}>
              Player A: 85 - 5 = 80<br/>
              Player B: 95 - 15 = 80
            </div>
            <div style={{ marginTop: theme.spacing[2], fontWeight: theme.typography.semibold }}>
              Result: It's a tie! Both players performed equally well relative to their skill level.
            </div>
          </div>
        </div>

        <div style={styles.conceptCard}>
          <h3 style={styles.conceptTitle}>Handicaps in Wolf Goat Pig</h3>
          <p style={{ fontSize: theme.typography.base, lineHeight: 1.6 }}>
            In Wolf Goat Pig, handicaps can be used to level the playing field when players of 
            different skill levels play together. This ensures that betting and partnerships 
            remain fair and competitive regardless of skill differences.
          </p>
        </div>

        <TutorialQuiz
          questionId="handicap-basic-1"
          question="Player C has a handicap of 8 and shoots an 88. What is their net score?"
          options={["80", "88", "96", "Cannot be determined"]}
          correctAnswer={0}
          explanation="Net score = Gross score - Handicap. So 88 - 8 = 80."
        />
      </div>
    );
  };

  const CourseKnowledgeStep = () => {
    const styles = {
      container: {
        maxWidth: 800,
        margin: '0 auto'
      },
      
      holeTypes: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: theme.spacing[4],
        marginBottom: theme.spacing[6]
      },
      
      holeCard: {
        ...theme.cardStyle,
        padding: theme.spacing[4],
        textAlign: 'center'
      },
      
      holeIcon: {
        fontSize: '3rem',
        marginBottom: theme.spacing[3]
      },
      
      courseLayout: {
        ...theme.cardStyle,
        padding: theme.spacing[5],
        marginBottom: theme.spacing[4]
      },
      
      conceptTitle: {
        fontSize: theme.typography.lg,
        fontWeight: theme.typography.semibold,
        color: theme.colors.primary,
        marginBottom: theme.spacing[3]
      }
    };

    return (
      <div style={styles.container}>
        <div style={styles.courseLayout}>
          <h3 style={styles.conceptTitle}>Golf Course Basics</h3>
          <p style={{ fontSize: theme.typography.base, lineHeight: 1.6, marginBottom: theme.spacing[4] }}>
            A standard golf course has 18 holes, each with its own par value. Understanding hole 
            types helps you strategize your play and make better decisions in Wolf Goat Pig.
          </p>
        </div>

        <div style={styles.holeTypes}>
          <div style={styles.holeCard}>
            <div style={styles.holeIcon}>🏌️‍♂️</div>
            <h4>Par 3 Holes</h4>
            <p><strong>Distance:</strong> 100-250 yards</p>
            <p><strong>Strategy:</strong> Precision over power</p>
            <p><strong>Typical shots:</strong> Tee to green in one shot</p>
          </div>
          
          <div style={styles.holeCard}>
            <div style={styles.holeIcon}>⛳</div>
            <h4>Par 4 Holes</h4>
            <p><strong>Distance:</strong> 250-450 yards</p>
            <p><strong>Strategy:</strong> Position for approach shot</p>
            <p><strong>Typical shots:</strong> Drive, then approach</p>
          </div>
          
          <div style={styles.holeCard}>
            <div style={styles.holeIcon}>🏌️</div>
            <h4>Par 5 Holes</h4>
            <p><strong>Distance:</strong> 450+ yards</p>
            <p><strong>Strategy:</strong> Three good shots to reach</p>
            <p><strong>Typical shots:</strong> Drive, layup, approach</p>
          </div>
        </div>

        <div style={styles.courseLayout}>
          <h3 style={styles.conceptTitle}>Course Features That Matter</h3>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: theme.spacing[4],
            marginTop: theme.spacing[4]
          }}>
            <div>
              <h5>💧 Water Hazards</h5>
              <p style={{ fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
                Penalty strokes if your ball lands in water
              </p>
            </div>
            
            <div>
              <h5>🌳 Trees & Rough</h5>
              <p style={{ fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
                Make shots more difficult but no penalty
              </p>
            </div>
            
            <div>
              <h5>⛳ Green Conditions</h5>
              <p style={{ fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
                Fast/slow greens affect putting strategy
              </p>
            </div>
            
            <div>
              <h5>🏖️ Sand Bunkers</h5>
              <p style={{ fontSize: theme.typography.sm, color: theme.colors.textSecondary }}>
                Require special technique to escape
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const TerminologyQuizStep = () => {
    const dragDropData = {
      items: [
        { id: 'birdie', label: 'Birdie', correctCategory: 'scoring' },
        { id: 'fairway', label: 'Fairway', correctCategory: 'course' },
        { id: 'handicap', label: 'Handicap', correctCategory: 'player' },
        { id: 'par', label: 'Par', correctCategory: 'scoring' },
        { id: 'rough', label: 'Rough', correctCategory: 'course' },
        { id: 'bogey', label: 'Bogey', correctCategory: 'scoring' },
        { id: 'tee', label: 'Tee', correctCategory: 'course' },
        { id: 'stance', label: 'Stance', correctCategory: 'player' }
      ],
      categories: [
        { id: 'scoring', name: 'Scoring Terms' },
        { id: 'course', name: 'Course Features' },
        { id: 'player', name: 'Player Related' }
      ]
    };

    return (
      <div style={{ maxWidth: 800, margin: '0 auto' }}>
        <div style={{
          ...theme.cardStyle,
          padding: theme.spacing[5],
          marginBottom: theme.spacing[4],
          textAlign: 'center'
        }}>
          <h3 style={{
            fontSize: theme.typography.xl,
            fontWeight: theme.typography.bold,
            color: theme.colors.primary,
            marginBottom: theme.spacing[3]
          }}>
            Golf Terminology Challenge
          </h3>
          <p style={{ fontSize: theme.typography.base, lineHeight: 1.6 }}>
            Drag each golf term to its correct category. Understanding these terms 
            will help you follow along with the rest of the tutorial.
          </p>
        </div>

        <TutorialDragDrop
          items={dragDropData.items}
          categories={dragDropData.categories}
          instructions="Drag the golf terms below into their appropriate categories. You need to get at least 80% correct to proceed."
          onComplete={(success) => {
            if (success) {
              tutorial.addFeedback('Great job! You understand the basic golf terminology.');
            }
          }}
        />

        <div style={{ marginTop: theme.spacing[6] }}>
          <TutorialQuiz
            questionId="terminology-final"
            question="In Wolf Goat Pig, why is understanding basic golf terminology important?"
            options={[
              "It makes you sound more professional",
              "It helps you understand game commentary and strategies",
              "It's required by golf rules",
              "It impresses other players"
            ]}
            correctAnswer={1}
            explanation="Understanding golf terminology helps you follow the game commentary, understand strategic discussions, and make better informed decisions during play."
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

export default GolfBasicsModule;