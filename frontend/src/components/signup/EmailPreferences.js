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
      // For now using player ID 1, in real app this would come from auth
      const response = await fetch(`${API_URL}/players/1/email-preferences`);
      
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

      const response = await fetch(`${API_URL}/players/1/email-preferences`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
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
    <div style={{ maxWidth: '600px' }}>
      {error && (
        <div style={{ 
          backgroundColor: '#f8d7da', 
          color: '#721c24', 
          padding: '12px', 
          borderRadius: '6px', 
          marginBottom: '20px',
          border: '1px solid #f5c6cb'
        }}>
          {error}
        </div>
      )}

      {success && (
        <div style={{ 
          backgroundColor: '#d4edda', 
          color: '#155724', 
          padding: '12px', 
          borderRadius: '6px', 
          marginBottom: '20px',
          border: '1px solid #c3e6cb'
        }}>
          ✅ Email preferences saved successfully!
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
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginBottom: '15px' }}>
            <div>
              <label style={{ fontSize: '12px', color: '#6c757d', fontWeight: '600' }}>Test Email Address:</label>
              <input
                type="email"
                value={testEmail}
                onChange={(e) => setTestEmail(e.target.value)}
                placeholder="Enter email to test"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ced4da',
                  borderRadius: '4px',
                  fontSize: '14px',
                  marginTop: '4px'
                }}
              />
            </div>
            <div style={{ display: 'flex', alignItems: 'end' }}>
              <button
                onClick={sendTestEmail}
                disabled={testLoading || !testEmail}
                style={{
                  background: testLoading ? '#6c757d' : '#007bff',
                  color: 'white',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  fontSize: '14px',
                  cursor: testLoading || !testEmail ? 'not-allowed' : 'pointer',
                  opacity: testLoading || !testEmail ? 0.7 : 1
                }}
              >
                {testLoading ? '⏳ Testing...' : '🧪 Test Email'}
              </button>
            </div>
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

        <div style={{ display: 'grid', gap: '16px' }}>
          {/* Daily Signups */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            padding: '12px',
            background: '#f8f9fa',
            borderRadius: '6px'
          }}>
            <div>
              <div style={{ fontWeight: '600', color: '#495057', marginBottom: '4px' }}>
                Daily Sign-up Summaries
              </div>
              <div style={{ fontSize: '13px', color: '#6c757d' }}>
                Get daily emails showing who has signed up to play
              </div>
            </div>
            <label style={{ cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={preferences.daily_signups_enabled}
                onChange={(e) => updatePreference('daily_signups_enabled', e.target.checked)}
                style={{ transform: 'scale(1.2)' }}
              />
            </label>
          </div>

          {/* Signup Confirmations */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            padding: '12px',
            background: '#f8f9fa',
            borderRadius: '6px'
          }}>
            <div>
              <div style={{ fontWeight: '600', color: '#495057', marginBottom: '4px' }}>
                Sign-up Confirmations
              </div>
              <div style={{ fontSize: '13px', color: '#6c757d' }}>
                Get notified when someone signs up for the same day as you
              </div>
            </div>
            <label style={{ cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={preferences.signup_confirmations_enabled}
                onChange={(e) => updatePreference('signup_confirmations_enabled', e.target.checked)}
                style={{ transform: 'scale(1.2)' }}
              />
            </label>
          </div>

          {/* Signup Reminders */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            padding: '12px',
            background: '#f8f9fa',
            borderRadius: '6px'
          }}>
            <div>
              <div style={{ fontWeight: '600', color: '#495057', marginBottom: '4px' }}>
                Sign-up Reminders
              </div>
              <div style={{ fontSize: '13px', color: '#6c757d' }}>
                Get reminders to sign up for upcoming days
              </div>
            </div>
            <label style={{ cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={preferences.signup_reminders_enabled}
                onChange={(e) => updatePreference('signup_reminders_enabled', e.target.checked)}
                style={{ transform: 'scale(1.2)' }}
              />
            </label>
          </div>

          {/* Game Invitations */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            padding: '12px',
            background: '#f8f9fa',
            borderRadius: '6px'
          }}>
            <div>
              <div style={{ fontWeight: '600', color: '#495057', marginBottom: '4px' }}>
                Direct Game Invitations
              </div>
              <div style={{ fontSize: '13px', color: '#6c757d' }}>
                Get emails when someone specifically invites you to play
              </div>
            </div>
            <label style={{ cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={preferences.game_invitations_enabled}
                onChange={(e) => updatePreference('game_invitations_enabled', e.target.checked)}
                style={{ transform: 'scale(1.2)' }}
              />
            </label>
          </div>

          {/* Weekly Summary */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            padding: '12px',
            background: '#f8f9fa',
            borderRadius: '6px'
          }}>
            <div>
              <div style={{ fontWeight: '600', color: '#495057', marginBottom: '4px' }}>
                Weekly Activity Summary
              </div>
              <div style={{ fontSize: '13px', color: '#6c757d' }}>
                Get a weekly recap of golf activity and your participation
              </div>
            </div>
            <label style={{ cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={preferences.weekly_summary_enabled}
                onChange={(e) => updatePreference('weekly_summary_enabled', e.target.checked)}
                style={{ transform: 'scale(1.2)' }}
              />
            </label>
          </div>
        </div>
      </div>

      {/* Email Frequency & Timing */}
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
          ⏰ Email Timing & Frequency
        </h3>
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '20px'
        }}>
          {/* Email Frequency */}
          <div>
            <label style={{ 
              display: 'block', 
              fontSize: '14px', 
              color: '#495057',
              marginBottom: '8px',
              fontWeight: '600'
            }}>
              Overall Email Frequency:
            </label>
            <select
              value={preferences.email_frequency}
              onChange={(e) => updatePreference('email_frequency', e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ced4da',
                borderRadius: '4px',
                fontSize: '14px'
              }}
            >
              {frequencyOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <div style={{ fontSize: '12px', color: '#6c757d', marginTop: '4px' }}>
              This overrides individual settings above when set to "Never"
            </div>
          </div>

          {/* Notification Time */}
          <div>
            <label style={{ 
              display: 'block', 
              fontSize: '14px', 
              color: '#495057',
              marginBottom: '8px',
              fontWeight: '600'
            }}>
              Preferred Notification Time:
            </label>
            <select
              value={preferences.preferred_notification_time}
              onChange={(e) => updatePreference('preferred_notification_time', e.target.value)}
              style={{
                width: '100%',
                padding: '10px',
                border: '1px solid #ced4da',
                borderRadius: '4px',
                fontSize: '14px'
              }}
            >
              {timeOptions.map(time => (
                <option key={time} value={time}>
                  {time}
                </option>
              ))}
            </select>
            <div style={{ fontSize: '12px', color: '#6c757d', marginTop: '4px' }}>
              When you'd like to receive daily notifications
            </div>
          </div>
        </div>
      </div>

      {/* Quick Presets */}
      <div style={{
        border: '1px solid #dee2e6',
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '20px',
        background: '#f8f9fa'
      }}>
        <h4 style={{ 
          color: '#495057', 
          marginBottom: '10px',
          fontSize: '16px'
        }}>
          🚀 Quick Presets
        </h4>
        
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
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
            style={{
              background: '#28a745',
              color: 'white',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '4px',
              fontSize: '13px',
              cursor: 'pointer'
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
            style={{
              background: '#007bff',
              color: 'white',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '4px',
              fontSize: '13px',
              cursor: 'pointer'
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
            style={{
              background: '#6c757d',
              color: 'white',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '4px',
              fontSize: '13px',
              cursor: 'pointer'
            }}
          >
            🔕 Invites Only
          </button>
        </div>
      </div>

      {/* Save Button */}
      <div style={{ textAlign: 'center' }}>
        <button
          onClick={savePreferences}
          disabled={saving}
          style={{
            background: '#007bff',
            color: 'white',
            border: 'none',
            padding: '12px 24px',
            borderRadius: '6px',
            fontSize: '16px',
            cursor: saving ? 'not-allowed' : 'pointer',
            opacity: saving ? 0.7 : 1,
            fontWeight: '600'
          }}
        >
          {saving ? 'Saving...' : '💾 Save Email Preferences'}
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