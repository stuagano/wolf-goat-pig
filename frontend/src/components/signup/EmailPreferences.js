import React, { useState, useEffect } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import '../../styles/mobile-touch.css';

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
  const [emailStatus, setEmailStatus] = useState(null);
  const [testEmail, setTestEmail] = useState(user?.email || '');
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState(null);

  // Email frequency options
  const frequencyOptions = [
    { value: 'daily', label: 'Daily' },
    { value: 'weekly', label: 'Weekly' },
    { value: 'monthly', label: 'Monthly' },
    { value: 'never', label: 'Never' }
  ];

  // Notification time options
  const timeOptions = [
    '6:00 AM', '7:00 AM', '8:00 AM', '9:00 AM', '10:00 AM',
    '12:00 PM', '1:00 PM', '5:00 PM', '6:00 PM', '7:00 PM'
  ];

  // Check email service status
  const checkEmailStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/email/status`);
      if (response.ok) {
        const data = await response.json();
        setEmailStatus(data);
      }
    } catch (err) {
      console.error('Error checking email status:', err);
      setEmailStatus({ configured: false });
    }
  };

  // Load current email preferences
  const loadPreferences = async () => {
    try {
      setLoading(true);
      // Use authenticated user endpoint
      const response = await fetch(`${API_URL}/players/me/email-preferences`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        }
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
    checkEmailStatus();
    if (user?.email) {
      setTestEmail(user.email);
    }
  }, [user]);

  // Update a preference
  const updatePreference = (key, value) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // Save preferences
  const savePreferences = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      const response = await fetch(`${API_URL}/players/me/email-preferences`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify(preferences)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save preferences');
      }

      const updatedPreferences = await response.json();
      setPreferences(updatedPreferences);
      setSuccess(true);
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
      
    } catch (err) {
      console.error('Save error:', err);
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  // Send test email
  const sendTestEmail = async () => {
    if (!testEmail) {
      setError('Please enter an email address for testing');
      return;
    }

    if (!emailStatus?.configured) {
      setError('Email service is not configured. Please check server configuration.');
      return;
    }

    setTestLoading(true);
    setTestResult(null);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/email/send-test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          to_email: testEmail,
          player_name: user?.name || 'Test Player',
          signup_date: new Date().toLocaleDateString()
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setTestResult({ success: true, message: data.message });
      } else {
        setTestResult({ success: false, message: data.detail });
      }
    } catch (err) {
      setTestResult({ success: false, message: err.message });
    } finally {
      setTestLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '40px',
        fontSize: '16px',
        color: '#6c757d'
      }}>
        Loading your email preferences...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '600px', padding: '0 12px' }}>
      {error && (
        <div style={{
          backgroundColor: '#fef2f2',
          color: '#991b1b',
          padding: '14px',
          borderRadius: '10px',
          marginBottom: '16px',
          border: '1px solid #fecaca',
          fontSize: '14px'
        }}>
          {error}
        </div>
      )}

      {success && (
        <div style={{
          backgroundColor: '#ecfdf5',
          color: '#065f46',
          padding: '14px',
          borderRadius: '10px',
          marginBottom: '16px',
          border: '1px solid #a7f3d0',
          fontSize: '14px'
        }}>
          ✅ Preferences saved!
        </div>
      )}

      {/* Email Service Status */}
      <div style={{
        border: `1px solid ${emailStatus?.configured ? '#28a745' : '#dc3545'}`,
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '20px',
        background: emailStatus?.configured ? '#d4edda' : '#f8d7da'
      }}>
        <h3 style={{ 
          color: emailStatus?.configured ? '#155724' : '#721c24', 
          marginBottom: '15px',
          fontSize: '18px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          {emailStatus?.configured ? '✅' : '⚠️'} Email Service Status
        </h3>
        
        <div style={{ fontSize: '14px', color: emailStatus?.configured ? '#155724' : '#721c24', marginBottom: '15px' }}>
          {emailStatus?.configured 
            ? `Email service is configured and ready to send notifications via ${emailStatus.smtp_host}` 
            : 'Email service is not configured. Please check server settings.'}
        </div>

        {emailStatus?.configured && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '15px' }}>
            <div>
              <label style={{ fontSize: '13px', color: '#6b7280', fontWeight: '600', display: 'block', marginBottom: '6px' }}>Test Email Address:</label>
              <input
                type="email"
                value={testEmail}
                onChange={(e) => setTestEmail(e.target.value)}
                placeholder="Enter email to test"
                className="mobile-form-control"
                style={{
                  width: '100%',
                  minHeight: '48px',
                  padding: '12px',
                  border: '2px solid #e5e7eb',
                  borderRadius: '10px',
                  fontSize: '16px',
                  boxSizing: 'border-box'
                }}
              />
            </div>
            <button
              onClick={sendTestEmail}
              disabled={testLoading || !testEmail}
              className="mobile-button"
              style={{
                width: '100%',
                minHeight: '48px',
                background: testLoading || !testEmail ? '#9ca3af' : '#3b82f6',
                color: 'white',
                border: 'none',
                padding: '12px 16px',
                borderRadius: '10px',
                fontSize: '15px',
                fontWeight: '600',
                cursor: testLoading || !testEmail ? 'not-allowed' : 'pointer',
                touchAction: 'manipulation'
              }}
            >
              {testLoading ? '⏳ Testing...' : '🧪 Send Test Email'}
            </button>
          </div>
        )}

        {testResult && (
          <div style={{
            padding: '12px',
            borderRadius: '6px',
            background: testResult.success ? '#d4edda' : '#f8d7da',
            border: `1px solid ${testResult.success ? '#c3e6cb' : '#f5c6cb'}`,
            color: testResult.success ? '#155724' : '#721c24',
            fontSize: '14px',
            marginTop: '10px'
          }}>
            {testResult.success ? '✅' : '❌'} {testResult.message}
          </div>
        )}
      </div>

      {/* Email Notification Types */}
      <div style={{
        border: '1px solid #dee2e6',
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '20px'
      }}>
        <h3 style={{ 
          color: '#495057', 
          marginBottom: '15px',
          fontSize: '18px'
        }}>
          📧 Email Notifications
        </h3>
        
        <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '20px' }}>
          Choose which types of emails you'd like to receive about golf activities.
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Daily Signups */}
          <label
            className="mobile-checkbox-container"
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '14px',
              background: '#f9fafb',
              borderRadius: '10px',
              cursor: 'pointer',
              minHeight: '60px',
              touchAction: 'manipulation'
            }}
          >
            <div style={{ flex: 1, paddingRight: '12px' }}>
              <div style={{ fontWeight: '600', color: '#1f2937', marginBottom: '4px', fontSize: '15px' }}>
                Daily Sign-up Summaries
              </div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>
                Who has signed up to play
              </div>
            </div>
            <input
              type="checkbox"
              checked={preferences.daily_signups_enabled}
              onChange={(e) => updatePreference('daily_signups_enabled', e.target.checked)}
              className="mobile-checkbox"
              style={{ width: '28px', height: '28px', minWidth: '28px', accentColor: '#047857' }}
            />
          </label>

          {/* Signup Confirmations */}
          <label
            className="mobile-checkbox-container"
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '14px',
              background: '#f9fafb',
              borderRadius: '10px',
              cursor: 'pointer',
              minHeight: '60px',
              touchAction: 'manipulation'
            }}
          >
            <div style={{ flex: 1, paddingRight: '12px' }}>
              <div style={{ fontWeight: '600', color: '#1f2937', marginBottom: '4px', fontSize: '15px' }}>
                Sign-up Confirmations
              </div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>
                When someone joins your day
              </div>
            </div>
            <input
              type="checkbox"
              checked={preferences.signup_confirmations_enabled}
              onChange={(e) => updatePreference('signup_confirmations_enabled', e.target.checked)}
              className="mobile-checkbox"
              style={{ width: '28px', height: '28px', minWidth: '28px', accentColor: '#047857' }}
            />
          </label>

          {/* Signup Reminders */}
          <label
            className="mobile-checkbox-container"
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '14px',
              background: '#f9fafb',
              borderRadius: '10px',
              cursor: 'pointer',
              minHeight: '60px',
              touchAction: 'manipulation'
            }}
          >
            <div style={{ flex: 1, paddingRight: '12px' }}>
              <div style={{ fontWeight: '600', color: '#1f2937', marginBottom: '4px', fontSize: '15px' }}>
                Sign-up Reminders
              </div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>
                Reminders for upcoming days
              </div>
            </div>
            <input
              type="checkbox"
              checked={preferences.signup_reminders_enabled}
              onChange={(e) => updatePreference('signup_reminders_enabled', e.target.checked)}
              className="mobile-checkbox"
              style={{ width: '28px', height: '28px', minWidth: '28px', accentColor: '#047857' }}
            />
          </label>

          {/* Game Invitations */}
          <label
            className="mobile-checkbox-container"
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '14px',
              background: '#f9fafb',
              borderRadius: '10px',
              cursor: 'pointer',
              minHeight: '60px',
              touchAction: 'manipulation'
            }}
          >
            <div style={{ flex: 1, paddingRight: '12px' }}>
              <div style={{ fontWeight: '600', color: '#1f2937', marginBottom: '4px', fontSize: '15px' }}>
                Game Invitations
              </div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>
                Direct invites to play
              </div>
            </div>
            <input
              type="checkbox"
              checked={preferences.game_invitations_enabled}
              onChange={(e) => updatePreference('game_invitations_enabled', e.target.checked)}
              className="mobile-checkbox"
              style={{ width: '28px', height: '28px', minWidth: '28px', accentColor: '#047857' }}
            />
          </label>

          {/* Weekly Summary */}
          <label
            className="mobile-checkbox-container"
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '14px',
              background: '#f9fafb',
              borderRadius: '10px',
              cursor: 'pointer',
              minHeight: '60px',
              touchAction: 'manipulation'
            }}
          >
            <div style={{ flex: 1, paddingRight: '12px' }}>
              <div style={{ fontWeight: '600', color: '#1f2937', marginBottom: '4px', fontSize: '15px' }}>
                Weekly Summary
              </div>
              <div style={{ fontSize: '13px', color: '#6b7280' }}>
                Recap of golf activity
              </div>
            </div>
            <input
              type="checkbox"
              checked={preferences.weekly_summary_enabled}
              onChange={(e) => updatePreference('weekly_summary_enabled', e.target.checked)}
              className="mobile-checkbox"
              style={{ width: '28px', height: '28px', minWidth: '28px', accentColor: '#047857' }}
            />
          </label>
        </div>
      </div>

      {/* Email Frequency & Timing */}
      <div style={{
        border: '2px solid #e5e7eb',
        borderRadius: '12px',
        padding: '16px',
        marginBottom: '16px'
      }}>
        <h3 style={{
          color: '#1f2937',
          marginBottom: '16px',
          fontSize: '17px',
          fontWeight: '700'
        }}>
          ⏰ Timing & Frequency
        </h3>

        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}>
          {/* Email Frequency */}
          <div>
            <label style={{
              display: 'block',
              fontSize: '14px',
              color: '#374151',
              marginBottom: '8px',
              fontWeight: '600'
            }}>
              Email Frequency:
            </label>
            <select
              value={preferences.email_frequency}
              onChange={(e) => updatePreference('email_frequency', e.target.value)}
              className="mobile-select"
              style={{
                width: '100%',
                minHeight: '48px',
                padding: '12px 40px 12px 12px',
                border: '2px solid #e5e7eb',
                borderRadius: '10px',
                fontSize: '16px',
                background: 'white',
                appearance: 'none',
                WebkitAppearance: 'none',
                backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23374151' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`,
                backgroundRepeat: 'no-repeat',
                backgroundPosition: 'right 14px center'
              }}
            >
              {frequencyOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '6px' }}>
              Set to "Never" to pause all emails
            </div>
          </div>

          {/* Notification Time */}
          <div>
            <label style={{
              display: 'block',
              fontSize: '14px',
              color: '#374151',
              marginBottom: '8px',
              fontWeight: '600'
            }}>
              Notification Time:
            </label>
            <select
              value={preferences.preferred_notification_time}
              onChange={(e) => updatePreference('preferred_notification_time', e.target.value)}
              className="mobile-select"
              style={{
                width: '100%',
                minHeight: '48px',
                padding: '12px 40px 12px 12px',
                border: '2px solid #e5e7eb',
                borderRadius: '10px',
                fontSize: '16px',
                background: 'white',
                appearance: 'none',
                WebkitAppearance: 'none',
                backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23374151' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`,
                backgroundRepeat: 'no-repeat',
                backgroundPosition: 'right 14px center'
              }}
            >
              {timeOptions.map(time => (
                <option key={time} value={time}>
                  {time}
                </option>
              ))}
            </select>
            <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '6px' }}>
              When to receive daily notifications
            </div>
          </div>
        </div>
      </div>

      {/* Quick Presets */}
      <div style={{
        border: '2px solid #e5e7eb',
        borderRadius: '12px',
        padding: '16px',
        marginBottom: '16px',
        background: '#f9fafb'
      }}>
        <h4 style={{
          color: '#1f2937',
          marginBottom: '12px',
          fontSize: '15px',
          fontWeight: '700'
        }}>
          🚀 Quick Presets
        </h4>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <button
            onClick={() => setPreferences(prev => ({
              ...prev,
              daily_signups_enabled: true,
              signup_confirmations_enabled: true,
              signup_reminders_enabled: true,
              game_invitations_enabled: true,
              weekly_summary_enabled: true,
              email_frequency: 'daily'
            }))}
            className="mobile-button"
            style={{
              width: '100%',
              minHeight: '48px',
              background: '#047857',
              color: 'white',
              border: 'none',
              padding: '12px 16px',
              borderRadius: '10px',
              fontSize: '15px',
              fontWeight: '600',
              cursor: 'pointer',
              touchAction: 'manipulation'
            }}
          >
            📧 All Emails
          </button>

          <button
            onClick={() => setPreferences(prev => ({
              ...prev,
              daily_signups_enabled: false,
              signup_confirmations_enabled: true,
              signup_reminders_enabled: false,
              game_invitations_enabled: true,
              weekly_summary_enabled: true,
              email_frequency: 'weekly'
            }))}
            className="mobile-button"
            style={{
              width: '100%',
              minHeight: '48px',
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              padding: '12px 16px',
              borderRadius: '10px',
              fontSize: '15px',
              fontWeight: '600',
              cursor: 'pointer',
              touchAction: 'manipulation'
            }}
          >
            📋 Essential Only
          </button>

          <button
            onClick={() => setPreferences(prev => ({
              ...prev,
              daily_signups_enabled: false,
              signup_confirmations_enabled: false,
              signup_reminders_enabled: false,
              game_invitations_enabled: true,
              weekly_summary_enabled: false,
              email_frequency: 'never'
            }))}
            className="mobile-button"
            style={{
              width: '100%',
              minHeight: '48px',
              background: '#6b7280',
              color: 'white',
              border: 'none',
              padding: '12px 16px',
              borderRadius: '10px',
              fontSize: '15px',
              fontWeight: '600',
              cursor: 'pointer',
              touchAction: 'manipulation'
            }}
          >
            🔕 Invites Only
          </button>
        </div>
      </div>

      {/* Save Button */}
      <div style={{ marginBottom: '20px' }}>
        <button
          onClick={savePreferences}
          disabled={saving}
          className="mobile-button mobile-button-primary"
          style={{
            width: '100%',
            minHeight: '56px',
            background: saving ? '#9ca3af' : '#047857',
            color: 'white',
            border: 'none',
            padding: '16px 24px',
            borderRadius: '12px',
            fontSize: '17px',
            cursor: saving ? 'not-allowed' : 'pointer',
            fontWeight: '700',
            touchAction: 'manipulation'
          }}
        >
          {saving ? '⏳ Saving...' : '💾 Save Preferences'}
        </button>
      </div>

      {/* Info Box */}
      <div style={{
        marginTop: '20px',
        padding: '16px',
        background: '#e3f2fd',
        borderRadius: '6px',
        border: '1px solid #bbdefb'
      }}>
        <div style={{ color: '#1976d2', fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>
          💡 Email Management Tips
        </div>
        <ul style={{ color: '#1976d2', fontSize: '13px', margin: 0, paddingLeft: '18px' }}>
          <li>Set frequency to "Never" to disable all emails while keeping your other settings</li>
          <li>"Essential Only" preset keeps invitations and confirmations but reduces daily noise</li>
          <li>Weekly summaries are great for staying informed without daily interruptions</li>
        </ul>
      </div>
    </div>
  );
};

export default EmailPreferences;