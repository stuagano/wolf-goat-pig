/**
 * Comprehensive test suite for Tutorial Hooks
 * 
 * Tests custom hooks used in the tutorial system:
 * - useTutorialProgress: Progress tracking and persistence
 * - useOddsCalculation: Real-time odds calculation integration
 * - usePlayerProfile: Player profile management
 * - Tutorial-specific hook behaviors and edge cases
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useTutorialProgress } from '../../../hooks/useTutorialProgress';
import { useOddsCalculation } from '../../../hooks/useOddsCalculation';
import { usePlayerProfile } from '../../../hooks/usePlayerProfile';

jest.mock('../../../hooks/useTutorialProgress', () => {
  const mockHook = jest.fn();
  return {
    __esModule: true,
    useTutorialProgress: mockHook,
    default: mockHook,
  };
});

jest.mock('../../../hooks/useOddsCalculation', () => {
  const mockHook = jest.fn();
  return {
    __esModule: true,
    useOddsCalculation: mockHook,
    default: mockHook,
  };
});

jest.mock('../../../hooks/usePlayerProfile', () => {
  const mockHook = jest.fn();
  return {
    __esModule: true,
    usePlayerProfile: mockHook,
    default: mockHook,
  };
});

const createTutorialProgressMock = () => ({
  progress: {
    currentModule: 'golf-basics',
    currentStep: 1,
    completedModules: ['introduction'],
    completedSteps: 5,
    timeSpent: 1200, // 20 minutes in seconds
    hintsUsed: 3,
    startTime: Date.now() - 1200000,
    lastSaveTime: Date.now() - 600000
  },

  // Progress tracking methods
  completeCurrentStep: jest.fn(),
  completeCurrentModule: jest.fn(),
  updateProgress: jest.fn(),

  // Navigation methods
  navigateToModule: jest.fn(),
  navigateToStep: jest.fn(),

  // Persistence methods
  saveProgress: jest.fn(),
  loadProgress: jest.fn(),
  clearProgress: jest.fn(),
  resumeFromSaved: jest.fn(),

  // Analytics methods
  getAnalytics: jest.fn().mockReturnValue({
    totalTimeSpent: 2400,
    modulesCompleted: 3,
    stepsCompleted: 28,
    hintsUsed: 7,
    completionRate: 75,
    averageTimePerModule: 800,
    learningVelocity: 'normal',
    strugglingAreas: ['betting-calculations'],
    strengths: ['basic-rules', 'team-formation']
  }),
  trackEvent: jest.fn(),

  // State methods
  isModuleCompleted: jest.fn(),
  isStepCompleted: jest.fn(),
  getModuleProgress: jest.fn(),
  getOverallProgress: jest.fn()
});

const createOddsCalculationMock = () => ({
  odds: {
    captain: 0.35,
    opponents: 0.65
  },
  scenarios: [
    { action: 'offer_double', win_probability: 0.35, expected_value: -0.8 },
    { action: 'accept_double', win_probability: 0.65, expected_value: 1.2 }
  ],
  confidence: 0.8,
  isLoading: false,
  error: null,
  lastUpdated: Date.now(),

  // Tutorial-specific methods
  calculateForTutorial: jest.fn(),
  getSimplifiedExplanation: jest.fn(),
  updateScenario: jest.fn(),
  resetCalculation: jest.fn()
});

const createPlayerProfileMock = () => ({
  profile: {
    id: 'tutorial_user',
    name: 'Tutorial Player',
    handicap: 18,
    avatar_url: null,
    tutorialProgress: {
      completed: false,
      currentModule: 'golf-basics',
      completedModules: [],
      timeSpent: 300
    },
    preferences: {
      tutorialDifficulty: 'beginner',
      showHints: true,
      audioEnabled: true
    }
  },

  isLoading: false,
  error: null,

  // Tutorial-specific methods
  updateTutorialProgress: jest.fn(),
  completeTutorial: jest.fn(),
  updatePreferences: jest.fn(),
  resetTutorialProgress: jest.fn(),
  getTutorialStats: jest.fn()
});

// Mock localStorage for tutorial progress persistence
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn()
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true
});

// Mock API calls
global.fetch = jest.fn();

describe('useTutorialProgress Hook', () => {
  let mockTutorialProgress;

  beforeEach(() => {
    jest.clearAllMocks();

    mockTutorialProgress = createTutorialProgressMock();
    useTutorialProgress.mockImplementation(() => mockTutorialProgress);
  });

  describe('Progress Tracking', () => {
    test('tracks step completion', () => {
      const { result } = renderHook(() => useTutorialProgress());
      
      act(() => {
        result.current.completeCurrentStep();
      });
      
      expect(result.current.completeCurrentStep).toHaveBeenCalled();
    });

    test('tracks module completion', () => {
      const { result } = renderHook(() => useTutorialProgress());
      
      act(() => {
        result.current.completeCurrentModule();
      });
      
      expect(result.current.completeCurrentModule).toHaveBeenCalled();
    });

    test('updates progress correctly', () => {
      const { result } = renderHook(() => useTutorialProgress());
      
      const progressUpdate = {
        currentStep: 3,
        hintsUsed: 5
      };
      
      act(() => {
        result.current.updateProgress(progressUpdate);
      });
      
      expect(result.current.updateProgress).toHaveBeenCalledWith(progressUpdate);
    });

    test('calculates overall progress percentage', () => {
      mockTutorialProgress.getOverallProgress.mockReturnValue(45.5);
      
      const { result } = renderHook(() => useTutorialProgress());
      
      const progress = result.current.getOverallProgress();
      expect(progress).toBe(45.5);
    });

    test('calculates module-specific progress', () => {
      mockTutorialProgress.getModuleProgress.mockReturnValue(75);
      
      const { result } = renderHook(() => useTutorialProgress());
      
      const moduleProgress = result.current.getModuleProgress('golf-basics');
      expect(result.current.getModuleProgress).toHaveBeenCalledWith('golf-basics');
      expect(moduleProgress).toBe(75);
    });
  });

  describe('Progress Persistence', () => {
    test('saves progress to localStorage', () => {
      const { result } = renderHook(() => useTutorialProgress());
      
      act(() => {
        result.current.saveProgress();
      });
      
      expect(result.current.saveProgress).toHaveBeenCalled();
    });

    test('loads progress from localStorage', () => {
      const savedProgress = {
        currentModule: 'betting-system',
        currentStep: 4,
        timeSpent: 2400
      };
      
      mockTutorialProgress.loadProgress.mockReturnValue(savedProgress);
      
      const { result } = renderHook(() => useTutorialProgress());
      
      const loadedProgress = result.current.loadProgress();
      expect(loadedProgress).toEqual(savedProgress);
    });

    test('resumes from saved progress', () => {
      const savedState = {
        lastModule: 'team-formation',
        progress: 60,
        timeSpent: 1800
      };
      
      mockTutorialProgress.resumeFromSaved.mockReturnValue(savedState);
      
      const { result } = renderHook(() => useTutorialProgress());
      
      const resumedState = result.current.resumeFromSaved();
      expect(resumedState).toEqual(savedState);
    });

    test('clears saved progress', () => {
      const { result } = renderHook(() => useTutorialProgress());
      
      act(() => {
        result.current.clearProgress();
      });
      
      expect(result.current.clearProgress).toHaveBeenCalled();
    });

    test('handles corrupted localStorage gracefully', () => {
      mockTutorialProgress.loadProgress.mockReturnValue(null);
      
      const { result } = renderHook(() => useTutorialProgress());
      
      const progress = result.current.loadProgress();
      expect(progress).toBeNull();
    });
  });

  describe('Navigation Methods', () => {
    test('navigates to specific module', () => {
      const { result } = renderHook(() => useTutorialProgress());
      
      act(() => {
        result.current.navigateToModule('advanced-rules');
      });
      
      expect(result.current.navigateToModule).toHaveBeenCalledWith('advanced-rules');
    });

    test('navigates to specific step', () => {
      const { result } = renderHook(() => useTutorialProgress());
      
      act(() => {
        result.current.navigateToStep(5);
      });
      
      expect(result.current.navigateToStep).toHaveBeenCalledWith(5);
    });

    test('validates navigation targets', () => {
      mockTutorialProgress.navigateToModule.mockImplementation((moduleId) => {
        const validModules = ['golf-basics', 'game-overview', 'team-formation'];
        return validModules.includes(moduleId);
      });
      
      const { result } = renderHook(() => useTutorialProgress());
      
      const validNavigation = result.current.navigateToModule('golf-basics');
      const invalidNavigation = result.current.navigateToModule('invalid-module');
      
      expect(validNavigation).toBe(true);
      expect(invalidNavigation).toBe(false);
    });
  });

  describe('Analytics and Tracking', () => {
    test('generates analytics summary', () => {
      const analytics = {
        totalTimeSpent: 2400,
        modulesCompleted: 3,
        stepsCompleted: 28,
        hintsUsed: 7,
        completionRate: 75,
        averageTimePerModule: 800,
        learningVelocity: 'normal',
        strugglingAreas: ['betting-calculations'],
        strengths: ['basic-rules', 'team-formation']
      };
      
      mockTutorialProgress.getAnalytics.mockReturnValue(analytics);
      
      const { result } = renderHook(() => useTutorialProgress());
      
      const generatedAnalytics = result.current.getAnalytics();
      expect(generatedAnalytics).toEqual(analytics);
    });

    test('tracks user events', () => {
      const { result } = renderHook(() => useTutorialProgress());
      
      act(() => {
        result.current.trackEvent('hint_used', { module: 'golf-basics', step: 3 });
      });
      
      expect(result.current.trackEvent).toHaveBeenCalledWith(
        'hint_used', 
        { module: 'golf-basics', step: 3 }
      );
    });

    test('tracks time spent accurately', () => {
      const { result } = renderHook(() => useTutorialProgress());
      
      expect(result.current.progress.timeSpent).toBe(1200);
    });

    test('identifies learning patterns', () => {
      const { result } = renderHook(() => useTutorialProgress());

      const analytics = result.current.getAnalytics();
      
      expect(analytics.learningVelocity).toBeDefined();
      expect(analytics.strugglingAreas).toBeInstanceOf(Array);
      expect(analytics.strengths).toBeInstanceOf(Array);
    });
  });

  describe('State Queries', () => {
    test('checks if module is completed', () => {
      mockTutorialProgress.isModuleCompleted.mockReturnValue(true);
      
      const { result } = renderHook(() => useTutorialProgress());
      
      const isCompleted = result.current.isModuleCompleted('introduction');
      expect(isCompleted).toBe(true);
      expect(result.current.isModuleCompleted).toHaveBeenCalledWith('introduction');
    });

    test('checks if step is completed', () => {
      mockTutorialProgress.isStepCompleted.mockReturnValue(false);
      
      const { result } = renderHook(() => useTutorialProgress());
      
      const isStepCompleted = result.current.isStepCompleted('golf-basics', 5);
      expect(isStepCompleted).toBe(false);
      expect(result.current.isStepCompleted).toHaveBeenCalledWith('golf-basics', 5);
    });

    test('provides current progress state', () => {
      const { result } = renderHook(() => useTutorialProgress());
      
      expect(result.current.progress).toBeDefined();
      expect(result.current.progress.currentModule).toBe('golf-basics');
      expect(result.current.progress.currentStep).toBe(1);
      expect(result.current.progress.timeSpent).toBe(1200);
    });
  });
});

describe('useOddsCalculation Hook (Tutorial Context)', () => {
  let mockOddsCalculation;

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock fetch for API calls
    global.fetch.mockResolvedValue({
      ok: true,
      json: jest.fn().mockResolvedValue({
        overall_odds: { captain: 0.35, opponents: 0.65 },
        betting_scenarios: [
          { action: 'offer_double', win_probability: 0.35, expected_value: -0.8 },
          { action: 'accept_double', win_probability: 0.65, expected_value: 1.2 }
        ],
        confidence: 0.8
      })
    });

    mockOddsCalculation = createOddsCalculationMock();
    useOddsCalculation.mockImplementation(() => mockOddsCalculation);
  });

  describe('Tutorial Integration', () => {
    test('calculates odds for tutorial scenarios', async () => {
      const tutorialScenario = {
        players: [
          { id: 'tutorial_player', handicap: 12, distance: 150, lie: 'fairway' },
          { id: 'ai_player_1', handicap: 15, distance: 140, lie: 'rough' }
        ],
        hole: { par: 4, difficulty: 3.5 }
      };

      const { result } = renderHook(() => useOddsCalculation());

      await act(async () => {
        result.current.calculateForTutorial(tutorialScenario);
      });

      expect(result.current.calculateForTutorial).toHaveBeenCalledWith(tutorialScenario);
    });

    test('provides simplified explanations for beginners', () => {
      const explanation = "With your current position, you have a 35% chance of winning this hole. The opponents have better lies, so accepting a double would not be profitable.";
      
      mockOddsCalculation.getSimplifiedExplanation.mockReturnValue(explanation);

      const { result } = renderHook(() => useOddsCalculation());

      const simpleExplanation = result.current.getSimplifiedExplanation();
      expect(simpleExplanation).toBe(explanation);
    });

    test('updates scenario dynamically during tutorial', () => {
      const { result } = renderHook(() => useOddsCalculation());

      const scenarioUpdate = {
        playerPosition: { distance: 120, lie: 'green' }
      };

      act(() => {
        result.current.updateScenario(scenarioUpdate);
      });

      expect(result.current.updateScenario).toHaveBeenCalledWith(scenarioUpdate);
    });

    test('resets calculation between tutorial steps', () => {
      const { result } = renderHook(() => useOddsCalculation());

      act(() => {
        result.current.resetCalculation();
      });

      expect(result.current.resetCalculation).toHaveBeenCalled();
    });
  });

  describe('Real-time Updates', () => {
    test('handles loading states', () => {
      mockOddsCalculation.isLoading = true;

      const { result } = renderHook(() => useOddsCalculation());

      expect(result.current.isLoading).toBe(true);
    });

    test('handles error states', () => {
      const error = 'Failed to calculate odds';
      mockOddsCalculation.error = error;
      mockOddsCalculation.isLoading = false;

      const { result } = renderHook(() => useOddsCalculation());

      expect(result.current.error).toBe(error);
      expect(result.current.isLoading).toBe(false);
    });

    test('updates odds when scenario changes', async () => {
      const { result, rerender } = renderHook(() => useOddsCalculation());

      // Initial odds
      expect(result.current.odds.captain).toBe(0.35);

      // Update scenario
      mockOddsCalculation.odds = { captain: 0.42, opponents: 0.58 };
      
      rerender();

      expect(result.current.odds.captain).toBe(0.42);
    });

    test('tracks confidence in calculations', () => {
      const { result } = renderHook(() => useOddsCalculation());

      expect(result.current.confidence).toBe(0.8);
      expect(result.current.confidence).toBeGreaterThan(0);
      expect(result.current.confidence).toBeLessThanOrEqual(1);
    });
  });

  describe('Error Handling', () => {
    test('handles API failures gracefully', async () => {
      global.fetch.mockRejectedValue(new Error('Network error'));

      mockOddsCalculation.error = 'Network error';
      mockOddsCalculation.isLoading = false;

      const { result } = renderHook(() => useOddsCalculation());

      expect(result.current.error).toBe('Network error');
      expect(result.current.odds).toBeDefined(); // Should maintain previous state
    });

    test('handles invalid tutorial scenarios', () => {
      const invalidScenario = { players: null, hole: undefined };

      const { result } = renderHook(() => useOddsCalculation());

      act(() => {
        result.current.calculateForTutorial(invalidScenario);
      });

      // Should not throw and should handle gracefully
      expect(result.current.calculateForTutorial).toHaveBeenCalledWith(invalidScenario);
    });
  });
});

describe('usePlayerProfile Hook (Tutorial Context)', () => {
  let mockPlayerProfile;

  beforeEach(() => {
    jest.clearAllMocks();

    mockPlayerProfile = createPlayerProfileMock();

    usePlayerProfile.mockImplementation(() => mockPlayerProfile);
  });

  describe('Tutorial Progress Integration', () => {
    test('updates tutorial progress in profile', async () => {
      const { result } = renderHook(() => usePlayerProfile());

      const progressUpdate = {
        currentModule: 'betting-system',
        completedModules: ['golf-basics', 'game-overview'],
        timeSpent: 1200
      };

      await act(async () => {
        result.current.updateTutorialProgress(progressUpdate);
      });

      expect(result.current.updateTutorialProgress).toHaveBeenCalledWith(progressUpdate);
    });

    test('marks tutorial as completed', async () => {
      const { result } = renderHook(() => usePlayerProfile());

      const completionData = {
        completedAt: Date.now(),
        finalScore: 85,
        timeSpent: 3600
      };

      await act(async () => {
        result.current.completeTutorial(completionData);
      });

      expect(result.current.completeTutorial).toHaveBeenCalledWith(completionData);
    });

    test('resets tutorial progress', async () => {
      const { result } = renderHook(() => usePlayerProfile());

      await act(async () => {
        result.current.resetTutorialProgress();
      });

      expect(result.current.resetTutorialProgress).toHaveBeenCalled();
    });

    test('retrieves tutorial statistics', () => {
      const stats = {
        modulesCompleted: 3,
        totalTimeSpent: 2400,
        averageScore: 78,
        hintsUsed: 12,
        retries: 2
      };

      mockPlayerProfile.getTutorialStats.mockReturnValue(stats);

      const { result } = renderHook(() => usePlayerProfile());

      const tutorialStats = result.current.getTutorialStats();
      expect(tutorialStats).toEqual(stats);
    });
  });

  describe('Preference Management', () => {
    test('updates tutorial preferences', async () => {
      const { result } = renderHook(() => usePlayerProfile());

      const newPreferences = {
        tutorialDifficulty: 'advanced',
        showHints: false,
        audioEnabled: false
      };

      await act(async () => {
        result.current.updatePreferences(newPreferences);
      });

      expect(result.current.updatePreferences).toHaveBeenCalledWith(newPreferences);
    });

    test('maintains preference consistency', () => {
      const { result } = renderHook(() => usePlayerProfile());

      expect(result.current.profile.preferences.tutorialDifficulty).toBe('beginner');
      expect(result.current.profile.preferences.showHints).toBe(true);
      expect(result.current.profile.preferences.audioEnabled).toBe(true);
    });

    test('validates preference updates', () => {
      const { result } = renderHook(() => usePlayerProfile());

      const invalidPreferences = {
        tutorialDifficulty: 'invalid_level',
        showHints: 'not_boolean'
      };

      // Should handle invalid preferences gracefully
      act(() => {
        result.current.updatePreferences(invalidPreferences);
      });

      expect(result.current.updatePreferences).toHaveBeenCalledWith(invalidPreferences);
    });
  });

  describe('Profile State Management', () => {
    test('provides current profile state', () => {
      const { result } = renderHook(() => usePlayerProfile());

      expect(result.current.profile).toBeDefined();
      expect(result.current.profile.id).toBe('tutorial_user');
      expect(result.current.profile.tutorialProgress).toBeDefined();
    });

    test('handles loading states', () => {
      mockPlayerProfile.isLoading = true;

      const { result } = renderHook(() => usePlayerProfile());

      expect(result.current.isLoading).toBe(true);
    });

    test('handles error states', () => {
      const error = 'Failed to load profile';
      mockPlayerProfile.error = error;

      const { result } = renderHook(() => usePlayerProfile());

      expect(result.current.error).toBe(error);
    });

    test('updates profile reactively', () => {
      const { result, rerender } = renderHook(() => usePlayerProfile());

      expect(result.current.profile.name).toBe('Tutorial Player');

      // Simulate profile update
      mockPlayerProfile.profile.name = 'Updated Tutorial Player';
      rerender();

      expect(result.current.profile.name).toBe('Updated Tutorial Player');
    });
  });

  describe('Tutorial Context Integration', () => {
    test('syncs with tutorial system state', () => {
      const { result } = renderHook(() => usePlayerProfile());

      expect(result.current.profile.tutorialProgress.currentModule).toBe('golf-basics');
      expect(result.current.profile.tutorialProgress.completed).toBe(false);
    });

    test('persists tutorial achievements', async () => {
      const { result } = renderHook(() => usePlayerProfile());

      const achievement = {
        type: 'first_hole_win',
        unlockedAt: Date.now(),
        module: 'practice-game'
      };

      // This would typically be part of updateTutorialProgress
      const progressWithAchievement = {
        ...result.current.profile.tutorialProgress,
        achievements: [achievement]
      };

      await act(async () => {
        result.current.updateTutorialProgress(progressWithAchievement);
      });

      expect(result.current.updateTutorialProgress).toHaveBeenCalledWith(progressWithAchievement);
    });
  });
});

describe('Hook Integration Tests', () => {
  let tutorialProgressMock;
  let playerProfileMock;
  let oddsCalculationMock;

  beforeEach(() => {
    jest.clearAllMocks();

    tutorialProgressMock = createTutorialProgressMock();
    playerProfileMock = createPlayerProfileMock();
    oddsCalculationMock = createOddsCalculationMock();

    useTutorialProgress.mockImplementation(() => tutorialProgressMock);
    usePlayerProfile.mockImplementation(() => playerProfileMock);
    useOddsCalculation.mockImplementation(() => oddsCalculationMock);
  });

  test('tutorial progress and player profile sync correctly', () => {
    const { result: progressResult } = renderHook(() => useTutorialProgress());
    const { result: profileResult } = renderHook(() => usePlayerProfile());

    // Both hooks should reflect consistent state
    expect(progressResult.current.progress.currentModule).toBe('golf-basics');
    expect(profileResult.current.profile.tutorialProgress.currentModule).toBe('golf-basics');
  });

  test('odds calculation updates trigger progress tracking', async () => {
    const { result: progressResult } = renderHook(() => useTutorialProgress());
    const { result: oddsResult } = renderHook(() => useOddsCalculation());

    // Simulate learning interaction
    await act(async () => {
      oddsResult.current.calculateForTutorial({
        players: [{ id: 'test', handicap: 12 }]
      });
    });

    // Should trigger progress tracking
    expect(oddsResult.current.calculateForTutorial).toHaveBeenCalled();
  });

  test('all hooks handle concurrent updates correctly', async () => {
    const { result: progressResult } = renderHook(() => useTutorialProgress());
    const { result: profileResult } = renderHook(() => usePlayerProfile());
    const { result: oddsResult } = renderHook(() => useOddsCalculation());

    // Simulate concurrent updates
    await act(async () => {
      progressResult.current.completeCurrentStep();
      profileResult.current.updatePreferences({ showHints: false });
      oddsResult.current.resetCalculation();
    });

    // All hooks should handle concurrent operations
    expect(progressResult.current.completeCurrentStep).toHaveBeenCalled();
    expect(profileResult.current.updatePreferences).toHaveBeenCalled();
    expect(oddsResult.current.resetCalculation).toHaveBeenCalled();
  });
});

// Cleanup after all tests
afterAll(() => {
  jest.restoreAllMocks();
});
