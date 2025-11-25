import React, { useState, useEffect } from 'react';

const EmailSettings = () => {
  const [emailStatus, setEmailStatus] = useState(null);
  const [schedulerStatus, setSchedulerStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    checkEmailStatus();
    checkSchedulerStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const checkEmailStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/email/status`);
      const data = await response.json();
      setEmailStatus(data);
    } catch (error) {
      console.error('Failed to check email status:', error);
    }
  };

  const checkSchedulerStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/email/scheduler-status`);
      const data = await response.json();
      setSchedulerStatus(data);
    } catch (error) {
      console.error('Failed to check scheduler status:', error);
    }
  };

  const initializeScheduler = async () => {
    setLoading(true);
    setMessage('');
    
    try {
      const response = await fetch(`${API_URL}/email/initialize-scheduler`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setMessage('Email scheduler initialized successfully!');
        checkSchedulerStatus();
      } else {
        setMessage(`Failed to initialize: ${data.detail}`);
      }
    } catch (error) {
      setMessage(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const sendTestEmail = async () => {
    setLoading(true);
    setMessage('');
    
    try {
      const response = await fetch(`${API_URL}/email/send-test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          to_email: prompt('Enter email address to send test to:'),
        }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        setMessage('Test email sent successfully!');
      } else {
        setMessage(`Failed to send test email: ${data.detail}`);
      }
    } catch (error) {
      setMessage(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h2>Email Configuration</h2>
      
      {/* Email Service Status */}
      <div style={{ 
        border: '1px solid #ddd', 
        borderRadius: '8px', 
        padding: '15px', 
        marginBottom: '20px',
        backgroundColor: emailStatus?.configured ? '#f0fff0' : '#fff0f0'
      }}>
        <h3>Email Service Status</h3>
        {emailStatus ? (
          <>
            <p><strong>Configured:</strong> {emailStatus.configured ? '✅ Yes' : '❌ No'}</p>
            <p><strong>SMTP Host:</strong> {emailStatus.smtp_host}</p>
            <p><strong>SMTP Port:</strong> {emailStatus.smtp_port}</p>
            <p><strong>From Email:</strong> {emailStatus.from_email}</p>
            {emailStatus.missing_config?.length > 0 && (
              <p style={{ color: 'red' }}>
                <strong>Missing Configuration:</strong> {emailStatus.missing_config.join(', ')}
              </p>
            )}
          </>
        ) : (
          <p>Loading...</p>
        )}
      </div>

      {/* Email Scheduler Status */}
      <div style={{ 
        border: '1px solid #ddd', 
        borderRadius: '8px', 
        padding: '15px', 
        marginBottom: '20px',
        backgroundColor: schedulerStatus?.running ? '#f0fff0' : '#fffef0'
      }}>
        <h3>Email Scheduler Status</h3>
        {schedulerStatus ? (
          <>
            <p><strong>Initialized:</strong> {schedulerStatus.initialized ? '✅ Yes' : '❌ No'}</p>
            <p><strong>Running:</strong> {schedulerStatus.running ? '✅ Yes' : '⚠️ No'}</p>
            <p style={{ fontSize: '14px', color: '#666' }}>{schedulerStatus.message}</p>
          </>
        ) : (
          <p>Loading...</p>
        )}
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
        {!schedulerStatus?.running && (
          <button
            onClick={initializeScheduler}
            disabled={loading}
            style={{
              padding: '10px 20px',
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1,
            }}
          >
            {loading ? 'Initializing...' : 'Initialize Email Scheduler'}
          </button>
        )}
        
        {emailStatus?.configured && (
          <button
            onClick={sendTestEmail}
            disabled={loading}
            style={{
              padding: '10px 20px',
              backgroundColor: '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1,
            }}
          >
            Send Test Email
          </button>
        )}
        
        <button
          onClick={() => {
            checkEmailStatus();
            checkSchedulerStatus();
          }}
          disabled={loading}
          style={{
            padding: '10px 20px',
            backgroundColor: '#9E9E9E',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1,
          }}
        >
          Refresh Status
        </button>
      </div>

      {/* Message Display */}
      {message && (
        <div style={{
          padding: '10px',
          borderRadius: '4px',
          backgroundColor: message.includes('success') ? '#d4edda' : '#f8d7da',
          color: message.includes('success') ? '#155724' : '#721c24',
          border: `1px solid ${message.includes('success') ? '#c3e6cb' : '#f5c6cb'}`,
        }}>
          {message}
        </div>
      )}

      {/* Instructions */}
      <div style={{ 
        marginTop: '30px', 
        padding: '15px', 
        backgroundColor: '#f0f0f0', 
        borderRadius: '8px' 
      }}>
        <h4>Configuration Instructions</h4>
        <p>To configure email functionality, set the following environment variables on your server:</p>
        <ul style={{ fontSize: '14px' }}>
          <li><code>SMTP_HOST</code> - Your SMTP server hostname</li>
          <li><code>SMTP_PORT</code> - SMTP server port (usually 587 for TLS)</li>
          <li><code>SMTP_USER</code> - SMTP username</li>
          <li><code>SMTP_PASSWORD</code> - SMTP password</li>
          <li><code>FROM_EMAIL</code> - Email address to send from</li>
          <li><code>FROM_NAME</code> - Display name for sent emails</li>
        </ul>
        <p style={{ fontSize: '14px', fontStyle: 'italic' }}>
          Note: Email functionality is optional. The app will work without it.
        </p>
      </div>
    </div>
  );
};

export default EmailSettings;