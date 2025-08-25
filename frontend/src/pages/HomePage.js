import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../theme/Provider';
import { useAuth0 } from '@auth0/auth0-react';
import { LoginButton } from '../components/auth';

function HomePage() {
  const navigate = useNavigate();
  const theme = useTheme();
  const { isAuthenticated, user } = useAuth0();
  
  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 20 }}>
      <div style={theme.cardStyle}>
        <h2 style={{ color: theme.colors.primary, textAlign: "center", marginBottom: 30 }}>
          Welcome to Wolf Goat Pig{isAuthenticated ? `, ${user?.name || 'Player'}!` : ''}
        </h2>
        <p style={{ fontSize: 18, textAlign: "center", marginBottom: 30, color: theme.colors.textSecondary }}>
          "We accept bad golf, but not bad betting"
        </p>
        
        {!isAuthenticated && (
          <div style={{ 
            textAlign: 'center', 
            marginBottom: 30, 
            padding: '20px', 
            background: theme.colors.secondary,
            borderRadius: '8px'
          }}>
            <h3 style={{ color: theme.colors.primary, marginBottom: '16px' }}>
              🔐 Sign In to Play
            </h3>
            <p style={{ marginBottom: '16px', color: theme.colors.textSecondary }}>
              Please sign in to access games, simulations, and analytics features.
            </p>
            <LoginButton style={{ fontSize: '16px', padding: '12px 24px' }} />
          </div>
        )}
        
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 20, marginBottom: 30 }}>
          <div style={theme.cardStyle}>
            <h3 style={{ color: theme.colors.primary }}>🎮 Simulation Mode</h3>
            <p>
              New to Wolf Goat Pig? Practice against computer opponents to learn the betting strategies 
              and game mechanics. Get educational feedback after each hole!
            </p>
            <button 
              style={theme.buttonStyle}
              onClick={() => navigate('/simulation')}
            >
              Start Simulation
            </button>
          </div>
          
          <div style={theme.cardStyle}>
            <h3 style={{ color: theme.colors.primary }}>⚔️ Regular Game</h3>
            <p>
              Ready to play with real players? Set up a game with custom players and track your 
              Wolf Goat Pig matches with full betting and scoring.
            </p>
            <button 
              style={theme.buttonStyle}
              onClick={() => navigate('/setup')}
            >
              Set Up Game
            </button>
          </div>
          
          <div style={theme.cardStyle}>
            <h3 style={{ color: theme.colors.primary }}>🎨 Widget Dashboard</h3>
            <p>
              Check out the beautiful new widgets for displaying Wolf Goat Pig data! See shot results, 
              betting opportunities, and strategic analysis in a modern, interactive interface.
            </p>
            <button 
              style={theme.buttonStyle}
              onClick={() => navigate('/dashboard')}
            >
              View Dashboard
            </button>
          </div>
          
          <div style={theme.cardStyle}>
            <h3 style={{ color: theme.colors.primary }}>🚀 Enhanced Interface</h3>
            <p>
              Experience the enhanced Wolf Goat Pig interface with big decision buttons, comprehensive hole state
              visualization, enhanced timeline, and detailed post-hole analysis with strategic insights!
            </p>
            <button 
              style={theme.buttonStyle}
              onClick={() => navigate('/enhanced')}
            >
              Try Enhanced Interface
            </button>
          </div>
          
          <div style={theme.cardStyle}>
            <h3 style={{ color: theme.colors.primary }}>🔧 Unified Action API</h3>
            <p>
              Experience the unified action API demo! This shows how the backend centralizes all game logic
              and provides rich context for the frontend. Great for developers and API testing.
            </p>
            <button 
              style={theme.buttonStyle}
              onClick={() => navigate('/unified-demo')}
            >
              Try Unified API
            </button>
          </div>
        </div>
        
        <div style={theme.cardStyle}>
          <h3 style={{ color: theme.colors.primary }}>About Wolf Goat Pig</h3>
          <p>
            Wolf Goat Pig is a sophisticated golf betting game where strategy meets skill. 
            Players take turns as the "Captain" and must decide whether to:
          </p>
          <ul style={{ marginLeft: 20, color: theme.colors.textPrimary }}>
            <li><strong>Request a partner</strong> for a traditional best-ball team format</li>
            <li><strong>Go solo</strong> against the other three players (doubles the wager!)</li>
          </ul>
          <p>
            Add in doubling opportunities, the Float, the Option, and complex scoring rules like 
            the Karl Marx principle, and you have a game that rewards both golf skill and betting acumen.
          </p>
        </div>
      </div>
    </div>
  );
}

export default HomePage;