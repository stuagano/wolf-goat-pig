import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth0 } from '@auth0/auth0-react';
import { usePlayerProfile } from '../hooks/usePlayerProfile';
import { useAuthenticatedFetch } from '../hooks/useAuthenticatedFetch';
import { Card } from '../components/ui';
import SheetIntegrationDashboard from '../components/integration/SheetIntegrationDashboard';
import WGPAnalyticsDashboard from '../components/analytics/WGPAnalyticsDashboard';
import GHINIntegration from '../components/integration/GHINIntegration';
import FoursomesManager from './admin/FoursomesManager';
import DatabaseManager from './admin/DatabaseManager';
import AccountLinkingManager from './admin/AccountLinkingManager';
import AdminManager from './admin/AdminManager';
import FeatureToggles from './admin/FeatureToggles';
import AdminTabNav from './admin/AdminTabNav';
import EmailSettingsTab from './admin/EmailSettingsTab';
import BannerSettingsTab from './admin/BannerSettingsTab';
import { useEmailSettings } from './admin/useEmailSettings';
import { useBannerSettings } from './admin/useBannerSettings';

const AdminPage = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth0();
  const { isAdmin: serverIsAdmin, loading: profileLoading } = usePlayerProfile();
  const authenticatedFetch = useAuthenticatedFetch();
  const [activeTab, setActiveTab] = useState('email');
  // Verified /players/me role is authoritative; never grant from browser identity.
  const loading = authLoading || (isAuthenticated && profileLoading);
  const isAdmin = !loading && serverIsAdmin === true;

  const email = useEmailSettings(authenticatedFetch);
  const { emailMethod, fetchEmailConfig, fetchOAuth2Status } = email;
  const banner = useBannerSettings(authenticatedFetch);
  const { fetchBannerConfig } = banner;

  useEffect(() => {
    if (authLoading) return;
    // Wait for the profile fetch before loading admin data, unless the user
    // isn't authenticated (no profile will ever load).
    if (isAuthenticated && profileLoading) return;
    if (!isAdmin) return;
    if (activeTab === 'email') {
      if (emailMethod === 'smtp') {
        fetchEmailConfig();
      } else {
        fetchOAuth2Status();
      }
    } else if (activeTab === 'banners') {
      fetchBannerConfig();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, emailMethod, authLoading, user, isAuthenticated, isAdmin, serverIsAdmin, profileLoading]);

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
            {!isAuthenticated ? (
              <p className="text-gray-600 mb-6" data-testid="denied-signed-out">
                You're not signed in. Please sign in with an admin account to access the dashboard.
              </p>
            ) : (
              <p className="text-gray-600 mb-6" data-testid="denied-not-admin">
                You're signed in{user?.email ? <> as <strong>{user.email}</strong></> : null}, but this
                account is a normal user. Super-admin access is granted server-side
                by verified Auth0 login email.
              </p>
            )}
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
        <AdminTabNav activeTab={activeTab} setActiveTab={setActiveTab} />

        {/* Email Settings Tab */}
        {activeTab === 'email' && <EmailSettingsTab email={email} />}

        {/* Sheets Integration Tab */}
        {activeTab === 'sheets' && (
          <SheetIntegrationDashboard />
        )}

        {/* GHIN Integration Tab */}
        {activeTab === 'ghin' && (
          <GHINIntegration />
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <WGPAnalyticsDashboard />
        )}

        {/* Database Tab */}
        {activeTab === 'database' && (
          <DatabaseManager />
        )}

        {/* Foursomes Tab */}
        {activeTab === 'foursomes' && (
          <FoursomesManager />
        )}

        {/* Toggles Tab */}
        {activeTab === 'toggles' && <FeatureToggles />}

        {/* Players Tab */}
        {activeTab === 'players' && <AccountLinkingManager />}

        {/* Admins Tab */}
        {activeTab === 'admins' && <AdminManager />}

        {/* Banners Tab */}
        {activeTab === 'banners' && <BannerSettingsTab banner={banner} />}
      </div>
    </div>
  );
};

export default AdminPage;
