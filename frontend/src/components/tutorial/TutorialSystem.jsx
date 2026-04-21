import React, { useEffect, useState } from 'react';
import { useTutorial } from '../../context/TutorialContext';
import { useTutorialProgress } from '../../hooks/useTutorialProgress';
import { useTheme } from '../../theme/Provider';
import ProgressTracker from './ProgressTracker';
import TutorialOverlay from './TutorialOverlay';

// Import tutorial modules
import GolfBasicsModule from './modules/GolfBasicsModule';
import GameOverviewModule from './modules/GameOverviewModule';
import TeamFormationModule from './modules/TeamFormationModule';
import BettingSystemModule from './modules/BettingSystemModule';
import AdvancedRulesModule from './modules/AdvancedRulesModule';
import AnalysisToolsModule from './modules/AnalysisToolsModule';
import PracticeGameModule from './modules/PracticeGameModule';

// Module component mapping
const MODULE_COMPONENTS = {
  'golf-basics': GolfBasicsModule,
  'game-overview': GameOverviewModule,
  'team-formation': TeamFormationModule,
  'betting-system': BettingSystemModule,
  'advanced-rules': AdvancedRulesModule,
  'analysis-tools': AnalysisToolsModule,
  'practice-game': PracticeGameModule
};

const TutorialSystem = ({ onComplete, onExit }) => {
  const tutorial = useTutorial();
  const progress = useTutorialProgress();
  const theme = useTheme();
  const [sidebarWidth, setSidebarWidth] = useState(300);
  const [showWelcome, setShowWelcome] = useState(!tutorial.isActive);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const [showMobileSidebar, setShowMobileSidebar] = useState(false);

  // Handle window resize for mobile responsiveness
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth <= 768;
      setIsMobile(mobile);
      if (mobile) {
        setSidebarWidth(280); // Smaller sidebar on mobile
      } else {
        setSidebarWidth(300);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Initialize tutorial on mount
  useEffect(() => {
    if (!tutorial.isActive && !showWelcome) {
      // Try to resume from saved progress
      const savedProgress = progress.resumeFromSaved();
      if (savedProgress && savedProgress.lastModule) {
        tutorial.startTutorial(savedProgress.lastModule);
      } else {
        tutorial.startTutorial();
      }
    }
  }, [tutorial, progress, showWelcome]);

  // Handle tutorial completion
  useEffect(() => {
    if (tutorial.completed) {
      const analytics = progress.getAnalytics();
      onComplete && onComplete(analytics);
    }
  }, [tutorial.completed, progress, onComplete]);

  const styles = {
    container: {
      display: 'flex',
      height: '100vh',
      fontFamily: theme.typography.fontFamily,
      background: theme.colors.background,
      color: theme.colors.textPrimary,
      fontSize: tutorial.largeText ? '1.1em' : '1em',
      filter: tutorial.highContrast ? 'contrast(150%)' : 'none',
      flexDirection: isMobile ? 'column' : 'row',
      position: 'relative'
    },

    sidebar: {
      width: isMobile
        ? '100%'
        : tutorial.sidebarCollapsed
          ? 60
          : sidebarWidth,
      minWidth: isMobile ? '100%' : tutorial.sidebarCollapsed ? 60 : 250,
      maxWidth: isMobile ? '100%' : 400,
      height: isMobile ? (showMobileSidebar ? '50vh' : '60px') : '100vh',
      background: theme.colors.paper,
      borderRight: isMobile ? 'none' : `1px solid ${theme.colors.border}`,
      borderBottom: isMobile ? `1px solid ${theme.colors.border}` : 'none',
      display: 'flex',
      flexDirection: 'column',
      boxShadow: theme.shadows.base,
      transition: tutorial.reducedMotion ? 'none' : 'all 0.3s ease',
      resize: isMobile ? 'none' : 'horizontal',
      overflow: 'hidden',
      position: isMobile ? 'relative' : 'static',
      zIndex: isMobile ? 100 : 'auto'
    },

    mainContent: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      height: isMobile ? 'calc(100vh - 60px)' : '100vh'
    },

    moduleContainer: {
      flex: 1,
      padding: isMobile ? theme.spacing : theme.spacing,
      overflow: 'auto',
      maxWidth: 'none',
      WebkitOverflowScrolling: 'touch'
    },

    header: {
      padding: theme.spacing,
      background: theme.colors.primary,
      color: '#ffffff',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: theme.spacing,
      boxShadow: theme.shadows.base
    },

    headerActions: {
      display: 'flex',
      gap: theme.spacing,
      alignItems: 'center'
    },

    actionButton: {
      padding: '8px 16px',
      borderRadius: 4,
      cursor: 'pointer',
      background: '#ffffff',
      color: theme.colors.primary,
      border: 'none',
      fontSize: '0.95em',
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      transition: tutorial.reducedMotion ? 'none' : 'transform 0.2s ease',
      outline: 'none'
    },

    toggleSidebar: {
      padding: '8px 12px',
      background: 'rgba(0,0,0,0.1)',
      borderRadius: 4,
      color: '#ffffff',
      border: 'none',
      cursor: 'pointer'
    },

    overlayButton: {
      padding: '8px 12px',
      background: tutorial.overlayVisible ? '#ffc107' : '#ffffff',
      color: tutorial.overlayVisible ? '#000' : theme.colors.primary,
      borderRadius: 4,
      border: 'none',
      cursor: 'pointer'
    },

    moduleList: {
      flex: 1,
      overflowY: 'auto',
      padding: theme.spacing,
      display: 'flex',
      flexDirection: 'column',
      gap: theme.spacing,
      WebkitOverflowScrolling: 'touch'
    },

    moduleCard: (moduleId) => ({
      borderRadius: 8,
      padding: '12px 16px',
      background: tutorial.currentModule === moduleId
        ? theme.colors.primaryLight
        : theme.colors.paper,
      color: tutorial.currentModule === moduleId
        ? theme.colors.primaryContrast
        : theme.colors.textPrimary,
      cursor: 'pointer',
      border: `1px solid ${tutorial.currentModule === moduleId ? theme.colors.primary : theme.colors.border}`,
      transition: tutorial.reducedMotion ? 'none' : 'all 0.2s ease'
    }),

    moduleCardContent: {
      display: 'flex',
      flexDirection: 'column',
      gap: 4
    },

    moduleTitle: {
      fontSize: '1em',
      fontWeight: 600,
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    },

    moduleDescription: {
      fontSize: '0.9em',
      color: theme.colors.textSecondary,
      margin: 0
    },

    moduleStats: {
      display: 'flex',
      justifyContent: 'space-between',
      fontSize: '0.8em',
      color: theme.colors.textSecondary
    },

    contentHeader: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: theme.spacing,
      borderBottom: `1px solid ${theme.colors.border}`
    },

    contentTitle: {
      display: 'flex',
      flexDirection: 'column',
      gap: 4
    },

    moduleNavigation: {
      display: 'flex',
      gap: theme.spacing,
      alignItems: 'center'
    },

    navigationButton: (variant = 'primary') => ({
      padding: '8px 16px',
      borderRadius: 4,
      cursor: 'pointer',
      backgroundColor: variant === 'primary' ? theme.colors.primary : theme.colors.secondary,
      color: '#ffffff',
      border: 'none',
      fontSize: '0.9em',
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      opacity: 1,
      transition: tutorial.reducedMotion ? 'none' : 'opacity 0.2s ease'
    }),

    navigationButtonDisabled: {
      opacity: 0.5,
      cursor: 'not-allowed'
    },

    stepInfo: {
      fontSize: theme.typography.sm,
      color: theme.colors.textSecondary,
      fontWeight: theme.typography.medium
    },

    statusInfo: {
      padding: theme.spacing,
      display: 'flex',
      flexDirection: 'column',
      gap: 4,
      background: theme.colors.paper,
      borderBottom: `1px solid ${theme.colors.border}`
    },

    statusMetrics: {
      display: 'flex',
      gap: theme.spacing,
      flexWrap: 'wrap'
    },

    metric: {
      padding: '6px 12px',
      borderRadius: 999,
      background: theme.colors.primaryLight,
      color: theme.colors.primary
    },

    contentBody: {
      flex: 1,
      display: 'grid',
      gridTemplateColumns: tutorial.showSidebar ? '2fr 1fr' : '1fr',
      gap: theme.spacing,
      padding: theme.spacing,
      height: '100%',
      overflow: 'hidden'
    },

    hintsPanel: {
      background: theme.colors.paper,
      borderRadius: 12,
      padding: theme.spacing,
      border: `1px solid ${theme.colors.border}`,
      display: 'flex',
      flexDirection: 'column',
      gap: theme.spacing,
      height: '100%'
    },

    hintCard: {
      padding: '12px 16px',
      borderRadius: 8,
      background: theme.colors.primaryLight,
      color: theme.colors.primaryContrast,
      display: 'flex',
      flexDirection: 'column',
      gap: 8
    },

    hintTitle: {
      fontWeight: 600,
      fontSize: '0.95em'
    },

    hintContent: {
      fontSize: '0.85em',
      lineHeight: 1.4
    },

    tutorialOverlayTrigger: {
      position: 'fixed',
      bottom: theme.spacing,
      right: theme.spacing,
      padding: '12px 20px',
      borderRadius: 999,
      background: theme.colors.primary,
      color: '#ffffff',
      border: 'none',
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      boxShadow: theme.shadows.lg
    },

    welcomeScreen: {
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)',
      padding: '40px 16px'
    },

    welcomeCard: {
      maxWidth: 960,
      width: '100%',
      background: '#ffffff',
      borderRadius: 24,
      padding: '40px 48px',
      boxShadow: '0 30px 60px rgba(15, 32, 39, 0.2)',
      display: 'flex',
      flexDirection: 'column',
      gap: 24
    },

    welcomeTitle: {
      fontSize: isMobile ? '2em' : '2.5em',
      color: '#0f2027',
      margin: 0
    },

    welcomeContent: {
      display: 'grid',
      gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)',
      gap: 24
    },

    welcomeDescription: {
      fontSize: '1.1em',
      lineHeight: 1.6,
      color: '#334e68'
    },

    featureGrid: {
      display: 'grid',
      gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)',
      gap: 16
    },

    feature: {
      padding: '16px 20px',
      borderRadius: 16,
      background: '#f8fbff',
      border: '1px solid rgba(15, 32, 39, 0.1)',
      display: 'flex',
      flexDirection: 'column',
      gap: 8
    },

    featureIcon: {
      fontSize: '1.8em'
    },

    estimatedTime: {
      padding: '16px 24px',
      borderRadius: 12,
      background: '#eef7ff',
      color: '#0f2027'
    },

    welcomeActions: {
      display: 'flex',
      gap: 16,
      flexWrap: 'wrap'
    },

    primaryAction: {
      padding: '12px 24px',
      borderRadius: 999,
      background: '#0f2027',
      color: '#ffffff',
      border: 'none',
      fontSize: '1em',
      cursor: 'pointer',
      boxShadow: '0 12px 24px rgba(15, 32, 39, 0.2)'
    },

    secondaryAction: {
      padding: '12px 24px',
      borderRadius: 999,
      background: 'transparent',
      color: '#0f2027',
      border: '1px solid rgba(15, 32, 39, 0.2)',
      fontSize: '1em',
      cursor: 'pointer'
    },

    resumeAction: {
      padding: '12px 24px',
      borderRadius: 999,
      background: '#1b998b',
      color: '#ffffff',
      border: 'none',
      fontSize: '1em',
      cursor: 'pointer'
    },

    mobileSidebarToggle: {
      position: 'fixed',
      bottom: 16,
      left: '50%',
      transform: 'translateX(-50%)',
      padding: '12px 24px',
      borderRadius: 999,
      background: theme.colors.primary,
      color: '#ffffff',
      border: 'none',
      display: isMobile ? 'flex' : 'none',
      alignItems: 'center',
      gap: 8,
      boxShadow: theme.shadows.lg,
      zIndex: 200
    },

    loading: {
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#f5f7fa',
      color: '#0f2027',
      fontSize: '1.2em'
    },

    error: {
      padding: theme.spacing,
      background: '#ffebee',
      color: '#c62828',
      borderRadius: 8,
      marginBottom: theme.spacing
    },

    preferencesPanel: {
      display: 'flex',
      gap: theme.spacing,
      flexWrap: 'wrap'
    },

    preferenceToggle: {
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  };

  const modules = Array.isArray(tutorial.modules) ? tutorial.modules : [];
  const currentModuleIndex = modules.findIndex((module) => module.id === tutorial.currentModule);
  const isFirstModule = currentModuleIndex <= 0;
  const isLastModule = modules.length === 0 || currentModuleIndex === modules.length - 1;
  const modulePosition = currentModuleIndex >= 0 ? currentModuleIndex + 1 : 0;
  const totalModules = modules.length;

  // Keyboard navigation
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (!tutorial.isActive) return;
      
      switch (e.key) {
        case 'ArrowLeft':
          if (e.ctrlKey) tutorial.previousModule();
          else tutorial.previousStep();
          break;
        case 'ArrowRight':
          if (e.ctrlKey) tutorial.nextModule();
          else tutorial.nextStep();
          break;
        case 'Escape':
          if (tutorial.overlayVisible) tutorial.toggleOverlay();
          break;
        case 'h':
          if (e.ctrlKey) tutorial.toggleHints();
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    const previousKeyDown = window.onkeydown;
    window.onkeydown = handleKeyPress;
    return () => {
      window.removeEventListener('keydown', handleKeyPress);
      if (window.onkeydown === handleKeyPress) {
        window.onkeydown = previousKeyDown || null;
      }
    };
  }, [tutorial]);

  // Welcome screen component
  const WelcomeScreen = () => (
    <div style={styles.welcomeScreen}>
      <div style={styles.welcomeCard}>
        <h1 style={styles.welcomeTitle}>Welcome to Wolf Goat Pig Tutorial</h1>
        
        <div style={styles.welcomeContent}>
          <p style={styles.welcomeDescription}>
            Master the exciting world of Wolf Goat Pig golf betting with our comprehensive 
            interactive tutorial. Learn at your own pace with adaptive content and personalized guidance.
          </p>
          
          <div style={styles.featureGrid}>
            <div style={styles.feature}>
              <div style={styles.featureIcon}>🎯</div>
              <h3>Interactive Learning</h3>
              <p>Hands-on demonstrations and practice scenarios</p>
            </div>
            <div style={styles.feature}>
              <div style={styles.featureIcon}>📊</div>
              <h3>Progress Tracking</h3>
              <p>Monitor your learning progress and achievements</p>
            </div>
            <div style={styles.feature}>
              <div style={styles.featureIcon}>🎮</div>
              <h3>Guided Practice</h3>
              <p>Play your first game with contextual help</p>
            </div>
            <div style={styles.feature}>
              <div style={styles.featureIcon}>♿</div>
              <h3>Accessibility</h3>
              <p>Full keyboard navigation and screen reader support</p>
            </div>
          </div>

          <div style={styles.estimatedTime}>
            <strong>Estimated Time:</strong> 45-75 minutes total
          </div>
          
          <div style={styles.welcomeActions}>
            <button 
              style={styles.startButton}
              onClick={() => {
                setShowWelcome(false);
                tutorial.startTutorial();
              }}
            >
              Start Tutorial
            </button>
            
            <button 
              style={styles.resumeButton}
              onClick={() => {
                const savedProgress = progress.resumeFromSaved();
                if (savedProgress) {
                  setShowWelcome(false);
                  tutorial.startTutorial(savedProgress.lastModule);
                }
              }}
              disabled={!progress.loadProgress()}
            >
              Resume Previous Session
            </button>
            
            <button 
              style={styles.skipButton}
              onClick={() => onExit && onExit()}
            >
              Skip Tutorial
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // Get current module component
  const getCurrentModuleComponent = () => {
    if (!tutorial.currentModule) return null;

    const ModuleComponent = MODULE_COMPONENTS[tutorial.currentModule];
    if (!ModuleComponent) {
      return <div style={styles.error}>Module not found: {tutorial.currentModule}</div>;
    }

    return (
      <ModuleComponent
        onStepComplete={progress.completeCurrentStep}
        onModuleComplete={progress.completeCurrentModule}
        currentStep={tutorial.currentStep}
        goToStep={tutorial.goToStep}
      />
    );
  };

  if (showWelcome) {
    return <WelcomeScreen />;
  }

  if (!tutorial.isActive) {
    return <div style={styles.loading}>Initializing tutorial...</div>;
  }
  return (
    <div 
      style={styles.container}
      role="application"
      aria-label="Wolf Goat Pig Tutorial System"
    >
      {/* Sidebar with progress and navigation */}
      <div 
        style={styles.sidebar}
        role="complementary"
        aria-label="Tutorial progress and navigation"
      >
        <div style={styles.header}>
          <h2 style={styles.headerTitle}>
            {tutorial.sidebarCollapsed ? 'WGP' : 'Tutorial Progress'}
          </h2>
          <div style={styles.headerActions}>
            <button 
              style={styles.headerButton}
              onClick={() => {
                if (isMobile) {
                  setShowMobileSidebar(!showMobileSidebar);
                } else {
                  tutorial.toggleSidebar();
                }
              }}
              title={isMobile ? "Toggle progress" : "Toggle sidebar"}
            >
              {isMobile 
                ? (showMobileSidebar ? '▼' : '▲') 
                : (tutorial.sidebarCollapsed ? '→' : '←')
              }
            </button>
            <button 
              style={styles.headerButton}
              onClick={tutorial.toggleHints}
              title="Toggle hints"
            >
              {tutorial.showHints ? '💡' : '💡'}
            </button>
            <button 
              style={styles.headerButton}
              onClick={() => onExit && onExit()}
              title="Exit tutorial"
            >
              ✕
            </button>
          </div>
        </div>
        
        {(isMobile ? showMobileSidebar : !tutorial.sidebarCollapsed) && (
          <ProgressTracker />
        )}
      </div>

      {/* Main content area */}
      <div 
        style={styles.mainContent}
        role="main"
        aria-label="Tutorial content"
        aria-live="polite"
        aria-atomic="false"
      >
        <div 
          style={styles.moduleContainer}
        >
          {getCurrentModuleComponent()}
        </div>
        
        {/* Navigation controls */}
        <nav 
          style={styles.navigation}
          role="navigation"
          aria-label="Tutorial module navigation"
        >
          <button 
            style={{
              ...styles.navigationButton('secondary'),
              ...(isFirstModule ? styles.navigationButtonDisabled : {})
            }}
            onClick={tutorial.previousModule}
            disabled={isFirstModule}
            aria-label="Go to previous module"
          >
            ← Previous Module
          </button>
          
          <div 
            style={styles.stepInfo}
            role="status"
            aria-live="polite"
          >
            Module {modulePosition} of {totalModules}
          </div>
          
          <button 
            style={{
              ...styles.navigationButton('primary'),
              ...(isLastModule ? styles.navigationButtonDisabled : {})
            }}
            onClick={tutorial.nextModule}
            disabled={isLastModule}
            aria-label="Go to next module"
          >
            Next Module →
          </button>
        </nav>
      </div>

      {/* Tutorial overlay for contextual guidance */}
      {tutorial.overlayVisible && <TutorialOverlay />}
    </div>
  );
};

export default TutorialSystem;
