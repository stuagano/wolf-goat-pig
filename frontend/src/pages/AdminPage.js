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
  
  // OAuth2 specific state
  const [emailMethod, setEmailMethod] = useState('oauth2'); // 'smtp' or 'oauth2'
  const [oauth2Status, setOauth2Status] = useState(null);
  const [oauth2Loading, setOauth2Loading] = useState(false);
  const [credentialsFile, setCredentialsFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');

  // Check admin access
  useEffect(() => {
    checkAdminAccess();
    if (activeTab === 'email') {
      if (emailMethod === 'smtp') {
        fetchEmailConfig();
      } else {
        fetchOAuth2Status();
      }
    }
  }, [activeTab, emailMethod]);

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

  // OAuth2 functions
  const fetchOAuth2Status = async () => {
    try {
      const response = await fetch(`${API_URL}/admin/oauth2-status`, {
        headers: {
          'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setOauth2Status(data.status);
      }
    } catch (error) {
      console.error('Error fetching OAuth2 status:', error);
    }
  };

  const uploadCredentialsFile = async () => {
    if (!credentialsFile) {
      setUploadStatus('Please select a credentials file');
      return;
    }

    setUploadStatus('uploading');
    try {
      const formData = new FormData();
      formData.append('file', credentialsFile);

      const response = await fetch(`${API_URL}/admin/upload-credentials`, {
        method: 'POST',
        headers: {
          'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com'
        },
        body: formData
      });

      if (response.ok) {
        setUploadStatus('success');
        fetchOAuth2Status(); // Refresh status
        setTimeout(() => setUploadStatus(''), 3000);
      } else {
        const error = await response.text();
        setUploadStatus(`error: ${error}`);
      }
    } catch (error) {
      console.error('Error uploading credentials:', error);
      setUploadStatus('error: ' + error.message);
    }
  };

  const startOAuth2Flow = async () => {
    setOauth2Loading(true);
    try {
      const response = await fetch(`${API_URL}/admin/oauth2-authorize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com'
        },
        body: JSON.stringify({
          from_email: emailConfig.from_email,
          from_name: emailConfig.from_name
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        // Listen for OAuth success message from popup
        const handleMessage = (event) => {
          if (event.data && event.data.type === 'oauth2-success') {
            window.removeEventListener('message', handleMessage);
            setOauth2Loading(false);
            fetchOAuth2Status();
            setTestStatus('OAuth2 authorization completed successfully!');
            setTimeout(() => setTestStatus(''), 3000);
          }
        };
        window.addEventListener('message', handleMessage);
        
        // Open OAuth2 URL in new window
        window.open(data.auth_url, 'oauth2', 'width=600,height=600');
        
        // Poll for completion as backup
        const pollForCompletion = setInterval(() => {
          fetchOAuth2Status();
          if (oauth2Status?.configured) {
            clearInterval(pollForCompletion);
            setOauth2Loading(false);
            window.removeEventListener('message', handleMessage);
          }
        }, 3000);
        
        // Stop polling after 2 minutes
        setTimeout(() => {
          clearInterval(pollForCompletion);
          setOauth2Loading(false);
          window.removeEventListener('message', handleMessage);
        }, 120000);
      } else {
        const error = await response.text();
        setTestStatus(`OAuth2 Error: ${error}`);
        setOauth2Loading(false);
      }
    } catch (error) {
      console.error('Error starting OAuth2 flow:', error);
      setTestStatus('OAuth2 Error: ' + error.message);
      setOauth2Loading(false);
    }
  };

  const testOAuth2Email = async () => {
    if (!testEmail) {
      setTestStatus('Please enter a test email address');
      return;
    }

    setTestStatus('sending');
    try {
      const response = await fetch(`${API_URL}/admin/oauth2-test-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Email': localStorage.getItem('userEmail') || 'stuagano@gmail.com'
        },
        body: JSON.stringify({ 
          test_email: testEmail
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
      console.error('Error testing OAuth2 email:', error);
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
            {/* Email Method Selection */}
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-6">Email Configuration Method</h2>
              <div className="flex space-x-4 mb-6">
                <button
                  onClick={() => setEmailMethod('oauth2')}
                  className={`flex-1 p-4 rounded-lg border-2 transition-colors ${
                    emailMethod === 'oauth2'
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <div className="text-center">
                    <h3 className="font-semibold text-lg">OAuth2 (Recommended)</h3>
                    <p className="text-sm text-gray-600 mt-2">
                      More secure, no passwords needed. Works with Gmail's latest security requirements.
                    </p>
                    <div className="mt-2">
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        ✓ 2024 Compatible
                      </span>
                    </div>
                  </div>
                </button>
                
                <button
                  onClick={() => setEmailMethod('smtp')}
                  className={`flex-1 p-4 rounded-lg border-2 transition-colors ${
                    emailMethod === 'smtp'
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <div className="text-center">
                    <h3 className="font-semibold text-lg">SMTP with App Password</h3>
                    <p className="text-sm text-gray-600 mt-2">
                      Traditional method using SMTP with app-specific passwords.
                    </p>
                    <div className="mt-2">
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                        ⚠ May be limited
                      </span>
                    </div>
                  </div>
                </button>
              </div>
            </Card>

            {/* OAuth2 Configuration */}
            {emailMethod === 'oauth2' && (
              <>
                <Card className="p-6">
                  <h2 className="text-xl font-semibold mb-6">OAuth2 Gmail Configuration</h2>
                  
                  {/* Status Display */}
                  {oauth2Status && (
                    <div className="mb-6 p-4 rounded-lg bg-gray-50">
                      <h3 className="font-semibold mb-3">Configuration Status</h3>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium">OAuth2 Configured:</span>
                          <span className={`ml-2 ${oauth2Status.configured ? 'text-green-600' : 'text-red-600'}`}>
                            {oauth2Status.configured ? '✓ Yes' : '✗ No'}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium">Credentials File:</span>
                          <span className={`ml-2 ${oauth2Status.credentials_file_exists ? 'text-green-600' : 'text-red-600'}`}>
                            {oauth2Status.credentials_file_exists ? '✓ Uploaded' : '✗ Missing'}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium">Token Valid:</span>
                          <span className={`ml-2 ${oauth2Status.credentials_valid ? 'text-green-600' : 'text-red-600'}`}>
                            {oauth2Status.credentials_valid ? '✓ Valid' : '✗ Invalid'}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium">From Email:</span>
                          <span className="ml-2">{oauth2Status.from_email || 'Not set'}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Step 1: Upload Credentials */}
                  <div className="mb-6">
                    <h3 className="font-semibold mb-3">Step 1: Upload Gmail Credentials File</h3>
                    <div className="space-y-4">
                      <input
                        type="file"
                        accept=".json"
                        onChange={(e) => setCredentialsFile(e.target.files[0])}
                        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                      />
                      <button
                        onClick={uploadCredentialsFile}
                        disabled={!credentialsFile || uploadStatus === 'uploading'}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                      >
                        {uploadStatus === 'uploading' ? 'Uploading...' : 'Upload Credentials'}
                      </button>
                      {uploadStatus && uploadStatus !== 'uploading' && (
                        <div className={`text-sm ${
                          uploadStatus === 'success' ? 'text-green-600' : 
                          uploadStatus.startsWith('error') ? 'text-red-600' : 'text-blue-600'
                        }`}>
                          {uploadStatus === 'success' ? '✓ Credentials uploaded successfully!' : uploadStatus}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Step 2: Basic Settings */}
                  <div className="mb-6">
                    <h3 className="font-semibold mb-3">Step 2: Email Settings</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">From Email</label>
                        <input
                          type="email"
                          value={emailConfig.from_email}
                          onChange={(e) => handleEmailConfigChange('from_email', e.target.value)}
                          placeholder="your-email@gmail.com"
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">From Name</label>
                        <input
                          type="text"
                          value={emailConfig.from_name}
                          onChange={(e) => handleEmailConfigChange('from_name', e.target.value)}
                          placeholder="Wolf Goat Pig Admin"
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Step 3: OAuth2 Authorization */}
                  <div className="mb-6">
                    <h3 className="font-semibold mb-3">Step 3: Complete OAuth2 Authorization</h3>
                    <button
                      onClick={startOAuth2Flow}
                      disabled={!oauth2Status?.credentials_file_exists || oauth2Loading}
                      className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                    >
                      {oauth2Loading ? 'Authorizing...' : oauth2Status?.configured ? 'Re-authorize' : 'Start OAuth2 Setup'}
                    </button>
                    <p className="text-sm text-gray-600 mt-2">
                      This will open a new window for Google authorization. 
                      {oauth2Loading && ' Please complete the authorization in the popup window...'}
                    </p>
                  </div>
                </Card>

                {/* OAuth2 Test Email */}
                <Card className="p-6">
                  <h2 className="text-xl font-semibold mb-6">Test OAuth2 Email</h2>
                  
                  <div className="flex space-x-4">
                    <input
                      type="email"
                      value={testEmail}
                      onChange={(e) => setTestEmail(e.target.value)}
                      placeholder="Enter email address to test"
                      className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <button
                      onClick={testOAuth2Email}
                      disabled={!oauth2Status?.configured || testStatus === 'sending'}
                      className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                    >
                      {testStatus === 'sending' ? 'Sending...' : 'Send OAuth2 Test'}
                    </button>
                  </div>
                  
                  {testStatus && testStatus !== 'sending' && (
                    <div className={`mt-4 p-4 rounded-lg ${
                      testStatus === 'success' ? 'bg-green-100 text-green-800' :
                      testStatus.startsWith('error') || testStatus.startsWith('OAuth2 Error') ? 'bg-red-100 text-red-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {testStatus === 'success' ? '✓ OAuth2 test email sent successfully!' : testStatus}
                    </div>
                  )}
                </Card>
              </>
            )}

            {/* SMTP Configuration */}
            {emailMethod === 'smtp' && (
              <>
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
              </>
            )}

            {/* Setup Guide */}
            <Card className="p-6">
              <h2 className="text-xl font-semibold mb-4">📚 Email Setup Guide</h2>
              
              {emailMethod === 'oauth2' ? (
                <div className="space-y-6 text-sm text-gray-600">
                  <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                    <h3 className="font-semibold text-blue-900 mb-2">🚀 OAuth2 Setup (Recommended)</h3>
                    <p className="text-blue-800">
                      OAuth2 is the most secure and future-proof method for sending emails via Gmail. 
                      Follow these steps to set it up:
                    </p>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-gray-900">Step 1: Create Google Cloud Project & Enable Gmail API</h3>
                    <ol className="list-decimal list-inside space-y-2 mt-2 ml-4">
                      <li>Go to <a href="https://console.cloud.google.com/" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">Google Cloud Console</a></li>
                      <li>Create a new project or select an existing one</li>
                      <li>Enable the Gmail API:
                        <ul className="list-disc list-inside ml-4 mt-1">
                          <li>Go to APIs & Services → Library</li>
                          <li>Search for "Gmail API" and click on it</li>
                          <li>Click "Enable"</li>
                        </ul>
                      </li>
                    </ol>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-gray-900">Step 2: Create OAuth2 Credentials</h3>
                    <ol className="list-decimal list-inside space-y-2 mt-2 ml-4">
                      <li>Go to APIs & Services → Credentials</li>
                      <li>Click "Create Credentials" → "OAuth client ID"</li>
                      <li>If prompted, configure the OAuth consent screen:
                        <ul className="list-disc list-inside ml-4 mt-1">
                          <li>Choose "External" user type</li>
                          <li>Fill in app name: "Wolf Goat Pig"</li>
                          <li>Add your email as a developer contact</li>
                          <li>Add scopes: ../auth/gmail.send</li>
                          <li>Add your email as a test user</li>
                        </ul>
                      </li>
                      <li>For application type, choose "Desktop application"</li>
                      <li>Give it a name like "Wolf Goat Pig Email"</li>
                      <li>Click "Create"</li>
                      <li>Download the JSON credentials file</li>
                    </ol>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-gray-900">Step 3: Upload & Configure</h3>
                    <ol className="list-decimal list-inside space-y-1 mt-2 ml-4">
                      <li>Upload the downloaded JSON file using the form above</li>
                      <li>Set your "From Email" and "From Name"</li>
                      <li>Click "Start OAuth2 Setup" and complete authorization</li>
                      <li>Send a test email to verify everything works</li>
                    </ol>
                  </div>
                  
                  <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                    <h4 className="font-semibold text-green-900 mb-2">✅ Benefits of OAuth2:</h4>
                    <ul className="list-disc list-inside text-green-800 space-y-1">
                      <li>More secure than passwords</li>
                      <li>Tokens automatically refresh</li>
                      <li>Complies with Google's latest security requirements</li>
                      <li>No need to manage app passwords</li>
                      <li>Better error handling and monitoring</li>
                    </ul>
                  </div>
                </div>
              ) : (
                <div className="space-y-4 text-sm text-gray-600">
                  <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                    <h4 className="font-semibold text-yellow-900 mb-2">⚠️ SMTP with App Password</h4>
                    <p className="text-yellow-800">
                      Note: Google has deprecated "Less Secure App Access" and may limit SMTP access in the future. 
                      OAuth2 is recommended for new setups.
                    </p>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold text-gray-900">Gmail SMTP Setup:</h3>
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
              )}
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