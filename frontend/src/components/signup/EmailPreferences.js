import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';

const API_URL = process.env.REACT_APP_API_URL || "";

const EmailPreferences = () => {
  const { user } = useAuth0();
  const [preferences, setPreferences] = useState({
    daily_signups_enabled: true,
    signup_confirmations_enabled: true,
    signup_reminders_enabled: true,
    game_invitations_enabled: true,
    weekly_summary_enabled: true,
    email_frequency: 'daily',
    preferred_notification_time: '8:00 AM'
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const frequencyOptions = [
    { value: 'daily', label: 'Daily' },
    { value: 'weekly', label: 'Weekly' },
    { value: 'monthly', label: 'Monthly' },
    { value: 'never', label: 'Never' }
  ];

  const timeOptions = [
    '6:00 AM', '7:00 AM', '8:00 AM', '9:00 AM', '10:00 AM',
    '12:00 PM', '1:00 PM', '5:00 PM', '6:00 PM', '7:00 PM'
  ];

  const loadPreferences = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/players/me/email-preferences`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
      });

      if (response.ok) {
        const data = await response.json();
        setPreferences(data);
      }
      setError(null);
    } catch (err) {
      console.error('Error loading preferences:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPreferences();
  }, [user]);

  const updatePreference = (key, value) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
    setSuccess(false);
  };

  const savePreferences = async () => {
    try {
      setSaving(true);
      setError(null);

      const response = await fetch(`${API_URL}/players/me/email-preferences`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify(preferences)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save');
      }

      const updatedPreferences = await response.json();
      setPreferences(updatedPreferences);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error('Save error:', err);
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const setPreset = (preset) => {
    switch (preset) {
      case 'all':
        setPreferences(prev => ({
          ...prev,
          daily_signups_enabled: true,
          signup_confirmations_enabled: true,
          signup_reminders_enabled: true,
          game_invitations_enabled: true,
          weekly_summary_enabled: true,
          email_frequency: 'daily'
        }));
        break;
      case 'essential':
        setPreferences(prev => ({
          ...prev,
          daily_signups_enabled: false,
          signup_confirmations_enabled: true,
          signup_reminders_enabled: false,
          game_invitations_enabled: true,
          weekly_summary_enabled: true,
          email_frequency: 'weekly'
        }));
        break;
      case 'minimal':
        setPreferences(prev => ({
          ...prev,
          daily_signups_enabled: false,
          signup_confirmations_enabled: false,
          signup_reminders_enabled: false,
          game_invitations_enabled: true,
          weekly_summary_enabled: false,
          email_frequency: 'never'
        }));
        break;
      default:
        return;
    }
    setSuccess(false);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '60px', color: '#6b7280' }}>
        Loading...
      </div>
    );
  }

  const notificationTypes = [
    { key: 'daily_signups_enabled', label: 'Daily Sign-up Summaries', desc: 'Who has signed up to play' },
    { key: 'signup_confirmations_enabled', label: 'Sign-up Confirmations', desc: 'When someone joins your day' },
    { key: 'signup_reminders_enabled', label: 'Sign-up Reminders', desc: 'Reminders for upcoming days' },
    { key: 'game_invitations_enabled', label: 'Game Invitations', desc: 'Direct invites to play' },
    { key: 'weekly_summary_enabled', label: 'Weekly Summary', desc: 'Recap of golf activity' }
  ];

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '16px' }}>
      {error && (
        <div style={{
          background: '#fef2f2',
          color: '#dc2626',
          padding: '12px',
          borderRadius: '8px',
          marginBottom: '16px',
          fontSize: '14px'
        }}>
          {error}
          <button onClick={() => setError(null)} style={{ float: 'right', background: 'none', border: 'none', cursor: 'pointer' }}>×</button>
        </div>
      )}

      {success && (
        <div style={{
          background: '#ecfdf5',
          color: '#065f46',
          padding: '12px',
          borderRadius: '8px',
          marginBottom: '16px',
          fontSize: '14px'
        }}>
          ✓ Preferences saved!
        </div>
      )}

      {/* Quick Presets */}
      <div style={{
        display: 'flex',
        gap: '8px',
        marginBottom: '20px'
      }}>
        {[
          { key: 'all', label: 'All Emails', color: '#047857' },
          { key: 'essential', label: 'Essential', color: '#0369a1' },
          { key: 'minimal', label: 'Minimal', color: '#6b7280' }
        ].map(preset => (
          <button
            key={preset.key}
            onClick={() => setPreset(preset.key)}
            style={{
              flex: 1,
              padding: '10px 12px',
              background: preset.color,
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Notification Types */}
      <div style={{
        background: '#fff',
        border: '1px solid #e5e7eb',
        borderRadius: '12px',
        overflow: 'hidden',
        marginBottom: '20px'
      }}>
        <div style={{
          background: '#f9fafb',
          padding: '12px 16px',
          borderBottom: '1px solid #e5e7eb',
          fontSize: '14px',
          fontWeight: '600',
          color: '#374151'
        }}>
          📧 Email Notifications
        </div>

        <div style={{ padding: '8px' }}>
          {notificationTypes.map(type => (
            <label
              key={type.key}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '12px',
                borderRadius: '8px',
                cursor: 'pointer',
                background: preferences[type.key] ? '#f0fdf4' : 'transparent'
              }}
            >
              <div style={{ flex: 1, paddingRight: '12px' }}>
                <div style={{ fontWeight: '500', color: '#1f2937', fontSize: '14px' }}>
                  {type.label}
                </div>
                <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '2px' }}>
                  {type.desc}
                </div>
              </div>
              <input
                type="checkbox"
                checked={preferences[type.key]}
                onChange={(e) => updatePreference(type.key, e.target.checked)}
                style={{ width: '20px', height: '20px', accentColor: '#047857' }}
              />
            </label>
          ))}
        </div>
      </div>

      {/* Timing */}
      <div style={{
        background: '#fff',
        border: '1px solid #e5e7eb',
        borderRadius: '12px',
        overflow: 'hidden',
        marginBottom: '20px'
      }}>
        <div style={{
          background: '#f9fafb',
          padding: '12px 16px',
          borderBottom: '1px solid #e5e7eb',
          fontSize: '14px',
          fontWeight: '600',
          color: '#374151'
        }}>
          ⏰ Timing
        </div>

        <div style={{ padding: '16px' }}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '13px', color: '#6b7280', marginBottom: '6px' }}>
              Frequency
            </label>
            <select
              value={preferences.email_frequency}
              onChange={(e) => updatePreference('email_frequency', e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '14px'
              }}
            >
              {frequencyOptions.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', color: '#6b7280', marginBottom: '6px' }}>
              Notification Time
            </label>
            <select
              value={preferences.preferred_notification_time}
              onChange={(e) => updatePreference('preferred_notification_time', e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                fontSize: '14px'
              }}
            >
              {timeOptions.map(time => (
                <option key={time} value={time}>{time}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <button
        onClick={savePreferences}
        disabled={saving}
        style={{
          width: '100%',
          padding: '14px',
          background: saving ? '#9ca3af' : '#047857',
          color: 'white',
          border: 'none',
          borderRadius: '10px',
          fontSize: '16px',
          fontWeight: '600',
          cursor: saving ? 'not-allowed' : 'pointer'
        }}
      >
        {saving ? 'Saving...' : '💾 Save Preferences'}
      </button>

      {/* Info */}
      <div style={{
        marginTop: '20px',
        padding: '12px',
        background: '#e0f2fe',
        borderRadius: '8px',
        fontSize: '12px',
        color: '#0369a1'
      }}>
        💡 Set frequency to "Never" to pause all emails while keeping your other settings.
      </div>
    </div>
  );
};

export default EmailPreferences;
