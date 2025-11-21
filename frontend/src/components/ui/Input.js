import React, { useId } from 'react';
import { useTheme } from '../../theme/Provider';

const Input = ({
  label,
  error,
  disabled = false,
  type = 'text',
  placeholder,
  value,
  onChange,
  style = {},
  inputStyle = {},
  id,
  variant = 'default', // 'default' | 'inline'
  browserProtection = true, // Enable browser extension protection by default
  ...props
}) => {
  const theme = useTheme();
  const generatedId = useId();
  const inputId = id || generatedId;
  
  const containerStyle = {
    marginBottom: theme.spacing[4],
    ...style
  };

  const labelStyle = {
    display: 'block',
    marginBottom: theme.spacing[2],
    fontSize: theme.typography.sm,
    fontWeight: theme.typography.medium,
    color: theme.colors.textPrimary,
  };

  const baseInputStyle = {
    ...theme.inputStyle,
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.base,
    backgroundColor: disabled ? theme.colors.gray100 : theme.colors.paper,
    cursor: disabled ? 'not-allowed' : 'text',
    opacity: disabled ? 0.6 : 1,
    transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
    '&:focus': {
      outline: 'none',
      borderColor: theme.colors.primary,
      boxShadow: `0 0 0 3px ${theme.colors.primary}20`,
    },
    ...(error && {
      borderColor: theme.colors.error,
      '&:focus': {
        borderColor: theme.colors.error,
        boxShadow: `0 0 0 3px ${theme.colors.error}20`,
      }
    }),
    ...inputStyle
  };

  const errorStyle = {
    marginTop: theme.spacing[1],
    fontSize: theme.typography.xs,
    color: theme.colors.error,
  };

  // Browser extension protection attributes
  const protectionProps = browserProtection ? {
    autoComplete: 'off',
    'data-lpignore': 'true',
    'data-form-type': 'other',
    'data-1p-ignore': 'true'
  } : {};

  // Input element
  const inputElement = (
    <input
      type={type}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      disabled={disabled}
      style={variant === 'inline' ? inputStyle : baseInputStyle}
      id={inputId}
      {...protectionProps}
      {...props}
    />
  );

  // Inline variant: just return the input
  if (variant === 'inline') {
    return inputElement;
  }

  // Default variant: return input with label and error
  return (
    <div style={containerStyle}>
      {label && (
        <label style={labelStyle} htmlFor={inputId}>
          {label}
        </label>
      )}
      {inputElement}
      {error && (
        <div style={errorStyle}>
          {error}
        </div>
      )}
    </div>
  );
};

export default Input;
