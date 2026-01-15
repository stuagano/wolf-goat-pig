import React from 'react';
import { useTheme } from '../../theme/Provider';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'ghost' | 'outline' | 'danger';
  size?: 'small' | 'medium' | 'large';
  fullWidth?: boolean;
}

const Button: React.FC<ButtonProps> = ({ 
  children, 
  variant = 'primary', 
  size = 'medium', 
  fullWidth = false,
  style = {},
  disabled = false,
  type = 'button',
  ...props 
}) => {
  const theme = useTheme();
  
  const getVariantStyles = () => {
    switch (variant) {
      case 'primary':
        return {
          backgroundColor: theme.colors.primary,
          color: '#ffffff',
          border: 'none',
        };
      case 'secondary':
        return {
          backgroundColor: theme.colors.gray200,
          color: theme.colors.textPrimary,
          border: `1px solid ${theme.colors.gray300}`,
        };
      case 'success':
        return {
          backgroundColor: theme.colors.success,
          color: '#ffffff',
          border: 'none',
        };
      case 'warning':
        return {
          backgroundColor: theme.colors.warning,
          color: '#ffffff',
          border: 'none',
        };
      case 'error':
      case 'danger':
        return {
          backgroundColor: theme.colors.error,
          color: '#ffffff',
          border: 'none',
        };
      case 'ghost':
        return {
          backgroundColor: 'transparent',
          color: theme.colors.primary,
          border: `1px solid ${theme.colors.primary}`,
        };
      case 'outline':
        return {
          backgroundColor: 'transparent',
          color: theme.colors.primary,
          border: `2px solid ${theme.colors.primary}`,
        };
      default:
        return {
          backgroundColor: theme.colors.primary,
          color: '#ffffff',
          border: 'none',
        };
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          padding: '8px 12px',
          fontSize: theme.typography.sm,
        };
      case 'large':
        return {
          padding: '16px 24px',
          fontSize: theme.typography.lg,
        };
      case 'medium':
      default:
        return {
          padding: '12px 16px',
          fontSize: theme.typography.base,
        };
    }
  };

  const baseButtonStyle: React.CSSProperties = {
    ...theme.buttonStyle,
    ...getVariantStyles(),
    ...getSizeStyles(),
    width: fullWidth ? '100%' : 'auto',
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.6 : 1,
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: theme.typography.semibold,
    fontFamily: theme.typography.fontFamily,
    transition: 'all 0.2s ease',
    userSelect: 'none',
    textDecoration: 'none',
    outline: 'none',
    ...style
  };

  return (
    <button 
      type={type}
      style={baseButtonStyle} 
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;