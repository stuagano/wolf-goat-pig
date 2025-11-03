import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { LoginButton, AuthHealthCheck } from '../components/auth';

function HomePage() {
  const navigate = useNavigate();
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
        .wgp-join-title {
          font-size: 1.8rem !important;
        }
        .wgp-join-description {
          font-size: 1.1rem !important;
        }
      }
      @media (max-width: 480px) {
        .wgp-main-title {
          font-size: 2rem !important;
        }
        .wgp-subtitle {
          font-size: 1rem !important;
        }
        .wgp-join-title {
          font-size: 1.5rem !important;
        }
        .wgp-join-description {
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
      action: () => navigate('/game'),
      buttonText: 'Start Game',
      color: '#047857' // deep forest green
    },
    {
      icon: '🎮',
      title: 'Practice Mode',
      description: 'Practice against computer opponents to learn strategies',
      action: () => navigate('/simulation'),
      buttonText: 'Start Practice',
      color: '#0369A1' // deep water blue
    },
    {
      icon: '📝',
      title: 'Sign Up Players',
      description: 'Organize games and manage player availability',
      action: () => navigate('/signup'),
      buttonText: 'Sign Up',
      color: '#7C2D12' // warm brown
    },
    {
      icon: '🎓',
      title: 'Tutorial',
      description: 'Learn the rules and strategies of Wolf Goat Pig',
      action: () => navigate('/tutorial'),
      buttonText: 'Start Tutorial',
      color: '#065F46' // pine green
    }
  ];
  
  const menuItems = [
    { icon: 'ℹ️', label: 'About Wolf Goat Pig', path: '/about' },
    { icon: '📖', label: 'Game Rules', path: '/rules' },
    { icon: '🎮', label: 'Create Multiplayer Game', path: '/create-game' },
    { icon: '🔗', label: 'Join Game with Code', path: '/join' },
    { icon: '🧪', label: 'Test Multiplayer', path: '/test-multiplayer' },
    { icon: '⚔️', label: 'Regular Game', path: '/game' },
    { icon: '🎮', label: 'Practice Mode', path: '/simulation' },
    { icon: '📝', label: 'Sign Up Players', path: '/signup' },
    { icon: '🏆', label: 'Leaderboard', path: '/leaderboard' },
    { icon: '🎓', label: 'Tutorial', path: '/tutorial' },
    { icon: '📊', label: 'Analytics', path: '/analytics' },
    { icon: '🔄', label: 'Live Sync', path: '/live-sync' },
  ];
  
  return (
    <div style={{ 
      minHeight: '100vh',
      backgroundImage: `linear-gradient(rgba(6, 78, 59, 0.3), rgba(4, 120, 87, 0.4)), url('https://www.wingpointgolf.com/_filelib/ImageGallery/2020_Images/DJI_0093.jpeg')`,
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
          marginBottom: '40px',
          background: 'linear-gradient(135deg, rgba(6, 78, 59, 0.8), rgba(4, 120, 87, 0.7))',
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
            textShadow: '1px 1px 3px rgba(0, 0, 0, 0.8)',
            marginBottom: '20px'
          }}>
            "We accept bad golf, but not bad betting"
          </p>
          <p style={{
            fontSize: '1.2rem',
            color: 'rgba(255, 255, 255, 0.95)',
            marginBottom: '30px',
            fontWeight: '500'
          }}>
            🏌️ Wing Point Golf & Country Club • Est. 1903
          </p>
          
          {!isAuthenticated ? (
            <div style={{
              background: 'rgba(255, 255, 255, 0.95)',
              borderRadius: '16px',
              padding: '40px',
              marginTop: '30px',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)'
            }}>
              <h2 className="wgp-join-title" style={{
                fontSize: '2.2rem',
                fontWeight: 'bold',
                color: '#1F2937',
                marginBottom: '20px',
                textShadow: 'none'
              }}>
                🔐 Join the Game
              </h2>
              <p className="wgp-join-description" style={{
                color: '#4B5563',
                fontSize: '1.3rem',
                marginBottom: '30px',
                lineHeight: '1.6'
              }}>
                Sign in to track your Wolf Goat Pig stats, compete in tournaments, and join the Wing Point leaderboard.
              </p>
              <LoginButton style={{ 
                fontSize: '20px', 
                padding: '16px 40px',
                background: '#047857',
                color: 'white',
                border: 'none',
                borderRadius: '12px',
                cursor: 'pointer',
                fontWeight: '700',
                boxShadow: '0 10px 15px -3px rgba(4, 120, 87, 0.5)',
                transform: 'translateY(0)',
                transition: 'all 0.3s ease'
              }} />
              <p style={{
                color: '#6B7280',
                fontSize: '1rem',
                marginTop: '20px'
              }}>
                New to Wing Point? Your first login creates your account automatically.
              </p>
            </div>
          ) : (
            <div style={{
              background: 'linear-gradient(135deg, rgba(4, 120, 87, 0.95), rgba(6, 95, 70, 0.9))',
              borderRadius: '16px',
              padding: '30px',
              marginTop: '30px',
              boxShadow: '0 20px 25px -5px rgba(4, 120, 87, 0.4)'
            }}>
              <h2 style={{
                fontSize: '1.8rem',
                fontWeight: 'bold',
                color: 'white',
                marginBottom: '10px',
                textShadow: '1px 1px 3px rgba(0, 0, 0, 0.3)'
              }}>
                Welcome back, {user?.name || 'Player'}! 👋
              </h2>
              <p style={{
                color: 'rgba(255, 255, 255, 0.9)',
                fontSize: '1.1rem'
              }}>
                Ready to play some Wolf Goat Pig?
              </p>
            </div>
          )}
        </div>
        
        {/* Multiplayer Section - Always visible */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.95)',
          borderRadius: '16px',
          padding: '40px',
          marginBottom: '40px',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)',
          backdropFilter: 'blur(10px)'
        }}>
          <h3 style={{
            fontSize: '2rem',
            fontWeight: 'bold',
            color: '#1F2937',
            marginBottom: '16px',
            textAlign: 'center'
          }}>
            🌐 Multiplayer Games
          </h3>
          <p style={{
            color: '#6B7280',
            fontSize: '1.1rem',
            textAlign: 'center',
            marginBottom: '30px'
          }}>
            Create a game and share a join code with your friends!
          </p>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '20px'
          }}>
            <button
              onClick={() => navigate('/create-game')}
              style={{
                padding: '20px',
                background: '#047857',
                color: 'white',
                border: 'none',
                borderRadius: '12px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = '#065F46';
                e.target.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = '#047857';
                e.target.style.transform = 'translateY(0)';
              }}
            >
              <div style={{ fontSize: '2rem', marginBottom: '8px' }}>🎮</div>
              <div>Create New Game</div>
              <div style={{ fontSize: '0.9rem', opacity: 0.9, marginTop: '8px' }}>
                Start a game & get join code
              </div>
            </button>
            <button
              onClick={() => navigate('/join')}
              style={{
                padding: '20px',
                background: '#0369A1',
                color: 'white',
                border: 'none',
                borderRadius: '12px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = '#075985';
                e.target.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = '#0369A1';
                e.target.style.transform = 'translateY(0)';
              }}
            >
              <div style={{ fontSize: '2rem', marginBottom: '8px' }}>🔗</div>
              <div>Join with Code</div>
              <div style={{ fontSize: '0.9rem', opacity: 0.9, marginTop: '8px' }}>
                Enter friend's join code
              </div>
            </button>
            <button
              onClick={() => navigate('/test-multiplayer')}
              style={{
                padding: '20px',
                background: '#7C2D12',
                color: 'white',
                border: 'none',
                borderRadius: '12px',
                fontSize: '16px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
              }}
              onMouseEnter={(e) => {
                e.target.style.background = '#9A3412';
                e.target.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.target.style.background = '#7C2D12';
                e.target.style.transform = 'translateY(0)';
              }}
            >
              <div style={{ fontSize: '2rem', marginBottom: '8px' }}>🧪</div>
              <div>Test Mode</div>
              <div style={{ fontSize: '0.9rem', opacity: 0.9, marginTop: '8px' }}>
                Test without login
              </div>
            </button>
          </div>
        </div>

        {/* Main Game Boxes - Show only when authenticated */}
        {isAuthenticated && (
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
        )}
        
        {/* Show game options only after authentication */}
        {!isAuthenticated && (
          <div style={{
            background: 'rgba(255, 255, 255, 0.95)',
            borderRadius: '16px',
            padding: '40px',
            textAlign: 'center',
            marginBottom: '40px',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)',
            backdropFilter: 'blur(10px)'
          }}>
            <h3 style={{
              fontSize: '2rem',
              fontWeight: 'bold',
              color: '#1F2937',
              marginBottom: '20px'
            }}>
              🏌️ Preview the Experience
            </h3>
            <p style={{
              color: '#4B5563',
              fontSize: '1.1rem',
              marginBottom: '30px',
              lineHeight: '1.6'
            }}>
              Wolf Goat Pig is Wing Point's signature golf betting game. Sign in above to unlock full access to games, stats tracking, and tournaments.
            </p>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '20px',
              marginTop: '30px'
            }}>
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: '10px' }}>🎮</div>
                <h4 style={{ color: '#1F2937', marginBottom: '8px' }}>Practice Mode</h4>
                <p style={{ color: '#6B7280', fontSize: '0.9rem' }}>Learn against AI</p>
              </div>
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: '10px' }}>🏆</div>
                <h4 style={{ color: '#1F2937', marginBottom: '8px' }}>Live Leaderboard</h4>
                <p style={{ color: '#6B7280', fontSize: '0.9rem' }}>Track your ranking</p>
              </div>
              <div style={{ textAlign: 'center', padding: '20px' }}>
                <div style={{ fontSize: '2.5rem', marginBottom: '10px' }}>⚔️</div>
                <h4 style={{ color: '#1F2937', marginBottom: '8px' }}>Real Games</h4>
                <p style={{ color: '#6B7280', fontSize: '0.9rem' }}>Play with members</p>
              </div>
            </div>
          </div>
        )}
        
        {/* Auth Status Check for Development */}
        <AuthHealthCheck />
        
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
              background: 'rgba(240, 253, 250, 0.8)',
              padding: '20px',
              borderRadius: '12px',
              borderLeft: '4px solid #047857'
            }}>
              <strong style={{ color: '#065F46' }}>🤝 Request a Partner</strong>
              <p style={{ marginTop: '8px', color: '#6B7280' }}>
                Team up for a traditional best-ball format
              </p>
            </div>
            <div style={{
              background: 'rgba(254, 242, 242, 0.8)',
              padding: '20px',
              borderRadius: '12px',
              borderLeft: '4px solid #B45309'
            }}>
              <strong style={{ color: '#92400E' }}>🎯 Go Solo</strong>
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
