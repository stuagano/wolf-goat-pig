import React, { useState } from "react";
import { Routes, Route, useNavigate, Navigate } from "react-router-dom";
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
import { ThemeProvider, useTheme } from "./theme/Provider";
import { GameProvider, SheetSyncProvider } from "./context";
import { MockAuthProvider } from "./context/MockAuthContext";
import { AuthProvider } from "./context/AuthContext";
import { TutorialProvider } from "./context/TutorialContext";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import { HomePage } from "./pages";
import SignupPage from "./pages/SignupPage";
import AboutPage from "./pages/AboutPage";
import RulesPage from "./pages/RulesPage";
import EmailSettings from "./components/email/EmailSettings";
import Navigation from "./components/Navigation";

const API_URL = process.env.REACT_APP_API_URL || "";


// Navigation component has been moved to its own file

function App() {
  const theme = useTheme();
  const navigate = useNavigate();
  
  const [backendReady, setBackendReady] = useState(false);
  const [showSplash, setShowSplash] = useState(true);

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

  // If backend isn't ready, show cold start handler
  if (!backendReady) {
    return (
      <ColdStartHandler onReady={handleBackendReady}>
        {/* This content will show once backend is ready */}
      </ColdStartHandler>
    );
  }

  // Show splash screen only on homepage after backend is ready
  if (showSplash && window.location.pathname === '/') {
    return (
      <div style={{display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',height:'100vh',background:theme.colors.background}}>
        <div style={{...theme.cardStyle, textAlign:'center', maxWidth: 400, marginTop: -80}}>
          <h1 style={{color:theme.colors.primary, fontSize:32, marginBottom:16}}>Wolf Goat Pig</h1>
          <p style={{fontSize:18, color:theme.colors.textPrimary, marginBottom:24}}>Golf Game Tracker</p>
          <button style={{...theme.buttonStyle, fontSize:22, width:220, margin:'0 auto'}} onClick={() => setShowSplash(false)}>
            Start New Game
          </button>
        </div>
      </div>
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
          <Route path="/leaderboard" element={<WGPAnalyticsDashboard />} />
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