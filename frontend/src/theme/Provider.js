import React, { createContext, useContext } from 'react';
import theme from './theme';

// Create theme context
const ThemeContext = createContext(theme);

// Theme provider component
export const ThemeProvider = ({ children }) => {
  return (
    <ThemeContext.Provider value={theme}>
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