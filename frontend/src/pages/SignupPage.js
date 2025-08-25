import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import SignupCalendar from '../components/signup/SignupCalendar';
import PlayerAvailability from '../components/signup/PlayerAvailability';
import EmailPreferences from '../components/signup/EmailPreferences';

const SignupPage = () => {
  const { user, isAuthenticated, loginWithRedirect } = useAuth0();
  const [activeTab, setActiveTab] = useState('calendar');
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Tab configuration
  const tabs = [
    { id: 'calendar', label: '📅 Daily Signups', icon: '📅' },
    { id: 'availability', label: '🕒 My Availability', icon: '🕒' },
    { id: 'preferences', label: '📧 Email Settings', icon: '📧' }
  ];

  const handleSignupChange = () => {
    // Trigger refresh of any related components
    setRefreshTrigger(prev => prev + 1);
  };

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
      <div style={{ marginBottom: '30px' }}>
        <h1 style={{ 
          color: '#333',
          marginBottom: '10px',
          fontSize: '28px',
          fontWeight: '700'
        }}>
          🏌️ Golf Sign-up & Preferences
        </h1>
        <p style={{ 
          color: '#6c757d', 
          fontSize: '16px',
          margin: 0
        }}>
          Manage your daily golf sign-ups, availability, and email preferences
        </p>
        {user && (
          <div style={{
            marginTop: '10px',
            padding: '8px 12px',
            background: '#e3f2fd',
            color: '#1976d2',
            borderRadius: '6px',
            fontSize: '14px',
            display: 'inline-block'
          }}>
            Welcome, {user.name || user.email}
          </div>
        )}
      </div>

      {/* Tab Navigation */}
      <div style={{
        borderBottom: '2px solid #dee2e6',
        marginBottom: '30px'
      }}>
        <div style={{
          display: 'flex',
          gap: '0'
        }}>
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                background: activeTab === tab.id ? '#007bff' : 'transparent',
                color: activeTab === tab.id ? 'white' : '#495057',
                border: 'none',
                padding: '12px 20px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600',
                borderTopLeftRadius: '6px',
                borderTopRightRadius: '6px',
                marginBottom: '-2px',
                borderBottom: activeTab === tab.id ? '2px solid #007bff' : '2px solid transparent',
                transition: 'all 0.2s'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div style={{ minHeight: '500px' }}>
        {activeTab === 'calendar' && (
          <div>
            <div style={{ marginBottom: '20px' }}>
              <h2 style={{ color: '#333', marginBottom: '10px' }}>
                📅 Daily Golf Sign-ups
              </h2>
              <p style={{ color: '#6c757d', fontSize: '14px' }}>
                View and manage sign-ups for the next 7 days. Click on any day to sign up or cancel your spot.
              </p>
            </div>
            <SignupCalendar 
              key={refreshTrigger} 
              onSignupChange={handleSignupChange} 
            />
          </div>
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

      {/* Footer Info */}
      <div style={{
        marginTop: '40px',
        padding: '20px',
        background: '#f8f9fa',
        borderRadius: '8px',
        border: '1px solid #dee2e6'
      }}>
        <h4 style={{ color: '#495057', marginBottom: '10px' }}>
          💡 How it works
        </h4>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
          gap: '15px',
          fontSize: '14px',
          color: '#6c757d'
        }}>
          <div>
            <strong>Daily Sign-ups:</strong> View who's playing each day and add yourself to the list. 
            Perfect for organizing regular games.
          </div>
          <div>
            <strong>Availability:</strong> Set your preferred times so others know when you're typically free to play.
          </div>
          <div>
            <strong>Email Control:</strong> Choose what notifications you want to receive and reduce email overload.
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignupPage;