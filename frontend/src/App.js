import React, { useEffect, useState } from "react";
import { Routes, Route, useNavigate, Navigate } from "react-router-dom";
import { UnifiedGameInterface } from "./components/game";
import { SimulationMode, MonteCarloSimulation } from "./components/simulation";
import ShotRangeAnalyzer from "./components/ShotRangeAnalyzer";
import { ThemeProvider, useTheme } from "./theme/Provider";
import { GameProvider } from "./context";
import { HomePage } from "./pages";

const API_URL = process.env.REACT_APP_API_URL || "";

// Helper to check if the game state is blank (no real game started)
function isBlankGameState(data) {
  if (!data || !Array.isArray(data.players)) return true;
  // Consider blank if no players or all player names are empty/blank
  return data.players.length === 0 || data.players.every(p => !p.name || p.name.trim() === "");
}

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
  
  // Derived styles from theme
  const tableContainerStyle = {
    overflowX: "auto",
    WebkitOverflowScrolling: "touch",
    marginBottom: theme.spacing[4],
  };

  const tableStyle = {
    width: "100%",
    minWidth: 400,
    borderCollapse: "collapse",
  };

  const thStyle = {
    background: theme.colors.background,
    color: theme.colors.textPrimary,
    fontWeight: theme.typography.bold,
    textAlign: "left",
    padding: `${theme.spacing[3]} ${theme.spacing[2]}`,
    borderBottom: `2px solid ${theme.colors.border}`,
  };

  const tdStyle = {
    padding: `${theme.spacing[2]} ${theme.spacing[1]}`,
    borderBottom: `1px solid ${theme.colors.border}`,
    background: theme.colors.paper,
  };

  const stickyHeaderStyle = {
    position: "sticky",
    top: 0,
    zIndex: 10,
  };

  const mobileNavStyle = {
    position: "fixed",
    left: 0,
    right: 0,
    bottom: 0,
    background: theme.colors.paper,
    borderTop: `2px solid ${theme.colors.border}`,
    padding: `${theme.spacing[3]} ${theme.spacing[4]}`,
    display: "flex",
    justifyContent: "space-around",
    zIndex: 1000,
    boxShadow: theme.shadows.lg,
  };

  const navBtnStyle = {
    ...theme.buttonStyle,
    background: theme.colors.primary,
    borderRadius: theme.borderRadius.full,
    fontSize: theme.typography.xs,
    padding: `${theme.spacing[2]} ${theme.spacing[3]}`,
    margin: 0,
    minWidth: 70,
    textAlign: "center",
  };

  const [gameState, setGameState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scoreInputs, setScoreInputs] = useState({});
  const [partnerSelect, setPartnerSelect] = useState("");
  const [showDebug, setShowDebug] = useState(false);
  const [bettingTips, setBettingTips] = useState([]);
  const [playerStrokes, setPlayerStrokes] = useState({});
  const [showSplash, setShowSplash] = useState(true);
  const [rules, setRules] = useState([]);
  const [ruleIdx, setRuleIdx] = useState(0);

  useEffect(() => {
    fetch(`${API_URL}/rules`).then(res => res.json()).then(data => setRules(data));
  }, []);

  useEffect(() => {
    if (!loading || rules.length === 0) return;
    const interval = setInterval(() => {
      setRuleIdx(idx => (idx + 1) % rules.length);
    }, 3000);
    return () => clearInterval(interval);
  }, [loading, rules]);

  useEffect(() => {
    fetch(`${API_URL}/game/state`)
      .then(res => res.json())
      .then(data => {
        if (isBlankGameState(data)) {
          setGameState(null);
        } else {
          setGameState(data);
        }
        setLoading(false);
      });
    fetch(`${API_URL}/game/tips`).then(res => res.json()).then(data => setBettingTips(data.tips || []));
    fetch(`${API_URL}/game/player_strokes`).then(res => res.json()).then(data => setPlayerStrokes(data));
  }, []);

  const refreshState = () => {
    setLoading(true);
    fetch(`${API_URL}/game/state`)
      .then(res => res.json())
      .then(data => {
        setGameState(data);
        setLoading(false);
        fetch(`${API_URL}/game/tips`).then(res => res.json()).then(data => setBettingTips(data.tips || []));
        fetch(`${API_URL}/game/player_strokes`).then(res => res.json()).then(data => setPlayerStrokes(data));
      });
  };

  const doAction = async (action, payload = {}) => {
    setLoading(true);
    const res = await fetch(`${API_URL}/game/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, payload }),
    });
    const data = await res.json();
    setGameState(data.game_state);
    setLoading(false);
    setScoreInputs({});
    setPartnerSelect("");
  };

  const startGame = () => doAction("next_hole"); // Actually, restart is handled by /game/start
  const restartGame = () => {
    if (!window.confirm("Are you sure you want to restart the game? All progress will be lost.")) return;
    setLoading(true);
    fetch(`${API_URL}/game/start`, { method: "POST" })
      .then(res => res.json())
      .then(data => {
        setGameState(data.game_state);
        setLoading(false);
        setScoreInputs({});
        setPartnerSelect("");
      });
  };

  const createNewGame = () => {
    if (!window.confirm("Are you sure you want to start a new game? All progress will be lost.")) return;
    setLoading(true);
    fetch(`${API_URL}/game/start`, { method: "POST" })
      .then(res => res.json())
      .then(data => {
        setGameState(null); // Force setup screen
        setLoading(false);
        setScoreInputs({});
        setPartnerSelect("");
      });
  };

  const handleSetup = (state) => {
    setGameState(state);
    setLoading(false);
  };

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