import React from 'react';
import { useSheetSync } from '../context';
import { Card } from './ui';

const GoogleSheetsLiveSync = () => {
  const {
    sheetUrl,
    setSheetUrl,
    syncStatus,
    lastSync,
    syncInterval,
    setSyncInterval,
    autoSync,
    setAutoSync,
    syncData,
    error,
    performLiveSync,
  } = useSheetSync();





  const getStatusColor = () => {
    switch (syncStatus) {
      case 'connecting': return 'text-blue-600';
      case 'syncing': return 'text-yellow-600';
      case 'success': return 'text-green-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = () => {
    switch (syncStatus) {
      case 'connecting': return '🔗';
      case 'syncing': return '🔄';
      case 'success': return '✅';
      case 'error': return '❌';
      default: return '⚪';
    }
  };

  const getStatusText = () => {
    switch (syncStatus) {
      case 'connecting': return 'Connecting to Google Sheets...';
      case 'syncing': return 'Syncing data...';
      case 'success': return 'Sync successful!';
      case 'error': return `Error: ${error}`;
      default: return 'Ready to sync';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">🔄 Live Google Sheets Sync</h1>
          <p className="text-gray-600">Connect your Google Sheet for real-time data synchronization</p>
        </div>

        {/* Configuration */}
        <Card className="p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Sheet Configuration</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Google Sheets URL
              </label>
              <input
                type="text"
                value={sheetUrl}
                onChange={(e) => setSheetUrl(e.target.value)}
                placeholder="https://docs.google.com/spreadsheets/d/your-sheet-id/edit..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Paste your Google Sheets URL here (make sure it's publicly viewable)
              </p>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="autoSync"
                  checked={autoSync}
                  onChange={(e) => setAutoSync(e.target.checked)}
                  className="mr-2"
                />
                <label htmlFor="autoSync" className="text-sm text-gray-700">
                  Enable Auto Sync
                </label>
              </div>
              
              {autoSync && (
                <div className="flex items-center space-x-2">
                  <label className="text-sm text-gray-700">Every</label>
                  <select
                    value={syncInterval}
                    onChange={(e) => setSyncInterval(Number(e.target.value))}
                    className="px-2 py-1 border border-gray-300 rounded text-sm"
                  >
                    <option value={10}>10 seconds</option>
                    <option value={30}>30 seconds</option>
                    <option value={60}>1 minute</option>
                    <option value={300}>5 minutes</option>
                  </select>
                </div>
              )}
            </div>
          </div>
        </Card>

        {/* Sync Status */}
        <Card className="p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold mb-2">Sync Status</h2>
              <div className={`flex items-center space-x-2 ${getStatusColor()}`}>
                <span className="text-lg">{getStatusIcon()}</span>
                <span className="font-medium">{getStatusText()}</span>
              </div>
              {lastSync && (
                <p className="text-sm text-gray-500 mt-1">
                  Last sync: {lastSync.toLocaleString()}
                </p>
              )}
            </div>
            
            <button
              onClick={() => performLiveSync()}
              disabled={!sheetUrl || syncStatus === 'connecting' || syncStatus === 'syncing'}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <span>🔄</span>
              <span>Sync Now</span>
            </button>
          </div>
        </Card>

        {/* Preview Data */}
        {syncData.length > 0 && (
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Latest Synced Data</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {Object.keys(syncData[0] || {}).map(key => (
                      <th key={key} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {syncData.slice(0, 5).map((row, index) => (
                    <tr key={index}>
                      {Object.values(row).map((value, i) => (
                        <td key={i} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {value}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {syncData.length > 5 && (
              <p className="text-sm text-gray-500 mt-2">
                Showing first 5 rows of {syncData.length} total records
              </p>
            )}
          </Card>
        )}

        {/* Instructions */}
        <Card className="p-6 mt-6 bg-blue-50">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">📋 Setup Instructions</h3>
          <ol className="space-y-2 text-sm text-blue-800">
            <li><strong>1.</strong> Make sure your Google Sheet is publicly viewable (Share → "Anyone with the link can view")</li>
            <li><strong>2.</strong> Copy the full Google Sheets URL and paste it above</li>
            <li><strong>3.</strong> Click "Sync Now" to test the connection</li>
            <li><strong>4.</strong> Enable Auto Sync for continuous updates</li>
            <li><strong>5.</strong> Check the leaderboard to see your updated data!</li>
          </ol>
        </Card>
      </div>
    </div>
  );
};

export default GoogleSheetsLiveSync;