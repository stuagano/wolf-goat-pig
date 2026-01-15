import React, { useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import PlayerProfileManager from '../components/PlayerProfileManager';
import PlayerStatistics from '../components/PlayerStatistics';
import { Card } from '../components/ui';

/**
 * PlayerDashboardPage - Main page for player profile management and personal analytics
 */
const PlayerDashboardPage = () => {
  const { isAuthenticated, loginWithRedirect } = useAuth0();
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [activeTab, setActiveTab] = useState('profiles'); // 'profiles' or 'stats'

  const handleProfileSelect = (profile) => {
    setSelectedProfile(profile);
    // When a profile is selected, we can also show their stats
    if (profile) {
      setActiveTab('stats');
    }
  };

  if (!isAuthenticated) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        textAlign: 'center',
        padding: '40px 20px'
      }}>
        <Card className="p-8 max-w-md">
          <h2 className="text-2xl font-bold mb-4">👤 Player Dashboard</h2>
          <p className="text-gray-600 mb-6">
            Log in to manage your player profiles, track your handicap, and view your career statistics.
          </p>
          <button
            onClick={() => loginWithRedirect()}
            className="w-full py-3 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 transition-colors"
          >
            Log In to Continue
          </button>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">👤 Player Dashboard</h1>
        <p className="text-gray-600">Manage your profiles and analyze your performance.</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200 mb-8">
        <button
          onClick={() => setActiveTab('profiles')}
          className={`px-6 py-3 font-medium text-sm transition-colors border-b-2 ${
            activeTab === 'profiles'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          Player Profiles
        </button>
        <button
          onClick={() => setActiveTab('stats')}
          className={`px-6 py-3 font-medium text-sm transition-colors border-b-2 ${
            activeTab === 'stats'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
          }`}
        >
          Personal Statistics
        </button>
      </div>

      {/* Tab Content */}
      <div className="min-h-[500px]">
        {activeTab === 'profiles' && (
          <PlayerProfileManager 
            onProfileSelect={handleProfileSelect}
            selectedProfile={selectedProfile}
          />
        )}

        {activeTab === 'stats' && (
          <div>
            {!selectedProfile ? (
              <Card className="p-12 text-center">
                <div className="text-5xl mb-4">📊</div>
                <h3 className="text-xl font-bold mb-2">No Profile Selected</h3>
                <p className="text-gray-600 mb-6">
                  Select a player profile to view their detailed performance statistics and analytics.
                </p>
                <button
                  onClick={() => setActiveTab('profiles')}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Go to Profiles
                </button>
              </Card>
            ) : (
              <PlayerStatistics 
                playerId={selectedProfile.id}
                playerName={selectedProfile.name}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PlayerDashboardPage;
