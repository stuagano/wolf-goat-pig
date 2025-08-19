import React, { createContext, useContext, useReducer, useCallback } from 'react';

// Tutorial Context
const TutorialContext = createContext();

// Tutorial modules configuration
export const TUTORIAL_MODULES = [
  {
    id: 'golf-basics',
    title: 'Basic Golf Concepts & Scoring',
    duration: 5,
    description: 'Learn fundamental golf terminology, scoring, and handicap systems',
    requiredForNext: true
  },
  {
    id: 'game-overview',
    title: 'Wolf Goat Pig Overview & Objectives',
    duration: 10,
    description: 'Understand the core game mechanics and winning conditions',
    requiredForNext: true
  },
  {
    id: 'team-formation',
    title: 'Team Formation & Partnership Rules',
    duration: 15,
    description: 'Master team selection, partner dynamics, and role assignments',
    requiredForNext: true
  },
  {
    id: 'betting-system',
    title: 'Betting System & Wager Types',
    duration: 20,
    description: 'Learn betting mechanics, odds calculation, and risk management',
    requiredForNext: true
  },
  {
    id: 'advanced-rules',
    title: 'Special Rules & Advanced Strategies',
    duration: 15,
    description: 'Explore complex scenarios, edge cases, and strategic considerations',
    requiredForNext: false
  },
  {
    id: 'analysis-tools',
    title: 'Shot-by-Shot Mode & Analysis Tools',
    duration: 10,
    description: 'Utilize statistical analysis and performance tracking features',
    requiredForNext: false
  },
  {
    id: 'practice-game',
    title: 'Practice Game with Guidance',
    duration: 30,
    description: 'Play your first guided game with contextual hints and feedback',
    requiredForNext: false
  }
];

// Initial tutorial state
const initialTutorialState = {
  // Current tutorial session
  isActive: false,
  currentModule: null,
  currentStep: 0,
  
  // Progress tracking
  completedModules: new Set(),
  completedSteps: {},
  startTime: null,
  timeSpent: {},
  
  // User preferences and adaptations
  learningPreferences: {
    visualLearner: true,
    auditoryLearner: false,
    kinestheticLearner: true,
    skipBasics: false,
    pace: 'normal' // 'slow', 'normal', 'fast'
  },
  
  // Adaptive learning
  comprehensionScores: {},
  difficultTopics: new Set(),
  needsReinforcement: new Set(),
  
  // Interactive state
  quizAnswers: {},
  practiceResults: {},
  achievements: new Set(),
  
  // UI state
  showHints: true,
  overlayVisible: false,
  sidebarCollapsed: false,
  
  // Accessibility
  highContrast: false,
  largeText: false,
  reducedMotion: false,
  screenReaderMode: false,
  
  // Error and loading states
  loading: false,
  error: null,
  
  // Tutorial completion
  completed: false,
  completionTime: null,
  finalScore: null
};

// Tutorial action types
const TutorialActions = {
  // Session control
  START_TUTORIAL: 'START_TUTORIAL',
  END_TUTORIAL: 'END_TUTORIAL',
  PAUSE_TUTORIAL: 'PAUSE_TUTORIAL',
  RESUME_TUTORIAL: 'RESUME_TUTORIAL',
  
  // Navigation
  SET_CURRENT_MODULE: 'SET_CURRENT_MODULE',
  SET_CURRENT_STEP: 'SET_CURRENT_STEP',
  NEXT_MODULE: 'NEXT_MODULE',
  PREVIOUS_MODULE: 'PREVIOUS_MODULE',
  NEXT_STEP: 'NEXT_STEP',
  PREVIOUS_STEP: 'PREVIOUS_STEP',
  
  // Progress tracking
  COMPLETE_MODULE: 'COMPLETE_MODULE',
  COMPLETE_STEP: 'COMPLETE_STEP',
  UPDATE_TIME_SPENT: 'UPDATE_TIME_SPENT',
  
  // Learning preferences
  UPDATE_PREFERENCES: 'UPDATE_PREFERENCES',
  SET_LEARNING_PACE: 'SET_LEARNING_PACE',
  
  // Adaptive learning
  UPDATE_COMPREHENSION_SCORE: 'UPDATE_COMPREHENSION_SCORE',
  ADD_DIFFICULT_TOPIC: 'ADD_DIFFICULT_TOPIC',
  MARK_FOR_REINFORCEMENT: 'MARK_FOR_REINFORCEMENT',
  
  // Interactive elements
  SUBMIT_QUIZ_ANSWER: 'SUBMIT_QUIZ_ANSWER',
  RECORD_PRACTICE_RESULT: 'RECORD_PRACTICE_RESULT',
  UNLOCK_ACHIEVEMENT: 'UNLOCK_ACHIEVEMENT',
  
  // UI state
  TOGGLE_HINTS: 'TOGGLE_HINTS',
  TOGGLE_OVERLAY: 'TOGGLE_OVERLAY',
  TOGGLE_SIDEBAR: 'TOGGLE_SIDEBAR',
  
  // Accessibility
  TOGGLE_HIGH_CONTRAST: 'TOGGLE_HIGH_CONTRAST',
  TOGGLE_LARGE_TEXT: 'TOGGLE_LARGE_TEXT',
  TOGGLE_REDUCED_MOTION: 'TOGGLE_REDUCED_MOTION',
  TOGGLE_SCREEN_READER: 'TOGGLE_SCREEN_READER',
  
  // Error handling
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
  
  // Completion
  COMPLETE_TUTORIAL: 'COMPLETE_TUTORIAL',
  RESET_TUTORIAL: 'RESET_TUTORIAL'
};

