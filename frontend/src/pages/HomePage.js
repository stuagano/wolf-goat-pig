import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../theme/Provider';
import { useAuth0 } from '@auth0/auth0-react';
import { LoginButton, AuthHealthCheck } from '../components/auth';

function HomePage() {
  const navigate = useNavigate();
  const theme = useTheme();
  const { isAuthenticated, user } = useAuth0();
  const [menuOpen, setMenuOpen] = useState(false);
  
  // Add responsive styles
  React.useEffect(() => {
    const styleSheet = document.createElement('style');
    styleSheet.textContent = `
      @media (max-width: 768px) {
        .wgp-main-title {
          font-size: 2.5rem !important;
        }
        .wgp-subtitle {
          font-size: 1.2rem !important;
        }
        .wgp-header-container {
          padding: 25px 15px !important;
        }
        .wgp-main-grid {
          grid-template-columns: 1fr !important;
        }
        .wgp-box-grid {
          grid-template-columns: 1fr !important;
        }
      }
      @media (max-width: 480px) {
        .wgp-main-title {
          font-size: 2rem !important;
        }
        .wgp-subtitle {
          font-size: 1rem !important;
        }
      }
    `;
    document.head.appendChild(styleSheet);
    return () => document.head.removeChild(styleSheet);
  }, []);
  
  const mainBoxes = [
    {
      icon: '⚔️',
      title: 'Regular Game',
      description: 'Play with real players and track your Wolf Goat Pig matches',
      action: () => navigate('/setup'),
      buttonText: 'Start Game',
      color: '#10B981' // green
    },
    {
      icon: '🎮',
      title: 'Simulation Mode',
      description: 'Practice against computer opponents to learn strategies',
      action: () => navigate('/simulation'),
      buttonText: 'Start Practice',
      color: '#3B82F6' // blue
    },
    {
      icon: '📝',
      title: 'Sign Up',
      description: 'Register for tournaments and track your stats',
      action: () => navigate('/sign-ups'),
      buttonText: 'Sign Up',
      color: '#8B5CF6' // purple
    },
    {
      icon: '🏆',
      title: 'Leaderboard',
      description: 'View rankings and player statistics',
      action: () => navigate('/leaderboard'),
      buttonText: 'View Leaderboard',
      color: '#F59E0B' // amber
    }
  ];
  
  const menuItems = [
    { icon: 'ℹ️', label: 'About Wolf Goat Pig', path: '/about' },
    { icon: '📖', label: 'Game Rules', path: '/rules' },
    { icon: '🎨', label: 'Widget Dashboard', path: '/dashboard' },
    { icon: '🚀', label: 'Enhanced Interface', path: '/enhanced' },
    { icon: '🔧', label: 'Unified API Demo', path: '/unified-demo' },
    { icon: '📊', label: 'Analytics', path: '/analytics' },
    { icon: '🎓', label: 'Tutorial', path: '/tutorial' },
    { icon: '🔍', label: 'Feed Analyzer', path: '/feed-analyzer' },
    { icon: '📊', label: 'Sheet Sync', path: '/sheets' },
    { icon: '🔄', label: 'Live Sync', path: '/live-sync' },
  ];
  
  return (
    <div style={{ 
      minHeight: '100vh',
      backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.5)), url('https://www.wingpointgolf.com/_filelib/ImageGallery/2020_Images/DJI_0093.jpeg')`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat',
      backgroundAttachment: 'fixed',
      padding: '20px',
      position: 'relative'
    }}>
      {/* Hamburger Menu */}
      <div style={{
        position: 'fixed',
        top: 20,
        right: 20,
        zIndex: 1000
      }}>
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          style={{
            background: 'white',
            border: 'none',
            borderRadius: '8px',
            padding: '12px',
            cursor: 'pointer',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px'
          }}
        >
          <div style={{ width: '24px', height: '3px', background: '#374151', borderRadius: '2px' }}></div>
          <div style={{ width: '24px', height: '3px', background: '#374151', borderRadius: '2px' }}></div>
          <div style={{ width: '24px', height: '3px', background: '#374151', borderRadius: '2px' }}></div>
        </button>
        
        {menuOpen && (
          <div style={{
            position: 'absolute',
            top: '60px',
            right: 0,
            background: 'white',
            borderRadius: '12px',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)',
            padding: '12px',
            minWidth: '220px'
          }}>
            {menuItems.map((item, index) => (
              <button
                key={index}
                onClick={() => {
                  navigate(item.path);
                  setMenuOpen(false);
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  width: '100%',
                  padding: '12px',
                  border: 'none',
                  background: 'transparent',
                  cursor: 'pointer',
                  borderRadius: '8px',
                  transition: 'background 0.2s',
                  fontSize: '14px',
                  color: '#374151'
                }}
                onMouseEnter={(e) => e.target.style.background = '#F3F4F6'}
                onMouseLeave={(e) => e.target.style.background = 'transparent'}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </div>
        )}
      </div>
      
      {/* Main Content */}
      <div style={{ maxWidth: '1200px', margin: '0 auto', paddingTop: '40px' }}>
        {/* Header */}
        <div className="wgp-header-container" style={{ 
          textAlign: 'center', 
          marginBottom: '60px',
          background: 'rgba(0, 0, 0, 0.6)',
          padding: '40px 20px',
          borderRadius: '16px',
          backdropFilter: 'blur(10px)'
        }}>
          <h1 className="wgp-main-title" style={{ 
            fontSize: '4rem', 
            fontWeight: 'bold',
            color: 'white',
            marginBottom: '16px',
            textShadow: '2px 2px 4px rgba(0, 0, 0, 0.8)',
            letterSpacing: '1px'
          }}>
            Welcome to Wolf Goat Pig
          </h1>
          <p className="wgp-subtitle" style={{ 
            fontSize: '1.5rem', 
            color: 'white',
            fontStyle: 'italic',
            textShadow: '1px 1px 3px rgba(0, 0, 0, 0.8)'
          }}>
            "We accept bad golf, but not bad betting"
          </p>
          <p style={{
            fontSize: '1.1rem',
            color: 'rgba(255, 255, 255, 0.9)',
            marginTop: '15px'
          }}>
            🏌️ Home of Wing Point Golf & Country Club • Est. 1903
          </p>
          
          {isAuthenticated && (
            <p style={{
              marginTop: '20px',
              fontSize: '1.2rem',
              color: 'white'
            }}>
              Welcome back, {user?.name || 'Player'}! 👋
            </p>
          )}
        </div>
        
        {/* Four Main Boxes */}
        <div className="wgp-main-grid" style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '30px',
          marginBottom: '60px'
        }}>
          {mainBoxes.map((box, index) => (
            <div
              key={index}
              style={{
                background: 'rgba(255, 255, 255, 0.95)',
                borderRadius: '16px',
                padding: '30px',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.1)',
                transform: 'translateY(0)',
                transition: 'all 0.3s ease',
                cursor: 'pointer',
                backdropFilter: 'blur(10px)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-8px)';
                e.currentTarget.style.boxShadow = '0 25px 30px -5px rgba(0, 0, 0, 0.15), 0 15px 15px -5px rgba(0, 0, 0, 0.08)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)';
              }}
              onClick={box.action}
            >
              <div style={{ 
                fontSize: '3rem', 
                marginBottom: '16px',
                textAlign: 'center'
              }}>
                {box.icon}
              </div>
              <h2 style={{
                fontSize: '1.5rem',
                fontWeight: 'bold',
                color: '#1F2937',
                marginBottom: '12px',
                textAlign: 'center'
              }}>
                {box.title}
              </h2>
              <p style={{
                color: '#6B7280',
                marginBottom: '24px',
                textAlign: 'center',
                minHeight: '48px'
              }}>
                {box.description}
              </p>
              <button
                style={{
                  width: '100%',
                  padding: '12px 24px',
                  background: box.color,
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'opacity 0.2s'
                }}
                onMouseEnter={(e) => e.target.style.opacity = '0.9'}
                onMouseLeave={(e) => e.target.style.opacity = '1'}
              >
                {box.buttonText}
              </button>
            </div>
          ))}
        </div>
        
        {/* Auth Status Check for Development */}
        <AuthHealthCheck />
        
        {/* Sign In Prompt for Non-Authenticated Users */}
        {!isAuthenticated && (
          <div style={{
            background: 'white',
            borderRadius: '16px',
            padding: '30px',
            textAlign: 'center',
            marginBottom: '40px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)'
          }}>
            <h3 style={{
              fontSize: '1.5rem',
              fontWeight: 'bold',
              color: '#1F2937',
              marginBottom: '16px'
            }}>
              🔐 Sign In for Full Access
            </h3>
            <p style={{
              color: '#6B7280',
              marginBottom: '24px'
            }}>
              Create an account or sign in to save your progress, track statistics, and compete in tournaments.
            </p>
            <LoginButton style={{ 
              fontSize: '18px', 
              padding: '14px 32px',
              background: '#4F46E5',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '600'
            }} />
          </div>
        )}
        
        {/* About Section */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.98)',
          borderRadius: '16px',
          padding: '40px',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.2)',
          backdropFilter: 'blur(10px)'
        }}>
          <h3 style={{
            fontSize: '2rem',
            fontWeight: 'bold',
            color: '#1F2937',
            marginBottom: '20px',
            textAlign: 'center'
          }}>
            About Wolf Goat Pig 🐺🐐🐷
          </h3>
          <p style={{
            color: '#4B5563',
            fontSize: '1.1rem',
            lineHeight: '1.8',
            marginBottom: '20px'
          }}>
            Wolf Goat Pig is a sophisticated golf betting game where strategy meets skill. 
            Players take turns as the "Captain" and must decide whether to:
          </p>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '20px',
            marginBottom: '20px'
          }}>
            <div style={{
              background: '#F3F4F6',
              padding: '20px',
              borderRadius: '12px',
              borderLeft: '4px solid #10B981'
            }}>
              <strong style={{ color: '#065F46' }}>🤝 Request a Partner</strong>
              <p style={{ marginTop: '8px', color: '#6B7280' }}>
                Team up for a traditional best-ball format
              </p>
            </div>
            <div style={{
              background: '#F3F4F6',
              padding: '20px',
              borderRadius: '12px',
              borderLeft: '4px solid #EF4444'
            }}>
              <strong style={{ color: '#991B1B' }}>🎯 Go Solo</strong>
              <p style={{ marginTop: '8px', color: '#6B7280' }}>
                Face all three players alone (doubles the wager!)
              </p>
            </div>
          </div>
          <p style={{
            color: '#4B5563',
            fontSize: '1.1rem',
            lineHeight: '1.8'
          }}>
            With doubling opportunities, the Float, the Option, and complex scoring rules like 
            the Karl Marx principle, Wolf Goat Pig rewards both golf skill and betting acumen.
          </p>
        </div>
      </div>
    </div>
  );
}

export default HomePage;