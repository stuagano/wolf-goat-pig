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
    return () => window.removeEventListener('keydown', handleKeyPress);
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
      WebkitOverflowScrolling: 'touch' // Smooth scrolling on iOS
    },
    
    header: {
      padding: theme.spacing,
      background: theme.colors.primary,
      color: '#ffffff',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    },
    
    headerTitle: {
      margin: 0,
      fontSize: theme.typography.xl,
      fontWeight: theme.typography.semibold
    },
    
    headerActions: {
      display: 'flex',
      gap: theme.spacing
    },
    
    headerButton: {
      background: 'rgba(255, 255, 255, 0.2)',
      color: '#ffffff',
      border: 'none',
      borderRadius: theme.borderRadius.base,
      padding: `${theme.spacing[2]} ${theme.spacing[3]}`,
      cursor: 'pointer',
      fontSize: theme.typography.sm,
      transition: tutorial.reducedMotion ? 'none' : 'background-color 0.2s ease'
    },
    
    navigation: {
      padding: isMobile ? theme.spacing : theme.spacing,
      borderTop: `1px solid ${theme.colors.border}`,
      background: theme.colors.gray50,
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      flexWrap: isMobile ? 'wrap' : 'nowrap',
      gap: isMobile ? theme.spacing : 0
    },
    
    navButton: {
      ...theme.buttonStyle,
      fontSize: theme.typography.sm,
      padding: `${theme.spacing[2]} ${theme.spacing[4]}`
    },
    
    navButtonDisabled: {
      ...theme.buttonStyle,
      fontSize: theme.typography.sm,
      padding: `${theme.spacing[2]} ${theme.spacing[4]}`,
      backgroundColor: theme.colors.gray300,
      color: theme.colors.gray500,
      cursor: 'not-allowed'
    },
    
    stepInfo: {
      fontSize: theme.typography.sm,
      color: theme.colors.textSecondary,
      fontWeight: theme.typography.medium
    },
    
    // Welcome screen styles
    welcomeScreen: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: theme.colors.background,
      padding: theme.spacing
    },
    
    welcomeCard: {
      ...theme.cardStyle,
      maxWidth: 800,
      padding: theme.spacing,
      textAlign: 'center'
    },
    
    welcomeTitle: {
      fontSize: theme.typography['3xl'],
      color: theme.colors.primary,
      marginBottom: theme.spacing,
      fontWeight: theme.typography.bold
    },
    
    welcomeDescription: {
      fontSize: theme.typography.lg,
      lineHeight: 1.6,
      marginBottom: theme.spacing,
      color: theme.colors.textSecondary
    },
    
    featureGrid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
      gap: theme.spacing,
      marginBottom: theme.spacing
    },
    
    feature: {
      textAlign: 'center'
    },
    
    featureIcon: {
      fontSize: '2.5rem',
      marginBottom: theme.spacing
    },
    
    estimatedTime: {
      background: theme.colors.gray100,
      padding: theme.spacing,
      borderRadius: theme.borderRadius.base,
      marginBottom: theme.spacing,
      fontSize: theme.typography.base
    },
    
    welcomeActions: {
      display: 'flex',
      gap: theme.spacing,
      justifyContent: 'center',
      flexWrap: 'wrap'
    },
    
    startButton: {
      ...theme.buttonStyle,
      fontSize: theme.typography.lg,
      padding: `${theme.spacing[4]} ${theme.spacing[8]}`,
      backgroundColor: theme.colors.success
    },
    
    resumeButton: {
      ...theme.buttonStyle,
      fontSize: theme.typography.lg,
      padding: `${theme.spacing[4]} ${theme.spacing[8]}`,
      backgroundColor: theme.colors.accent
    },
    
    skipButton: {
      ...theme.buttonStyle,
      fontSize: theme.typography.lg,
      padding: `${theme.spacing[4]} ${theme.spacing[8]}`,
      backgroundColor: theme.colors.gray400
    },
    
    // Preferences setup styles
    preferencesSetup: {
      padding: theme.spacing
    },
    
    preferenceGroup: {
      marginBottom: theme.spacing
    },
    
    checkboxLabel: {
      display: 'block',
      marginBottom: theme.spacing,
      cursor: 'pointer'
    },
    
    select: {
      ...theme.inputStyle,
      width: 'auto'
    },
    
    loading: {
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      fontSize: theme.typography.xl
    },
    
    error: {
      padding: theme.spacing,
      color: theme.colors.error,
      textAlign: 'center',
      fontSize: theme.typography.lg
    }
  };

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
      >
        <div 
          style={styles.moduleContainer}
          aria-live="polite"
          aria-atomic="false"
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
            style={tutorial.currentModule === tutorial.modules?.id ? styles.navButtonDisabled : styles.navButton}
            onClick={tutorial.previousModule}
            disabled={tutorial.currentModule === tutorial.modules?.id}
            aria-label="Go to previous module"
          >
            ← Previous Module
          </button>
          
          <div 
            style={styles.stepInfo}
            role="status"
            aria-live="polite"
          >
            Module {tutorial.modules.findIndex(m => m.id === tutorial.currentModule) + 1} of {tutorial.modules.length}
          </div>
          
          <button 
            style={tutorial.currentModule === tutorial.modules[tutorial.modules.length - 1]?.id ? styles.navButtonDisabled : styles.navButton}
            onClick={tutorial.nextModule}
            disabled={tutorial.currentModule === tutorial.modules[tutorial.modules.length - 1]?.id}
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