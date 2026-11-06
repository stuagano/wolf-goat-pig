import React from 'react';
import { Card } from '../../components/ui';

const EmailSetupGuide = ({ emailMethod }) => (
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
);

export default EmailSetupGuide;
