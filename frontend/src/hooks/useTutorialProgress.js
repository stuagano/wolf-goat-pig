import { useState, useEffect, useCallback } from 'react';
import { useTutorial } from '../context/TutorialContext';

/**
 * Advanced tutorial progress tracking hook
 * Provides time tracking, persistence, analytics, and adaptive learning
 */
export const useTutorialProgress = () => {
  const tutorial = useTutorial();
  const [sessionStartTime, setSessionStartTime] = useState(null);
  const [stepStartTime, setStepStartTime] = useState(null);
  const [persistenceEnabled, setPersistenceEnabled] = useState(true);

  // Initialize session timing
  useEffect(() => {
    if (tutorial.isActive && !sessionStartTime) {
      setSessionStartTime(Date.now());
    }
  }, [tutorial.isActive, sessionStartTime]);

  // Track step timing
  useEffect(() => {
    if (tutorial.isActive) {
      setStepStartTime(Date.now());
    }
  }, [tutorial.currentModule, tutorial.currentStep, tutorial.isActive]);

  // Save progress to localStorage
  const saveProgress = useCallback(() => {
    if (!persistenceEnabled) return;
    
    try {
      const progressData = {
        completedModules: Array.from(tutorial.completedModules),
        completedSteps: tutorial.completedSteps,
        timeSpent: tutorial.timeSpent,
        learningPreferences: tutorial.learningPreferences,
        comprehensionScores: tutorial.comprehensionScores,
        difficultTopics: Array.from(tutorial.difficultTopics),
        achievements: Array.from(tutorial.achievements),
        quizAnswers: tutorial.quizAnswers,
        lastModule: tutorial.currentModule,
        lastStep: tutorial.currentStep,
        lastSaved: new Date().toISOString()
      };
      
      localStorage.setItem('wgp-tutorial-progress', JSON.stringify(progressData));
    } catch (error) {
      console.warn('Failed to save tutorial progress:', error);
    }
  }, [tutorial, persistenceEnabled]);

  // Load progress from localStorage
  const loadProgress = useCallback(() => {
    if (!persistenceEnabled) return null;
    
    try {
      const savedData = localStorage.getItem('wgp-tutorial-progress');
      if (savedData) {
        return JSON.parse(savedData);
      }
    } catch (error) {
      console.warn('Failed to load tutorial progress:', error);
    }
    return null;
  }, [persistenceEnabled]);

  // Clear saved progress
  const clearSavedProgress = useCallback(() => {
    try {
      localStorage.removeItem('wgp-tutorial-progress');
    } catch (error) {
      console.warn('Failed to clear tutorial progress:', error);
    }
  }, []);

  // Auto-save progress on changes
  useEffect(() => {
    const timeoutId = setTimeout(saveProgress, 1000); // Debounce saves
    return () => clearTimeout(timeoutId);
  }, [
    tutorial.completedModules,
    tutorial.completedSteps,
    tutorial.timeSpent,
    tutorial.comprehensionScores,
    tutorial.currentModule,
    tutorial.currentStep,
    saveProgress
  ]);

  // Calculate time spent on current step
  const getCurrentStepTime = useCallback(() => {
    if (!stepStartTime) return 0;
    return Math.floor((Date.now() - stepStartTime) / 1000);
  }, [stepStartTime]);

  // Calculate total session time
  const getSessionTime = useCallback(() => {
    if (!sessionStartTime) return 0;
    return Math.floor((Date.now() - sessionStartTime) / 1000);
  }, [sessionStartTime]);

  const checkForAchievements = useCallback((stepTime) => {
    const achievements = [];

    if (stepTime < 30 && !tutorial.achievements.has('speed-learner')) {
      achievements.push('speed-learner');
    }

    const progress = tutorial.overallProgress;
    if (progress >= 25 && !tutorial.achievements.has('quarter-complete')) {
      achievements.push('quarter-complete');
    }
    if (progress >= 50 && !tutorial.achievements.has('halfway-hero')) {
      achievements.push('halfway-hero');
    }
    if (progress >= 75 && !tutorial.achievements.has('almost-expert')) {
      achievements.push('almost-expert');
    }
    if (progress >= 100 && !tutorial.achievements.has('wgp-master')) {
      achievements.push('wgp-master');
    }

    const quizAnswers = Object.values(tutorial.quizAnswers);
    const quizCorrect = quizAnswers.filter(a => a.correct).length;
    if (quizAnswers.length >= 5 && quizCorrect / quizAnswers.length >= 0.9 && !tutorial.achievements.has('quiz-ace')) {
      achievements.push('quiz-ace');
    }

    achievements.forEach(achievement => {
      tutorial.unlockAchievement(achievement);
    });

    return achievements;
  }, [tutorial]);

  const checkModuleAchievements = useCallback(() => {
    const completedCount = tutorial.completedModules.size;
    const achievements = [];

    if (completedCount === 1 && !tutorial.achievements.has('first-steps')) {
      achievements.push('first-steps');
    }

    if (completedCount === tutorial.modules.length && !tutorial.achievements.has('completionist')) {
      achievements.push('completionist');
    }

    achievements.forEach(achievement => {
      tutorial.unlockAchievement(achievement);
    });
  }, [tutorial]);

  // Complete current step with time tracking
  const completeCurrentStep = useCallback(() => {
    const timeSpent = getCurrentStepTime();
    tutorial.completeStep(tutorial.currentModule, tutorial.currentStep);
    tutorial.updateTimeSpent(tutorial.currentModule, timeSpent);
    
    // Trigger achievement checks
    checkForAchievements(timeSpent);
  }, [tutorial, getCurrentStepTime, checkForAchievements]); // Added checkForAchievements

  // Complete current module with validation
  const completeCurrentModule = useCallback(() => {
    if (!tutorial.currentModule) return false;
    
    tutorial.completeModule(tutorial.currentModule);
    
    // Calculate module completion score
    const moduleTimeSpent = tutorial.timeSpent[tutorial.currentModule] || 0;
    const expectedTime = tutorial.currentModuleData?.duration * 60; // Convert to seconds
    const efficiencyScore = expectedTime > 0 ? Math.max(0, 100 - ((moduleTimeSpent - expectedTime) / expectedTime) * 50) : 100;
    
    tutorial.updateComprehensionScore(tutorial.currentModule, Math.round(efficiencyScore));
    
    // Check for module-based achievements
    checkModuleAchievements();
    
    return true;
  }, [tutorial, checkModuleAchievements]); // Added checkModuleAchievements

  // Adaptive learning recommendations
  const getRecommendations = useCallback(() => {
    const recommendations = [];
    
    // Check for difficult topics
    if (tutorial.difficultTopics.size > 0) {
      recommendations.push({
        type: 'review',
        priority: 'high',
        message: 'Consider reviewing topics you found challenging',
        topics: Array.from(tutorial.difficultTopics)
      });
    }
    
    // Check comprehension scores
    const lowScoreModules = Object.entries(tutorial.comprehensionScores)
      .filter(([_, score]) => score < 70)
      .map(([moduleId, _]) => moduleId);
    
    if (lowScoreModules.length > 0) {
      recommendations.push({
        type: 'practice',
        priority: 'medium',
        message: 'Additional practice recommended for these modules',
        modules: lowScoreModules
      });
    }
    
    // Check learning pace
    const sessionTime = getSessionTime();
    const expectedSessionTime = tutorial.modules
      .filter(m => tutorial.completedModules.has(m.id))
      .reduce((total, m) => total + (m.duration * 60), 0);
    
    if (sessionTime > expectedSessionTime * 1.5) {
      recommendations.push({
        type: 'pace',
        priority: 'low',
        message: 'Consider taking breaks to maintain focus',
        suggestion: 'break'
      });
    }
    
    return recommendations;
  }, [tutorial, getSessionTime]);

  // Progress analytics
  const calculateLearningEfficiency = useCallback(() => {
    const completedModules = Array.from(tutorial.completedModules);
    if (completedModules.length === 0) return 0;

    const totalExpectedTime = completedModules
      .map(moduleId => tutorial.modules.find(m => m.id === moduleId)?.duration || 0)
      .reduce((sum, duration) => sum + duration * 60, 0);

    const totalActualTime = completedModules
      .reduce((sum, moduleId) => sum + (tutorial.timeSpent[moduleId] || 0), 0);

    if (totalActualTime === 0) return 100;
    return Math.max(0, Math.min(100, (totalExpectedTime / totalActualTime) * 100));
  }, [tutorial]);

  const getAnalytics = useCallback(() => {
    return {
      sessionTime: getSessionTime(),
      completionRate: tutorial.overallProgress,
      averageModuleTime: Object.values(tutorial.timeSpent).reduce((sum, time) => sum + time, 0) / Math.max(1, Object.keys(tutorial.timeSpent).length),
      quizAccuracy: Object.values(tutorial.quizAnswers).length > 0
        ? Object.values(tutorial.quizAnswers).filter(a => a.correct).length / Object.values(tutorial.quizAnswers).length
        : 0,
      achievementCount: tutorial.achievements.size,
      difficultTopicCount: tutorial.difficultTopics.size,
      learningEfficiency: calculateLearningEfficiency()
    };
  }, [calculateLearningEfficiency, getSessionTime, tutorial]);

  // Resume from saved progress
  const resumeFromSaved = useCallback(() => {
    const savedProgress = loadProgress();
    if (!savedProgress) return false;
    
    try {
      // Restore progress data
      // Note: This would require additional actions in the tutorial context
      // For now, we'll return the saved data for manual restoration
      return savedProgress;
    } catch (error) {
      console.warn('Failed to resume from saved progress:', error);
      return false;
    }
  }, [loadProgress]);

  return {
    // Progress tracking
    completeCurrentStep,
    completeCurrentModule,
    getCurrentStepTime,
    getSessionTime,
    
    // Persistence
    saveProgress,
    loadProgress,
    clearSavedProgress,
    resumeFromSaved,
    persistenceEnabled,
    setPersistenceEnabled,
    
    // Analytics and recommendations
    getAnalytics,
    getRecommendations,
    checkForAchievements,
    
    // State
    sessionStartTime,
    stepStartTime
  };
};

export default useTutorialProgress;
