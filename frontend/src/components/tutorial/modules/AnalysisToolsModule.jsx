import React, { useState } from 'react';
// import { useTutorial } from '../../../context/TutorialContext'; // Removed - not used
import { useTheme } from '../../../theme/Provider';
import TutorialModule from '../TutorialModule';
import { TutorialQuiz } from '../InteractiveElement';

const AnalysisToolsModule = ({ onStepComplete, onModuleComplete, currentStep, goToStep }) => {
  const theme = useTheme();

  const steps = [
    {
      id: 'shot-analysis',
      title: 'Shot-by-Shot Analysis',
      hints: 'Learn to use detailed shot tracking for strategic insights.',
      content: 'shot-analysis'
    },
    {
      id: 'performance-metrics',
      title: 'Performance Tracking & Statistics',
      hints: 'Key metrics help you understand your strengths and weaknesses.',
      content: 'performance-metrics'
    },
    {
      id: 'strategic-tools',
      title: 'Strategic Planning Tools',
      hints: 'Use data to make better decisions during play.',
      content: 'strategic-tools'
    }
  ];

  const moduleProps = {
    moduleId: 'analysis-tools',
    title: 'Shot-by-Shot Mode & Analysis Tools',
    description: 'Master the analytical tools and statistical features that give you a competitive edge in Wolf Goat Pig.',
    estimatedTime: 10,
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
      case 'shot-analysis':
        return <ShotAnalysisStep />;
      case 'performance-metrics':
        return <PerformanceMetricsStep />;
      case 'strategic-tools':
        return <StrategicToolsStep />;
      default:
        return <div>Step content not found</div>;
    }
  };

  const ShotAnalysisStep = () => {
    const [selectedShot, setSelectedShot] = useState(0);
    
    const shotExample = [
      { club: 'Driver', distance: 285, accuracy: 'Fairway', outcome: 'Good position' },
      { club: '7-Iron', distance: 155, accuracy: 'Green (20ft)', outcome: 'Birdie putt' },
      { club: 'Putter', distance: 20, accuracy: 'Made', outcome: 'Birdie!' }
    ];

    return (
      <div style={{maxWidth: 900, margin: '0 auto'}}>
        <div style={{...theme.cardStyle, padding: theme.spacing[5], marginBottom: theme.spacing[4]}}>
          <h3 style={{color: theme.colors.primary, marginBottom: theme.spacing[3]}}>
            Shot-by-Shot Tracking Benefits
          </h3>
          <p style={{lineHeight: 1.6, marginBottom: theme.spacing[4]}}>
            Detailed shot analysis provides insights that help you make better strategic decisions 
            and improve your overall game performance.
          </p>
          
          <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: theme.spacing[4]}}>
            <div style={{padding: theme.spacing[3], border: `1px solid ${theme.colors.border}`, borderRadius: theme.borderRadius.base}}>
              <h4 style={{color: theme.colors.success, marginBottom: theme.spacing[2]}}>📊 Pattern Recognition</h4>
              <p style={{fontSize: theme.typography.sm}}>Identify which holes and situations you excel in</p>
            </div>
            <div style={{padding: theme.spacing[3], border: `1px solid ${theme.colors.border}`, borderRadius: theme.borderRadius.base}}>
              <h4 style={{color: theme.colors.warning, marginBottom: theme.spacing[2]}}>🎯 Weakness Identification</h4>
              <p style={{fontSize: theme.typography.sm}}>Spot areas needing improvement in your game</p>
            </div>
            <div style={{padding: theme.spacing[3], border: `1px solid ${theme.colors.border}`, borderRadius: theme.borderRadius.base}}>
              <h4 style={{color: theme.colors.error, marginBottom: theme.spacing[2]}}>⚡ Real-time Strategy</h4>
              <p style={{fontSize: theme.typography.sm}}>Make better role choices based on historical data</p>
            </div>
          </div>
        </div>

        <div style={{...theme.cardStyle, padding: theme.spacing[5], marginBottom: theme.spacing[4]}}>
          <h3 style={{color: theme.colors.primary, marginBottom: theme.spacing[4]}}>
            Example: Hole Analysis Breakdown
          </h3>
          
          <div style={{display: 'flex', justifyContent: 'center', gap: theme.spacing[2], marginBottom: theme.spacing[4]}}>
            {shotExample.map((shot, index) => (
              <button
                key={index}
                onClick={() => setSelectedShot(index)}
                style={{
                  padding: `${theme.spacing[2]} ${theme.spacing[3]}`,
                  borderRadius: theme.borderRadius.base,
                  border: `2px solid ${selectedShot === index ? theme.colors.primary : theme.colors.border}`,
                  backgroundColor: selectedShot === index ? theme.colors.primaryLight + '20' : theme.colors.paper,
                  cursor: 'pointer'
                }}
              >
                Shot {index + 1}
              </button>
            ))}
          </div>
          
          <div style={{
            padding: theme.spacing[4],
            backgroundColor: theme.colors.gray50,
            borderRadius: theme.borderRadius.base,
            textAlign: 'center'
          }}>
            <h4>Shot {selectedShot + 1}: {shotExample[selectedShot].club}</h4>
            <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: theme.spacing[3], marginTop: theme.spacing[3]}}>
              <div>
                <strong>Distance</strong><br/>
                {shotExample[selectedShot].distance} yards
              </div>
              <div>
                <strong>Accuracy</strong><br/>
                {shotExample[selectedShot].accuracy}
              </div>
              <div>
                <strong>Outcome</strong><br/>
                {shotExample[selectedShot].outcome}
              </div>
            </div>
          </div>
        </div>

        <TutorialQuiz
          questionId="shot-analysis"
          question="Based on shot-by-shot data, you discover you make birdie 60% of the time on par 3s under 150 yards, but only 20% on par 3s over 180 yards. How should this affect your Wolf Goat Pig strategy?"
          options={[
            "Always go Wolf on short par 3s",
            "Consider going Wolf more often on short par 3s, avoid it on long ones",
            "This data isn't relevant to role selection",
            "Only use this data for side bets"
          ]}
          correctAnswer={1}
          explanation="Statistical data should inform but not dictate your strategy. Higher success rates on short par 3s make Wolf more attractive, while lower success on long par 3s suggests more conservative approaches."
        />
      </div>
    );
  };

  const PerformanceMetricsStep = () => (
    <div style={{maxWidth: 900, margin: '0 auto'}}>
      <div style={{...theme.cardStyle, padding: theme.spacing[5], marginBottom: theme.spacing[4]}}>
        <h3 style={{color: theme.colors.primary, marginBottom: theme.spacing[3]}}>Key Performance Indicators</h3>
        
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: theme.spacing[4]}}>
          <div style={{padding: theme.spacing[4], backgroundColor: theme.colors.successLight + '20', borderRadius: theme.borderRadius.base}}>
            <h4 style={{color: theme.colors.success, marginBottom: theme.spacing[2]}}>Wolf Success Rate</h4>
            <div style={{fontSize: theme.typography.xl, fontWeight: theme.typography.bold, marginBottom: theme.spacing[2]}}>42%</div>
            <p style={{fontSize: theme.typography.sm}}>Percentage of Wolf holes won. Target: 35%+ for profitability</p>
          </div>
          
          <div style={{padding: theme.spacing[4], backgroundColor: theme.colors.warningLight + '20', borderRadius: theme.borderRadius.base}}>
            <h4 style={{color: theme.colors.warning, marginBottom: theme.spacing[2]}}>Partnership Win Rate</h4>
            <div style={{fontSize: theme.typography.xl, fontWeight: theme.typography.bold, marginBottom: theme.spacing[2]}}>58%</div>
            <p style={{fontSize: theme.typography.sm}}>Goat team performance. Shows partnership compatibility</p>
          </div>
          
          <div style={{padding: theme.spacing[4], backgroundColor: theme.colors.errorLight + '20', borderRadius: theme.borderRadius.base}}>
            <h4 style={{color: theme.colors.error, marginBottom: theme.spacing[2]}}>Pressure Performance</h4>
            <div style={{fontSize: theme.typography.xl, fontWeight: theme.typography.bold, marginBottom: theme.spacing[2]}}>-0.8</div>
            <p style={{fontSize: theme.typography.sm}}>Strokes worse under pressure. Work on mental game</p>
          </div>
        </div>
      </div>

      <div style={{...theme.cardStyle, padding: theme.spacing[5]}}>
        <h3 style={{color: theme.colors.primary, marginBottom: theme.spacing[4]}}>Trend Analysis</h3>
        
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: theme.spacing[6]}}>
          <div>
            <h4>Improving Areas</h4>
            <ul style={{lineHeight: 1.8, color: theme.colors.success}}>
              <li>Par 4 Wolf success: +15% vs last month</li>
              <li>Partnership communication: Better</li>
              <li>Late-round performance: More consistent</li>
            </ul>
          </div>
          <div>
            <h4>Areas for Focus</h4>
            <ul style={{lineHeight: 1.8, color: theme.colors.error}}>
              <li>Par 5 Wolf attempts: Too aggressive</li>
              <li>Betting size: Inconsistent with confidence</li>
              <li>Short game under pressure: Needs work</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );

  const StrategicToolsStep = () => (
    <div style={{maxWidth: 900, margin: '0 auto'}}>
      <div style={{...theme.cardStyle, padding: theme.spacing[5], marginBottom: theme.spacing[4]}}>
        <h3 style={{color: theme.colors.primary, marginBottom: theme.spacing[3]}}>Pre-Round Planning Tools</h3>
        
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: theme.spacing[4]}}>
          <div style={{textAlign: 'center', padding: theme.spacing[3]}}>
            <div style={{fontSize: '2rem', marginBottom: theme.spacing[2]}}>📋</div>
            <h4>Hole Strategy Cards</h4>
            <p style={{fontSize: theme.typography.sm}}>Pre-planned approach for each hole based on your strengths</p>
          </div>
          <div style={{textAlign: 'center', padding: theme.spacing[3]}}>
            <div style={{fontSize: '2rem', marginBottom: theme.spacing[2]}}>🎯</div>
            <h4>Opponent Analysis</h4>
            <p style={{fontSize: theme.typography.sm}}>Track playing partners' tendencies and weaknesses</p>
          </div>
          <div style={{textAlign: 'center', padding: theme.spacing[3]}}>
            <div style={{fontSize: '2rem', marginBottom: theme.spacing[2]}}>💰</div>
            <h4>Bankroll Strategy</h4>
            <p style={{fontSize: theme.typography.sm}}>Betting progression plan based on current position</p>
          </div>
          <div style={{textAlign: 'center', padding: theme.spacing[3]}}>
            <div style={{fontSize: '2rem', marginBottom: theme.spacing[2]}}>🌤️</div>
            <h4>Condition Adjustments</h4>
            <p style={{fontSize: theme.typography.sm}}>How weather and course conditions affect your strategy</p>
          </div>
        </div>
      </div>

      <div style={{...theme.cardStyle, padding: theme.spacing[5]}}>
        <h3 style={{color: theme.colors.primary, marginBottom: theme.spacing[4]}}>Real-Time Decision Support</h3>
        
        <div style={{backgroundColor: theme.colors.gray50, padding: theme.spacing[4], borderRadius: theme.borderRadius.base}}>
          <h4 style={{marginBottom: theme.spacing[3]}}>Hole 7 - Par 4, 385 yards</h4>
          
          <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: theme.spacing[4]}}>
            <div>
              <h5 style={{color: theme.colors.success}}>Your Historical Performance</h5>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.6}}>
                <li>Average score: 4.2</li>
                <li>Wolf success: 45%</li>
                <li>Best recent: Birdie (last week)</li>
              </ul>
            </div>
            <div>
              <h5 style={{color: theme.colors.warning}}>Group Dynamics</h5>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.6}}>
                <li>Sarah: Struggling today (-2)</li>
                <li>Mike: Hot streak (+3)</li>
                <li>Lisa: Consistent par player</li>
              </ul>
            </div>
            <div>
              <h5 style={{color: theme.colors.error}}>Recommendation</h5>
              <ul style={{fontSize: theme.typography.sm, lineHeight: 1.6}}>
                <li>Strong Wolf candidate</li>
                <li>Sarah struggling = opportunity</li>
                <li>Confidence level: High</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <div style={{marginTop: theme.spacing[6]}}>
        <TutorialQuiz
          questionId="strategic-tools"
          question="The analysis tools suggest you should go Wolf on a particular hole, but you're feeling uncertain about your putting today. What's the best approach?"
          options={[
            "Always follow the data recommendations",
            "Ignore the data and trust your gut feeling",
            "Consider both data and current form in your decision",
            "Ask your playing partners what they think"
          ]}
          correctAnswer={2}
          explanation="The best decisions combine statistical analysis with real-time assessment of your current form, confidence, and conditions. Data informs but doesn't replace judgment."
        />
      </div>
    </div>
  );

  return (
    <TutorialModule {...moduleProps}>
      {renderStepContent()}
    </TutorialModule>
  );
};

export default AnalysisToolsModule;