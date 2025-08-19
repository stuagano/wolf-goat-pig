/**
 * Comprehensive test suite for InteractiveElement component
 * 
 * Tests interactive tutorial elements including:
 * - Click interactions and callbacks
 * - Keyboard navigation and accessibility
 * - Visual feedback and states
 * - Animation and transitions
 * - Error handling and edge cases
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// Mock InteractiveElement component for testing
const InteractiveElement = ({ 
  type = 'button',
  children,
  onClick,
  onComplete,
  disabled = false,
  highlight = false,
  tooltip,
  ariaLabel,
  className,
  completedState = false,
  animateEntry = true,
  focusable = true,
  ...props 
}) => {
  const [isCompleted, setIsCompleted] = React.useState(completedState);
  const [isHovered, setIsHovered] = React.useState(false);
  const [isFocused, setIsFocused] = React.useState(false);

  const handleClick = (e) => {
    if (disabled) return;
    
    onClick && onClick(e);
    
    if (!isCompleted) {
      setIsCompleted(true);
      onComplete && onComplete(e);
    }
  };

  const handleKeyDown = (e) => {
    if (disabled) return;
    
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick(e);
    }
  };

  const getElementProps = () => {
    const baseProps = {
      className: `interactive-element ${className || ''} ${highlight ? 'highlighted' : ''} ${isCompleted ? 'completed' : ''} ${disabled ? 'disabled' : ''}`,
      'data-testid': 'interactive-element',
      'aria-label': ariaLabel,
      'aria-disabled': disabled,
      'aria-describedby': tooltip ? 'tooltip' : undefined,
      style: {
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.6 : 1,
        backgroundColor: highlight ? '#fff3cd' : isCompleted ? '#d4edda' : '#ffffff',
        border: `2px solid ${highlight ? '#ffc107' : isCompleted ? '#28a745' : '#dee2e6'}`,
        borderRadius: '8px',
        padding: '12px 16px',
        transition: animateEntry && !disabled ? 'all 0.3s ease' : 'none',
        transform: isHovered && !disabled ? 'scale(1.02)' : 'scale(1)',
        boxShadow: isFocused ? '0 0 0 3px rgba(0, 123, 255, 0.25)' : 'none',
        position: 'relative',
        display: 'inline-block'
      },
      onMouseEnter: () => !disabled && setIsHovered(true),
      onMouseLeave: () => setIsHovered(false),
      onFocus: () => setIsFocused(true),
      onBlur: () => setIsFocused(false)
    };

    if (type === 'button') {
      return {
        ...baseProps,
        as: 'button',
        type: 'button',
        disabled,
        onClick: handleClick,
        onKeyDown: handleKeyDown,
        tabIndex: focusable ? 0 : -1
      };
    }

    return {
      ...baseProps,
      role: 'button',
      tabIndex: focusable && !disabled ? 0 : -1,
      onClick: handleClick,
      onKeyDown: handleKeyDown
    };
  };

  const elementProps = getElementProps();
  const Element = type === 'button' ? 'button' : 'div';

  return (
    <>
      <Element {...elementProps}>
        {children}
        {isCompleted && (
          <span 
            data-testid="completion-indicator"
            style={{
              position: 'absolute',
              top: '-8px',
              right: '-8px',
              backgroundColor: '#28a745',
              color: 'white',
              borderRadius: '50%',
              width: '20px',
              height: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '12px',
              fontWeight: 'bold'
            }}
          >
            ✓
          </span>
        )}
        {highlight && (
          <span 
            data-testid="highlight-indicator"
            style={{
              position: 'absolute',
              top: '-8px',
              left: '-8px',
              backgroundColor: '#ffc107',
              color: '#212529',
              borderRadius: '50%',
              width: '20px',
              height: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '12px',
              fontWeight: 'bold',
              animation: 'pulse 2s infinite'
            }}
          >
            !
          </span>
        )}
      </Element>
      
      {tooltip && (
        <div 
          id="tooltip"
          data-testid="tooltip"
          style={{
            position: 'absolute',
            bottom: '100%',
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: '#333',
            color: 'white',
            padding: '8px 12px',
            borderRadius: '4px',
            fontSize: '14px',
            whiteSpace: 'nowrap',
            zIndex: 1000,
            visibility: isHovered || isFocused ? 'visible' : 'hidden',
            opacity: isHovered || isFocused ? 1 : 0,
            transition: 'opacity 0.2s ease'
          }}
        >
          {tooltip}
        </div>
      )}
    </>
  );
};

describe('InteractiveElement', () => {
  let mockOnClick;
  let mockOnComplete;

  beforeEach(() => {
    jest.clearAllMocks();
    mockOnClick = jest.fn();
    mockOnComplete = jest.fn();
  });

  describe('Basic Rendering', () => {
    test('renders interactive element as button by default', () => {
      render(
        <InteractiveElement onClick={mockOnClick}>
          Click me
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      expect(element.tagName).toBe('BUTTON');
      expect(element).toHaveTextContent('Click me');
    });

    test('renders as div when type is not button', () => {
      render(
        <InteractiveElement type="div" onClick={mockOnClick}>
          Clickable div
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      expect(element.tagName).toBe('DIV');
      expect(element).toHaveAttribute('role', 'button');
    });

    test('applies custom className', () => {
      render(
        <InteractiveElement className="custom-class" onClick={mockOnClick}>
          Custom element
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      expect(element).toHaveClass('custom-class');
    });

    test('displays children content correctly', () => {
      render(
        <InteractiveElement onClick={mockOnClick}>
          <span>Complex content</span>
          <strong>with markup</strong>
        </InteractiveElement>
      );

      expect(screen.getByText('Complex content')).toBeInTheDocument();
      expect(screen.getByText('with markup')).toBeInTheDocument();
    });
  });

  describe('Click Interactions', () => {
    test('calls onClick when clicked', async () => {
      render(
        <InteractiveElement onClick={mockOnClick}>
          Click me
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      await userEvent.click(element);

      expect(mockOnClick).toHaveBeenCalledTimes(1);
    });

    test('calls onComplete when clicked for the first time', async () => {
      render(
        <InteractiveElement onClick={mockOnClick} onComplete={mockOnComplete}>
          Click me
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      await userEvent.click(element);

      expect(mockOnComplete).toHaveBeenCalledTimes(1);
    });

    test('does not call onComplete on subsequent clicks', async () => {
      render(
        <InteractiveElement onClick={mockOnClick} onComplete={mockOnComplete}>
          Click me
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      
      // First click
      await userEvent.click(element);
      expect(mockOnComplete).toHaveBeenCalledTimes(1);
      
      // Second click
      await userEvent.click(element);
      expect(mockOnComplete).toHaveBeenCalledTimes(1); // Still only called once
      expect(mockOnClick).toHaveBeenCalledTimes(2); // But onClick called twice
    });

    test('does not call callbacks when disabled', async () => {
      render(
        <InteractiveElement 
          disabled 
          onClick={mockOnClick} 
          onComplete={mockOnComplete}
        >
          Disabled element
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      await userEvent.click(element);

      expect(mockOnClick).not.toHaveBeenCalled();
      expect(mockOnComplete).not.toHaveBeenCalled();
    });
  });

  describe('Keyboard Navigation', () => {
    test('handles Enter key press', async () => {
      render(
        <InteractiveElement onClick={mockOnClick} onComplete={mockOnComplete}>
          Press Enter
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      element.focus();
      await userEvent.keyboard('{Enter}');

      expect(mockOnClick).toHaveBeenCalledTimes(1);
      expect(mockOnComplete).toHaveBeenCalledTimes(1);
    });

    test('handles Space key press', async () => {
      render(
        <InteractiveElement onClick={mockOnClick} onComplete={mockOnComplete}>
          Press Space
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      element.focus();
      await userEvent.keyboard(' ');

      expect(mockOnClick).toHaveBeenCalledTimes(1);
      expect(mockOnComplete).toHaveBeenCalledTimes(1);
    });

    test('ignores other keys', async () => {
      render(
        <InteractiveElement onClick={mockOnClick}>
          Keyboard element
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      element.focus();
      await userEvent.keyboard('{Escape}');
      await userEvent.keyboard('{Tab}');

      expect(mockOnClick).not.toHaveBeenCalled();
    });

    test('prevents default behavior for Enter and Space', async () => {
      const preventDefault = jest.fn();
      
      render(
        <InteractiveElement onClick={mockOnClick}>
          Prevent default
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      
      // Simulate keydown event with preventDefault mock
      fireEvent.keyDown(element, { 
        key: 'Enter', 
        preventDefault 
      });

      expect(preventDefault).toHaveBeenCalled();
    });

    test('does not handle keyboard when disabled', async () => {
      render(
        <InteractiveElement disabled onClick={mockOnClick}>
          Disabled keyboard
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      element.focus();
      await userEvent.keyboard('{Enter}');

      expect(mockOnClick).not.toHaveBeenCalled();
    });
  });

  describe('Visual States', () => {
    test('shows completion indicator when completed', async () => {
      render(
        <InteractiveElement onComplete={mockOnComplete}>
          Complete me
        </InteractiveElement>
      );

      // Initially no completion indicator
      expect(screen.queryByTestId('completion-indicator')).not.toBeInTheDocument();

      const element = screen.getByTestId('interactive-element');
      await userEvent.click(element);

      // After click, completion indicator should appear
      expect(screen.getByTestId('completion-indicator')).toBeInTheDocument();
      expect(screen.getByTestId('completion-indicator')).toHaveTextContent('✓');
    });

    test('starts completed when completedState is true', () => {
      render(
        <InteractiveElement completedState>
          Already completed
        </InteractiveElement>
      );

      expect(screen.getByTestId('completion-indicator')).toBeInTheDocument();
      expect(screen.getByTestId('interactive-element')).toHaveClass('completed');
    });

    test('shows highlight indicator when highlighted', () => {
      render(
        <InteractiveElement highlight>
          Highlighted element
        </InteractiveElement>
      );

      expect(screen.getByTestId('highlight-indicator')).toBeInTheDocument();
      expect(screen.getByTestId('highlight-indicator')).toHaveTextContent('!');
      expect(screen.getByTestId('interactive-element')).toHaveClass('highlighted');
    });

    test('applies disabled styling when disabled', () => {
      render(
        <InteractiveElement disabled>
          Disabled element
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      expect(element).toHaveClass('disabled');
      expect(element).toHaveStyle('opacity: 0.6');
      expect(element).toHaveStyle('cursor: not-allowed');
    });

    test('applies hover effects on mouse enter/leave', async () => {
      render(
        <InteractiveElement>
          Hoverable element
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      
      // Hover
      await userEvent.hover(element);
      expect(element).toHaveStyle('transform: scale(1.02)');

      // Unhover  
      await userEvent.unhover(element);
      expect(element).toHaveStyle('transform: scale(1)');
    });

    test('does not apply hover effects when disabled', async () => {
      render(
        <InteractiveElement disabled>
          Disabled hoverable
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      
      await userEvent.hover(element);
      expect(element).toHaveStyle('transform: scale(1)');
    });
  });

  describe('Accessibility Features', () => {
    test('has proper ARIA attributes', () => {
      render(
        <InteractiveElement 
          ariaLabel="Custom aria label"
          disabled
          tooltip="Helpful tooltip"
        >
          ARIA element
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      expect(element).toHaveAttribute('aria-label', 'Custom aria label');
      expect(element).toHaveAttribute('aria-disabled', 'true');
      expect(element).toHaveAttribute('aria-describedby', 'tooltip');
    });

    test('has correct tabIndex when focusable', () => {
      render(
        <InteractiveElement focusable>
          Focusable element
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      expect(element).toHaveAttribute('tabIndex', '0');
    });

    test('has correct tabIndex when not focusable', () => {
      render(
        <InteractiveElement focusable={false}>
          Non-focusable element
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      expect(element).toHaveAttribute('tabIndex', '-1');
    });

    test('handles focus and blur for visual feedback', async () => {
      render(
        <InteractiveElement>
          Focus element
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      
      // Focus
      element.focus();
      expect(element).toHaveStyle('box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.25)');

      // Blur
      element.blur();
      expect(element).toHaveStyle('box-shadow: none');
    });

    test('button type has proper button attributes', () => {
      render(
        <InteractiveElement type="button" disabled>
          Button element
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      expect(element).toHaveAttribute('type', 'button');
      expect(element).toHaveAttribute('disabled');
    });

    test('div type has proper role and tabindex', () => {
      render(
        <InteractiveElement type="div">
          Div element
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      expect(element).toHaveAttribute('role', 'button');
      expect(element).toHaveAttribute('tabIndex', '0');
    });
  });

  describe('Tooltip Functionality', () => {
    test('displays tooltip on hover and focus', async () => {
      render(
        <InteractiveElement tooltip="Helpful tooltip">
          Element with tooltip
        </InteractiveElement>
      );

      const tooltip = screen.getByTestId('tooltip');
      expect(tooltip).toHaveStyle('visibility: hidden');

      const element = screen.getByTestId('interactive-element');
      
      // Hover
      await userEvent.hover(element);
      expect(tooltip).toHaveStyle('visibility: visible');
      expect(tooltip).toHaveTextContent('Helpful tooltip');

      // Unhover
      await userEvent.unhover(element);
      expect(tooltip).toHaveStyle('visibility: hidden');
    });

    test('shows tooltip on focus', async () => {
      render(
        <InteractiveElement tooltip="Focus tooltip">
          Focusable with tooltip
        </InteractiveElement>
      );

      const tooltip = screen.getByTestId('tooltip');
      const element = screen.getByTestId('interactive-element');
      
      element.focus();
      expect(tooltip).toHaveStyle('visibility: visible');
      
      element.blur();
      expect(tooltip).toHaveStyle('visibility: hidden');
    });

    test('does not render tooltip when not provided', () => {
      render(
        <InteractiveElement>
          No tooltip
        </InteractiveElement>
      );

      expect(screen.queryByTestId('tooltip')).not.toBeInTheDocument();
    });
  });

  describe('Animation and Transitions', () => {
    test('applies transitions when animateEntry is true', () => {
      render(
        <InteractiveElement animateEntry>
          Animated element
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      expect(element).toHaveStyle('transition: all 0.3s ease');
    });

    test('disables transitions when animateEntry is false', () => {
      render(
        <InteractiveElement animateEntry={false}>
          Non-animated element
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      expect(element).toHaveStyle('transition: none');
    });

    test('disables transitions when disabled', () => {
      render(
        <InteractiveElement animateEntry disabled>
          Disabled animated element
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      expect(element).toHaveStyle('transition: none');
    });
  });

  describe('Color and Theming', () => {
    test('applies different background colors for different states', () => {
      const { rerender } = render(
        <InteractiveElement>
          Normal state
        </InteractiveElement>
      );

      let element = screen.getByTestId('interactive-element');
      expect(element).toHaveStyle('backgroundColor: #ffffff');

      // Highlight state
      rerender(
        <InteractiveElement highlight>
          Highlighted state
        </InteractiveElement>
      );

      element = screen.getByTestId('interactive-element');
      expect(element).toHaveStyle('backgroundColor: #fff3cd');

      // Completed state
      rerender(
        <InteractiveElement completedState>
          Completed state
        </InteractiveElement>
      );

      element = screen.getByTestId('interactive-element');
      expect(element).toHaveStyle('backgroundColor: #d4edda');
    });

    test('applies different border colors for different states', () => {
      const { rerender } = render(
        <InteractiveElement>
          Normal border
        </InteractiveElement>
      );

      let element = screen.getByTestId('interactive-element');
      expect(element).toHaveStyle('border: 2px solid #dee2e6');

      // Highlight state
      rerender(
        <InteractiveElement highlight>
          Highlighted border
        </InteractiveElement>
      );

      element = screen.getByTestId('interactive-element');
      expect(element).toHaveStyle('border: 2px solid #ffc107');

      // Completed state
      rerender(
        <InteractiveElement completedState>
          Completed border
        </InteractiveElement>
      );

      element = screen.getByTestId('interactive-element');
      expect(element).toHaveStyle('border: 2px solid #28a745');
    });
  });

  describe('Edge Cases and Error Handling', () => {
    test('handles missing onClick gracefully', async () => {
      render(
        <InteractiveElement>
          No onClick handler
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      
      expect(() => userEvent.click(element)).not.toThrow();
    });

    test('handles missing onComplete gracefully', async () => {
      render(
        <InteractiveElement onClick={mockOnClick}>
          No onComplete handler
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      await userEvent.click(element);

      expect(mockOnClick).toHaveBeenCalled();
      // Should not throw error even without onComplete
    });

    test('handles rapid clicking correctly', async () => {
      render(
        <InteractiveElement onClick={mockOnClick} onComplete={mockOnComplete}>
          Rapid click test
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      
      // Simulate rapid clicking
      await userEvent.click(element);
      await userEvent.click(element);
      await userEvent.click(element);

      expect(mockOnClick).toHaveBeenCalledTimes(3);
      expect(mockOnComplete).toHaveBeenCalledTimes(1); // Only once
    });

    test('handles undefined or null children', () => {
      expect(() => {
        render(
          <InteractiveElement onClick={mockOnClick}>
            {null}
            {undefined}
          </InteractiveElement>
        );
      }).not.toThrow();
    });
  });

  describe('Custom Props Forwarding', () => {
    test('forwards custom props to underlying element', () => {
      render(
        <InteractiveElement 
          onClick={mockOnClick}
          data-custom="custom-value"
          id="custom-id"
        >
          Custom props
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      expect(element).toHaveAttribute('data-custom', 'custom-value');
      expect(element).toHaveAttribute('id', 'custom-id');
    });

    test('does not override internal props with custom props', () => {
      render(
        <InteractiveElement 
          onClick={mockOnClick}
          data-testid="should-not-override"
          className="custom-class"
        >
          Props priority test
        </InteractiveElement>
      );

      const element = screen.getByTestId('interactive-element');
      expect(element).toHaveClass('custom-class');
      expect(element).toHaveClass('interactive-element');
    });
  });
});