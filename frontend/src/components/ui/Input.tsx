import React, { useId } from 'react';
import { useTheme } from '../../theme/Provider';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string | null;
  inputStyle?: React.CSSProperties;
  variant?: 'default' | 'inline';
  browserProtection?: boolean;
}

const Input: React.FC<InputProps> = ({ 
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
  variant = 'default',
  browserProtection = false,
  ...props 
}) => {
  const theme = useTheme();
  const generatedId = useId();
  const inputId = id || generatedId;
  
  const containerStyle: React.CSSProperties = {
    marginBottom: variant === 'inline' ? 0 : theme.spacing[4],
    ...style
  };

  const labelStyle: React.CSSProperties = {
    display: 'block',
    marginBottom: theme.spacing[2],
    fontSize: theme.typography.sm,
    fontWeight: theme.typography.medium,
    color: theme.colors.textPrimary,
  };

  const baseInputStyle: React.CSSProperties = {
    ...theme.inputStyle,
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.base,
    backgroundColor: disabled ? theme.colors.gray100 : theme.colors.paper,
    cursor: disabled ? 'not-allowed' : 'text',
    opacity: disabled ? 0.6 : 1,
    transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
    ...(error && {
      borderColor: theme.colors.error,
    }),
    ...inputStyle
  };

  const errorStyle: React.CSSProperties = {
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
        id={inputId}
        type={type}
        value={value}
        onChange={onChange}
        disabled={disabled}
        placeholder={placeholder}
        style={baseInputStyle}
        autoComplete={browserProtection ? 'off' : undefined}
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