// Tutorial reducer
const tutorialReducer = (state, action) => {
  switch (action.type) {
    case TutorialActions.START_TUTORIAL:
      return {
        ...state,
        isActive: true,
        currentModule: action.payload?.startModule || TUTORIAL_MODULES[0].id,
        currentStep: 0,
        startTime: new Date().toISOString(),
        error: null
      };
      
    case TutorialActions.END_TUTORIAL:
      return {
        ...state,
        isActive: false,
        currentModule: null,
        currentStep: 0,
        overlayVisible: false
      };
      
    case TutorialActions.SET_CURRENT_MODULE:
      return {
        ...state,
        currentModule: action.payload,
        currentStep: 0
      };
      
    case TutorialActions.SET_CURRENT_STEP:
      return {
        ...state,
        currentStep: action.payload
      };
      
    case TutorialActions.NEXT_MODULE: {
      const currentIndex = TUTORIAL_MODULES.findIndex(m => m.id === state.currentModule);
      const nextModule = TUTORIAL_MODULES[currentIndex + 1];
      return {
        ...state,
        currentModule: nextModule ? nextModule.id : state.currentModule,
        currentStep: 0
      };
    }
    
    case TutorialActions.PREVIOUS_MODULE: {
      const currentIndex = TUTORIAL_MODULES.findIndex(m => m.id === state.currentModule);
      const prevModule = TUTORIAL_MODULES[currentIndex - 1];
      return {
        ...state,
        currentModule: prevModule ? prevModule.id : state.currentModule,
        currentStep: 0
      };
    }
    
    case TutorialActions.NEXT_STEP:
      return {
        ...state,
        currentStep: state.currentStep + 1
      };
      
    case TutorialActions.PREVIOUS_STEP:
      return {
        ...state,
        currentStep: Math.max(0, state.currentStep - 1)
      };
      
    case TutorialActions.COMPLETE_MODULE: {
      const newCompleted = new Set(state.completedModules);
      newCompleted.add(action.payload);
      return {
        ...state,
        completedModules: newCompleted
      };
    }
    
    case TutorialActions.COMPLETE_STEP: {
      const { moduleId, stepIndex } = action.payload;
      return {
        ...state,
        completedSteps: {
          ...state.completedSteps,
          [`${moduleId}-${stepIndex}`]: true
        }
      };
    }
    
    case TutorialActions.UPDATE_TIME_SPENT: {
      const { moduleId, timeSpent } = action.payload;
      return {
        ...state,
        timeSpent: {
          ...state.timeSpent,
          [moduleId]: (state.timeSpent[moduleId] || 0) + timeSpent
        }
      };
    }
    
    case TutorialActions.UPDATE_PREFERENCES:
      return {
        ...state,
        learningPreferences: {
          ...state.learningPreferences,
          ...action.payload
        }
      };
      
    case TutorialActions.UPDATE_COMPREHENSION_SCORE: {
      const { moduleId, score } = action.payload;
      return {
        ...state,
        comprehensionScores: {
          ...state.comprehensionScores,
          [moduleId]: score
        }
      };
    }
    
    case TutorialActions.ADD_DIFFICULT_TOPIC: {
      const newDifficult = new Set(state.difficultTopics);
      newDifficult.add(action.payload);
      return {
        ...state,
        difficultTopics: newDifficult
      };
    }
    
    case TutorialActions.SUBMIT_QUIZ_ANSWER: {
      const { questionId, answer, correct } = action.payload;
      return {
        ...state,
        quizAnswers: {
          ...state.quizAnswers,
          [questionId]: { answer, correct, timestamp: new Date().toISOString() }
        }
      };
    }
    
    case TutorialActions.UNLOCK_ACHIEVEMENT: {
      const newAchievements = new Set(state.achievements);
      newAchievements.add(action.payload);
      return {
        ...state,
        achievements: newAchievements
      };
    }
    
    case TutorialActions.TOGGLE_HINTS:
      return {
        ...state,
        showHints: !state.showHints
      };
      
    case TutorialActions.TOGGLE_OVERLAY:
      return {
        ...state,
        overlayVisible: !state.overlayVisible
      };
      
    case TutorialActions.TOGGLE_HIGH_CONTRAST:
      return {
        ...state,
        highContrast: !state.highContrast
      };
      
    case TutorialActions.TOGGLE_LARGE_TEXT:
      return {
        ...state,
        largeText: !state.largeText
      };
      
    case TutorialActions.TOGGLE_REDUCED_MOTION:
      return {
        ...state,
        reducedMotion: !state.reducedMotion
      };
      
    case TutorialActions.SET_LOADING:
      return {
        ...state,
        loading: action.payload
      };
      
    case TutorialActions.SET_ERROR:
      return {
        ...state,
        error: action.payload,
        loading: false
      };
      
    case TutorialActions.CLEAR_ERROR:
      return {
        ...state,
        error: null
      };
      
    case TutorialActions.COMPLETE_TUTORIAL:
      return {
        ...state,
        completed: true,
        completionTime: new Date().toISOString(),
        finalScore: action.payload,
        isActive: false
      };
      
    case TutorialActions.RESET_TUTORIAL:
      return {
        ...initialTutorialState,
        learningPreferences: state.learningPreferences,
        highContrast: state.highContrast,
        largeText: state.largeText,
        reducedMotion: state.reducedMotion
      };
      
    default:
      return state;
  }
};

