import React, { createContext } from 'react';

const MockAuthContext = createContext();

export const useAuth = () => {
  return {
    isAuthenticated: true,
    user: { name: 'Test User', email: 'test@example.com' },
    loginWithRedirect: () => Promise.resolve(),
    logout: () => Promise.resolve(),
  };
};

export const MockAuthProvider = ({ children }) => {
  const value = {
    isAuthenticated: true,
    user: { name: 'Test User', email: 'test@example.com' },
    loginWithRedirect: () => Promise.resolve(),
    logout: () => Promise.resolve(),
  };

  return (
    <MockAuthContext.Provider value={value}>
      {children}
    </MockAuthContext.Provider>
  );
};

export default MockAuthProvider;
