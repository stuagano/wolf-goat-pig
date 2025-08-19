import React, { useState } from "react";
import { Routes, Route, useNavigate, Navigate } from "react-router-dom";
import { UnifiedGameInterface } from "./components/game";
import { SimulationMode, MonteCarloSimulation } from "./components/simulation";
import ShotRangeAnalyzer from "./components/ShotRangeAnalyzer";
import ColdStartHandler from "./components/ColdStartHandler";
import { ThemeProvider, useTheme } from "./theme/Provider";
import { GameProvider } from "./context";
import { HomePage } from "./pages";

const API_URL = process.env.REACT_APP_API_URL || "";


function Navigation() {
  const navigate = useNavigate();
  const theme = useTheme();
  
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
        <div>
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
        </div>
      </div>
    </nav>
  );
}

function App() {
  const theme = useTheme();
  
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
          <Route path="/game" element={<UnifiedGameInterface />} />
          <Route path="/simulation" element={<SimulationMode />} />
          <Route path="/monte-carlo" element={<MonteCarloSimulation />} />
          <Route path="/analytics" element={<ShotRangeAnalyzer />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </div>
    </ThemeProvider>
  );
}

// Main App wrapper with providers
const AppWithProviders = () => {
  return (
    <GameProvider>
      <ThemeProvider>
        <App />
      </ThemeProvider>
    </GameProvider>
  );
};

export default AppWithProviders; 