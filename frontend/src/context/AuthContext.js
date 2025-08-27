import React, { createContext, useContext } from 'react';
import { Auth0Provider } from '@auth0/auth0-react';

// Auth0 integration for Wolf Goat Pig authentication
const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  // Support both React and Vite environment variable formats
  const domain = process.env.REACT_APP_AUTH0_DOMAIN || process.env.VITE_AUTH0_DOMAIN;
  const clientId = process.env.REACT_APP_AUTH0_CLIENT_ID || process.env.VITE_AUTH0_CLIENT_ID;
  // Temporarily disable audience to fix login issues
  // const audience = process.env.REACT_APP_AUTH0_AUDIENCE;

  if (!domain || !clientId) {
    console.warn('Auth0 environment variables not found. Please define REACT_APP_AUTH0_DOMAIN and REACT_APP_AUTH0_CLIENT_ID. Falling back to mock auth.');
    // Return a fallback provider that won't crash the app
    return (
      <AuthContext.Provider value={{}}>
        {children}
      </AuthContext.Provider>
    );
  }

  const value = {
    // Additional auth context values can be added here
  };

  try {
    return (
      <Auth0Provider
        domain={domain}
        clientId={clientId}
        authorizationParams={{
          redirect_uri: window.location.origin,
          // Audience disabled to prevent login errors
          // ...(audience && { audience: audience }),
          scope: "openid profile email"
        }}
        cacheLocation="localstorage"
      >
        <AuthContext.Provider value={value}>
          {children}
        </AuthContext.Provider>
      </Auth0Provider>
    );
  } catch (error) {
    console.error('Auth0Provider initialization failed:', error);
    // Return a fallback provider that won't crash the app
    return (
      <AuthContext.Provider value={{}}>
        {children}
      </AuthContext.Provider>
    );
  }
};

export default AuthProvider;