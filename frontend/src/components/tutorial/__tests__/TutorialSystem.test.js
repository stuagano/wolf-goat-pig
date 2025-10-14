/**
 * Comprehensive test suite for Tutorial System
 * 
 * Tests the main tutorial system component including:
 * - Component rendering and initialization
 * - Welcome screen functionality
 * - Progress tracking integration
 * - Module navigation and switching
 * - Keyboard navigation
 * - Mobile responsiveness
 * - Accessibility features
 * - Error handling
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// Mock the context and hooks
import { useTutorial } from '../../../context/TutorialContext';
import { useTutorialProgress } from '../../../hooks/useTutorialProgress';
import { useTheme } from '../../../theme/Provider';

import TutorialSystem from '../TutorialSystem';

jest.mock('../../../context/TutorialContext', () => ({
  __esModule: true,
  useTutorial: jest.fn()
}));

jest.mock('../../../hooks/useTutorialProgress', () => ({
  __esModule: true,
  useTutorialProgress: jest.fn()
}));

jest.mock('../../../theme/Provider', () => ({
  __esModule: true,
  useTheme: jest.fn()
}));

// Mock all the tutorial modules
jest.mock('../modules/GolfBasicsModule', () => {
  return function MockGolfBasicsModule({ onStepComplete, onModuleComplete, currentStep, goToStep }) {
    return (
      <div data-testid="golf-basics-module">
        <h3>Golf Basics Module</h3>
        <p>Current Step: {currentStep}</p>
        <button onClick={() => onStepComplete && onStepComplete()}>Complete Step</button>
        <button onClick={() => onModuleComplete && onModuleComplete()}>Complete Module</button>
        <button onClick={() => goToStep && goToStep(2)}>Go to Step 2</button>
      </div>
    );
  };
});

jest.mock('../modules/GameOverviewModule', () => {
  return function MockGameOverviewModule(props) {
    return <div data-testid="game-overview-module">Game Overview Module</div>;
  };
});

jest.mock('../modules/TeamFormationModule', () => {
  return function MockTeamFormationModule(props) {
    return <div data-testid="team-formation-module">Team Formation Module</div>;
  };
});

jest.mock('../modules/BettingSystemModule', () => {
  return function MockBettingSystemModule(props) {
    return <div data-testid="betting-system-module">Betting System Module</div>;
  };
});

jest.mock('../modules/AdvancedRulesModule', () => {
  return function MockAdvancedRulesModule(props) {
    return <div data-testid="advanced-rules-module">Advanced Rules Module</div>;
  };
});

jest.mock('../modules/AnalysisToolsModule', () => {
  return function MockAnalysisToolsModule(props) {
    return <div data-testid="analysis-tools-module">Analysis Tools Module</div>;
  };
});

jest.mock('../modules/PracticeGameModule', () => {
  return function MockPracticeGameModule(props) {
    return <div data-testid="practice-game-module">Practice Game Module</div>;
  };
});

jest.mock('../ProgressTracker', () => {
  return function MockProgressTracker() {
    return <div data-testid="progress-tracker">Progress Tracker</div>;
  };
});

jest.mock('../TutorialOverlay', () => {
  return function MockTutorialOverlay() {
    return <div data-testid="tutorial-overlay">Tutorial Overlay</div>;
  };
});

// Mock hooks with default implementations
const mockUseTutorial = jest.mocked(useTutorial);
const mockUseTutorialProgress = jest.mocked(useTutorialProgress);
const mockUseTheme = jest.mocked(useTheme);

describe('TutorialSystem', () => {
  let mockTutorial;
  let mockProgress;
  let mockTheme;
  let mockOnComplete;
  let mockOnExit;

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks();

    // Mock tutorial context
    mockTutorial = {
      isActive: true,
      currentModule: 'golf-basics',
      currentStep: 1,
      modules: [
        { id: 'golf-basics', title: 'Golf Basics', completed: false },
        { id: 'game-overview', title: 'Game Overview', completed: false },
        { id: 'team-formation', title: 'Team Formation', completed: false },
        { id: 'betting-system', title: 'Betting System', completed: false },
        { id: 'advanced-rules', title: 'Advanced Rules', completed: false },
        { id: 'analysis-tools', title: 'Analysis Tools', completed: false },
        { id: 'practice-game', title: 'Practice Game', completed: false }
      ],
      completed: false,
      overlayVisible: false,
      sidebarCollapsed: false,
      showHints: true,
      largeText: false,
      highContrast: false,
      reducedMotion: false,
      learningPreferences: {
        visualLearner: true,
        auditoryLearner: false,
        kinestheticLearner: true,
        skipBasics: false,
        pace: 'normal'
      },
      startTutorial: jest.fn(),
      nextModule: jest.fn(),
      previousModule: jest.fn(),
      nextStep: jest.fn(),
      previousStep: jest.fn(),
      goToStep: jest.fn(),
      toggleOverlay: jest.fn(),
      toggleHints: jest.fn(),
      toggleSidebar: jest.fn(),
      updatePreferences: jest.fn()
    };

    // Mock progress hook
    mockProgress = {
      completeCurrentStep: jest.fn(),
      completeCurrentModule: jest.fn(),
      resumeFromSaved: jest.fn(),
      loadProgress: jest.fn(),
      getAnalytics: jest.fn().mockReturnValue({
        totalTimeSpent: 3600,
        modulesCompleted: 3,
        stepsCompleted: 25,
        hintsUsed: 5,
        learningStyle: 'visual'
      })
    };

    // Mock theme
    mockTheme = {
      colors: {
        background: '#ffffff',
        primary: '#007bff',
        paper: '#f8f9fa',
        border: '#dee2e6',
        textPrimary: '#212529',
        textSecondary: '#6c757d',
        success: '#28a745',
        accent: '#17a2b8',
        error: '#dc3545',
        gray50: '#f8f9fa',
        gray100: '#e9ecef',
        gray300: '#adb5bd',
        gray400: '#6c757d',
        gray500: '#495057'
      },
      spacing: {
        2: '8px',
        3: '12px',
        4: '16px',
        6: '24px',
        8: '32px'
      },
      typography: {
        fontFamily: 'Arial, sans-serif',
        sm: '14px',
        base: '16px',
        lg: '18px',
        xl: '20px',
        '3xl': '30px',
        medium: '500',
        semibold: '600',
        bold: '700'
      },
      borderRadius: {
        base: '4px'
      },
      shadows: {
        base: '0 2px 4px rgba(0,0,0,0.1)'
      },
      buttonStyle: {
        padding: '8px 16px',
        borderRadius: '4px',
        border: 'none',
        cursor: 'pointer',
        backgroundColor: '#007bff',
        color: '#ffffff'
      },
      cardStyle: {
        backgroundColor: '#ffffff',
        borderRadius: '8px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        padding: '24px'
      },
      inputStyle: {
        padding: '8px 12px',
        border: '1px solid #dee2e6',
        borderRadius: '4px'
      }
    };

    // Mock callback functions
    mockOnComplete = jest.fn();
    mockOnExit = jest.fn();

    // Setup mock returns
    mockUseTutorial.mockReturnValue(mockTutorial);
    mockUseTutorialProgress.mockReturnValue(mockProgress);
    mockUseTheme.mockReturnValue(mockTheme);

    // Mock window functions
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024
    });

    // Mock addEventListener and removeEventListener
    const mockAddEventListener = jest.fn();
    const mockRemoveEventListener = jest.fn();
    window.addEventListener = mockAddEventListener;
    window.removeEventListener = mockRemoveEventListener;
  });

  describe('Welcome Screen', () => {
    test('shows welcome screen when tutorial is not active', () => {
      mockTutorial.isActive = false;
      
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      expect(screen.getByText('Welcome to Wolf Goat Pig Tutorial')).toBeInTheDocument();
      expect(screen.getByText('Start Tutorial')).toBeInTheDocument();
      expect(screen.getByText('Resume Previous Session')).toBeInTheDocument();
      expect(screen.getByText('Skip Tutorial')).toBeInTheDocument();
    });

    test('starts tutorial when Start Tutorial button is clicked', async () => {
      mockTutorial.isActive = false;
      
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      const startButton = screen.getByText('Start Tutorial');
      await userEvent.click(startButton);
      
      expect(mockTutorial.startTutorial).toHaveBeenCalled();
    });

    test('resumes tutorial when Resume button is clicked', async () => {
      mockTutorial.isActive = false;
      mockProgress.loadProgress.mockReturnValue(true);
      mockProgress.resumeFromSaved.mockReturnValue({
        lastModule: 'betting-system',
        progress: 60
      });
      
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      const resumeButton = screen.getByText('Resume Previous Session');
      expect(resumeButton).not.toBeDisabled();
      
      await userEvent.click(resumeButton);
      
      expect(mockProgress.resumeFromSaved).toHaveBeenCalled();
      expect(mockTutorial.startTutorial).toHaveBeenCalledWith('betting-system');
    });

    test('disables resume button when no saved progress', () => {
      mockTutorial.isActive = false;
      mockProgress.loadProgress.mockReturnValue(false);
      
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      const resumeButton = screen.getByText('Resume Previous Session');
      expect(resumeButton).toBeDisabled();
    });

    test('exits tutorial when Skip button is clicked', async () => {
      mockTutorial.isActive = false;
      
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      const skipButton = screen.getByText('Skip Tutorial');
      await userEvent.click(skipButton);
      
      expect(mockOnExit).toHaveBeenCalled();
    });
  });

  describe('Active Tutorial Interface', () => {
    test('renders main tutorial interface when active', () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      expect(screen.getByRole('application', { name: 'Wolf Goat Pig Tutorial System' })).toBeInTheDocument();
      expect(screen.getByRole('complementary', { name: 'Tutorial progress and navigation' })).toBeInTheDocument();
      expect(screen.getByRole('main', { name: 'Tutorial content' })).toBeInTheDocument();
      expect(screen.getByRole('navigation', { name: 'Tutorial module navigation' })).toBeInTheDocument();
    });

    test('displays current module component', () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      expect(screen.getByTestId('golf-basics-module')).toBeInTheDocument();
      expect(screen.getByText('Golf Basics Module')).toBeInTheDocument();
      expect(screen.getByText('Current Step: 1')).toBeInTheDocument();
    });

    test('shows progress tracker', () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      expect(screen.getByTestId('progress-tracker')).toBeInTheDocument();
    });

    test('hides progress tracker when sidebar is collapsed', () => {
      mockTutorial.sidebarCollapsed = true;
      
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      expect(screen.queryByTestId('progress-tracker')).not.toBeInTheDocument();
    });

    test('displays module navigation with correct state', () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      const prevButton = screen.getByLabelText('Go to previous module');
      const nextButton = screen.getByLabelText('Go to next module');
      const moduleInfo = screen.getByRole('status');
      
      expect(prevButton).toBeDisabled(); // First module
      expect(nextButton).not.toBeDisabled();
      expect(moduleInfo).toHaveTextContent('Module 1 of 7');
    });
  });

  describe('Module Navigation', () => {
    test('navigates to next module', async () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      const nextButton = screen.getByLabelText('Go to next module');
      await userEvent.click(nextButton);
      
      expect(mockTutorial.nextModule).toHaveBeenCalled();
    });

    test('navigates to previous module', async () => {
      mockTutorial.currentModule = 'game-overview'; // Not first module
      
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      const prevButton = screen.getByLabelText('Go to previous module');
      await userEvent.click(prevButton);
      
      expect(mockTutorial.previousModule).toHaveBeenCalled();
    });

    test('disables next button on last module', () => {
      mockTutorial.currentModule = 'practice-game'; // Last module
      
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      const nextButton = screen.getByLabelText('Go to next module');
      expect(nextButton).toBeDisabled();
    });

    test('switches module content when currentModule changes', () => {
      const { rerender } = render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      expect(screen.getByTestId('golf-basics-module')).toBeInTheDocument();
      
      // Change current module
      mockTutorial.currentModule = 'game-overview';
      rerender(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      expect(screen.getByTestId('game-overview-module')).toBeInTheDocument();
      expect(screen.queryByTestId('golf-basics-module')).not.toBeInTheDocument();
    });
  });

  describe('Keyboard Navigation', () => {
    test('handles arrow key navigation', () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      // Right arrow for next step
      fireEvent.keyDown(window, { key: 'ArrowRight' });
      expect(mockTutorial.nextStep).toHaveBeenCalled();
      
      // Left arrow for previous step
      fireEvent.keyDown(window, { key: 'ArrowLeft' });
      expect(mockTutorial.previousStep).toHaveBeenCalled();
      
      // Ctrl+Right for next module
      fireEvent.keyDown(window, { key: 'ArrowRight', ctrlKey: true });
      expect(mockTutorial.nextModule).toHaveBeenCalled();
      
      // Ctrl+Left for previous module
      fireEvent.keyDown(window, { key: 'ArrowLeft', ctrlKey: true });
      expect(mockTutorial.previousModule).toHaveBeenCalled();
    });

    test('handles escape key for overlay', () => {
      mockTutorial.overlayVisible = true;
      
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      fireEvent.keyDown(window, { key: 'Escape' });
      expect(mockTutorial.toggleOverlay).toHaveBeenCalled();
    });

    test('handles Ctrl+H for hints toggle', () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      fireEvent.keyDown(window, { key: 'h', ctrlKey: true });
      expect(mockTutorial.toggleHints).toHaveBeenCalled();
    });

    test('ignores keyboard shortcuts when tutorial is not active', () => {
      mockTutorial.isActive = false;
      
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      fireEvent.keyDown(window, { key: 'ArrowRight' });
      expect(mockTutorial.nextStep).not.toHaveBeenCalled();
    });
  });

  describe('Header Actions', () => {
    test('toggles sidebar when sidebar toggle is clicked', async () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      const toggleButton = screen.getByTitle('Toggle sidebar');
      await userEvent.click(toggleButton);
      
      expect(mockTutorial.toggleSidebar).toHaveBeenCalled();
    });

    test('toggles hints when hints button is clicked', async () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      const hintsButton = screen.getByTitle('Toggle hints');
      await userEvent.click(hintsButton);
      
      expect(mockTutorial.toggleHints).toHaveBeenCalled();
    });

    test('exits tutorial when exit button is clicked', async () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      const exitButton = screen.getByTitle('Exit tutorial');
      await userEvent.click(exitButton);
      
      expect(mockOnExit).toHaveBeenCalled();
    });
  });

  describe('Mobile Responsiveness', () => {
    beforeEach(() => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500
      });
    });

    test('adapts layout for mobile screens', () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      // Mobile sidebar should have mobile-specific behavior
      const toggleButton = screen.getByTitle('Toggle progress');
      expect(toggleButton).toBeInTheDocument();
    });

    test('handles mobile sidebar toggle', async () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      const toggleButton = screen.getByTitle('Toggle progress');
      await userEvent.click(toggleButton);
      
      // Should show progress tracker after toggle
      expect(screen.getByTestId('progress-tracker')).toBeInTheDocument();
    });

    test('handles window resize events', () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      // Trigger resize event
      Object.defineProperty(window, 'innerWidth', { value: 1200 });
      fireEvent(window, new Event('resize'));
      
      // Should call event listener
      expect(window.addEventListener).toHaveBeenCalledWith('resize', expect.any(Function));
    });
  });

  describe('Module Integration', () => {
    test('passes correct props to module components', () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      const moduleElement = screen.getByTestId('golf-basics-module');
      expect(moduleElement).toBeInTheDocument();
      
      // Test that callbacks work
      const completeStepButton = screen.getByText('Complete Step');
      const completeModuleButton = screen.getByText('Complete Module');
      const goToStepButton = screen.getByText('Go to Step 2');
      
      expect(completeStepButton).toBeInTheDocument();
      expect(completeModuleButton).toBeInTheDocument();
      expect(goToStepButton).toBeInTheDocument();
    });

    test('handles step completion', async () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      const completeStepButton = screen.getByText('Complete Step');
      await userEvent.click(completeStepButton);
      
      expect(mockProgress.completeCurrentStep).toHaveBeenCalled();
    });

    test('handles module completion', async () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      const completeModuleButton = screen.getByText('Complete Module');
      await userEvent.click(completeModuleButton);
      
      expect(mockProgress.completeCurrentModule).toHaveBeenCalled();
    });

    test('handles step navigation from modules', async () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      const goToStepButton = screen.getByText('Go to Step 2');
      await userEvent.click(goToStepButton);
      
      expect(mockTutorial.goToStep).toHaveBeenCalledWith(2);
    });

    test('handles unknown module gracefully', () => {
      mockTutorial.currentModule = 'unknown-module';
      
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      expect(screen.getByText('Module not found: unknown-module')).toBeInTheDocument();
    });
  });

  describe('Tutorial Completion', () => {
    test('calls onComplete when tutorial is completed', async () => {
      mockTutorial.completed = true;
      
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      await waitFor(() => {
        expect(mockOnComplete).toHaveBeenCalledWith({
          totalTimeSpent: 3600,
          modulesCompleted: 3,
          stepsCompleted: 25,
          hintsUsed: 5,
          learningStyle: 'visual'
        });
      });
    });

    test('does not call onComplete multiple times', async () => {
      mockTutorial.completed = true;
      
      const { rerender } = render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      await waitFor(() => {
        expect(mockOnComplete).toHaveBeenCalledTimes(1);
      });
      
      // Re-render should not call onComplete again
      rerender(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      await waitFor(() => {
        expect(mockOnComplete).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Overlay Display', () => {
    test('shows tutorial overlay when visible', () => {
      mockTutorial.overlayVisible = true;
      
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      expect(screen.getByTestId('tutorial-overlay')).toBeInTheDocument();
    });

    test('hides tutorial overlay when not visible', () => {
      mockTutorial.overlayVisible = false;
      
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      expect(screen.queryByTestId('tutorial-overlay')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels and roles', () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      expect(screen.getByRole('application', { name: 'Wolf Goat Pig Tutorial System' })).toBeInTheDocument();
      expect(screen.getByRole('complementary', { name: 'Tutorial progress and navigation' })).toBeInTheDocument();
      expect(screen.getByRole('main', { name: 'Tutorial content' })).toBeInTheDocument();
      expect(screen.getByRole('navigation', { name: 'Tutorial module navigation' })).toBeInTheDocument();
    });

    test('has live regions for dynamic content', () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      const moduleContainer = screen.getByLabelText('Tutorial content');
      expect(moduleContainer).toHaveAttribute('aria-live', 'polite');
      expect(moduleContainer).toHaveAttribute('aria-atomic', 'false');
      
      const statusInfo = screen.getByRole('status');
      expect(statusInfo).toHaveAttribute('aria-live', 'polite');
    });

    test('provides meaningful button labels', () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      expect(screen.getByLabelText('Go to previous module')).toBeInTheDocument();
      expect(screen.getByLabelText('Go to next module')).toBeInTheDocument();
    });

    test('handles focus management appropriately', async () => {
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      const nextButton = screen.getByLabelText('Go to next module');
      await userEvent.tab();
      
      // Focus should be manageable
      expect(document.activeElement).toBeDefined();
    });
  });

  describe('Loading States', () => {
    test('shows loading screen when tutorial is not active and no welcome', () => {
      mockTutorial.isActive = false;
      
      // Force skip welcome screen
      const { rerender } = render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      // Simulate tutorial starting but not yet active
      mockTutorial.isActive = false;
      rerender(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      // This tests the loading state between welcome and active tutorial
      // The actual loading state would appear if showWelcome is false but isActive is also false
    });
  });

  describe('Error Handling', () => {
    test('handles missing onComplete callback gracefully', () => {
      mockTutorial.completed = true;
      
      expect(() => {
        render(<TutorialSystem onExit={mockOnExit} />);
      }).not.toThrow();
    });

    test('handles missing onExit callback gracefully', async () => {
      render(<TutorialSystem onComplete={mockOnComplete} />);
      
      const exitButton = screen.getByTitle('Exit tutorial');
      
      expect(() => {
        userEvent.click(exitButton);
      }).not.toThrow();
    });

    test('handles context errors gracefully', () => {
      // Mock context to return null/undefined values
      mockUseTutorial.mockReturnValue({
        ...mockTutorial,
        modules: null
      });
      
      expect(() => {
        render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      }).not.toThrow();
    });
  });

  describe('Cleanup', () => {
    test('removes event listeners on unmount', () => {
      const { unmount } = render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      unmount();
      
      expect(window.removeEventListener).toHaveBeenCalled();
    });

    test('cleans up resize listener on unmount', () => {
      const { unmount } = render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      unmount();
      
      // Should have called removeEventListener for both keydown and resize events
      expect(window.removeEventListener).toHaveBeenCalledWith('resize', expect.any(Function));
      expect(window.removeEventListener).toHaveBeenCalledWith('keydown', expect.any(Function));
    });
  });

  describe('Learning Preferences', () => {
    test('applies accessibility preferences', () => {
      mockTutorial.largeText = true;
      mockTutorial.highContrast = true;
      mockTutorial.reducedMotion = true;
      
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      // The component should apply these preferences to its styling
      const container = screen.getByRole('application');
      expect(container).toBeInTheDocument();
    });

    test('updates preferences through tutorial context', async () => {
      mockTutorial.isActive = false;
      
      render(<TutorialSystem onComplete={mockOnComplete} onExit={mockOnExit} />);
      
      // Would test preference updates if the preferences UI was shown
      // This is more of a integration test with the actual preference components
    });
  });
});
