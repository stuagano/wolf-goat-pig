import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { useTheme } from '../theme/Provider';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  
  // Use mock auth if environment variable is set
  const useMockAuth = process.env.REACT_APP_USE_MOCK_AUTH === 'true';
  
  // Get auth state from Auth0 or mock
  const { isAuthenticated: auth0IsAuthenticated, user: auth0User, loginWithRedirect, logout } = useAuth0();
  
  const isAuthenticated = useMockAuth ? true : auth0IsAuthenticated;
  const user = useMockAuth ? { name: 'Test User' } : auth0User;

  // Check if user is admin (you can enhance this check)
  const adminEmails = ['stuagano@gmail.com', 'admin@wgp.com'];
  const userEmail = localStorage.getItem('userEmail') || user?.email || 'stuagano@gmail.com'; // Default for testing
  
  // Store user email if available
  if (user?.email && !localStorage.getItem('userEmail')) {
    localStorage.setItem('userEmail', user.email);
  }
  
  const showAdminLink = adminEmails.includes(userEmail);

  const navLinks = [
    { path: '/', label: '🏠 Home', primary: true },
    { path: '/game', label: '⚔️ Regular Game', primary: true },
    { path: '/simulation', label: '🎮 Practice Mode', primary: true },
    { path: '/signup', label: '📝 Sign Up Players', primary: true },
    { path: '/leaderboard', label: '🏆 Leaderboard', primary: true },
    { path: '/tutorial', label: '🎓 Tutorial', primary: false },
    { path: '/about', label: 'ℹ️ About', primary: false },
    { path: '/rules', label: '📋 Rules', primary: false },
    ...(showAdminLink ? [{ path: '/admin', label: '🔧 Admin', primary: false }] : [])
  ];

  const navStyle = {
    background: theme.colors.primary,
    color: '#fff',
    padding: '16px 0',
    marginBottom: 20,
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    position: 'relative'
  };
  
  const navContainerStyle = {
    maxWidth: 1200,
    margin: '0 auto',
    padding: '0 20px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  };
  
  const navButtonStyle = {
    background: 'transparent',
    color: '#fff',
    border: '2px solid #fff',
    borderRadius: 6,
    padding: '8px 16px',
    margin: '0 8px',
    cursor: 'pointer',
    fontWeight: 600,
    transition: 'all 0.2s',
    whiteSpace: 'nowrap'
  };

  const mobileMenuButtonStyle = {
    display: 'none',
    background: 'transparent',
    color: '#fff',
    border: '2px solid #fff',
    borderRadius: 6,
    padding: '8px 16px',
    cursor: 'pointer',
    fontSize: '20px',
    '@media (max-width: 768px)': {
      display: 'block'
    }
  };

  const mobileMenuStyle = {
    position: 'absolute',
    top: '100%',
    left: 0,
    right: 0,
    background: theme.colors.primary,
    borderTop: '1px solid rgba(255,255,255,0.2)',
    padding: '20px',
    display: isMobileMenuOpen ? 'block' : 'none',
    zIndex: 1000,
    maxHeight: '70vh',
    overflowY: 'auto',
    overflowX: 'hidden',
    boxSizing: 'border-box'
  };

  const mobileNavItemStyle = {
    display: 'block',
    padding: '12px 16px',
    color: '#fff',
    background: 'transparent',
    border: '1px solid rgba(255,255,255,0.3)',
    borderRadius: 6,
    marginBottom: '10px',
    cursor: 'pointer',
    width: '100%',
    textAlign: 'left',
    fontWeight: 500,
    transition: 'all 0.2s',
    boxSizing: 'border-box',
    wordBreak: 'break-word',
    overflowWrap: 'break-word',
    whiteSpace: 'normal'
  };

  // Responsive hook to detect mobile screen size
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    handleResize(); // Initialize on mount
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleNavigate = (path) => {
    navigate(path);
    setIsMobileMenuOpen(false);
  };

  return (
    <nav style={navStyle}>
      <div style={navContainerStyle}>
        <h1 style={{ margin: 0, fontSize: isMobile ? '20px' : '24px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '250px' }}>🐺🐐🐷 Wolf Goat Pig</h1>
        
        {/* Desktop Navigation */}
        <div style={{ display: isMobile ? 'none' : 'flex', alignItems: 'center' }}>
          {navLinks.filter(link => link.primary || !isMobile).map(({ path, label }) => {
            const isActive = location.pathname === path || 
                           (path === '/signup' && location.pathname.startsWith('/signup'));
            return (
              <button 
                key={path}
                style={{
                  ...navButtonStyle,
                  background: isActive ? 'rgba(255,255,255,0.2)' : navButtonStyle.background,
                  fontWeight: isActive ? '600' : navButtonStyle.fontWeight
                }} 
                onClick={() => handleNavigate(path)}
              >
                {label}
              </button>
            );
          })}
          
          {/* Auth Section */}
          <div style={{ marginLeft: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            {isAuthenticated ? (
              <>
                <span style={{ color: '#fff' }}>{user?.name || 'User'}</span>
                {!useMockAuth && (
                  <button 
                    style={{...navButtonStyle, fontSize: 14}} 
                    onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
                  >
                    Logout
                  </button>
                )}
              </>
            ) : (
              !useMockAuth && (
                <button 
                  style={{...navButtonStyle, fontSize: 14}} 
                  onClick={() => loginWithRedirect()}
                >
                  Login
                </button>
              )
            )}
          </div>
        </div>

        {/* Mobile Menu Button */}
        <button 
          style={{ 
            display: isMobile ? 'block' : 'none',
            ...mobileMenuButtonStyle 
          }}
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          aria-label="Toggle navigation menu"
        >
          {isMobileMenuOpen ? '✕' : '☰'}
        </button>
      </div>

      {/* Mobile Menu */}
      {isMobile && (
        <div style={mobileMenuStyle}>
          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ color: '#fff', marginBottom: '10px', fontSize: '16px' }}>Main Menu</h3>
            {navLinks.filter(link => link.primary).map(({ path, label }) => (
              <button
                key={path}
                style={mobileNavItemStyle}
                onClick={() => handleNavigate(path)}
              >
                {label}
              </button>
            ))}
          </div>

          <div style={{ marginBottom: '20px' }}>
            <h3 style={{ color: '#fff', marginBottom: '10px', fontSize: '16px' }}>More Options</h3>
            {navLinks.filter(link => !link.primary).map(({ path, label }) => (
              <button
                key={path}
                style={mobileNavItemStyle}
                onClick={() => handleNavigate(path)}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Mobile Auth Section */}
          <div style={{ 
            borderTop: '1px solid rgba(255,255,255,0.2)', 
            paddingTop: '20px' 
          }}>
            {isAuthenticated ? (
              <>
                <div style={{ color: '#fff', marginBottom: '10px' }}>
                  Logged in as: {user?.name || 'User'}
                </div>
                {!useMockAuth && (
                  <button 
                    style={mobileNavItemStyle}
                    onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
                  >
                    Logout
                  </button>
                )}
              </>
            ) : (
              !useMockAuth && (
                <button 
                  style={mobileNavItemStyle}
                  onClick={() => loginWithRedirect()}
                >
                  Login
                </button>
              )
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navigation;
