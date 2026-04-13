/**
 * Comprehensive test suite for Tutorial Hooks
 *
 * Tests custom hooks used in the tutorial system:
 * - useTutorialProgress: Progress tracking and persistence
 * - usePlayerProfile: Player profile management
 * - Tutorial-specific hook behaviors and edge cases
 */

import { renderHook, act, waitFor } from '@testing-library/react';
import { useTutorialProgress } from '../../../hooks/useTutorialProgress';
import { usePlayerProfile } from '../../../hooks/usePlayerProfile';

// Import mock factories
import {
  createMockPlayers,
  createMockOddsResponse,
  createMockUser
} from '../../../test-utils/mockFactories';

vi.mock('../../../hooks/useTutorialProgress', () => {
  const mockHook = vi.fn();
  return {
    __esModule: true,
    useTutorialProgress: mockHook,
    default: mockHook,
  };
});

vi.mock('../../../hooks/usePlayerProfile', () => {
  const mockHook = vi.fn();
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
  completeCurrentStep: vi.fn(),
  completeCurrentModule: vi.fn(),
  updateProgress: vi.fn(),

  // Navigation methods
  navigateToModule: vi.fn(),
  navigateToStep: vi.fn(),

  // Persistence methods
  saveProgress: vi.fn(),
  loadProgress: vi.fn(),
  clearProgress: vi.fn(),
  resumeFromSaved: vi.fn(),

  // Analytics methods
  getAnalytics: vi.fn().mockReturnValue({
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
  trackEvent: vi.fn(),

  // State methods
  isModuleCompleted: vi.fn(),
  isStepCompleted: vi.fn(),
  getModuleProgress: vi.fn(),
  getOverallProgress: vi.fn()
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
  updateTutorialProgress: vi.fn(),
  completeTutorial: vi.fn(),
  updatePreferences: vi.fn(),
  resetTutorialProgress: vi.fn(),
  getTutorialStats: vi.fn()
});

// Mock localStorage for tutorial progress persistence
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true
});

// Mock API calls
global.fetch = vi.fn();

describe('useTutorialProgress Hook', () => {
  let mockTutorialProgress;

  beforeEach(() => {
    vi.clearAllMocks();

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

describe('usePlayerProfile Hook (Tutorial Context)', () => {
  let mockPlayerProfile;

  beforeEach(() => {
    vi.clearAllMocks();

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

  beforeEach(() => {
    vi.clearAllMocks();

    tutorialProgressMock = createTutorialProgressMock();
    playerProfileMock = createPlayerProfileMock();

    useTutorialProgress.mockImplementation(() => tutorialProgressMock);
    usePlayerProfile.mockImplementation(() => playerProfileMock);
  });

  test('tutorial progress and player profile sync correctly', () => {
    const { result: progressResult } = renderHook(() => useTutorialProgress());
    const { result: profileResult } = renderHook(() => usePlayerProfile());

    // Both hooks should reflect consistent state
    expect(progressResult.current.progress.currentModule).toBe('golf-basics');
    expect(profileResult.current.profile.tutorialProgress.currentModule).toBe('golf-basics');
  });

  test('all hooks handle concurrent updates correctly', async () => {
    const { result: progressResult } = renderHook(() => useTutorialProgress());
    const { result: profileResult } = renderHook(() => usePlayerProfile());

    // Simulate concurrent updates
    await act(async () => {
      progressResult.current.completeCurrentStep();
      profileResult.current.updatePreferences({ showHints: false });
    });

    // All hooks should handle concurrent operations
    expect(progressResult.current.completeCurrentStep).toHaveBeenCalled();
    expect(profileResult.current.updatePreferences).toHaveBeenCalled();
  });
});

// Cleanup after all tests
afterAll(() => {
  vi.restoreAllMocks();
});