// Tutorial Provider Component
export const TutorialProvider = ({ children }) => {
  const [state, dispatch] = useReducer(tutorialReducer, initialTutorialState);

  // Progress calculation utilities
  const getModuleProgress = useCallback((moduleId) => {
    if (state.completedModules.has(moduleId)) return 100;
    
    const moduleSteps = Object.keys(state.completedSteps)
      .filter(key => key.startsWith(`${moduleId}-`));
    
    // Estimate steps based on module duration (rough approximation)
    const estimatedSteps = Math.ceil(TUTORIAL_MODULES.find(m => m.id === moduleId)?.duration / 2) || 5;
    return Math.round((moduleSteps.length / estimatedSteps) * 100);
  }, [state.completedModules, state.completedSteps]);

  const getOverallProgress = useCallback(() => {
    const totalModules = TUTORIAL_MODULES.length;
    const completedCount = state.completedModules.size;
    return Math.round((completedCount / totalModules) * 100);
  }, [state.completedModules]);

  const getCurrentModule = useCallback(() => {
    return TUTORIAL_MODULES.find(m => m.id === state.currentModule);
  }, [state.currentModule]);

  const canAdvanceToModule = useCallback((moduleId) => {
    const module = TUTORIAL_MODULES.find(m => m.id === moduleId);
    if (!module) return false;
    
    const moduleIndex = TUTORIAL_MODULES.indexOf(module);
    if (moduleIndex === 0) return true;
    
    // Check if all required previous modules are completed
    for (let i = 0; i < moduleIndex; i++) {
      const prevModule = TUTORIAL_MODULES[i];
      if (prevModule.requiredForNext && !state.completedModules.has(prevModule.id)) {
        return false;
      }
    }
    return true;
  }, [state.completedModules]);

  // Action creators
  const actions = {
    // Session control
    startTutorial: (startModule) => dispatch({ type: TutorialActions.START_TUTORIAL, payload: { startModule } }),
    endTutorial: () => dispatch({ type: TutorialActions.END_TUTORIAL }),
    pauseTutorial: () => dispatch({ type: TutorialActions.PAUSE_TUTORIAL }),
    resumeTutorial: () => dispatch({ type: TutorialActions.RESUME_TUTORIAL }),
    
    // Navigation
    goToModule: (moduleId) => {
      if (canAdvanceToModule(moduleId)) {
        dispatch({ type: TutorialActions.SET_CURRENT_MODULE, payload: moduleId });
      }
    },
    goToStep: (stepIndex) => dispatch({ type: TutorialActions.SET_CURRENT_STEP, payload: stepIndex }),
    nextModule: () => dispatch({ type: TutorialActions.NEXT_MODULE }),
    previousModule: () => dispatch({ type: TutorialActions.PREVIOUS_MODULE }),
    nextStep: () => dispatch({ type: TutorialActions.NEXT_STEP }),
    previousStep: () => dispatch({ type: TutorialActions.PREVIOUS_STEP }),
    
    // Progress tracking
    completeModule: (moduleId) => dispatch({ type: TutorialActions.COMPLETE_MODULE, payload: moduleId }),
    completeStep: (moduleId, stepIndex) => dispatch({ 
      type: TutorialActions.COMPLETE_STEP, 
      payload: { moduleId, stepIndex } 
    }),
    updateTimeSpent: (moduleId, timeSpent) => dispatch({ 
      type: TutorialActions.UPDATE_TIME_SPENT, 
      payload: { moduleId, timeSpent } 
    }),
    
    // Learning adaptation
    updatePreferences: (preferences) => dispatch({ type: TutorialActions.UPDATE_PREFERENCES, payload: preferences }),
    updateComprehensionScore: (moduleId, score) => dispatch({ 
      type: TutorialActions.UPDATE_COMPREHENSION_SCORE, 
      payload: { moduleId, score } 
    }),
    markDifficultTopic: (topic) => dispatch({ type: TutorialActions.ADD_DIFFICULT_TOPIC, payload: topic }),
    
    // Interactive elements
    submitQuizAnswer: (questionId, answer, correct) => dispatch({ 
      type: TutorialActions.SUBMIT_QUIZ_ANSWER, 
      payload: { questionId, answer, correct } 
    }),
    unlockAchievement: (achievement) => dispatch({ type: TutorialActions.UNLOCK_ACHIEVEMENT, payload: achievement }),
    
    // UI controls
    toggleHints: () => dispatch({ type: TutorialActions.TOGGLE_HINTS }),
    toggleOverlay: () => dispatch({ type: TutorialActions.TOGGLE_OVERLAY }),
    toggleHighContrast: () => dispatch({ type: TutorialActions.TOGGLE_HIGH_CONTRAST }),
    toggleLargeText: () => dispatch({ type: TutorialActions.TOGGLE_LARGE_TEXT }),
    toggleReducedMotion: () => dispatch({ type: TutorialActions.TOGGLE_REDUCED_MOTION }),
    
    // Error handling
    setError: (error) => dispatch({ type: TutorialActions.SET_ERROR, payload: error }),
    clearError: () => dispatch({ type: TutorialActions.CLEAR_ERROR }),
    
    // Completion
    completeTutorial: (finalScore) => dispatch({ type: TutorialActions.COMPLETE_TUTORIAL, payload: finalScore }),
    resetTutorial: () => dispatch({ type: TutorialActions.RESET_TUTORIAL })
  };

  const value = {
    ...state,
    ...actions,
    
    // Computed values
    modules: TUTORIAL_MODULES,
    currentModuleData: getCurrentModule(),
    overallProgress: getOverallProgress(),
    getModuleProgress,
    canAdvanceToModule,
    
    // Raw dispatch for advanced use cases
    dispatch
  };

  return (
    <TutorialContext.Provider value={value}>
      {children}
    </TutorialContext.Provider>
  );
};

// Custom hook to use tutorial context
export const useTutorial = () => {
  const context = useContext(TutorialContext);
  if (!context) {
    throw new Error('useTutorial must be used within a TutorialProvider');
  }
  return context;
};

export { TutorialActions };
export default TutorialProvider;