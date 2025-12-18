/**
 * Simplified Unified Theme System for Wolf Goat Pig
 * Supports light and dark mode
 */

// Base color palette (shared colors)
const baseColors = {
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

  // Special WGP colors (golf course inspired)
  hoepfinger: '#9c27b0',
  vinnie: '#795548', // earth brown
  gold: '#B45309', // warm sand/bronze
  purple: '#9b59b6',
  sandTrap: '#D2B48C', // sand color
  fairway: '#22C55E', // bright fairway green
};

// Light mode colors
export const lightColors = {
  ...baseColors,

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

  // Input colors
  inputBackground: '#ffffff',
};

// Dark mode colors
export const darkColors = {
  ...baseColors,

  // Adjust primary for better visibility on dark
  primary: '#10B981', // brighter emerald for dark mode
  primaryLight: '#34D399',
  primaryDark: '#059669',

  // Neutral colors (inverted)
  gray50: '#1a1a1a',
  gray100: '#242424',
  gray200: '#2d2d2d',
  gray300: '#383838',
  gray400: '#4a4a4a',
  gray500: '#6b6b6b',
  gray600: '#8c8c8c',
  gray700: '#a3a3a3',
  gray800: '#c4c4c4',
  gray900: '#e5e5e5',

  // Background and surface colors
  background: '#121212',
  paper: '#1e1e1e',

  // Text colors
  textPrimary: '#e5e5e5',
  textSecondary: '#a3a3a3',
  textDisabled: '#6b6b6b',

  // Border colors
  border: '#383838',
  borderMedium: '#4a4a4a',

  // Input colors
  inputBackground: '#2d2d2d',
};

// Default to light colors for backwards compatibility
export const colors = lightColors;

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

// Function to create theme object for a given color palette
export const createTheme = (themeColors, mode = 'light') => {
  const themedCardStyle = {
    background: themeColors.paper,
    borderRadius: borderRadius.md,
    boxShadow: mode === 'dark' ? 'none' : shadows.base,
    padding: spacing[4],
    marginBottom: spacing[4],
    border: `1px solid ${themeColors.border}`,
  };

  const themedButtonStyle = {
    background: themeColors.primary,
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

  const themedInputStyle = {
    border: `1px solid ${themeColors.border}`,
    borderRadius: borderRadius.base,
    padding: `${spacing[3]} ${spacing[4]}`,
    fontSize: typography.base,
    fontFamily: typography.fontFamily,
    width: '100%',
    backgroundColor: themeColors.inputBackground || themeColors.paper,
    color: themeColors.textPrimary,
  };

  const createCardVariant = (variant) => {
    const successBg = mode === 'dark' ? '#1a3a1a' : '#e8f5e8';
    const warningBg = mode === 'dark' ? '#3a2a1a' : '#fff3e0';
    const errorBg = mode === 'dark' ? '#3a1a1a' : '#ffebee';

    const variants = {
      default: themedCardStyle,
      elevated: {
        ...themedCardStyle,
        boxShadow: mode === 'dark' ? '0 4px 12px rgba(0, 0, 0, 0.3)' : shadows.md
      },
      success: {
        ...themedCardStyle,
        borderLeft: `4px solid ${themeColors.success}`,
        backgroundColor: successBg
      },
      warning: {
        ...themedCardStyle,
        borderLeft: `4px solid ${themeColors.warning}`,
        backgroundColor: warningBg
      },
      error: {
        ...themedCardStyle,
        borderLeft: `4px solid ${themeColors.error}`,
        backgroundColor: errorBg
      }
    };
    return variants[variant] || variants.default;
  };

  const createButtonVariant = (variant) => {
    const variants = {
      primary: themedButtonStyle,
      secondary: {
        ...themedButtonStyle,
        backgroundColor: themeColors.gray200,
        color: themeColors.textPrimary,
        border: `1px solid ${themeColors.border}`
      },
      success: {
        ...themedButtonStyle,
        backgroundColor: themeColors.success
      },
      warning: {
        ...themedButtonStyle,
        backgroundColor: themeColors.warning
      },
      error: {
        ...themedButtonStyle,
        backgroundColor: themeColors.error
      },
      ghost: {
        ...themedButtonStyle,
        backgroundColor: 'transparent',
        color: themeColors.primary,
        border: `1px solid ${themeColors.primary}`
      }
    };
    return variants[variant] || variants.primary;
  };

  return {
    mode,
    colors: themeColors,
    typography,
    spacing,
    borderRadius,
    shadows,
    cardStyle: themedCardStyle,
    buttonStyle: themedButtonStyle,
    inputStyle: themedInputStyle,
    createCardVariant,
    createButtonVariant,
    layout
  };
};

// Pre-built light and dark themes
export const lightTheme = createTheme(lightColors, 'light');
export const darkTheme = createTheme(darkColors, 'dark');

// Export the complete theme object (default light for backwards compatibility)
export const theme = lightTheme;

export default theme;