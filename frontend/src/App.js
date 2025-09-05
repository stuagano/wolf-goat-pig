import React, { useState } from "react";
import { Routes, Route, useNavigate, Navigate, useLocation } from "react-router-dom";
import { useAuth0 } from "@auth0/auth0-react";
import { UnifiedGameInterface } from "./components/game";
import { SimulationMode, MonteCarloSimulation } from "./components/simulation";
import FeedAnalyzer from "./components/simulation/FeedAnalyzer";
import ShotRangeAnalyzer from "./components/ShotRangeAnalyzer";
import ColdStartHandler from "./components/ColdStartHandler";
import TutorialSystem from "./components/tutorial/TutorialSystem";
import WGPAnalyticsDashboard from "./components/WGPAnalyticsDashboard";
import SheetIntegrationDashboard from "./components/SheetIntegrationDashboard";
import GoogleSheetsLiveSync from "./components/GoogleSheetsLiveSync";
import Leaderboard from "./components/Leaderboard";
import { ThemeProvider, useTheme } from "./theme/Provider";
import { GameProvider, SheetSyncProvider } from "./context";
import { MockAuthProvider } from "./context/MockAuthContext";
import { AuthProvider } from "./context/AuthContext";
import { TutorialProvider } from "./context/TutorialContext";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import LoginButton from "./components/auth/LoginButton";
import { HomePage } from "./pages";
import SignupPage from "./pages/SignupPage";
import AboutPage from "./pages/AboutPage";
import RulesPage from "./pages/RulesPage";
import AdminPage from "./pages/AdminPage";
import Navigation from "./components/Navigation";

const API_URL = process.env.REACT_APP_API_URL || "";


// Navigation component has been moved to its own file

