import React, { useState, useEffect } from 'react';
import { Card } from '../ui';

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const EmailSettings = () => {
  const [emailStatus, setEmailStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [testEmail, setTestEmail] = useState('');
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    fetchEmailStatus();
  }, []);

  const fetchEmailStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/email/status`);
      const data = await response.json();
      setEmailStatus(data);
    } catch (error) {
      console.error('Error fetching email status:', error);
    } finally {
      setLoading(false);
    }
  };

  const sendTestEmail = async () => {
    if (!testEmail) {
      alert('Please enter an email address');
      return;
    }

    setTestLoading(true);
    setTestResult(null);

    try {
      const response = await fetch(`${API_URL}/email/send-test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          to_email: testEmail,
          player_name: 'Test Player',
          signup_date: 'Tomorrow'
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setTestResult({ success: true, message: data.message });
      } else {
        setTestResult({ success: false, message: data.detail });
      }
    } catch (error) {
      setTestResult({ success: false, message: error.message });
    } finally {
      setTestLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8">
        <Card className="p-6 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Loading email settings...</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">📧 Email Settings</h1>
      
      {/* Email Service Status */}
      <Card className="mb-8">
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            {emailStatus?.configured ? '✅' : '⚠️'} Email Service Status
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Configuration Status
              </label>
              <div className={`px-3 py-2 rounded-lg ${
                emailStatus?.configured 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {emailStatus?.configured ? 'Configured' : 'Not Configured'}
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                SMTP Host
              </label>
              <div className="px-3 py-2 bg-gray-100 rounded-lg">
                {emailStatus?.smtp_host}
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                SMTP Port
              </label>
              <div className="px-3 py-2 bg-gray-100 rounded-lg">
                {emailStatus?.smtp_port}
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                From Email
              </label>
              <div className="px-3 py-2 bg-gray-100 rounded-lg">
                {emailStatus?.from_email}
              </div>
            </div>
          </div>

          {emailStatus?.missing_config?.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h3 className="font-semibold text-yellow-800 mb-2">
                Missing Configuration
              </h3>
              <p className="text-yellow-700 mb-3">
                The following environment variables need to be set:
              </p>
              <ul className="list-disc list-inside text-yellow-700">
                {emailStatus.missing_config.map((config) => (
                  <li key={config} className="font-mono">{config}</li>
                ))}
              </ul>
              <div className="mt-4 p-3 bg-yellow-100 rounded-lg">
                <p className="text-sm text-yellow-800">
                  <strong>For Gmail:</strong> Generate an App Password at{' '}
                  <a 
                    href="https://myaccount.google.com/apppasswords" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="underline"
                  >
                    myaccount.google.com/apppasswords
                  </a>
                </p>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Test Email */}
      <Card>
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">🧪 Test Email Functionality</h2>
          
          {emailStatus?.configured ? (
            <div>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Test Email Address
                </label>
                <input
                  type="email"
                  value={testEmail}
                  onChange={(e) => setTestEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="your.email@example.com"
                />
              </div>
              
              <button
                onClick={sendTestEmail}
                disabled={testLoading || !testEmail}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {testLoading && (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                )}
                {testLoading ? 'Sending...' : 'Send Test Email'}
              </button>

              {testResult && (
                <div className={`mt-4 p-4 rounded-lg ${
                  testResult.success 
                    ? 'bg-green-50 border border-green-200' 
                    : 'bg-red-50 border border-red-200'
                }`}>
                  <p className={testResult.success ? 'text-green-800' : 'text-red-800'}>
                    {testResult.success ? '✅' : '❌'} {testResult.message}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <p className="text-gray-600">
                Email service must be configured before testing. 
                Please set the required environment variables and restart the server.
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Email Types Documentation */}
      <Card className="mt-8">
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">📋 Available Email Types</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="font-semibold text-blue-800 mb-2">🎯 Signup Confirmation</h3>
              <p className="text-blue-700 text-sm">
                Sent when a player signs up for a game. Includes game details and confirmation.
              </p>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="font-semibold text-green-800 mb-2">⏰ Daily Reminders</h3>
              <p className="text-green-700 text-sm">
                Daily notifications about available games players can sign up for.
              </p>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <h3 className="font-semibold text-purple-800 mb-2">📊 Weekly Summary</h3>
              <p className="text-purple-700 text-sm">
                Weekly performance reports with stats, earnings, and rankings.
              </p>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <h3 className="font-semibold text-orange-800 mb-2">🎮 Game Invitations</h3>
              <p className="text-orange-700 text-sm">
                Personal invitations from other players to join specific games.
              </p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default EmailSettings;