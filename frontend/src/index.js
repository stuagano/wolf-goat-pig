import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { BrowserRouter } from "react-router-dom";
import * as serviceWorkerRegistration from "./serviceWorkerRegistration";

// Error boundary for catching React render errors
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary] React error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '40px', textAlign: 'center', fontFamily: 'system-ui' }}>
          <h1 style={{ color: '#dc2626' }}>Something went wrong</h1>
          <pre style={{ 
            background: '#fee2e2', 
            padding: '20px', 
            borderRadius: '8px',
            textAlign: 'left',
            overflow: 'auto',
            maxWidth: '600px',
            margin: '20px auto'
          }}>
            {this.state.error?.message || 'Unknown error'}
          </pre>
          <button 
            onClick={() => window.location.reload()}
            style={{
              background: '#059669',
              color: 'white',
              padding: '12px 24px',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ErrorBoundary>
  </React.StrictMode>
);

// Register service worker for PWA offline capability
// Disabled in development to avoid reload loops
if (process.env.NODE_ENV === 'production') {
  serviceWorkerRegistration.register({
    onSuccess: (registration) => {
      console.log('[PWA] Service worker registered successfully:', registration);
    },
    onUpdate: (registration) => {
      console.log('[PWA] New content available; please refresh.');
    }
  });
} else {
  console.log('[DEV] Service worker disabled in development mode');
} // Deploy 20251218-112908
// Build trigger: $(date -u +%Y-%m-%dT%H:%M:%SZ)
// Deploy trigger: 2025-12-20T19:42:44Z
// Deployment verified: 2025-12-20T21:54:28Z
