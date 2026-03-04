import React, { useState, useEffect } from 'react';
import { useTheme } from '../theme/Provider';

const ColdStartHandler = ({ children, onReady }) => {
  const theme = useTheme();
  const [backendStatus, setBackendStatus] = useState('checking'); // checking, cold, warming, ready, error
  const [retryAttempt, setRetryAttempt] = useState(0);
  // const [startTime, setStartTime] = useState(Date.now()); // Moved to useEffect

  const API_URL = process.env.REACT_APP_API_URL || "";

  // Skip cold start handler in development - localhost should be instant
  const isLocalDevelopment = API_URL.includes('localhost') || API_URL.includes('127.0.0.1');

  useEffect(() => {
    let isMounted = true;
    const currentStartTime = Date.now();

    // In local development, skip the health check and render immediately
    if (isLocalDevelopment) {
      console.log('[ColdStartHandler] Local development detected - skipping health check');
      setBackendStatus('ready');
      if (onReady) onReady();
      return;
    }

    const checkBackendHealth = async (attempt = 0) => {
      if (!isMounted) return;
      
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
        
        const response = await fetch(`${API_URL}/health`, {
          signal: controller.signal,
          cache: 'no-cache'
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok && isMounted) {
          setBackendStatus('ready');
          if (onReady) onReady();
          return true;
        } else {
          throw new Error(`HTTP ${response.status}`);
        }
      } catch (error) {
        if (!isMounted) return;
        
        const elapsed = Date.now() - currentStartTime;
        
        if (error.name === 'AbortError' || elapsed > 5000) {
          // If it's taking longer than 5 seconds, assume cold start
          setBackendStatus('cold');
        }
        
        if (attempt < 30) { // Retry for up to 5 minutes
          setRetryAttempt(attempt + 1);
          setTimeout(() => {
            if (isMounted) {
              setBackendStatus('warming');
              checkBackendHealth(attempt + 1);
            }
          }, 10000); // Check every 10 seconds
        } else if (isMounted) {
          setBackendStatus('error');
        }
        
        return false;
      }
    };

    checkBackendHealth(0);

    return () => {
      isMounted = false;
    };
  }, [API_URL, onReady, isLocalDevelopment]);

  const getStatusMessage = () => {
    switch (backendStatus) {
      case 'checking':
        return {
          title: "🔍 Checking Backend...",
          message: "Connecting to the server...",
          detail: ""
        };
      case 'cold':
        return {
          title: "☕ Hold On Please...",
          message: "The owner is cheap and can't pay for fast startup",
          detail: "Free hosting = free problems. Give it 30-60 seconds... ⏰"
        };
      case 'warming':
        return {
          title: "🔥 Backend Warming Up...",
          message: "Almost there! The server is waking up from its nap",
          detail: `Attempt ${retryAttempt}/30 - This usually takes 30-60 seconds`
        };
      case 'error':
        return {
          title: "💥 Backend Issues",
          message: "The server seems to be having problems",
          detail: "Try refreshing the page or check back later"
        };
      default:
        return { title: "", message: "", detail: "" };
    }
  };

  const { title, message, detail } = getStatusMessage();

  if (backendStatus === 'ready') {
    return children;
  }

  const containerStyle = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
    background: theme.colors.background,
    padding: '20px'
  };

  const cardStyle = {
    ...theme.cardStyle,
    textAlign: 'center',
    maxWidth: 500,
    padding: '40px',
    background: theme.colors.paper,
    borderRadius: '12px',
    boxShadow: theme.shadows.lg
  };

  const titleStyle = {
    color: theme.colors.primary,
    fontSize: '28px',
    marginBottom: '16px',
    fontWeight: 'bold'
  };

  const messageStyle = {
    fontSize: '18px',
    color: theme.colors.textPrimary,
    marginBottom: '12px',
    fontWeight: '500'
  };

  const detailStyle = {
    fontSize: '14px',
    color: theme.colors.textSecondary,
    marginBottom: '24px',
    lineHeight: '1.5'
  };

  const spinnerStyle = {
    width: '40px',
    height: '40px',
    border: `4px solid ${theme.colors.border}`,
    borderTop: `4px solid ${theme.colors.primary}`,
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
    margin: '0 auto 20px'
  };

  return (
    <div style={containerStyle}>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
      `}</style>
      
      <div style={cardStyle}>
        {(backendStatus === 'checking' || backendStatus === 'warming') && (
          <div style={spinnerStyle}></div>
        )}
        
        {backendStatus === 'cold' && (
          <div style={{ fontSize: '48px', marginBottom: '20px', animation: 'pulse 2s infinite' }}>
            🐌
          </div>
        )}
        
        {backendStatus === 'error' && (
          <div style={{ fontSize: '48px', marginBottom: '20px' }}>
            😵
          </div>
        )}
        
        <h2 style={titleStyle}>{title}</h2>
        <p style={messageStyle}>{message}</p>
        {detail && <p style={detailStyle}>{detail}</p>}
        
        {backendStatus === 'cold' && (
          <div style={{ 
            background: theme.colors.warning, 
            color: '#fff', 
            padding: '12px', 
            borderRadius: '8px',
            fontSize: '14px',
            marginTop: '16px'
          }}>
            💡 <strong>Pro Tip:</strong> This only happens on the first visit after inactivity. 
            Once it's up, it'll be fast! 
          </div>
        )}
        
        {backendStatus === 'error' && (
          <button 
            style={{
              ...theme.buttonStyle,
              background: theme.colors.primary,
              marginTop: '16px'
            }}
            onClick={() => {
              setBackendStatus('checking');
              setRetryAttempt(0);
              window.location.reload(); // Simple reload to restart the check
            }}
          >
            🔄 Try Again
          </button>
        )}
      </div>
    </div>
  );
};

export default ColdStartHandler;