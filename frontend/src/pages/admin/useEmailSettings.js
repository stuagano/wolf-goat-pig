import { useState } from 'react';
import { apiConfig } from '../../config/api.config';

const API_URL = apiConfig.baseUrl;

// Email settings state and API calls for the admin Email tab (SMTP + OAuth2).
// State lives here, owned by AdminPage, so it survives switching tabs.
export function useEmailSettings(authenticatedFetch) {
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

  const fetchEmailConfig = async () => {
    try {
      const response = await authenticatedFetch(`${API_URL}/admin/email-config`);
      
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
      const response = await authenticatedFetch(`${API_URL}/admin/email-config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
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
      const response = await authenticatedFetch(`${API_URL}/admin/test-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
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
      const response = await authenticatedFetch(`${API_URL}/admin/oauth2-status`);
      
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

      const response = await authenticatedFetch(`${API_URL}/admin/upload-credentials`, {
        method: 'POST',
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
      const response = await authenticatedFetch(`${API_URL}/admin/oauth2-authorize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
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
      const response = await authenticatedFetch(`${API_URL}/admin/oauth2-test-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
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

  return {
    emailConfig,
    testEmail,
    setTestEmail,
    saveStatus,
    testStatus,
    emailMethod,
    setEmailMethod,
    oauth2Status,
    oauth2Loading,
    credentialsFile,
    setCredentialsFile,
    uploadStatus,
    fetchEmailConfig,
    handleEmailConfigChange,
    saveEmailConfig,
    testEmailConfiguration,
    fetchOAuth2Status,
    uploadCredentialsFile,
    startOAuth2Flow,
    testOAuth2Email,
  };
}
