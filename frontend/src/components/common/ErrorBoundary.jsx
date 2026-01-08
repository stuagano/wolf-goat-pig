/**
 * ErrorBoundary Component
 * 
 * Catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI instead of crashing.
 * 
 * Usage:
 *   <ErrorBoundary fallback={<CustomErrorUI />}>
 *     <ComponentThatMightError />
 *   </ErrorBoundary>
 */
import React from 'react';
import PropTypes from 'prop-types';

/**
 * Default error fallback component
 */
const DefaultErrorFallback = ({ error, resetError }) => (
  <div style={{
    padding: '20px',
    margin: '20px',
    borderRadius: '8px',
    backgroundColor: '#fff5f5',
    border: '1px solid #fc8181',
    color: '#c53030'
  }}>
    <h2 style={{ margin: '0 0 10px 0', fontSize: '18px' }}>
      Something went wrong
    </h2>
    <p style={{ margin: '0 0 15px 0', fontSize: '14px', color: '#742a2a' }}>
      {error?.message || 'An unexpected error occurred'}
    </p>
    {resetError && (
      <button
        onClick={resetError}
        style={{
          padding: '8px 16px',
          fontSize: '14px',
          backgroundColor: '#c53030',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        Try Again
      </button>
    )}
    {process.env.NODE_ENV === 'development' && error?.stack && (
      <details style={{ marginTop: '15px' }}>
        <summary style={{ cursor: 'pointer', fontSize: '12px', color: '#742a2a' }}>
          Error Details (Development Only)
        </summary>
        <pre style={{
          marginTop: '10px',
          padding: '10px',
          backgroundColor: '#1a1a1a',
          color: '#e2e8f0',
          borderRadius: '4px',
          fontSize: '11px',
          overflow: 'auto',
          maxHeight: '200px'
        }}>
          {error.stack}
        </pre>
      </details>
    )}
  </div>
);

DefaultErrorFallback.propTypes = {
  error: PropTypes.shape({
    message: PropTypes.string,
    stack: PropTypes.string,
  }),
  resetError: PropTypes.func,
};

/**
 * Error Boundary class component
 * (Must be a class component - hooks cannot catch render errors)
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log error to console in development
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Store error info for display
    this.setState({ errorInfo });
    
    // Call optional onError callback
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  resetError = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
      // Render custom fallback or default
      if (this.props.fallback) {
        return this.props.fallback;
      }
      
      if (this.props.FallbackComponent) {
        const FallbackComponent = this.props.FallbackComponent;
        return (
          <FallbackComponent 
            error={this.state.error} 
            resetError={this.resetError}
            errorInfo={this.state.errorInfo}
          />
        );
      }
      
      return (
        <DefaultErrorFallback 
          error={this.state.error} 
          resetError={this.resetError}
        />
      );
    }

    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
  fallback: PropTypes.node,
  FallbackComponent: PropTypes.elementType,
  onError: PropTypes.func,
};

/**
 * Game-specific error fallback with retry functionality
 */
export const GameErrorFallback = ({ error, resetError }) => (
  <div style={{
    padding: '40px 20px',
    textAlign: 'center',
    backgroundColor: '#fffbeb',
    border: '2px solid #f59e0b',
    borderRadius: '12px',
    margin: '20px'
  }}>
    <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
    <h2 style={{ margin: '0 0 12px 0', color: '#92400e' }}>
      Game Error
    </h2>
    <p style={{ margin: '0 0 20px 0', color: '#78350f', maxWidth: '400px', marginLeft: 'auto', marginRight: 'auto' }}>
      {error?.message || 'Something went wrong with the game. Your data has been saved.'}
    </p>
    <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
      <button
        onClick={resetError}
        style={{
          padding: '12px 24px',
          fontSize: '16px',
          fontWeight: 'bold',
          backgroundColor: '#f59e0b',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer'
        }}
      >
        Try Again
      </button>
      <button
        onClick={() => window.location.reload()}
        style={{
          padding: '12px 24px',
          fontSize: '16px',
          fontWeight: 'bold',
          backgroundColor: 'white',
          color: '#92400e',
          border: '2px solid #f59e0b',
          borderRadius: '8px',
          cursor: 'pointer'
        }}
      >
        Reload Page
      </button>
    </div>
  </div>
);

GameErrorFallback.propTypes = {
  error: PropTypes.shape({
    message: PropTypes.string,
  }),
  resetError: PropTypes.func,
};

export default ErrorBoundary;
