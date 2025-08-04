import React from 'react';
import { useTheme } from '../../theme/Provider';

const Card = ({ 
  children, 
  variant = 'default', 
  elevated = false,
  padding = true,
  style = {},
  ...props 
}) => {
  const theme = useTheme();
  
  const baseStyle = {
    backgroundColor: theme.colors.paper,
    borderRadius: theme.borderRadius.md,
    border: `1px solid ${theme.colors.border}`,
    marginBottom: theme.spacing[4],
    ...style
  };

  const variants = {
    default: {
      boxShadow: elevated ? theme.shadows.md : theme.shadows.base,
    },
    success: {
      borderLeft: `4px solid ${theme.colors.success}`,
      backgroundColor: '#e8f5e8',
      boxShadow: theme.shadows.base,
    },
    warning: {
      borderLeft: `4px solid ${theme.colors.warning}`,
      backgroundColor: '#fff3e0',
      boxShadow: theme.shadows.base,
    },
    error: {
      borderLeft: `4px solid ${theme.colors.error}`,
      backgroundColor: '#ffebee',
      boxShadow: theme.shadows.base,
    },
    info: {
      borderLeft: `4px solid ${theme.colors.accent}`,
      backgroundColor: '#e1f5fe',
      boxShadow: theme.shadows.base,
    }
  };

  const cardStyle = {
    ...baseStyle,
    ...variants[variant],
    padding: padding ? theme.spacing[4] : 0,
  };

  return (
    <div style={cardStyle} {...props}>
      {children}
    </div>
  );
};

export default Card;