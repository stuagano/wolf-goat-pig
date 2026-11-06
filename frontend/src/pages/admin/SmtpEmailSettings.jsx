import React from 'react';
import { Card } from '../../components/ui';

const SmtpEmailSettings = ({ email }) => {
  const {
    emailConfig,
    handleEmailConfigChange,
    saveEmailConfig,
    saveStatus,
    testEmail,
    setTestEmail,
    testEmailConfiguration,
    testStatus,
  } = email;

  return (
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
  );
};

export default SmtpEmailSettings;
