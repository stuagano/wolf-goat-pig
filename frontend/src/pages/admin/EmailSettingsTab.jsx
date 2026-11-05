import React from 'react';
import { Card } from '../../components/ui';
import OAuth2EmailSettings from './OAuth2EmailSettings';
import SmtpEmailSettings from './SmtpEmailSettings';
import EmailSetupGuide from './EmailSetupGuide';

const EmailSettingsTab = ({ email }) => {
  const { emailMethod, setEmailMethod } = email;

  return (
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
      {emailMethod === 'oauth2' && <OAuth2EmailSettings email={email} />}

      {/* SMTP Configuration */}
      {emailMethod === 'smtp' && <SmtpEmailSettings email={email} />}

      {/* Setup Guide */}
      <EmailSetupGuide emailMethod={emailMethod} />
    </div>
  );
};

export default EmailSettingsTab;
