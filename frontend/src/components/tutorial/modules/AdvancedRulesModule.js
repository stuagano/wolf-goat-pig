import React from 'react';
import { useTutorial } from '../../../context/TutorialContext';
import { useTheme } from '../../../theme/Provider';
import TutorialModule from '../TutorialModule';
import { TutorialQuiz, TutorialSimulation } from '../InteractiveElement';

const AdvancedRulesModule = ({ onStepComplete, onModuleComplete, currentStep, goToStep }) => {
  const tutorial = useTutorial();
  const theme = useTheme();

  const steps = [
    {
      id: 'special-situations',
      title: 'Special Situations & Edge Cases',
      hints: 'Learn how to handle unusual situations that arise during play.',
      content: 'special-situations'
    },
    {
      id: 'tie-resolution',
      title: 'Tie Breaking & Dispute Resolution',
      hints: 'Understanding how ties are resolved keeps the game moving smoothly.',
      content: 'tie-resolution'
    },
    {
      id: 'advanced-strategies',
      title: 'Tournament Play & Variations',
      hints: 'Different formats and house rules can change optimal strategies.',
      content: 'advanced-strategies'
    }
  ];

  const moduleProps = {
    moduleId: 'advanced-rules',
    title: 'Special Rules & Advanced Strategies',
    description: 'Master edge cases, special situations, and advanced strategic concepts for competitive Wolf Goat Pig play.',
    estimatedTime: 15,
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
      case 'special-situations':
        return <SpecialSituationsStep />;
      case 'tie-resolution':
        return <TieResolutionStep />;
      case 'advanced-strategies':
        return <AdvancedStrategiesStep />;
      default:
        return <div>Step content not found</div>;
    }
  };

  const SpecialSituationsStep = () => (
    <div style={{maxWidth: 900, margin: '0 auto'}}>
      <div style={{...theme.cardStyle, padding: theme.spacing[5], marginBottom: theme.spacing[4]}}>
        <h3 style={{color: theme.colors.primary, marginBottom: theme.spacing[3]}}>Weather & Course Conditions</h3>
        <p>Adverse conditions can dramatically affect strategy and fair play.</p>
        <ul style={{marginTop: theme.spacing[3], lineHeight: 1.8}}>
          <li><strong>Wind:</strong> May warrant betting adjustments or role reconsiderations</li>
          <li><strong>Rain:</strong> Consider lift, clean, and place rules impact</li>
          <li><strong>Course conditions:</strong> Soft/hard greens change risk calculations</li>
        </ul>
      </div>

      <div style={{...theme.cardStyle, padding: theme.spacing[5], marginBottom: theme.spacing[4]}}>
        <h3 style={{color: theme.colors.primary, marginBottom: theme.spacing[3]}}>Penalty Situations</h3>
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: theme.spacing[4]}}>
          <div>
            <h4>Water Hazards</h4>
            <ul style={{fontSize: theme.typography.sm, lineHeight: 1.6}}>
              <li>Stroke and distance penalty</li>
              <li>Lateral hazard drop options</li>
              <li>Impact on team scoring</li>
            </ul>
          </div>
          <div>
            <h4>Out of Bounds</h4>
            <ul style={{fontSize: theme.typography.sm, lineHeight: 1.6}}>
              <li>Stroke and distance mandatory</li>
              <li>Provisional ball procedures</li>
              <li>Time management considerations</li>
            </ul>
          </div>
        </div>
      </div>

      <TutorialQuiz
        questionId="special-situations"
        question="Your Wolf partner hits into a water hazard on a crucial hole. As their teammate, what should you do?"
        options={[
          "Play aggressively to make up for their mistake",
          "Play conservatively since you're now the team's safety net",
          "Give up on the hole since your partner is in trouble", 
          "Demand they replay the shot"
        ]}
        correctAnswer={1}
        explanation="When your partner is in trouble, you become the team's primary scorer. Play smart and conservative to ensure your team has at least one decent score."
      />
    </div>
  );

  const TieResolutionStep = () => (
    <div style={{maxWidth: 900, margin: '0 auto'}}>
      <div style={{...theme.cardStyle, padding: theme.spacing[5], marginBottom: theme.spacing[4]}}>
        <h3 style={{color: theme.colors.primary, marginBottom: theme.spacing[3]}}>Standard Tie Breaking</h3>
        <div style={{marginBottom: theme.spacing[4]}}>
          <h4>Two-way ties:</h4>
          <ul style={{lineHeight: 1.8}}>
            <li>Tied teams split winnings from losing teams</li>
            <li>No money exchanges between tied teams</li>
            <li>Simple and fair resolution</li>
          </ul>
        </div>
        <div>
          <h4>Three-way ties:</h4>
          <ul style={{lineHeight: 1.8}}>
            <li>Rare but possible situation</li>
            <li>All tied teams break even</li>
            <li>Only losing team(s) pay out</li>
          </ul>
        </div>
      </div>

      <div style={{...theme.cardStyle, padding: theme.spacing[5]}}>
        <h3 style={{color: theme.colors.primary, marginBottom: theme.spacing[3]}}>Dispute Resolution</h3>
        <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: theme.spacing[4]}}>
          <div>
            <h4>Score Disputes</h4>
            <ul style={{fontSize: theme.typography.sm, lineHeight: 1.6}}>
              <li>Require witness confirmation</li>
              <li>When in doubt, favor higher score</li>
              <li>Maintain detailed scorecards</li>
            </ul>
          </div>
          <div>
            <h4>Rule Clarifications</h4>
            <ul style={{fontSize: theme.typography.sm, lineHeight: 1.6}}>
              <li>Designate rules official before play</li>
              <li>Use USGA rules as baseline</li>
              <li>House rules should be pre-agreed</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );

  const AdvancedStrategiesStep = () => (
    <div style={{maxWidth: 900, margin: '0 auto'}}>
      <div style={{...theme.cardStyle, padding: theme.spacing[5], marginBottom: theme.spacing[4]}}>
        <h3 style={{color: theme.colors.primary, marginBottom: theme.spacing[3]}}>Tournament Variations</h3>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: theme.spacing[4]}}>
          <div>
            <h4>Match Play Format</h4>
            <ul style={{fontSize: theme.typography.sm, lineHeight: 1.6}}>
              <li>Holes won vs. strokes taken</li>
              <li>Concede strategies</li>
              <li>Psychological pressure management</li>
            </ul>
          </div>
          <div>
            <h4>Scramble WGP</h4>
            <ul style={{fontSize: theme.typography.sm, lineHeight: 1.6}}>
              <li>Team best ball on every shot</li>
              <li>Reduces individual pressure</li>
              <li>Emphasizes team strategy</li>
            </ul>
          </div>
          <div>
            <h4>Quota System</h4>
            <ul style={{fontSize: theme.typography.sm, lineHeight: 1.6}}>
              <li>Points-based scoring</li>
              <li>Levels playing field further</li>
              <li>Rewards improvement</li>
            </ul>
          </div>
        </div>
      </div>

      <TutorialSimulation
        title="Advanced Strategy Scenario"
        scenario="Final hole, you're trailing by $10. It's a risky par 5 with water. You have first choice and the confidence to execute, but one bad shot could cost you the round."
        options={[
          {
            title: "Go Wolf - High risk, high reward",
            description: "Win big if successful, lose big if you fail"
          },
          {
            title: "Choose Goat - Share the risk",
            description: "Find a reliable partner to improve your odds"
          },
          {
            title: "Accept Pig - Cut your losses", 
            description: "Minimize damage and hope others make mistakes"
          }
        ]}
        onDecision={(option) => {
          let feedback;
          if (option.title.includes('Wolf')) {
            feedback = "Bold choice! High risk but potentially high reward. This is what separates good players from great ones.";
          } else if (option.title.includes('Goat')) {
            feedback = "Strategic thinking! Sharing risk while still having upside potential is often the smartest play.";
          } else {
            feedback = "Conservative but reasonable. Sometimes the best play is to let others make mistakes.";
          }
          tutorial.addFeedback(feedback);
        }}
      />
    </div>
  );

  return (
    <TutorialModule {...moduleProps}>
      {renderStepContent()}
    </TutorialModule>
  );
};

export default AdvancedRulesModule;