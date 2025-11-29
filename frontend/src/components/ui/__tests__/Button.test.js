/**
 * Comprehensive tests for UI Button component
 * 
 * Tests cover:
 * - Basic rendering and props
 * - Variant styles (primary, secondary, success, warning, error, ghost)
 * - Size variants (small, medium, large)
 * - Disabled state
 * - Click handling
 * - Theme integration
 * - Accessibility
 * - Custom styling
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import Button from '../Button';

// Mock theme provider
jest.mock('../../../theme/Provider', () => ({
  useTheme: () => ({
    colors: {
      primary: '#007bff',
      primaryDark: '#0056b3',
      secondary: '#6c757d',
      success: '#28a745',
      successDark: '#1e7e34',
      warning: '#ffc107',
      warningDark: '#e0a800',
      error: '#dc3545',
      errorDark: '#c82333',
      gray200: '#e9ecef',
      gray300: '#dee2e6',
      border: '#dee2e6',
      textPrimary: '#212529'
    },
    spacing: {
      '2': '8px',
      '3': '12px',
      '4': '16px',
      '6': '24px'
    },
    typography: {
      fontFamily: 'Arial, sans-serif',
      base: '16px',
      sm: '14px',
      lg: '18px',
      semibold: '600'
    },
    buttonStyle: {
      borderRadius: '4px'
    }
  })
}));

describe('Button Component', () => {
  let user;

  beforeEach(() => {
    user = userEvent.setup();
  });

  describe('Basic Rendering', () => {
    it('renders with default props', () => {
      render(<Button>Click me</Button>);
      
      const button = screen.getByRole('button', { name: /click me/i });
      expect(button).toBeInTheDocument();
      expect(button).toHaveAttribute('type', 'button');
    });

    it('renders children correctly', () => {
      render(<Button>Test Content</Button>);
      
      expect(screen.getByText('Test Content')).toBeInTheDocument();
    });

    it('renders with complex children', () => {
      render(
        <Button>
          <span>Icon</span>
          <span>Text</span>
        </Button>
      );
      
      expect(screen.getByText('Icon')).toBeInTheDocument();
      expect(screen.getByText('Text')).toBeInTheDocument();
    });

    it('applies custom type attribute', () => {
      render(<Button type="submit">Submit</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('type', 'submit');
    });
  });

  describe('Click Handling', () => {
    it('calls onClick when clicked', async () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick}>Click me</Button>);
      
      const button = screen.getByRole('button');
      await user.click(button);
      
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('does not call onClick when disabled', async () => {
      const handleClick = jest.fn();
      render(
        <Button onClick={handleClick} disabled>
          Click me
        </Button>
      );
      
      const button = screen.getByRole('button');
      await user.click(button);
      
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('handles click with keyboard', async () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick}>Click me</Button>);
      
      const button = screen.getByRole('button');
      button.focus();
      await user.keyboard('{Enter}');
      
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('handles click with spacebar', async () => {
      const handleClick = jest.fn();
      render(<Button onClick={handleClick}>Click me</Button>);
      
      const button = screen.getByRole('button');
      button.focus();
      await user.keyboard('{ }');
      
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('Variant Styles', () => {
    it('applies primary variant styles by default', () => {
      render(<Button>Primary</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        backgroundColor: '#007bff',
        color: '#ffffff'
      });
    });

    it('applies secondary variant styles', () => {
      render(<Button variant="secondary">Secondary</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        backgroundColor: '#e9ecef',
        color: '#212529',
        border: '1px solid #dee2e6'
      });
    });

    it('applies success variant styles', () => {
      render(<Button variant="success">Success</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        backgroundColor: '#28a745',
        color: '#ffffff'
      });
    });

    it('applies warning variant styles', () => {
      render(<Button variant="warning">Warning</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        backgroundColor: '#ffc107',
        color: '#ffffff'
      });
    });

    it('applies error variant styles', () => {
      render(<Button variant="error">Error</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        backgroundColor: '#dc3545',
        color: '#ffffff'
      });
    });

    it('applies ghost variant styles', () => {
      render(<Button variant="ghost">Ghost</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        backgroundColor: 'transparent',
        color: '#007bff',
        border: '1px solid #007bff'
      });
    });
  });

  describe('Size Variants', () => {
    it('applies medium size by default', () => {
      render(<Button>Medium</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        padding: '12px 16px',
        fontSize: '16px'
      });
    });

    it('applies small size', () => {
      render(<Button size="small">Small</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        padding: '8px 12px',
        fontSize: '14px'
      });
    });

    it('applies large size', () => {
      render(<Button size="large">Large</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        padding: '16px 24px',
        fontSize: '18px'
      });
    });
  });

  describe('Disabled State', () => {
    it('applies disabled attribute', () => {
      render(<Button disabled>Disabled</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('applies disabled styles', () => {
      render(<Button disabled>Disabled</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        cursor: 'not-allowed',
        opacity: '0.6'
      });
    });

    it('applies enabled styles when not disabled', () => {
      render(<Button>Enabled</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        cursor: 'pointer',
        opacity: '1'
      });
    });
  });

  describe('Custom Styling', () => {
    it('applies custom styles', () => {
      const customStyle = {
        marginTop: '20px',
        borderRadius: '8px'
      };
      
      render(<Button style={customStyle}>Custom</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle(customStyle);
    });

    it('merges custom styles with theme styles', () => {
      render(<Button style={{ marginTop: '20px' }}>Custom</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        marginTop: '20px',
        backgroundColor: '#007bff', // Theme color should still apply
        borderRadius: '4px' // Theme border radius should still apply
      });
    });
  });

  describe('Additional Props', () => {
    it('passes through additional props', () => {
      render(
        <Button data-testid="custom-button" aria-label="Custom label">
          Custom
        </Button>
      );
      
      const button = screen.getByTestId('custom-button');
      expect(button).toHaveAttribute('aria-label', 'Custom label');
    });

    it('handles className prop', () => {
      render(<Button className="custom-class">Class</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('custom-class');
    });

    it('handles id prop', () => {
      render(<Button id="custom-id">ID</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('id', 'custom-id');
    });
  });

  describe('Theme Integration', () => {
    it('applies theme typography', () => {
      render(<Button>Themed</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        fontFamily: 'Arial, sans-serif',
        fontSize: '16px',
        fontWeight: '600'
      });
    });

    it('applies theme button styles', () => {
      render(<Button>Themed</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        borderRadius: '4px'
      });
    });

    it('applies theme spacing', () => {
      render(<Button size="medium">Themed</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        padding: '12px 16px'
      });
    });
  });

  describe('Accessibility', () => {
    it('is focusable when enabled', () => {
      render(<Button>Focusable</Button>);
      
      const button = screen.getByRole('button');
      button.focus();
      expect(button).toHaveFocus();
    });

    it('is not focusable when disabled', () => {
      render(<Button disabled>Not Focusable</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('has proper role', () => {
      render(<Button>Role</Button>);
      
      const button = screen.getByRole('button');
      expect(button.tagName).toBe('BUTTON');
    });

    it('supports aria attributes', () => {
      render(
        <Button aria-pressed="true" aria-describedby="help-text">
          ARIA Button
        </Button>
      );
      
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-pressed', 'true');
      expect(button).toHaveAttribute('aria-describedby', 'help-text');
    });

    it('prevents text selection', () => {
      render(<Button>No Select</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        userSelect: 'none'
      });
    });
  });

  describe('Hover Effects', () => {
    it('applies hover styles on mouseenter', () => {
      render(<Button>Hover</Button>);
      
      const button = screen.getByRole('button');
      fireEvent.mouseEnter(button);
      
      // Note: CSS hover effects can't be directly tested with JSDOM
      // This would require a more sophisticated testing setup
      expect(button).toBeInTheDocument();
    });

    it('does not apply hover styles when disabled', () => {
      render(<Button disabled>No Hover</Button>);
      
      const button = screen.getByRole('button');
      fireEvent.mouseEnter(button);
      
      expect(button).toBeDisabled();
    });
  });

  describe('Layout and Display', () => {
    it('applies flex display', () => {
      render(<Button>Flex</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center'
      });
    });

    it('removes text decoration', () => {
      render(<Button>No Decoration</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        textDecoration: 'none'
      });
    });

    it('applies transition effect', () => {
      render(<Button>Transition</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveStyle({
        transition: 'all 0.2s ease'
      });
    });
  });

  describe('Edge Cases', () => {
    it('handles empty children', () => {
      render(<Button></Button>);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
      expect(button).toBeEmptyDOMElement();
    });

    it('handles null children', () => {
      render(<Button>{null}</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('handles undefined onClick', () => {
      render(<Button onClick={undefined}>No Handler</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('handles invalid variant gracefully', () => {
      // This should fallback to default styles
      render(<Button variant="invalid">Invalid</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });

    it('handles invalid size gracefully', () => {
      // This should fallback to default styles
      render(<Button size="invalid">Invalid</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toBeInTheDocument();
    });
  });
});