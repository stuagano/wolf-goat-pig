import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { lightTheme, darkTheme } from './theme';

// Storage key for theme preference
const THEME_STORAGE_KEY = 'wgp-theme-mode';

// Create theme context with default value
const ThemeContext = createContext({
  ...lightTheme,
  isDark: false,
  toggleTheme: () => {},
  setThemeMode: () => {},
});

// Get initial theme based on localStorage or system preference
const getInitialThemeMode = () => {
  // First check localStorage
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === 'dark') return 'dark';
    if (stored === 'light') return 'light';
  } catch {
    // localStorage may not be available in some environments
  }

  // Fall back to system preference
  if (typeof window !== 'undefined' && window.matchMedia) {
    try {
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
      }
    } catch {
      // matchMedia may fail in some environments
    }
  }

  return 'light';
};

// Theme provider component
export const ThemeProvider = ({ children }) => {
  const [themeMode, setThemeModeState] = useState(() => getInitialThemeMode());

  const theme = themeMode === 'dark' ? darkTheme : lightTheme;

  // Set theme mode and persist to localStorage
  const setThemeMode = useCallback((mode) => {
    setThemeModeState(mode);
    localStorage.setItem(THEME_STORAGE_KEY, mode);
  }, []);

  // Toggle between light and dark
  const toggleTheme = useCallback(() => {
    setThemeMode(themeMode === 'dark' ? 'light' : 'dark');
  }, [themeMode, setThemeMode]);

  // Apply theme to document body for global styles
  useEffect(() => {
    document.body.style.backgroundColor = theme.colors.background;
    document.body.style.color = theme.colors.textPrimary;
    document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';

    // Set a data attribute for CSS targeting if needed
    document.documentElement.setAttribute('data-theme', themeMode);

    return () => {
      document.documentElement.removeAttribute('data-theme');
    };
  }, [theme, themeMode]);

  // Listen for system preference changes
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) {
      return;
    }

    let mediaQuery;
    try {
      mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    } catch {
      return;
    }

    const handleChange = (e) => {
      // Only auto-switch if user hasn't set a preference
      try {
        const stored = localStorage.getItem(THEME_STORAGE_KEY);
        if (!stored) {
          setThemeModeState(e.matches ? 'dark' : 'light');
        }
      } catch {
        // localStorage may not be available
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const value = {
    ...theme,
    isDark: themeMode === 'dark',
    toggleTheme,
    setThemeMode,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

// Custom hook to use theme
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export default ThemeProvider;