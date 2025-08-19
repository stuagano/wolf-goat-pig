import React, { useState, useEffect } from 'react';
import { useTutorial } from '../../context/TutorialContext';
import { useTheme } from '../../theme/Provider';

/**
 * Generic tutorial module wrapper component
 * Provides common functionality for all tutorial modules
 */
const TutorialModule = ({ 
  children,
  moduleId,
  title,
  description,
  estimatedTime,
  onStepComplete,
  onModuleComplete,
  steps = [],
  currentStep = 0,
  allowSkip = true,
  requiredCompletion = false
}) => {
  const tutorial = useTutorial();
  const theme = useTheme();
  const [localStep, setLocalStep] = useState(currentStep);
  const [startTime, setStartTime] = useState(Date.now());
  const [stepStartTime, setStepStartTime] = useState(Date.now());

  // Track time when step changes
  useEffect(() => {
    setStepStartTime(Date.now());
  }, [localStep]);

  // Initialize start time
  useEffect(() => {
    setStartTime(Date.now());
  }, []);

  const handleStepComplete = (stepIndex = localStep) => {
    const timeSpent = Date.now() - stepStartTime;
    
    // Mark step as completed
    tutorial.completeStep(moduleId, stepIndex);
    
    // Update time tracking
    tutorial.updateTimeSpent(moduleId, Math.floor(timeSpent / 1000));
    
    // Call external handler
    onStepComplete && onStepComplete(stepIndex, timeSpent);
    
    // Advance to next step
    if (stepIndex < steps.length - 1) {
      setLocalStep(stepIndex + 1);
      tutorial.goToStep(stepIndex + 1);
    }
  };

  const handleModuleComplete = () => {
    const totalTime = Date.now() - startTime;
    
    // Mark module as completed
    tutorial.completeModule(moduleId);
    
    // Update final time
    tutorial.updateTimeSpent(moduleId, Math.floor(totalTime / 1000));
    
    // Call external handler
    onModuleComplete && onModuleComplete(totalTime);
    
    // Achievement check
    if (totalTime < estimatedTime * 60 * 1000 * 0.8) {
      tutorial.unlockAchievement(`${moduleId}-speed`);
    }
  };

  const goToStep = (stepIndex) => {
    if (stepIndex >= 0 && stepIndex < steps.length) {
      setLocalStep(stepIndex);
      tutorial.goToStep(stepIndex);
    }
  };

  const nextStep = () => {
    if (localStep < steps.length - 1) {
      handleStepComplete();
    } else {
      handleModuleComplete();
    }
  };

  const previousStep = () => {
    if (localStep > 0) {
      setLocalStep(localStep - 1);
      tutorial.goToStep(localStep - 1);
    }
  };

  const skipModule = () => {
    if (allowSkip) {
      handleModuleComplete();
      tutorial.nextModule();
    }
  };

  const styles = {
    container: {
      maxWidth: 1000,
      margin: '0 auto',
      padding: theme.spacing[6]
    },
    
    header: {
      textAlign: 'center',
      marginBottom: theme.spacing[8],
      paddingBottom: theme.spacing[6],
      borderBottom: `2px solid ${theme.colors.border}`
    },
    
    title: {
      fontSize: theme.typography['3xl'],
      fontWeight: theme.typography.bold,
      color: theme.colors.primary,
      marginBottom: theme.spacing[3]
    },
    
    description: {
      fontSize: theme.typography.lg,
      color: theme.colors.textSecondary,
      lineHeight: 1.6,
      marginBottom: theme.spacing[4]
    },
    
    meta: {
      display: 'flex',
      justifyContent: 'center',
      gap: theme.spacing[6],
      fontSize: theme.typography.sm,
      color: theme.colors.textSecondary
    },
    
    metaItem: {
      display: 'flex',
      alignItems: 'center',
      gap: theme.spacing[2]
    },
    
    progressContainer: {
      marginBottom: theme.spacing[8]
    },
    
    progressBar: {
      width: '100%',
      height: 8,
      backgroundColor: theme.colors.gray200,
      borderRadius: theme.borderRadius.full,
      overflow: 'hidden',
      marginBottom: theme.spacing[3]
    },
    
    progressFill: {
      height: '100%',
      backgroundColor: theme.colors.primary,
      transition: tutorial.reducedMotion ? 'none' : 'width 0.3s ease',
      borderRadius: theme.borderRadius.full
    },
    
    progressText: {
      textAlign: 'center',
      fontSize: theme.typography.sm,
      color: theme.colors.textSecondary
    },
    
    stepNavigation: {
      display: 'flex',
      justifyContent: 'center',
      gap: theme.spacing[2],
      marginBottom: theme.spacing[6],
      flexWrap: 'wrap'
    },
    
    stepButton: {
      width: 40,
      height: 40,
      borderRadius: theme.borderRadius.full,
      border: `2px solid ${theme.colors.border}`,
      background: theme.colors.paper,
      color: theme.colors.textSecondary,
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontSize: theme.typography.sm,
      fontWeight: theme.typography.semibold,
      transition: tutorial.reducedMotion ? 'none' : 'all 0.2s ease'
    },
    
    stepButtonActive: {
      borderColor: theme.colors.primary,
      backgroundColor: theme.colors.primary,
      color: '#ffffff'
    },
    
    stepButtonCompleted: {
      borderColor: theme.colors.success,
      backgroundColor: theme.colors.success,
      color: '#ffffff'
    },
    
    content: {
      minHeight: 400,
      marginBottom: theme.spacing[8]
    },
    
    navigation: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingTop: theme.spacing[6],
      borderTop: `1px solid ${theme.colors.border}`
    },
    
    navButton: {
      ...theme.buttonStyle,
      padding: `${theme.spacing[3]} ${theme.spacing[6]}`,
      fontSize: theme.typography.base
    },
    
    navButtonSecondary: {
      ...theme.buttonStyle,
      padding: `${theme.spacing[3]} ${theme.spacing[6]}`,
      fontSize: theme.typography.base,
      backgroundColor: theme.colors.gray200,
      color: theme.colors.textPrimary,
      border: `1px solid ${theme.colors.border}`
    },
    
    navButtonDisabled: {
      ...theme.buttonStyle,
      padding: `${theme.spacing[3]} ${theme.spacing[6]}`,
      fontSize: theme.typography.base,
      backgroundColor: theme.colors.gray300,
      color: theme.colors.gray500,
      cursor: 'not-allowed'
    },
    
    hints: {
      background: theme.colors.gray50,
      border: `1px solid ${theme.colors.border}`,
      borderRadius: theme.borderRadius.base,
      padding: theme.spacing[4],
      marginTop: theme.spacing[4],
      fontSize: theme.typography.sm,
      lineHeight: 1.5
    },
    
    achievements: {
      position: 'fixed',
      top: 20,
      right: 20,
      zIndex: 1000,
      pointerEvents: 'none'
    },
    
    achievement: {
      background: theme.colors.success,
      color: '#ffffff',
      padding: theme.spacing[3],
      borderRadius: theme.borderRadius.base,
      marginBottom: theme.spacing[2],
      boxShadow: theme.shadows.md,
      animation: tutorial.reducedMotion ? 'none' : 'slideInRight 0.3s ease',
      fontSize: theme.typography.sm
    }
  };

  const progress = steps.length > 0 ? ((localStep + 1) / steps.length) * 100 : 0;
  const isCompleted = tutorial.completedModules.has(moduleId);

  return (
    <div style={styles.container}>
      {/* Module header */}
      <header style={styles.header}>
        <h1 style={styles.title}>{title}</h1>
        <p style={styles.description}>{description}</p>
        
        <div style={styles.meta}>
          <div style={styles.metaItem}>
            <span>⏱️</span>
            <span>{estimatedTime} min</span>
          </div>
          <div style={styles.metaItem}>
            <span>📋</span>
            <span>{steps.length} steps</span>
          </div>
          {isCompleted && (
            <div style={styles.metaItem}>
              <span>✅</span>
              <span>Completed</span>
            </div>
          )}
        </div>
      </header>

      {/* Progress indicator */}
      {steps.length > 0 && (
        <div style={styles.progressContainer}>
          <div style={styles.progressBar}>
            <div 
              style={{
                ...styles.progressFill,
                width: `${progress}%`
              }}
            />
          </div>
          <div style={styles.progressText}>
            Step {localStep + 1} of {steps.length} ({Math.round(progress)}% complete)
          </div>
        </div>
      )}

      {/* Step navigation */}
      {steps.length > 0 && (
        <div style={styles.stepNavigation}>
          {steps.map((step, index) => {
            const isActive = index === localStep;
            const isCompleted = tutorial.completedSteps[`${moduleId}-${index}`];
            
            let stepStyle = styles.stepButton;
            if (isCompleted) stepStyle = { ...stepStyle, ...styles.stepButtonCompleted };
            else if (isActive) stepStyle = { ...stepStyle, ...styles.stepButtonActive };
            
            return (
              <button
                key={index}
                style={stepStyle}
                onClick={() => goToStep(index)}
                title={step.title || `Step ${index + 1}`}
                aria-label={`Go to step ${index + 1}`}
              >
                {isCompleted ? '✓' : index + 1}
              </button>
            );
          })}
        </div>
      )}

      {/* Module content */}
      <div style={styles.content}>
        {children}
      </div>

      {/* Hints section */}
      {tutorial.showHints && steps[localStep]?.hints && (
        <div style={styles.hints}>
          <strong>💡 Hint:</strong> {steps[localStep].hints}
        </div>
      )}

      {/* Navigation controls */}
      <nav style={styles.navigation}>
        <button 
          style={localStep > 0 ? styles.navButtonSecondary : styles.navButtonDisabled}
          onClick={previousStep}
          disabled={localStep === 0}
        >
          ← Previous Step
        </button>
        
        <div style={{ display: 'flex', gap: theme.spacing[3] }}>
          {allowSkip && !requiredCompletion && (
            <button 
              style={styles.navButtonSecondary}
              onClick={skipModule}
            >
              Skip Module
            </button>
          )}
          
          <button 
            style={styles.navButton}
            onClick={nextStep}
          >
            {localStep < steps.length - 1 ? 'Next Step →' : 'Complete Module'}
          </button>
        </div>
      </nav>
    </div>
  );
};

export default TutorialModule;