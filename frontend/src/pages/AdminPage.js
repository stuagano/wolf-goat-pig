import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/ui';
import SheetIntegrationDashboard from '../components/SheetIntegrationDashboard';
import WGPAnalyticsDashboard from '../components/WGPAnalyticsDashboard';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const AdminPage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('email');
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);
  const [emailConfig, setEmailConfig] = useState({
    smtp_host: '',
    smtp_port: '',
    smtp_username: '',
    smtp_password: '',
    from_email: '',
    from_name: 'Wolf Goat Pig Admin'
  });
  const [testEmail, setTestEmail] = useState('');
  const [saveStatus, setSaveStatus] = useState('');
  const [testStatus, setTestStatus] = useState('');

  // Check admin access
  useEffect(() => {
    checkAdminAccess();
    if (activeTab === 'email') {
      fetchEmailConfig();
    }
  }, [activeTab]);

  const checkAdminAccess = async () => {
    try {
      // For now, using a simple admin check - you can enhance this with proper auth
      const adminEmails = ['stuagano@gmail.com', 'admin@wgp.com'];
      const userEmail = localStorage.getItem('userEmail') || 'stuagano@gmail.com'; // Default for testing
      
      if (adminEmails.includes(userEmail)) {
        setIsAdmin(true);
      } else {
        setIsAdmin(false);
      }
    } catch (error) {
      console.error('Error checking admin access:', error);
      setIsAdmin(false);
    } finally {
      setLoading(false);
    }
  };

  const fetchEmailConfig = async () => {
    try {
      const response = await fetch(`${API_URL}/admin/email-config`, {
        headers: {
          'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setEmailConfig(prev => ({
          ...prev,
          ...data.config
        }));
      }
    } catch (error) {
      console.error('Error fetching email config:', error);
    }
  };

  const handleEmailConfigChange = (field, value) => {
    setEmailConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const saveEmailConfig = async () => {
    setSaveStatus('saving');
    try {
      const response = await fetch(`${API_URL}/admin/email-config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com'
        },
        body: JSON.stringify(emailConfig)
      });

      if (response.ok) {
        setSaveStatus('success');
        setTimeout(() => setSaveStatus(''), 3000);
      } else {
        setSaveStatus('error');
      }
    } catch (error) {
      console.error('Error saving email config:', error);
      setSaveStatus('error');
    }
  };

  const testEmailConfiguration = async () => {
    if (!testEmail) {
      setTestStatus('Please enter a test email address');
      return;
    }

    setTestStatus('sending');
    try {
      const response = await fetch(`${API_URL}/admin/test-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com'
        },
        body: JSON.stringify({ 
          test_email: testEmail,
          config: emailConfig 
        })
      });

      if (response.ok) {
        setTestStatus('success');
        setTimeout(() => setTestStatus(''), 5000);
      } else {
        const error = await response.text();
        setTestStatus(`error: ${error}`);
      }
    } catch (error) {
      console.error('Error testing email:', error);
      setTestStatus('error: ' + error.message);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4">
          <Card className="p-8 text-center">
            <h2 className="text-2xl font-bold text-red-600 mb-4">Access Denied</h2>
            <p className="text-gray-600 mb-6">You don't have permission to access this page.</p>
            <button
              onClick={() => navigate('/')}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Go to Home
            </button>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">🔧 Admin Dashboard</h1>
          <p className="text-gray-600">Manage email settings, sheets integration, and analytics</p>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-1 mb-8 bg-gray-200 p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('email')}
            className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
              activeTab === 'email'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            📧 Email Settings
          </button>
          <button
            onClick={() => setActiveTab('sheets')}
            className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
              activeTab === 'sheets'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            📊 Sheets Integration
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`flex-1 px-4 py-2 rounded-md font-medium transition-colors ${
              activeTab === 'analytics'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            📈 Analytics
          </button>
        </div>

        {/* Email Settings Tab */}
        {activeTab === 'email' && (
          <div className="space-y-6">
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-6">SMTP Configuration</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    SMTP Host
                  </label>
                  <input
                    type="text"
                    value={emailConfig.smtp_host}
                    onChange={(e) => handleEmailConfigChange('smtp_host', e.target.value)}
                    placeholder="smtp.gmail.com"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    SMTP Port
                  </label>
                  <input
                    type="text"
                    value={emailConfig.smtp_port}
                    onChange={(e) => handleEmailConfigChange('smtp_port', e.target.value)}
                    placeholder="587"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    SMTP Username
                  </label>
                  <input
                    type="text"
                    value={emailConfig.smtp_username}
                    onChange={(e) => handleEmailConfigChange('smtp_username', e.target.value)}
                    placeholder="your-email@gmail.com"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    SMTP Password / App Password
                  </label>
                  <input
                    type="password"
                    value={emailConfig.smtp_password}
                    onChange={(e) => handleEmailConfigChange('smtp_password', e.target.value)}
                    placeholder="••••••••••••••••"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    For Gmail, use an App Password instead of your regular password
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    From Email
                  </label>
                  <input
                    type="email"
                    value={emailConfig.from_email}
                    onChange={(e) => handleEmailConfigChange('from_email', e.target.value)}
                    placeholder="noreply@wolfgoatpig.com"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    From Name
                  </label>
                  <input
                    type="text"
                    value={emailConfig.from_name}
                    onChange={(e) => handleEmailConfigChange('from_name', e.target.value)}
                    placeholder="Wolf Goat Pig Admin"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="mt-6 flex justify-end space-x-4">
                <button
                  onClick={saveEmailConfig}
                  disabled={saveStatus === 'saving'}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {saveStatus === 'saving' ? 'Saving...' : 
                   saveStatus === 'success' ? '✓ Saved' : 
                   saveStatus === 'error' ? 'Error - Try Again' : 
                   'Save Configuration'}
                </button>
              </div>
            </Card>

            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-6">Test Email Configuration</h2>
              
              <div className="flex space-x-4">
                <input
                  type="email"
                  value={testEmail}
                  onChange={(e) => setTestEmail(e.target.value)}
                  placeholder="Enter email address to test"
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  onClick={testEmailConfiguration}
                  disabled={testStatus === 'sending'}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  {testStatus === 'sending' ? 'Sending...' : 'Send Test Email'}
                </button>
              </div>
              
              {testStatus && testStatus !== 'sending' && (
                <div className={`mt-4 p-4 rounded-lg ${
                  testStatus === 'success' ? 'bg-green-100 text-green-800' :
                  testStatus.startsWith('error') ? 'bg-red-100 text-red-800' :
                  'bg-blue-100 text-blue-800'
                }`}>
                  {testStatus === 'success' ? '✓ Test email sent successfully!' : testStatus}
                </div>
              )}
            </Card>

            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-4">📚 Email Setup Guide</h2>
              <div className="space-y-4 text-sm text-gray-600">
                <div>
                  <h3 className="font-semibold text-gray-900">Gmail Setup:</h3>
                  <ol className="list-decimal list-inside space-y-1 mt-2">
                    <li>Enable 2-factor authentication in your Google account</li>
                    <li>Generate an App Password: Google Account → Security → 2-Step Verification → App passwords</li>
                    <li>Use smtp.gmail.com as host, port 587</li>
                    <li>Use your Gmail address as username</li>
                    <li>Use the generated App Password (not your regular password)</li>
                  </ol>
                </div>
                
                <div>
                  <h3 className="font-semibold text-gray-900">Other Providers:</h3>
                  <ul className="list-disc list-inside space-y-1 mt-2">
                    <li><strong>Outlook:</strong> smtp-mail.outlook.com, port 587</li>
                    <li><strong>Yahoo:</strong> smtp.mail.yahoo.com, port 587</li>
                    <li><strong>SendGrid:</strong> smtp.sendgrid.net, port 587</li>
                  </ul>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Sheets Integration Tab */}
        {activeTab === 'sheets' && (
          <SheetIntegrationDashboard />
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <WGPAnalyticsDashboard />
        )}
      </div>
    </div>
  );
};

export default AdminPage;