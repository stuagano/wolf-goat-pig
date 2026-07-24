import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { useSearchParams } from 'react-router-dom';
import ForeTeesTeeSheet from '../components/foretees/ForeTeesTeeSheet';
import DailySignupView from '../components/signup/DailySignupView';
// WgpSignupSheet is temporarily disconnected — it read/wrote the legacy
// thousand-cranes.com tee sheet, which is disabled for now. Re-add the import,
// the tab entry, and its render block below to bring it back.
import '../styles/mobile-touch.css';

// Supported tab IDs. Anything else in the URL (e.g. the retired `wgp-signup`
// tab) is normalized to the calendar view.
const VALID_TABS = ['calendar', 'tee-times'];
const normalizeTab = (tab) => (VALID_TABS.includes(tab) ? tab : 'calendar');

const SignupPage = () => {
  const { user, isAuthenticated, loginWithRedirect } = useAuth0();
  const [searchParams, setSearchParams] = useSearchParams();

  // Day-by-day weekly sheet is the familiar primary view.
  const [activeTab, setActiveTab] = useState(() => normalizeTab(searchParams.get('tab')));
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
    const rawTab = searchParams.get('tab');
    const normalized = normalizeTab(rawTab);
    if (normalized !== activeTab) {
      setActiveTab(normalized);
    }
    // Retire unsupported tab IDs (e.g. the old wgp-signup) from the URL so the
    // highlighted tab and the address bar stay in sync.
    if (rawTab && rawTab !== normalized) {
      const newParams = new URLSearchParams(searchParams);
      newParams.set('tab', normalized);
      setSearchParams(newParams, { replace: true });
    }
  }, [searchParams]); // eslint-disable-line react-hooks/exhaustive-deps

  const tabs = [
    { id: 'calendar', label: '📅 Daily Sign-ups', icon: '📅' },
    { id: 'tee-times', label: '🏌️ Book Tee Time', icon: '🏌️' },
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
            ⛳ Sign Up to Play
          </h2>
          <p style={{ color: '#6c757d', marginBottom: '30px', lineHeight: 1.5 }}>
            Sign up for a day's game and see who else is playing.
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
          Sign Up to Play
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
        {activeTab === 'tee-times' ? (
          <ForeTeesTeeSheet />
        ) : (
          <DailySignupView />
        )}
      </div>

    </div>
  );
};

export default SignupPage;
