import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { useTheme } from '../theme/Provider';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isMoreSheetOpen, setIsMoreSheetOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  // Use mock auth if environment variable is set
  const useMockAuth = process.env.REACT_APP_USE_MOCK_AUTH === 'true';

  // Get auth state from Auth0 or mock
  const { isAuthenticated: auth0IsAuthenticated, user: auth0User, loginWithRedirect, logout } = useAuth0();

  const isAuthenticated = useMockAuth ? true : auth0IsAuthenticated;
  const user = useMockAuth ? { name: 'Test User' } : auth0User;

  // Check if user is admin
  const adminEmails = ['stuagano@gmail.com', 'admin@wgp.com'];
  const userEmail = localStorage.getItem('userEmail') || user?.email || 'stuagano@gmail.com';

  if (user?.email && !localStorage.getItem('userEmail')) {
    localStorage.setItem('userEmail', user.email);
  }

  const showAdminLink = adminEmails.includes(userEmail);

  // Bottom tab bar items (always visible on mobile)
  const bottomTabItems = [
    { path: '/', label: 'Home', icon: '🏠' },
    { path: '/game', label: 'Game', icon: '⚔️' },
    { path: '/games/active', label: 'Active', icon: '🎮' },
    { path: '/games/completed', label: 'History', icon: '🏆' },
  ];

  // "More" sheet items
  const moreItems = [
    { path: '/signup', label: 'Sign Up Players', icon: '📝' },
    { path: '/leaderboard', label: 'Leaderboard', icon: '📊' },
    { path: '/simulation', label: 'Practice Mode', icon: '🎯' },
    { path: '/tutorial', label: 'Tutorial', icon: '🎓' },
    { path: '/rules', label: 'Rules', icon: '📋' },
    { path: '/about', label: 'About', icon: 'ℹ️' },
    ...(showAdminLink ? [{ path: '/admin', label: 'Admin', icon: '🔧' }] : [])
  ];

  // All nav links for desktop
  const allNavLinks = [
    { path: '/', label: '🏠 Home', primary: true },
    { path: '/game', label: '⚔️ Game', primary: true },
    { path: '/games/active', label: '🎮 Active', primary: true },
    { path: '/games/completed', label: '🏆 History', primary: true },
    { path: '/signup', label: '📝 Sign Up', primary: false },
    { path: '/leaderboard', label: '📊 Leaderboard', primary: false },
    { path: '/simulation', label: '🎯 Practice', primary: false },
    { path: '/tutorial', label: '🎓 Tutorial', primary: false },
    { path: '/about', label: 'ℹ️ About', primary: false },
    { path: '/rules', label: '📋 Rules', primary: false },
    ...(showAdminLink ? [{ path: '/admin', label: '🔧 Admin', primary: true }] : [])
  ];

  // Check if path is active
  const isActivePath = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  // Responsive hook
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Online/offline status
  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Close more sheet when navigating
  const handleNavigate = (path) => {
    navigate(path);
    setIsMobileMenuOpen(false);
    setIsMoreSheetOpen(false);
  };

  // Styles
  const navStyle = {
    background: theme.colors.primary,
    color: '#fff',
    padding: isMobile ? '12px 0' : '16px 0',
    marginBottom: isMobile ? 0 : 20,
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    position: 'relative',
    zIndex: 100
  };

  const navContainerStyle = {
    maxWidth: 1200,
    margin: '0 auto',
    padding: '0 16px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  };

  const navButtonStyle = {
    background: 'transparent',
    color: '#fff',
    border: '2px solid #fff',
    borderRadius: 6,
    padding: '8px 14px',
    margin: '0 4px',
    cursor: 'pointer',
    fontWeight: 600,
    transition: 'all 0.2s',
    whiteSpace: 'nowrap',
    fontSize: '14px'
  };

  // Bottom Tab Bar Styles
  const bottomTabBarStyle = {
    position: 'fixed',
    bottom: 0,
    left: 0,
    right: 0,
    background: theme.isDark ? '#1f2937' : '#ffffff',
    borderTop: `1px solid ${theme.isDark ? '#374151' : '#e5e7eb'}`,
    display: 'flex',
    justifyContent: 'space-around',
    alignItems: 'center',
    padding: '8px 0 env(safe-area-inset-bottom, 8px)',
    zIndex: 1000,
    boxShadow: '0 -2px 10px rgba(0,0,0,0.1)'
  };

  const tabItemStyle = (isActive) => ({
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '8px 12px',
    minHeight: '56px',
    minWidth: '64px',
    background: 'transparent',
    border: 'none',
    cursor: 'pointer',
    color: isActive ? theme.colors.primary : (theme.isDark ? '#9ca3af' : '#6b7280'),
    transition: 'all 0.2s',
    borderRadius: '12px',
    position: 'relative'
  });

  const tabIconStyle = (isActive) => ({
    fontSize: '24px',
    marginBottom: '4px',
    transform: isActive ? 'scale(1.1)' : 'scale(1)',
    transition: 'transform 0.2s'
  });

  const tabLabelStyle = (isActive) => ({
    fontSize: '11px',
    fontWeight: isActive ? '700' : '500',
    letterSpacing: '0.3px'
  });

  const activeIndicatorStyle = {
    position: 'absolute',
    top: '4px',
    left: '50%',
    transform: 'translateX(-50%)',
    width: '4px',
    height: '4px',
    borderRadius: '50%',
    background: theme.colors.primary
  };

  // More Sheet Styles
  const overlayStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0,0,0,0.5)',
    zIndex: 1001,
    opacity: isMoreSheetOpen ? 1 : 0,
    visibility: isMoreSheetOpen ? 'visible' : 'hidden',
    transition: 'opacity 0.3s, visibility 0.3s'
  };

  const moreSheetStyle = {
    position: 'fixed',
    bottom: 0,
    left: 0,
    right: 0,
    background: theme.isDark ? '#1f2937' : '#ffffff',
    borderTopLeftRadius: '20px',
    borderTopRightRadius: '20px',
    padding: '20px',
    paddingBottom: 'calc(80px + env(safe-area-inset-bottom, 20px))',
    zIndex: 1002,
    transform: isMoreSheetOpen ? 'translateY(0)' : 'translateY(100%)',
    transition: 'transform 0.3s ease-out',
    maxHeight: '70vh',
    overflowY: 'auto'
  };

  const sheetHandleStyle = {
    width: '40px',
    height: '4px',
    background: theme.isDark ? '#4b5563' : '#d1d5db',
    borderRadius: '2px',
    margin: '0 auto 20px'
  };

  const sheetItemStyle = (isActive) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    padding: '16px',
    background: isActive ? (theme.isDark ? '#374151' : '#f3f4f6') : 'transparent',
    border: 'none',
    borderRadius: '12px',
    cursor: 'pointer',
    width: '100%',
    textAlign: 'left',
    color: theme.isDark ? '#fff' : '#1f2937',
    fontSize: '16px',
    fontWeight: isActive ? '600' : '500',
    transition: 'background 0.2s',
    marginBottom: '8px'
  });

  const sheetIconStyle = {
    fontSize: '24px',
    width: '32px',
    textAlign: 'center'
  };

  return (
    <>
      {/* Top Navigation Bar */}
      <nav style={navStyle}>
        <div style={navContainerStyle}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1
              style={{
                margin: 0,
                fontSize: isMobile ? '18px' : '24px',
                whiteSpace: 'nowrap',
                cursor: 'pointer'
              }}
              onClick={() => handleNavigate('/')}
            >
              🐺🐐🐷 {!isMobile && 'Wolf Goat Pig'}
            </h1>
            {isOffline && (
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '4px 8px',
                  borderRadius: '12px',
                  background: '#f59e0b',
                  color: '#000',
                  fontSize: '11px',
                  fontWeight: '600'
                }}
                title="You are offline"
              >
                📴 {!isMobile && 'Offline'}
              </span>
            )}
          </div>

          {/* Desktop Navigation */}
          {!isMobile && (
            <div style={{ display: 'flex', alignItems: 'center' }}>
              {allNavLinks.filter(link => link.primary).map(({ path, label }) => {
                const isActive = isActivePath(path);
                return (
                  <button
                    key={path}
                    style={{
                      ...navButtonStyle,
                      background: isActive ? 'rgba(255,255,255,0.2)' : 'transparent',
                      borderColor: isActive ? '#fff' : 'rgba(255,255,255,0.5)'
                    }}
                    onClick={() => handleNavigate(path)}
                  >
                    {label}
                  </button>
                );
              })}

              {/* More dropdown for desktop */}
              <div style={{ position: 'relative' }}>
                <button
                  style={{
                    ...navButtonStyle,
                    borderColor: 'rgba(255,255,255,0.5)'
                  }}
                  onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                >
                  ••• More
                </button>

                {isMobileMenuOpen && (
                  <div style={{
                    position: 'absolute',
                    top: '100%',
                    right: 0,
                    marginTop: '8px',
                    background: theme.isDark ? '#1f2937' : '#fff',
                    borderRadius: '12px',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
                    padding: '8px',
                    minWidth: '200px',
                    zIndex: 1000
                  }}>
                    {allNavLinks.filter(link => !link.primary).map(({ path, label }) => {
                      const isActive = isActivePath(path);
                      return (
                        <button
                          key={path}
                          style={{
                            display: 'block',
                            width: '100%',
                            padding: '12px 16px',
                            background: isActive ? (theme.isDark ? '#374151' : '#f3f4f6') : 'transparent',
                            border: 'none',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            textAlign: 'left',
                            color: theme.isDark ? '#fff' : '#1f2937',
                            fontSize: '14px',
                            fontWeight: isActive ? '600' : '500',
                            marginBottom: '4px'
                          }}
                          onClick={() => handleNavigate(path)}
                        >
                          {label}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Theme Toggle & Auth */}
              <div style={{ marginLeft: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                <button
                  style={{
                    ...navButtonStyle,
                    fontSize: 16,
                    padding: '6px 12px',
                    minWidth: '40px',
                    borderColor: 'rgba(255,255,255,0.5)'
                  }}
                  onClick={theme.toggleTheme}
                  aria-label={theme.isDark ? 'Switch to light mode' : 'Switch to dark mode'}
                >
                  {theme.isDark ? '☀️' : '🌙'}
                </button>

                {isAuthenticated ? (
                  <>
                    <span style={{ color: '#fff', fontSize: '14px' }}>{user?.name || 'User'}</span>
                    {!useMockAuth && (
                      <button
                        style={{...navButtonStyle, fontSize: 14, borderColor: 'rgba(255,255,255,0.5)'}}
                        onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
                      >
                        Logout
                      </button>
                    )}
                  </>
                ) : (
                  !useMockAuth && (
                    <button
                      style={{...navButtonStyle, fontSize: 14, borderColor: 'rgba(255,255,255,0.5)'}}
                      onClick={() => loginWithRedirect()}
                    >
                      Login
                    </button>
                  )
                )}
              </div>
            </div>
          )}

          {/* Mobile: Theme toggle in header */}
          {isMobile && (
            <button
              style={{
                background: 'transparent',
                border: '2px solid rgba(255,255,255,0.5)',
                borderRadius: '8px',
                padding: '8px 12px',
                fontSize: '18px',
                cursor: 'pointer',
                color: '#fff'
              }}
              onClick={theme.toggleTheme}
              aria-label={theme.isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {theme.isDark ? '☀️' : '🌙'}
            </button>
          )}
        </div>
      </nav>

      {/* Mobile Bottom Tab Bar */}
      {isMobile && (
        <div style={bottomTabBarStyle}>
          {bottomTabItems.map(({ path, label, icon }) => {
            const isActive = isActivePath(path);
            return (
              <button
                key={path}
                style={tabItemStyle(isActive)}
                onClick={() => handleNavigate(path)}
                aria-label={label}
              >
                {isActive && <div style={activeIndicatorStyle} />}
                <span style={tabIconStyle(isActive)}>{icon}</span>
                <span style={tabLabelStyle(isActive)}>{label}</span>
              </button>
            );
          })}

          {/* More Tab */}
          <button
            style={tabItemStyle(isMoreSheetOpen)}
            onClick={() => setIsMoreSheetOpen(!isMoreSheetOpen)}
            aria-label="More options"
          >
            <span style={tabIconStyle(isMoreSheetOpen)}>•••</span>
            <span style={tabLabelStyle(isMoreSheetOpen)}>More</span>
          </button>
        </div>
      )}

      {/* More Sheet Overlay */}
      {isMobile && (
        <div style={overlayStyle} onClick={() => setIsMoreSheetOpen(false)} />
      )}

      {/* More Sheet */}
      {isMobile && (
        <div style={moreSheetStyle}>
          <div style={sheetHandleStyle} />

          <h3 style={{
            margin: '0 0 16px',
            fontSize: '18px',
            fontWeight: '700',
            color: theme.isDark ? '#fff' : '#1f2937'
          }}>
            More Options
          </h3>

          {moreItems.map(({ path, label, icon }) => {
            const isActive = isActivePath(path);
            return (
              <button
                key={path}
                style={sheetItemStyle(isActive)}
                onClick={() => handleNavigate(path)}
              >
                <span style={sheetIconStyle}>{icon}</span>
                <span>{label}</span>
                {isActive && (
                  <span style={{ marginLeft: 'auto', color: theme.colors.primary }}>✓</span>
                )}
              </button>
            );
          })}

          {/* Divider */}
          <div style={{
            height: '1px',
            background: theme.isDark ? '#374151' : '#e5e7eb',
            margin: '16px 0'
          }} />

          {/* Settings Section */}
          <h4 style={{
            margin: '0 0 12px',
            fontSize: '14px',
            fontWeight: '600',
            color: theme.isDark ? '#9ca3af' : '#6b7280',
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            Settings
          </h4>

          {/* Auth in More Sheet */}
          {isAuthenticated ? (
            <>
              <div style={{
                ...sheetItemStyle(false),
                cursor: 'default',
                background: theme.isDark ? '#374151' : '#f3f4f6'
              }}>
                <span style={sheetIconStyle}>👤</span>
                <span>{user?.name || 'User'}</span>
              </div>
              {!useMockAuth && (
                <button
                  style={sheetItemStyle(false)}
                  onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
                >
                  <span style={sheetIconStyle}>🚪</span>
                  <span>Logout</span>
                </button>
              )}
            </>
          ) : (
            !useMockAuth && (
              <button
                style={sheetItemStyle(false)}
                onClick={() => loginWithRedirect()}
              >
                <span style={sheetIconStyle}>🔐</span>
                <span>Login</span>
              </button>
            )
          )}
        </div>
      )}

      {/* Spacer for bottom tab bar on mobile */}
      {isMobile && <div style={{ height: '80px' }} />}

      {/* Click outside to close desktop dropdown */}
      {isMobileMenuOpen && !isMobile && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 999
          }}
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}
    </>
  );
};

export default Navigation;
