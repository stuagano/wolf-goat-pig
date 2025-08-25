import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { useTheme } from '../../theme/Provider';
import LoginButton from './LoginButton';

const ProtectedRoute = ({ children, fallback = null }) => {
  const { isAuthenticated, isLoading } = useAuth0();
  const theme = useTheme();

  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '50vh',
        background: theme.colors.background
      }}>
        <div style={{
          ...theme.cardStyle,
          textAlign: 'center',
          padding: '40px'
        }}>
          <div style={{ 
            fontSize: '24px',
            marginBottom: '16px',
            color: theme.colors.primary 
          }}>
            🔄 Loading...
          </div>
          <p style={{ color: theme.colors.textSecondary }}>
            Checking authentication status
          </p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    if (fallback) {
      return fallback;
    }

    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '50vh',
        background: theme.colors.background
      }}>
        <div style={{
          ...theme.cardStyle,
          textAlign: 'center',
          padding: '40px',
          maxWidth: '400px'
        }}>
          <div style={{ 
            fontSize: '48px',
            marginBottom: '16px' 
          }}>
            🔐
          </div>
          <h2 style={{ 
            color: theme.colors.primary,
            marginBottom: '16px'
          }}>
            Authentication Required
          </h2>
          <p style={{ 
            color: theme.colors.textSecondary,
            marginBottom: '24px'
          }}>
            Please log in to access this feature of the Wolf Goat Pig game.
          </p>
          <LoginButton style={{
            fontSize: '18px',
            padding: '12px 24px'
          }} />
        </div>
      </div>
    );
  }

  return children;
};

export default ProtectedRoute;