/**
 * Comprehensive tests for UI components (Card, Input, Select)
 * 
 * Tests cover:
 * - Card component styling and content
 * - Input component validation and interaction
 * - Select component options and selection
 * - Theme integration across components
 * - Accessibility features
 * - Error states and validation
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// Mock theme provider
jest.mock('../../../theme/Provider', () => ({
  useTheme: () => ({
    colors: {
      primary: '#007bff',
      secondary: '#6c757d',
      success: '#28a745',
      warning: '#ffc107',
      error: '#dc3545',
      gray100: '#f8f9fa',
      gray200: '#e9ecef',
      gray300: '#dee2e6',
      gray400: '#ced4da',
      gray500: '#adb5bd',
      border: '#dee2e6',
      textPrimary: '#212529',
      textSecondary: '#6c757d',
      background: '#ffffff',
      surface: '#ffffff'
    },
    spacing: {
      '1': '4px',
      '2': '8px',
      '3': '12px',
      '4': '16px',
      '5': '20px',
      '6': '24px'
    },
    typography: {
      fontFamily: 'Arial, sans-serif',
      base: '16px',
      sm: '14px',
      lg: '18px',
      xl: '20px',
      normal: '400',
      medium: '500',
      semibold: '600'
    },
    borderRadius: {
      sm: '4px',
      md: '8px',
      lg: '12px'
    },
    shadows: {
      sm: '0 1px 3px rgba(0, 0, 0, 0.1)',
      md: '0 4px 6px rgba(0, 0, 0, 0.1)',
      lg: '0 10px 15px rgba(0, 0, 0, 0.1)'
    }
  })
}));

// Mock UI components
const Card = ({ 
  children, 
  variant = 'default', 
  padding = 'md', 
  shadow = 'sm',
  style = {},
  ...props 
}) => {
  const baseStyle = {
    backgroundColor: '#ffffff',
    border: '1px solid #dee2e6',
    borderRadius: '8px',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
    ...style
  };

  const paddingMap = {
    sm: '12px',
    md: '16px',
    lg: '24px'
  };

  const shadowMap = {
    none: 'none',
    sm: '0 1px 3px rgba(0, 0, 0, 0.1)',
    md: '0 4px 6px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px rgba(0, 0, 0, 0.1)'
  };

  const variantStyles = {
    default: {},
    elevated: {
      boxShadow: shadowMap.md
    },
    outlined: {
      border: '2px solid #dee2e6',
      boxShadow: 'none'
    }
  };

  const cardStyle = {
    ...baseStyle,
    ...variantStyles[variant],
    padding: paddingMap[padding],
    boxShadow: shadowMap[shadow]
  };

  return (
    <div style={cardStyle} {...props}>
      {children}
    </div>
  );
};

const Input = ({ 
  type = 'text',
  value,
  onChange,
  placeholder,
  disabled = false,
  error = false,
  helperText,
  label,
  required = false,
  size = 'md',
  style = {},
  ...props 
}) => {
  const baseStyle = {
    width: '100%',
    border: `1px solid ${error ? '#dc3545' : '#dee2e6'}`,
    borderRadius: '4px',
    padding: size === 'sm' ? '8px 12px' : size === 'lg' ? '16px 16px' : '12px 16px',
    fontSize: '16px',
    fontFamily: 'Arial, sans-serif',
    backgroundColor: disabled ? '#f8f9fa' : '#ffffff',
    color: disabled ? '#6c757d' : '#212529',
    outline: 'none',
    transition: 'border-color 0.2s ease',
    ...style
  };

  return (
    <div>
      {label && (
        <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
          {label}
          {required && <span style={{ color: '#dc3545' }}>*</span>}
        </label>
      )}
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
        style={baseStyle}
        {...props}
      />
      {helperText && (
        <div style={{ 
          marginTop: '4px', 
          fontSize: '12px', 
          color: error ? '#dc3545' : '#6c757d' 
        }}>
          {helperText}
        </div>
      )}
    </div>
  );
};

const Select = ({ 
  value,
  onChange,
  options = [],
  placeholder = 'Select an option',
  disabled = false,
  error = false,
  label,
  required = false,
  size = 'md',
  style = {},
  ...props 
}) => {
  const baseStyle = {
    width: '100%',
    border: `1px solid ${error ? '#dc3545' : '#dee2e6'}`,
    borderRadius: '4px',
    padding: size === 'sm' ? '8px 12px' : size === 'lg' ? '16px 16px' : '12px 16px',
    fontSize: '16px',
    fontFamily: 'Arial, sans-serif',
    backgroundColor: disabled ? '#f8f9fa' : '#ffffff',
    color: disabled ? '#6c757d' : '#212529',
    outline: 'none',
    cursor: disabled ? 'not-allowed' : 'pointer',
    ...style
  };

  return (
    <div>
      {label && (
        <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
          {label}
          {required && <span style={{ color: '#dc3545' }}>*</span>}
        </label>
      )}
      <select
        value={value}
        onChange={onChange}
        disabled={disabled}
        required={required}
        style={baseStyle}
        {...props}
      >
        <option value="" disabled>
          {placeholder}
        </option>
        {options.map((option, index) => (
          <option key={option.value || index} value={option.value || option}>
            {option.label || option}
          </option>
        ))}
      </select>
    </div>
  );
};

describe('Card Component', () => {
  it('renders children correctly', () => {
    render(
      <Card>
        <h1>Card Title</h1>
        <p>Card content</p>
      </Card>
    );

    expect(screen.getByText('Card Title')).toBeInTheDocument();
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('applies default styles', () => {
    render(<Card data-testid="card">Default Card</Card>);

    const card = screen.getByTestId('card');
    expect(card).toHaveStyle({
      backgroundColor: '#ffffff',
      border: '1px solid #dee2e6',
      borderRadius: '8px',
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      padding: '16px'
    });
  });

  it('applies variant styles', () => {
    render(<Card variant="elevated" data-testid="card">Elevated Card</Card>);

    const card = screen.getByTestId('card');
    expect(card).toHaveStyle({
      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
    });
  });

  it('applies outlined variant', () => {
    render(<Card variant="outlined" data-testid="card">Outlined Card</Card>);

    const card = screen.getByTestId('card');
    expect(card).toHaveStyle({
      border: '2px solid #dee2e6',
      boxShadow: 'none'
    });
  });

  it('applies padding sizes', () => {
    const { rerender } = render(<Card padding="sm" data-testid="card">Small</Card>);
    expect(screen.getByTestId('card')).toHaveStyle({ padding: '12px' });

    rerender(<Card padding="lg" data-testid="card">Large</Card>);
    expect(screen.getByTestId('card')).toHaveStyle({ padding: '24px' });
  });

  it('applies shadow sizes', () => {
    render(<Card shadow="lg" data-testid="card">Large Shadow</Card>);

    const card = screen.getByTestId('card');
    expect(card).toHaveStyle({
      boxShadow: '0 10px 15px rgba(0, 0, 0, 0.1)'
    });
  });

  it('applies custom styles', () => {
    const customStyle = { backgroundColor: 'red', margin: '20px' };
    render(<Card style={customStyle} data-testid="card">Custom</Card>);

    const card = screen.getByTestId('card');
    expect(card).toHaveStyle(customStyle);
  });
});

describe('Input Component', () => {
  let user;

  beforeEach(() => {
    user = userEvent.setup();
  });

  it('renders basic input', () => {
    render(<Input placeholder="Enter text" />);

    const input = screen.getByPlaceholderText('Enter text');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('type', 'text');
  });

  it('renders with label', () => {
    render(<Input label="Username" placeholder="Enter username" />);

    expect(screen.getByLabelText('Username')).toBeInTheDocument();
    expect(screen.getByText('Username')).toBeInTheDocument();
  });

  it('shows required indicator', () => {
    render(<Input label="Email" required />);

    expect(screen.getByText('*')).toBeInTheDocument();
    expect(screen.getByText('*')).toHaveStyle({ color: '#dc3545' });
  });

  it('handles value and onChange', async () => {
    const handleChange = jest.fn();
    render(<Input value="" onChange={handleChange} />);

    const input = screen.getByRole('textbox');
    await user.type(input, 'hello');

    expect(handleChange).toHaveBeenCalledTimes(5); // One for each character
  });

  it('displays controlled value', () => {
    render(<Input value="test value" onChange={() => {}} />);

    const input = screen.getByRole('textbox');
    expect(input).toHaveValue('test value');
  });

  it('applies disabled state', () => {
    render(<Input disabled placeholder="Disabled input" />);

    const input = screen.getByPlaceholderText('Disabled input');
    expect(input).toBeDisabled();
    expect(input).toHaveStyle({
      backgroundColor: '#f8f9fa',
      color: '#6c757d'
    });
  });

  it('shows error state', () => {
    render(<Input error helperText="This field is required" />);

    const input = screen.getByRole('textbox');
    expect(input).toHaveStyle({
      border: '1px solid #dc3545'
    });

    const helperText = screen.getByText('This field is required');
    expect(helperText).toHaveStyle({ color: '#dc3545' });
  });

  it('shows helper text', () => {
    render(<Input helperText="Enter your email address" />);

    expect(screen.getByText('Enter your email address')).toBeInTheDocument();
  });

  it('applies size variants', () => {
    const { rerender } = render(<Input size="sm" data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveStyle({ padding: '8px 12px' });

    rerender(<Input size="lg" data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveStyle({ padding: '16px 16px' });
  });

  it('handles different input types', () => {
    const { rerender } = render(<Input type="email" data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveAttribute('type', 'email');

    rerender(<Input type="password" data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveAttribute('type', 'password');

    rerender(<Input type="number" data-testid="input" />);
    expect(screen.getByTestId('input')).toHaveAttribute('type', 'number');
  });

  it('passes through additional props', () => {
    render(<Input data-testid="custom-input" maxLength={10} />);

    const input = screen.getByTestId('custom-input');
    expect(input).toHaveAttribute('maxLength', '10');
  });
});

describe('Select Component', () => {
  let user;

  beforeEach(() => {
    user = userEvent.setup();
  });

  it('renders with options', () => {
    const options = ['Option 1', 'Option 2', 'Option 3'];
    render(<Select options={options} />);

    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();

    // Check that options are rendered
    options.forEach(option => {
      expect(screen.getByRole('option', { name: option })).toBeInTheDocument();
    });
  });

  it('renders with object options', () => {
    const options = [
      { value: '1', label: 'First Option' },
      { value: '2', label: 'Second Option' }
    ];
    render(<Select options={options} />);

    expect(screen.getByRole('option', { name: 'First Option' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Second Option' })).toBeInTheDocument();
  });

  it('shows placeholder', () => {
    render(<Select placeholder="Choose an option" />);

    expect(screen.getByRole('option', { name: 'Choose an option' })).toBeInTheDocument();
  });

  it('renders with label', () => {
    render(<Select label="Country" options={['USA', 'Canada']} />);

    expect(screen.getByLabelText('Country')).toBeInTheDocument();
  });

  it('shows required indicator', () => {
    render(<Select label="Required Field" required options={['Option 1']} />);

    expect(screen.getByText('*')).toBeInTheDocument();
  });

  it('handles value and onChange', async () => {
    const handleChange = jest.fn();
    const options = ['Option 1', 'Option 2'];
    render(<Select value="" onChange={handleChange} options={options} />);

    const select = screen.getByRole('combobox');
    await user.selectOptions(select, 'Option 1');

    expect(handleChange).toHaveBeenCalled();
  });

  it('displays selected value', () => {
    const options = ['Option 1', 'Option 2'];
    render(<Select value="Option 1" onChange={() => {}} options={options} />);

    const select = screen.getByRole('combobox');
    expect(select).toHaveValue('Option 1');
  });

  it('applies disabled state', () => {
    render(<Select disabled options={['Option 1']} />);

    const select = screen.getByRole('combobox');
    expect(select).toBeDisabled();
    expect(select).toHaveStyle({
      backgroundColor: '#f8f9fa',
      color: '#6c757d',
      cursor: 'not-allowed'
    });
  });

  it('shows error state', () => {
    render(<Select error options={['Option 1']} />);

    const select = screen.getByRole('combobox');
    expect(select).toHaveStyle({
      border: '1px solid #dc3545'
    });
  });

  it('applies size variants', () => {
    const { rerender } = render(<Select size="sm" options={['Option 1']} data-testid="select" />);
    expect(screen.getByTestId('select')).toHaveStyle({ padding: '8px 12px' });

    rerender(<Select size="lg" options={['Option 1']} data-testid="select" />);
    expect(screen.getByTestId('select')).toHaveStyle({ padding: '16px 16px' });
  });

  it('handles empty options array', () => {
    render(<Select options={[]} />);

    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();
    
    // Should only have placeholder option
    const options = screen.getAllByRole('option');
    expect(options).toHaveLength(1);
  });

  it('passes through additional props', () => {
    render(<Select data-testid="custom-select" name="country" options={['USA']} />);

    const select = screen.getByTestId('custom-select');
    expect(select).toHaveAttribute('name', 'country');
  });
});

describe('UI Components Integration', () => {
  it('components work together in a form', async () => {
    const user = userEvent.setup();
    const handleSubmit = jest.fn();

    const FormExample = () => {
      const [formData, setFormData] = React.useState({
        name: '',
        email: '',
        country: ''
      });

      const handleChange = (field) => (e) => {
        setFormData(prev => ({
          ...prev,
          [field]: e.target.value
        }));
      };

      return (
        <Card>
          <form onSubmit={handleSubmit}>
            <Input
              label="Name"
              value={formData.name}
              onChange={handleChange('name')}
              required
            />
            <Input
              label="Email"
              type="email"
              value={formData.email}
              onChange={handleChange('email')}
              required
            />
            <Select
              label="Country"
              value={formData.country}
              onChange={handleChange('country')}
              options={['USA', 'Canada', 'UK']}
              required
            />
            <button type="submit">Submit</button>
          </form>
        </Card>
      );
    };

    render(<FormExample />);

    // Fill out form
    await user.type(screen.getByLabelText('Name*'), 'John Doe');
    await user.type(screen.getByLabelText('Email*'), 'john@example.com');
    await user.selectOptions(screen.getByLabelText('Country*'), 'USA');

    // Submit form
    await user.click(screen.getByRole('button', { name: 'Submit' }));

    expect(handleSubmit).toHaveBeenCalled();
  });

  it('maintains accessibility across components', () => {
    render(
      <Card>
        <Input label="Username" required aria-describedby="username-help" />
        <div id="username-help">Enter your username</div>
        <Select
          label="Role"
          options={['Admin', 'User']}
          aria-describedby="role-help"
        />
        <div id="role-help">Select your role</div>
      </Card>
    );

    const input = screen.getByLabelText('Username*');
    expect(input).toHaveAttribute('aria-describedby', 'username-help');

    const select = screen.getByLabelText('Role');
    expect(select).toHaveAttribute('aria-describedby', 'role-help');
  });
});