import React, { useState } from "react";
import { Routes, Route, useNavigate, Navigate } from "react-router-dom";
import { UnifiedGameInterface } from "./components/game";
import { SimulationMode, MonteCarloSimulation } from "./components/simulation";
import ShotRangeAnalyzer from "./components/ShotRangeAnalyzer";
import ColdStartHandler from "./components/ColdStartHandler";
import TutorialSystem from "./components/tutorial/TutorialSystem";
import { ThemeProvider, useTheme } from "./theme/Provider";
import { GameProvider, AuthProvider } from "./context";
import { TutorialProvider } from "./context/TutorialContext";
import { HomePage } from "./pages";
import { LoginButton, LogoutButton, Profile, ProtectedRoute } from "./components/auth";
import { useAuth0 } from '@auth0/auth0-react';

const API_URL = process.env.REACT_APP_API_URL || "";


function Navigation() {
  const navigate = useNavigate();
  const theme = useTheme();
  const { isAuthenticated } = useAuth0();
  
  const navStyle = {
    background: theme.colors.primary,
    color: "#fff",
    padding: "16px 0",
    marginBottom: 20,
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
  };
  
  const navContainerStyle = {
    maxWidth: 1200,
    margin: "0 auto",
    padding: "0 20px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center"
  };
  
  const navButtonStyle = {
    background: "transparent",
    color: "#fff",
    border: "2px solid #fff",
    borderRadius: 6,
    padding: "8px 16px",
    margin: "0 8px",
    cursor: "pointer",
    fontWeight: 600,
    transition: "all 0.2s"
  };
  
  return (
    <nav style={navStyle}>
      <div style={navContainerStyle}>
        <h1 style={{ margin: 0 }}>🐺🐐🐷 Wolf Goat Pig</h1>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <button style={navButtonStyle} onClick={() => navigate('/')}>
            🏠 Home
          </button>
          <button style={navButtonStyle} onClick={() => navigate('/game')}>
            🎮 Game
          </button>
          <button style={navButtonStyle} onClick={() => navigate('/simulation')}>
            🎲 Simulation
          </button>
          <button style={navButtonStyle} onClick={() => navigate('/analytics')}>
            📊 Analytics
          </button>
          <button style={navButtonStyle} onClick={() => navigate('/tutorial')}>
            🎓 Tutorial
          </button>
          
          {/* Auth Section */}
          <div style={{ marginLeft: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            {isAuthenticated ? (
              <>
                <Profile />
                <LogoutButton />
              </>
            ) : (
              <LoginButton />
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}

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

  // Show splash screen after backend is ready
  if (showSplash) {
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
          <Route path="/simulation" element={
            <ProtectedRoute>
              <SimulationMode />
            </ProtectedRoute>
          } />
          <Route path="/monte-carlo" element={
            <ProtectedRoute>
              <MonteCarloSimulation />
            </ProtectedRoute>
          } />
          <Route path="/analytics" element={
            <ProtectedRoute>
              <ShotRangeAnalyzer />
            </ProtectedRoute>
          } />
          <Route path="/tutorial" element={<TutorialSystem onComplete={() => navigate('/game')} onExit={() => navigate('/')} />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </div>
    </ThemeProvider>
  );
}

// Main App wrapper with providers
const AppWithProviders = () => {
  return (
    <AuthProvider>
      <GameProvider>
        <TutorialProvider>
          <ThemeProvider>
            <App />
          </ThemeProvider>
        </TutorialProvider>
      </GameProvider>
    </AuthProvider>
  );
};

export default AppWithProviders; 