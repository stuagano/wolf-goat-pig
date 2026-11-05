import React from 'react';
import { Card } from '../../components/ui';

const OAuth2EmailSettings = ({ email }) => {
  const {
    oauth2Status,
    setCredentialsFile,
    uploadCredentialsFile,
    credentialsFile,
    uploadStatus,
    emailConfig,
    handleEmailConfigChange,
    startOAuth2Flow,
    oauth2Loading,
    testEmail,
    setTestEmail,
    testOAuth2Email,
    testStatus,
  } = email;

  return (
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
  );
};

export default OAuth2EmailSettings;
