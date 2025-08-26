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
  const audience = process.env.REACT_APP_AUTH0_AUDIENCE;

  if (!domain || !clientId) {
    throw new Error('Please define REACT_APP_AUTH0_DOMAIN and REACT_APP_AUTH0_CLIENT_ID environment variables');
  }

  const value = {
    // Additional auth context values can be added here
  };

  return (
    <Auth0Provider
      domain={domain}
      clientId={clientId}
      authorizationParams={{
        redirect_uri: window.location.origin,
        ...(audience && { audience: audience }),
        scope: "openid profile email"
      }}
      cacheLocation="localstorage"
    >
      <AuthContext.Provider value={value}>
        {children}
      </AuthContext.Provider>
    </Auth0Provider>
  );
};

export default AuthProvider;