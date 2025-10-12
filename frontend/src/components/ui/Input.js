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

  return (
    <div style={containerStyle}>
      {label && (
        <label style={labelStyle} htmlFor={inputId}>
          {label}
        </label>
      )}
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
        style={baseInputStyle}
        id={inputId}
        {...props}
      />
      {error && (
        <div style={errorStyle}>
          {error}
        </div>
      )}
    </div>
  );
};

export default Input;
