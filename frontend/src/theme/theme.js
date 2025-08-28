/**
 * Simplified Unified Theme System for Wolf Goat Pig
 */

// Base color palette
export const colors = {
  // Primary brand colors (golf course greens)
  primary: '#047857', // deep forest green
  primaryLight: '#059669', // emerald green  
  primaryDark: '#065F46', // pine green
  
  // Secondary/accent colors (water blues)
  accent: '#0369A1', // deep water blue
  accentLight: '#0EA5E9', // sky blue
  accentDark: '#0C4A6E', // dark blue
  
  // Semantic colors
  success: '#388e3c',
  successLight: '#66bb6a',
  successDark: '#1b5e20',
  
  warning: '#ff9800',
  warningLight: '#ffa726',
  warningDark: '#f57c00',
  
  error: '#d32f2f',
  errorLight: '#ef5350',
  errorDark: '#b71c1c',
  
  // Neutral colors
  gray50: '#fafafa',
  gray100: '#f5f5f5',
  gray200: '#eeeeee',
  gray300: '#e0e0e0',
  gray400: '#bdbdbd',
  gray500: '#9e9e9e',
  gray600: '#757575',
  gray700: '#616161',
  gray800: '#424242',
  gray900: '#212121',
  
  // Special WGP colors (golf course inspired)
  hoepfinger: '#9c27b0',
  vinnie: '#795548', // earth brown
  gold: '#B45309', // warm sand/bronze
  purple: '#9b59b6',
  sandTrap: '#D2B48C', // sand color
  fairway: '#22C55E', // bright fairway green
  
  // Background and surface colors
  background: '#f9fafe',
  paper: '#ffffff',
  
  // Text colors
  textPrimary: '#212121',
  textSecondary: '#757575',
  textDisabled: '#bdbdbd',
  
  // Border colors
  border: '#e0e0e0',
  borderMedium: '#bdbdbd',
};

// Typography system
export const typography = {
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  fontMono: 'Monaco, "Cascadia Code", "Segoe UI Mono", Consolas, monospace',
  
  // Font sizes
  xs: '0.75rem',    // 12px
  sm: '0.875rem',   // 14px
  base: '1rem',     // 16px
  lg: '1.125rem',   // 18px
  xl: '1.25rem',    // 20px
  '2xl': '1.5rem',  // 24px
  '3xl': '1.875rem', // 30px
  '4xl': '2.25rem',  // 36px
  
  // Font weights
  normal: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
};

// Spacing system (based on 4px grid)
export const spacing = {
  1: '0.25rem',  // 4px
  2: '0.5rem',   // 8px
  3: '0.75rem',  // 12px
  4: '1rem',     // 16px
  5: '1.25rem',  // 20px
  6: '1.5rem',   // 24px
  8: '2rem',     // 32px
  10: '2.5rem',  // 40px
  12: '3rem',    // 48px
  16: '4rem',    // 64px
  20: '5rem',    // 80px
  24: '6rem',    // 96px
};

// Border radius system
export const borderRadius = {
  none: '0',
  sm: '0.25rem',   // 4px
  base: '0.5rem',  // 8px
  md: '0.75rem',   // 12px
  lg: '1rem',      // 16px
  xl: '1.5rem',    // 24px
  full: '9999px'
};

// Shadow system
export const shadows = {
  none: 'none',
  sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
  base: '0 2px 8px rgba(0, 0, 0, 0.04)',
  md: '0 4px 12px rgba(0, 0, 0, 0.08)',
  lg: '0 8px 24px rgba(0, 0, 0, 0.12)',
  xl: '0 12px 32px rgba(0, 0, 0, 0.16)'
};

// Common style generators
export const cardStyle = {
  background: colors.paper,
  borderRadius: borderRadius.md,
  boxShadow: shadows.base,
  padding: spacing[4],
  marginBottom: spacing[4],
  border: `1px solid ${colors.border}`,
};

export const buttonStyle = {
  background: colors.primary,
  color: '#ffffff',
  border: 'none',
  borderRadius: borderRadius.base,
  padding: `${spacing[3]} ${spacing[6]}`,
  fontWeight: typography.semibold,
  fontSize: typography.base,
  cursor: 'pointer',
  transition: 'all 0.2s ease',
  fontFamily: typography.fontFamily,
};

export const inputStyle = {
  border: `1px solid ${colors.border}`,
  borderRadius: borderRadius.base,
  padding: `${spacing[3]} ${spacing[4]}`,
  fontSize: typography.base,
  fontFamily: typography.fontFamily,
  width: '100%',
  backgroundColor: colors.paper,
  color: colors.textPrimary,
};

// Style variant creators
export const createCardVariant = (variant) => {
  const variants = {
    default: cardStyle,
    elevated: {
      ...cardStyle,
      boxShadow: shadows.md
    },
    success: {
      ...cardStyle,
      borderLeft: `4px solid ${colors.success}`,
      backgroundColor: '#e8f5e8'
    },
    warning: {
      ...cardStyle,
      borderLeft: `4px solid ${colors.warning}`,
      backgroundColor: '#fff3e0'
    },
    error: {
      ...cardStyle,
      borderLeft: `4px solid ${colors.error}`,
      backgroundColor: '#ffebee'
    }
  };
  return variants[variant] || variants.default;
};

export const createButtonVariant = (variant) => {
  const variants = {
    primary: buttonStyle,
    secondary: {
      ...buttonStyle,
      backgroundColor: colors.gray200,
      color: colors.textPrimary,
      border: `1px solid ${colors.border}`
    },
    success: {
      ...buttonStyle,
      backgroundColor: colors.success
    },
    warning: {
      ...buttonStyle,
      backgroundColor: colors.warning
    },
    error: {
      ...buttonStyle,
      backgroundColor: colors.error
    },
    ghost: {
      ...buttonStyle,
      backgroundColor: 'transparent',
      color: colors.primary,
      border: `1px solid ${colors.primary}`
    }
  };
  return variants[variant] || variants.primary;
};

// Layout utilities
export const layout = {
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: `0 ${spacing[5]}`
  },
  
  flexCenter: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  
  flexBetween: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between'
  }
};

// Export the complete theme object
export const theme = {
  colors,
  typography,
  spacing,
  borderRadius,
  shadows,
  cardStyle,
  buttonStyle,
  inputStyle,
  createCardVariant,
  createButtonVariant,
  layout
};

export default theme;