function App() {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, isLoading } = useAuth0();
  
  const [backendReady, setBackendReady] = useState(false);
  const [showSplash, setShowSplash] = useState(true);
  
  // Check if we're using mock auth
  const useMockAuth = process.env.REACT_APP_USE_MOCK_AUTH === 'true';

  const handleBackendReady = () => {
    setBackendReady(true);
    // Load rules once backend is ready
    fetch(`${API_URL}/rules`)
      .then(res => res.json())
      .then(data => {
        // Handle rules data if needed
      })
      .catch(err => {
        console.warn('Could not load rules:', err);
      });
  };

  // Show loading screen while checking authentication
  if (isLoading && !useMockAuth) {
    return (
      <ThemeProvider>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
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
      </ThemeProvider>
    );
  }

  // Show login screen if not authenticated (unless using mock auth)
  if (!isAuthenticated && !useMockAuth) {
    return (
      <ThemeProvider>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          background: theme.colors.background,
          padding: '20px'
        }}>
          <div style={{
            ...theme.cardStyle,
            textAlign: 'center',
            padding: '40px',
            maxWidth: '500px'
          }}>
            <div style={{ 
              fontSize: '48px',
              marginBottom: '16px' 
            }}>
              🐷🐺🐐
            </div>
            <h1 style={{ 
              color: theme.colors.primary,
              marginBottom: '8px',
              fontSize: '2.5rem'
            }}>
              Wolf Goat Pig
            </h1>
            <p style={{ 
              color: theme.colors.textSecondary,
              marginBottom: '24px',
              fontSize: '1.2rem'
            }}>
              The Ultimate Golf Betting Game
            </p>
            <p style={{ 
              color: theme.colors.textSecondary,
              marginBottom: '32px'
            }}>
              Please log in to start playing Wolf Goat Pig with your friends.
            </p>
            <LoginButton style={{
              fontSize: '18px',
              padding: '16px 32px',
              minWidth: '200px'
            }} />
          </div>
        </div>
      </ThemeProvider>
    );
  }

  // If backend isn't ready, show cold start handler
  if (!backendReady) {
    return (
      <ColdStartHandler onReady={handleBackendReady}>
        {/* This content will show once backend is ready */}
      </ColdStartHandler>
    );
  }

  // Show splash screen only on homepage after backend is ready
  if (showSplash && location.pathname === '/') {
    return (
      <ThemeProvider>
        <div style={{display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',height:'100vh',background:theme.colors.background}}>
          <div style={{...theme.cardStyle, textAlign:'center', maxWidth: 400, marginTop: -80}}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>🐷🐺🐐</div>
            <h1 style={{color:theme.colors.primary, fontSize:32, marginBottom:16}}>Wolf Goat Pig</h1>
            <p style={{fontSize:18, color:theme.colors.textPrimary, marginBottom:24}}>Golf Game Tracker</p>
            {!isAuthenticated && !useMockAuth ? (
              <div style={{ marginBottom: '16px' }}>
                <p style={{ fontSize: 14, color: theme.colors.textSecondary, marginBottom: 16 }}>
                  Please log in to start playing
                </p>
                <LoginButton style={{
                  fontSize: '18px',
                  padding: '12px 32px',
                  minWidth: '180px'
                }} />
              </div>
            ) : (
              <button 
                style={{...theme.buttonStyle, fontSize:22, width:220, margin:'0 auto'}} 
                onClick={() => setShowSplash(false)}
              >
                Enter Game
              </button>
            )}
            <button 
              style={{
                ...theme.buttonStyle, 
                fontSize: 16, 
                width: 220, 
                margin: '8px auto 0', 
                background: 'transparent',
                color: theme.colors.textSecondary,
                border: `1px solid ${theme.colors.textSecondary}`
              }} 
              onClick={() => setShowSplash(false)}
            >
              Browse Without Login
            </button>
          </div>
        </div>
      </ThemeProvider>
    );
  }

  // Main application
  return (
    <ThemeProvider>
      <div>
        <Navigation />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/game" element={
            <ProtectedRoute>
              <UnifiedGameInterface />
            </ProtectedRoute>
          } />
          <Route path="/simulation" element={<SimulationMode />} />
          <Route path="/monte-carlo" element={
            <ProtectedRoute>
              <MonteCarloSimulation />
            </ProtectedRoute>
          } />
          <Route path="/analytics" element={
            <ProtectedRoute>
              <WGPAnalyticsDashboard />
            </ProtectedRoute>
          } />
          <Route path="/analyzer" element={
            <ProtectedRoute>
              <ShotRangeAnalyzer />
            </ProtectedRoute>
          } />
          <Route path="/signup" element={
            <ProtectedRoute>
              <SignupPage />
            </ProtectedRoute>
          } />
          <Route path="/feed-analyzer" element={
            <ProtectedRoute>
              <FeedAnalyzer />
            </ProtectedRoute>
          } />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/sheets" element={
            <ProtectedRoute>
              <SheetIntegrationDashboard />
            </ProtectedRoute>
          } />
          <Route path="/live-sync" element={
            <ProtectedRoute>
              <GoogleSheetsLiveSync />
            </ProtectedRoute>
          } />
          <Route path="/tutorial" element={<TutorialSystem onComplete={() => navigate('/game')} onExit={() => navigate('/')} />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/rules" element={<RulesPage />} />
          <Route path="/admin" element={
            <ProtectedRoute>
              <AdminPage />
            </ProtectedRoute>
          } />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </div>
    </ThemeProvider>
  );
}

// Main App wrapper with providers
const AppWithProviders = () => {
  // Choose between mock auth and real Auth0 based on environment
  const useMockAuth = process.env.REACT_APP_USE_MOCK_AUTH === 'true';
  const AuthProviderComponent = useMockAuth ? MockAuthProvider : AuthProvider;
  
  return (
    <AuthProviderComponent>
      <SheetSyncProvider>
        <GameProvider>
          <TutorialProvider>
          <ThemeProvider>
            <App />
          </ThemeProvider>
        </TutorialProvider>
      </GameProvider>
    </SheetSyncProvider>
    </AuthProviderComponent>
  );
};

export default AppWithProviders; 