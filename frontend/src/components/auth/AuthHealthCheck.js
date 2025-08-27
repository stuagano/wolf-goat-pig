import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { useTheme } from '../../theme/Provider';

const AuthHealthCheck = () => {
  const { isLoading, error, isAuthenticated, user } = useAuth0();
  const [authStatus, setAuthStatus] = useState('checking');
  const theme = useTheme();
  
  const useMockAuth = process.env.REACT_APP_USE_MOCK_AUTH === 'true';

  useEffect(() => {
    if (useMockAuth) {
      setAuthStatus('mock');
      return;
    }

    if (isLoading) {
      setAuthStatus('loading');
    } else if (error) {
      setAuthStatus('error');
    } else if (isAuthenticated) {
      setAuthStatus('authenticated');
    } else {
      setAuthStatus('unauthenticated');
    }
  }, [isLoading, error, isAuthenticated, useMockAuth]);

  const getStatusInfo = () => {
    switch (authStatus) {
      case 'mock':
        return {
          icon: '🎭',
          title: 'Mock Authentication Active',
          message: 'Using test authentication for development',
          color: theme.colors.warning || '#f59e0b'
        };
      case 'loading':
        return {
          icon: '⏳',
          title: 'Checking Authentication',
          message: 'Verifying your login status...',
          color: theme.colors.primary
        };
      case 'error':
        return {
          icon: '❌',
          title: 'Authentication Error',
          message: `Auth0 Error: ${error?.message || 'Unknown error'}`,
          color: theme.colors.danger || '#ef4444'
        };
      case 'authenticated':
        return {
          icon: '✅',
          title: 'Successfully Authenticated',
          message: `Welcome back, ${user?.name || user?.email || 'User'}!`,
          color: theme.colors.success || '#10b981'
        };
      case 'unauthenticated':
        return {
          icon: '🔐',
          title: 'Not Authenticated',
          message: 'Please log in to access protected features',
          color: theme.colors.textSecondary
        };
      default:
        return {
          icon: '❓',
          title: 'Unknown Status',
          message: 'Authentication status unclear',
          color: theme.colors.textSecondary
        };
    }
  };

  const status = getStatusInfo();

  return (
    <div style={{
      ...theme.cardStyle,
      padding: '16px',
      margin: '16px 0',
      borderLeft: `4px solid ${status.color}`,
      background: theme.colors.background
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px'
      }}>
        <span style={{ fontSize: '24px' }}>{status.icon}</span>
        <div>
          <h4 style={{
            margin: '0 0 4px 0',
            color: status.color,
            fontSize: '16px',
            fontWeight: '600'
          }}>
            {status.title}
          </h4>
          <p style={{
            margin: 0,
            color: theme.colors.textSecondary,
            fontSize: '14px'
          }}>
            {status.message}
          </p>
        </div>
      </div>
    </div>
  );
};

export default AuthHealthCheck;