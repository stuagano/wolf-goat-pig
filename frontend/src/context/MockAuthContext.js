import React, { createContext } from 'react';
import { Auth0Context } from '@auth0/auth0-react';

const MockAuthContext = createContext();

// Mock auth values used throughout the mock auth system
const mockAuthValues = {
  isAuthenticated: true,
  isLoading: false,
  user: { name: 'Test User', email: 'test@example.com', sub: 'mock|123' },
  loginWithRedirect: () => Promise.resolve(),
  logout: () => Promise.resolve(),
  getAccessTokenSilently: () => Promise.resolve('mock-token'),
  getIdTokenClaims: () => Promise.resolve({ __raw: 'mock-id-token' }),
};

export const useAuth = () => {
  return mockAuthValues;
};

// MockAuthProvider that also provides Auth0Context so useAuth0() works
export const MockAuthProvider = ({ children }) => {
  return (
    <Auth0Context.Provider value={mockAuthValues}>
      <MockAuthContext.Provider value={mockAuthValues}>
        {children}
      </MockAuthContext.Provider>
    </Auth0Context.Provider>
  );
};

export default MockAuthProvider;
