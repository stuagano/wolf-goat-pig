import React from 'react';
import { useTheme } from '../../theme/Provider';

const Select = ({ 
  label,
  error,
  disabled = false,
  placeholder = 'Select an option...',
  value,
  onChange,
  options = [],
  style = {},
  selectStyle = {},
  ...props 
}) => {
  const theme = useTheme();
  
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

  const baseSelectStyle = {
    ...theme.inputStyle,
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.base,
    backgroundColor: disabled ? theme.colors.gray100 : theme.colors.paper,
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.6 : 1,
    transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
    appearance: 'none',
    backgroundImage: `url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6,9 12,15 18,9'%3e%3c/polyline%3e%3c/svg%3e")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 12px center',
    backgroundSize: '16px',
    paddingRight: theme.spacing[10],
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
    ...selectStyle
  };

  const errorStyle = {
    marginTop: theme.spacing[1],
    fontSize: theme.typography.xs,
    color: theme.colors.error,
  };

  const optionStyle = {
    padding: theme.spacing[2],
    backgroundColor: theme.colors.paper,
    color: theme.colors.textPrimary,
  };

  return (
    <div style={containerStyle}>
      {label && (
        <label style={labelStyle}>
          {label}
        </label>
      )}
      <select
        value={value}
        onChange={onChange}
        disabled={disabled}
        style={baseSelectStyle}
        {...props}
      >
        {placeholder && (
          <option value="" style={optionStyle}>
            {placeholder}
          </option>
        )}
        {options.map((option, index) => (
          <option 
            key={option.value || index} 
            value={option.value || option}
            style={optionStyle}
          >
            {option.label || option}
          </option>
        ))}
      </select>
      {error && (
        <div style={errorStyle}>
          {error}
        </div>
      )}
    </div>
  );
};

export default Select;