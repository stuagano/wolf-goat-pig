import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { useSearchParams } from 'react-router-dom';
import ForeTeesTeeSheet from '../components/foretees/ForeTeesTeeSheet';
import PlayerAvailability from '../components/signup/PlayerAvailability';
import AllPlayersAvailability from '../components/signup/AllPlayersAvailability';
import MatchmakingSuggestions from '../components/signup/MatchmakingSuggestions';
import MyMatches from '../components/signup/MyMatches';
import EmailPreferences from '../components/signup/EmailPreferences';
import '../styles/mobile-touch.css';

const SignupPage = () => {
  const { user, isAuthenticated, loginWithRedirect } = useAuth0();
  const [searchParams, setSearchParams] = useSearchParams();

  // Default to 'calendar' (day view) - this is the primary view
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'calendar');
  const isUserNavigation = useRef(false);

  // Handle tab click: update state and URL together to avoid effect loops
  const handleTabClick = useCallback((tabId) => {
    isUserNavigation.current = true;
    setActiveTab(tabId);
    const newParams = new URLSearchParams(searchParams);
    newParams.set('tab', tabId);
    setSearchParams(newParams, { replace: true });
  }, [searchParams, setSearchParams]);

  // Handle browser back/forward buttons only
  useEffect(() => {
    if (isUserNavigation.current) {
      isUserNavigation.current = false;
      return;
    }
    const tabFromUrl = searchParams.get('tab');
    if (tabFromUrl && tabFromUrl !== activeTab) {
      setActiveTab(tabFromUrl);
    }
  }, [searchParams]); // eslint-disable-line react-hooks/exhaustive-deps

  // Tab configuration - Day view is first and default
  const tabs = [
    { id: 'calendar', label: '📅 Tee Sheet', icon: '📅' },
    { id: 'availability', label: '🕒 My Availability', icon: '🕒' },
    { id: 'all-availability', label: '👥 All Players', icon: '👥' },
    { id: 'my-matches', label: '🤝 My Matches', icon: '🤝' },
    { id: 'matchmaking', label: '⛳ Matchmaking', icon: '⛳' },
    { id: 'preferences', label: '📧 Email Settings', icon: '📧' }
  ];

  if (!isAuthenticated) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        textAlign: 'center',
        padding: '40px 20px'
      }}>
        <div style={{
          background: '#f8f9fa',
          padding: '40px',
          borderRadius: '12px',
          border: '1px solid #dee2e6',
          maxWidth: '400px'
        }}>
          <h2 style={{ color: '#495057', marginBottom: '20px' }}>
            🏌️ Golf Sign-up System
          </h2>
          <p style={{ color: '#6c757d', marginBottom: '30px', lineHeight: 1.5 }}>
            Sign up for daily golf games, set your availability preferences, and manage email notifications.
          </p>
          <button
            onClick={() => loginWithRedirect()}
            style={{
              background: '#28a745',
              color: 'white',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '6px',
              fontSize: '16px',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            Login to Continue
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      maxWidth: '1200px',
      margin: '0 auto',
      padding: '20px'
    }}>
      {/* Page Header */}
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{
          color: '#333',
          marginBottom: '4px',
          fontSize: '24px',
          fontWeight: '700'
        }}>
          WGP Tee Sheet
        </h1>
        {user && (
          <div style={{
            fontSize: '14px',
            color: '#6b7280'
          }}>
            {user.name || user.email}
          </div>
        )}
      </div>

      {/* Tab Navigation - Mobile Optimized */}
      <div
        className="mobile-tab-container"
        style={{
          borderBottom: '2px solid #dee2e6',
          marginBottom: '20px'
        }}
      >
        <div style={{
          display: 'flex',
          gap: '4px',
          minWidth: 'max-content',
          padding: '0 4px'
        }}>
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`signup-tab-button ${activeTab === tab.id ? 'signup-tab-active' : ''}`}
              onClick={() => handleTabClick(tab.id)}
            >
              <span style={{ fontSize: '16px' }}>{tab.icon}</span>
              <span className="tab-label-text">{tab.label.replace(tab.icon + ' ', '')}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div style={{ minHeight: '500px' }}>
        {activeTab === 'calendar' && (
          <ForeTeesTeeSheet />
        )}

        {activeTab === 'availability' && (
          <div>
            <div style={{ marginBottom: '20px' }}>
              <h2 style={{ color: '#333', marginBottom: '10px' }}>
                🕒 Your Weekly Availability
              </h2>
              <p style={{ color: '#6c757d', fontSize: '14px' }}>
                Set your preferred times for each day of the week to help with matchmaking.
              </p>
            </div>
            <PlayerAvailability />
          </div>
        )}

        {activeTab === 'all-availability' && (
          <div>
            <AllPlayersAvailability />
          </div>
        )}

        {activeTab === 'my-matches' && (
          <div>
            <div style={{ marginBottom: '20px' }}>
              <h2 style={{ color: '#333', marginBottom: '10px' }}>
                🤝 My Matches
              </h2>
              <p style={{ color: '#6c757d', fontSize: '14px' }}>
                Accept or decline match suggestions. Once everyone confirms, book a tee time together.
              </p>
            </div>
            <MyMatches />
          </div>
        )}

        {activeTab === 'matchmaking' && (
          <div>
            <MatchmakingSuggestions />
          </div>
        )}

        {activeTab === 'preferences' && (
          <div>
            <div style={{ marginBottom: '20px' }}>
              <h2 style={{ color: '#333', marginBottom: '10px' }}>
                📧 Email Preferences
              </h2>
              <p style={{ color: '#6c757d', fontSize: '14px' }}>
                Control what email notifications you receive and when.
              </p>
            </div>
            <EmailPreferences />
          </div>
        )}
      </div>

    </div>
  );
};

export default SignupPage;
