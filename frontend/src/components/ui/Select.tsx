import React, { useId } from 'react';
import { useTheme } from '../../theme/Provider';

interface SelectOption {
  value: string | number;
  label: string;
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string | null;
  options: (SelectOption | string)[];
  selectStyle?: React.CSSProperties;
  placeholder?: string;
}

const Select: React.FC<SelectProps> = ({ 
  label,
  error,
  disabled = false,
  placeholder = 'Select an option...',
  value,
  onChange,
  options = [],
  style = {},
  selectStyle = {},
  id,
  ...props 
}) => {
  const theme = useTheme();
  const generatedId = useId();
  const selectId = id || generatedId;
  
  const containerStyle: React.CSSProperties = {
    marginBottom: theme.spacing[4],
    ...style
  };

  const labelStyle: React.CSSProperties = {
    display: 'block',
    marginBottom: theme.spacing[2],
    fontSize: theme.typography.sm,
    fontWeight: theme.typography.medium,
    color: theme.colors.textPrimary,
  };

  const baseSelectStyle: React.CSSProperties = {
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
    ...(error && {
      borderColor: theme.colors.error,
    }),
    ...selectStyle
  };

  const errorStyle: React.CSSProperties = {
    marginTop: theme.spacing[1],
    fontSize: theme.typography.xs,
    color: theme.colors.error,
  };

  const optionStyle: React.CSSProperties = {
    padding: theme.spacing[2],
    backgroundColor: theme.colors.paper,
    color: theme.colors.textPrimary,
  };

  return (
    <div style={containerStyle}>
      {label && (
        <label style={labelStyle} htmlFor={selectId}>
          {label}
        </label>
      )}
      <select
        value={value}
        onChange={onChange}
        disabled={disabled}
        style={baseSelectStyle}
        id={selectId}
        {...props}
      >
        {placeholder && (
          <option value="" style={optionStyle}>
            {placeholder}
          </option>
        )}
        {options.map((option, index) => {
          const optValue = typeof option === 'string' ? option : option.value;
          const optLabel = typeof option === 'string' ? option : option.label;
          return (
            <option 
              key={String(optValue) || index} 
              value={optValue}
              style={optionStyle}
            >
              {optLabel}
            </option>
          );
        })}
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