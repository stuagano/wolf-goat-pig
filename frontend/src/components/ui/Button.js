import React from 'react';
import { useTheme } from '../../theme/Provider';

const Button = ({ 
  children, 
  variant = 'primary', 
  size = 'medium', 
  disabled = false, 
  onClick, 
  type = 'button',
  style = {},
  ...props 
}) => {
  const theme = useTheme();
  
  const baseStyle = {
    ...theme.buttonStyle,
    fontFamily: theme.typography.fontFamily,
    fontSize: theme.typography.base,
    fontWeight: theme.typography.semibold,
    border: 'none',
    cursor: disabled ? 'not-allowed' : 'pointer',
    opacity: disabled ? 0.6 : 1,
    transition: 'all 0.2s ease',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    textDecoration: 'none',
    userSelect: 'none',
    ...style
  };

  const variants = {
    primary: {
      backgroundColor: theme.colors.primary,
      color: '#ffffff',
      '&:hover': !disabled && {
        backgroundColor: theme.colors.primaryDark,
      }
    },
    secondary: {
      backgroundColor: theme.colors.gray200,
      color: theme.colors.textPrimary,
      border: `1px solid ${theme.colors.border}`,
      '&:hover': !disabled && {
        backgroundColor: theme.colors.gray300,
      }
    },
    success: {
      backgroundColor: theme.colors.success,
      color: '#ffffff',
      '&:hover': !disabled && {
        backgroundColor: theme.colors.successDark,
      }
    },
    warning: {
      backgroundColor: theme.colors.warning,
      color: '#ffffff',
      '&:hover': !disabled && {
        backgroundColor: theme.colors.warningDark,
      }
    },
    error: {
      backgroundColor: theme.colors.error,
      color: '#ffffff',
      '&:hover': !disabled && {
        backgroundColor: theme.colors.errorDark,
      }
    },
    ghost: {
      backgroundColor: 'transparent',
      color: theme.colors.primary,
      border: `1px solid ${theme.colors.primary}`,
      '&:hover': !disabled && {
        backgroundColor: theme.colors.primary,
        color: '#ffffff',
      }
    }
  };

  const sizes = {
    small: {
      padding: `${theme.spacing[2]} ${theme.spacing[3]}`,
      fontSize: theme.typography.sm,
    },
    medium: {
      padding: `${theme.spacing[3]} ${theme.spacing[4]}`,
      fontSize: theme.typography.base,
    },
    large: {
      padding: `${theme.spacing[4]} ${theme.spacing[6]}`,
      fontSize: theme.typography.lg,
    }
  };

  const buttonStyle = {
    ...baseStyle,
    ...variants[variant],
    ...sizes[size]
  };

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      style={buttonStyle}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;