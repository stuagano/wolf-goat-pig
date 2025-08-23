import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useTutorial } from '../../context/TutorialContext';
import { useTheme } from '../../theme/Provider';

/**
 * Tutorial overlay component for contextual guidance and tooltips
 * Provides step-by-step guidance with spotlight effect
 */
const TutorialOverlay = () => {
  const tutorial = useTutorial();
  const theme = useTheme();
  const [highlightElement, setHighlightElement] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });
  const [currentGuidance, setCurrentGuidance] = useState(null);
  const overlayRef = useRef(null);
  const tooltipRef = useRef(null);

  // Guidance data for different contexts
  const guidanceData = {
    'golf-basics': {
      steps: [
        {
          target: '.golf-basics-scoring',
          title: 'Understanding Golf Scoring',
          content: 'Golf scoring is based on strokes taken. Lower numbers are better!',
          position: 'bottom'
        },
        {
          target: '.golf-basics-handicap',
          title: 'Handicap System',
          content: 'Handicaps level the playing field between players of different skill levels.',
          position: 'top'
        }
      ]
    },
    'team-formation': {
      steps: [
        {
          target: '.team-formation-demo',
          title: 'Team Selection Process',
          content: 'Click and drag to see how teams are formed in Wolf Goat Pig.',
          position: 'right'
        },
        {
          target: '.partnership-rules',
          title: 'Partnership Dynamics',
          content: 'Partners work together to win holes and maximize winnings.',
          position: 'left'
        }
      ]
    },
    'betting-system': {
      steps: [
        {
          target: '.betting-calculator',
          title: 'Betting Calculator',
          content: 'Use this tool to understand how odds and payouts work.',
          position: 'top'
        },
        {
          target: '.risk-management',
          title: 'Risk Management',
          content: 'Learn to balance risk and reward in your betting strategy.',
          position: 'bottom'
        }
      ]
    }
  };

  // Update guidance based on current module
  useEffect(() => {
    if (tutorial.currentModule && guidanceData[tutorial.currentModule]) {
      setCurrentGuidance(guidanceData[tutorial.currentModule]);
    } else {
      setCurrentGuidance(null);
    }
  }, [tutorial.currentModule, guidanceData]); // Added guidanceData as dependency

  // Calculate tooltip position
  const calculateTooltipPosition = useCallback((targetElement, preferredPosition = 'bottom') => {
    if (!targetElement || !tooltipRef.current) return { x: 0, y: 0 };

    const targetRect = targetElement.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let x, y;

    switch (preferredPosition) {
      case 'top':
        x = targetRect.left + (targetRect.width / 2) - (tooltipRect.width / 2);
        y = targetRect.top - tooltipRect.height - 10;
        break;
      case 'bottom':
        x = targetRect.left + (targetRect.width / 2) - (tooltipRect.width / 2);
        y = targetRect.bottom + 10;
        break;
      case 'left':
        x = targetRect.left - tooltipRect.width - 10;
        y = targetRect.top + (targetRect.height / 2) - (tooltipRect.height / 2);
        break;
      case 'right':
        x = targetRect.right + 10;
        y = targetRect.top + (targetRect.height / 2) - (tooltipRect.height / 2);
        break;
      default:
        x = targetRect.left + (targetRect.width / 2) - (tooltipRect.width / 2);
        y = targetRect.bottom + 10;
        break;
    }

    // Ensure tooltip stays within viewport
    x = Math.max(10, Math.min(x, viewportWidth - tooltipRect.width - 10));
    y = Math.max(10, Math.min(y, viewportHeight - tooltipRect.height - 10));

    return { x, y };
  }, []);

  // Highlight target element
  const highlightTarget = useCallback((selector) => {
    const element = document.querySelector(selector);
    if (element) {
      setHighlightElement(element);
      const position = calculateTooltipPosition(element);
      setTooltipPosition(position);
    }
  }, [calculateTooltipPosition]); // Added calculateTooltipPosition as dependency

  // Handle step navigation within overlay
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const nextStep = useCallback(() => {
    if (currentGuidance && currentStepIndex < currentGuidance.steps.length - 1) {
      const newIndex = currentStepIndex + 1;
      setCurrentStepIndex(newIndex);
      highlightTarget(currentGuidance.steps[newIndex].target);
    }
  }, [currentGuidance, currentStepIndex, highlightTarget]);

  const previousStep = useCallback(() => {
    if (currentStepIndex > 0) {
      const newIndex = currentStepIndex - 1;
      setCurrentStepIndex(newIndex);
      highlightTarget(currentGuidance.steps[newIndex].target);
    }
  }, [currentGuidance, currentStepIndex, highlightTarget]);

  // Initialize first step when guidance changes
  useEffect(() => {
    if (currentGuidance && currentGuidance.steps.length > 0) {
      setCurrentStepIndex(0);
      highlightTarget(currentGuidance.steps[0].target);
    }
  }, [currentGuidance]);

  // Update tooltip position on resize or scroll
  useEffect(() => {
    const updatePosition = () => {
      if (highlightElement) {
        const step = currentGuidance?.steps[currentStepIndex];
        const position = calculateTooltipPosition(highlightElement, step?.position);
        setTooltipPosition(position);
      }
    };

    window.addEventListener('resize', updatePosition);
    window.addEventListener('scroll', updatePosition);
    
    return () => {
      window.removeEventListener('resize', updatePosition);
      window.removeEventListener('scroll', updatePosition);
    };
  }, [highlightElement, currentGuidance, currentStepIndex, calculateTooltipPosition]);

  // Keyboard navigation for overlay
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (!tutorial.overlayVisible) return;

      switch (e.key) {
        case 'ArrowRight':
        case 'Space':
          e.preventDefault();
          nextStep();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          previousStep();
          break;
        case 'Escape':
          e.preventDefault();
          tutorial.toggleOverlay();
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [tutorial, nextStep, previousStep]);

  if (!tutorial.overlayVisible || !currentGuidance) {
    return null;
  }

  const currentStep = currentGuidance.steps[currentStepIndex];
  const highlightRect = highlightElement ? highlightElement.getBoundingClientRect() : null;

  const styles = {
    overlay: {
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      zIndex: 9999,
      pointerEvents: 'auto'
    },

    spotlight: highlightRect ? {
      position: 'absolute',
      top: highlightRect.top - 8,
      left: highlightRect.left - 8,
      width: highlightRect.width + 16,
      height: highlightRect.height + 16,
      borderRadius: theme.borderRadius.base,
      boxShadow: `0 0 0 4px ${theme.colors.primary}, 0 0 0 9999px rgba(0, 0, 0, 0.7)`,
      pointerEvents: 'none',
      transition: tutorial.reducedMotion ? 'none' : 'all 0.3s ease'
    } : {},

    tooltip: {
      position: 'absolute',
      left: tooltipPosition.x,
      top: tooltipPosition.y,
      backgroundColor: theme.colors.paper,
      borderRadius: theme.borderRadius.md,
      boxShadow: theme.shadows.lg,
      padding: theme.spacing[6],
      maxWidth: 350,
      minWidth: 250,
      border: `2px solid ${theme.colors.primary}`,
      zIndex: 10000
    },

    tooltipHeader: {
      marginBottom: theme.spacing[4]
    },

    tooltipTitle: {
      fontSize: theme.typography.lg,
      fontWeight: theme.typography.bold,
      color: theme.colors.primary,
      marginBottom: theme.spacing[2]
    },

    tooltipContent: {
      fontSize: theme.typography.base,
      lineHeight: 1.6,
      color: theme.colors.textPrimary,
      marginBottom: theme.spacing[6]
    },

    tooltipActions: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    },

    stepIndicator: {
      fontSize: theme.typography.sm,
      color: theme.colors.textSecondary,
      fontWeight: theme.typography.medium
    },

    buttonGroup: {
      display: 'flex',
      gap: theme.spacing[2]
    },

    button: {
      padding: `${theme.spacing[2]} ${theme.spacing[4]}`,
      borderRadius: theme.borderRadius.base,
      border: 'none',
      cursor: 'pointer',
      fontSize: theme.typography.sm,
      fontWeight: theme.typography.medium,
      transition: tutorial.reducedMotion ? 'none' : 'all 0.2s ease'
    },

    primaryButton: {
      backgroundColor: theme.colors.primary,
      color: '#ffffff'
    },

    secondaryButton: {
      backgroundColor: theme.colors.gray200,
      color: theme.colors.textPrimary,
      border: `1px solid ${theme.colors.border}`
    },

    closeButton: {
      position: 'absolute',
      top: theme.spacing[3],
      right: theme.spacing[3],
      background: 'none',
      border: 'none',
      fontSize: theme.typography.lg,
      color: theme.colors.textSecondary,
      cursor: 'pointer',
      padding: theme.spacing[1],
      borderRadius: theme.borderRadius.base,
      transition: tutorial.reducedMotion ? 'none' : 'color 0.2s ease'
    },

    arrow: {
      position: 'absolute',
      width: 0,
      height: 0,
      borderStyle: 'solid'
    },

    // Arrow positioning based on tooltip position
    getArrowStyle: (position) => {
      const arrowSize = 8;
      switch (position) {
        case 'top':
          return {
            ...styles.arrow,
            top: '100%',
            left: '50%',
            marginLeft: -arrowSize,
            borderWidth: `${arrowSize}px ${arrowSize}px 0 ${arrowSize}px`,
            borderColor: `${theme.colors.paper} transparent transparent transparent`
          };
        case 'bottom':
          return {
            ...styles.arrow,
            bottom: '100%',
            left: '50%',
            marginLeft: -arrowSize,
            borderWidth: `0 ${arrowSize}px ${arrowSize}px ${arrowSize}px`,
            borderColor: `transparent transparent ${theme.colors.paper} transparent`
          };
        case 'left':
          return {
            ...styles.arrow,
            left: '100%',
            top: '50%',
            marginTop: -arrowSize,
            borderWidth: `${arrowSize}px 0 ${arrowSize}px ${arrowSize}px`,
            borderColor: `transparent transparent transparent ${theme.colors.paper}`
          };
        case 'right':
          return {
            ...styles.arrow,
            right: '100%',
            top: '50%',
            marginTop: -arrowSize,
            borderWidth: `${arrowSize}px ${arrowSize}px ${arrowSize}px 0`,
            borderColor: `transparent ${theme.colors.paper} transparent transparent`
          };
        default:
          return styles.arrow;
      }
    },

    keyboardHints: {
      marginTop: theme.spacing[4],
      padding: theme.spacing[3],
      backgroundColor: theme.colors.gray50,
      borderRadius: theme.borderRadius.base,
      fontSize: theme.typography.xs,
      color: theme.colors.textSecondary
    }
  };

  return (
    <div ref={overlayRef} style={styles.overlay}>
      {/* Spotlight effect */}
      {highlightRect && <div style={styles.spotlight} />}

      {/* Tooltip */}
      <div ref={tooltipRef} style={styles.tooltip}>
        {/* Arrow pointing to target */}
        <div style={styles.getArrowStyle(currentStep.position)} />

        {/* Close button */}
        <button 
          style={styles.closeButton}
          onClick={tutorial.toggleOverlay}
          title="Close guidance (Esc)"
        >
          ✕
        </button>

        {/* Content */}
        <div style={styles.tooltipHeader}>
          <h3 style={styles.tooltipTitle}>{currentStep.title}</h3>
          <p style={styles.tooltipContent}>{currentStep.content}</p>
        </div>

        {/* Actions */}
        <div style={styles.tooltipActions}>
          <div style={styles.stepIndicator}>
            Step {currentStepIndex + 1} of {currentGuidance.steps.length}
          </div>

          <div style={styles.buttonGroup}>
            <button 
              style={{
                ...styles.button,
                ...styles.secondaryButton,
                opacity: currentStepIndex === 0 ? 0.5 : 1
              }}
              onClick={previousStep}
              disabled={currentStepIndex === 0}
            >
              Previous
            </button>

            {currentStepIndex < currentGuidance.steps.length - 1 ? (
              <button 
                style={{
                  ...styles.button,
                  ...styles.primaryButton
                }}
                onClick={nextStep}
              >
                Next
              </button>
            ) : (
              <button 
                style={{
                  ...styles.button,
                  ...styles.primaryButton
                }}
                onClick={tutorial.toggleOverlay}
              >
                Finish
              </button>
            )}
          </div>
        </div>

        {/* Keyboard hints */}
        <div style={styles.keyboardHints}>
          <strong>Keyboard shortcuts:</strong> Space/→ Next, ← Previous, Esc Close
        </div>
      </div>
    </div>
  );
};

export default TutorialOverlay;