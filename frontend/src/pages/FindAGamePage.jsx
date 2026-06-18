import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { useSearchParams } from 'react-router-dom';
import AllPlayersAvailability from '../components/signup/AllPlayersAvailability';
import MatchmakingSuggestions from '../components/signup/MatchmakingSuggestions';
import '../styles/mobile-touch.css';

const FindAGamePage = () => {
  const { user, isAuthenticated, loginWithRedirect } = useAuth0();
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'all-availability');
  const isUserNavigation = useRef(false);

  const handleTabClick = useCallback((tabId) => {
    isUserNavigation.current = true;
    setActiveTab(tabId);
    const newParams = new URLSearchParams(searchParams);
    newParams.set('tab', tabId);
    setSearchParams(newParams, { replace: true });
  }, [searchParams, setSearchParams]);

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

  const tabs = [
    { id: 'all-availability', label: '👥 All Players', icon: '👥' },
    { id: 'matchmaking', label: '🔀 Matchmaking', icon: '🔀' },
  ];

  if (!isAuthenticated) {
    return (
      <div style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', minHeight: '60vh', textAlign: 'center', padding: '40px 20px',
      }}>
        <div style={{ background: '#f8f9fa', padding: '40px', borderRadius: '12px', border: '1px solid #dee2e6', maxWidth: '400px' }}>
          <h2 style={{ color: '#495057', marginBottom: '20px' }}>🤝 Find a Game</h2>
          <p style={{ color: '#6c757d', marginBottom: '30px', lineHeight: 1.5 }}>
            Set your availability, find other players, and get matched for a round.
          </p>
          <button
            onClick={() => loginWithRedirect()}
            style={{ background: '#28a745', color: 'white', border: 'none', padding: '12px 24px', borderRadius: '6px', fontSize: '16px', cursor: 'pointer', fontWeight: '600' }}
          >
            Login to Continue
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px' }}>
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ color: '#333', marginBottom: '4px', fontSize: '24px', fontWeight: '700' }}>
          Find a Game
        </h1>
        {user && <div style={{ fontSize: '14px', color: '#6b7280' }}>{user.name || user.email}</div>}
      </div>

      <div className="mobile-tab-container" style={{ borderBottom: '2px solid #dee2e6', marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '4px', minWidth: 'max-content', padding: '0 4px' }}>
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

      <div style={{ minHeight: '500px' }}>
        {activeTab === 'all-availability' && <AllPlayersAvailability />}
        {activeTab === 'matchmaking' && <MatchmakingSuggestions />}
      </div>
    </div>
  );
};

export default FindAGamePage;
