import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { useTheme } from '../theme/Provider';
import { usePlayerProfile } from '../hooks/usePlayerProfile';
import BadgeGallery from '../components/game/BadgeGallery';

const BadgesPage = () => {
  const { isAuthenticated, loginWithRedirect } = useAuth0();
  const theme = useTheme();
  const { profile, loading } = usePlayerProfile();

  if (!isAuthenticated) {
    return (
      <div style={{
        maxWidth: 600,
        margin: '40px auto',
        padding: '40px 20px',
        textAlign: 'center',
        color: theme.isDark ? '#fff' : '#1f2937'
      }}>
        <h2>Badges & Achievements</h2>
        <p style={{ marginBottom: 20, color: theme.isDark ? '#9ca3af' : '#6b7280' }}>
          Log in to view your badge collection and track your achievements.
        </p>
        <button
          onClick={() => loginWithRedirect()}
          style={{
            background: theme.colors.primary,
            color: '#fff',
            border: 'none',
            borderRadius: 8,
            padding: '12px 24px',
            fontSize: 16,
            fontWeight: 600,
            cursor: 'pointer'
          }}
        >
          Log In
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{
        maxWidth: 600,
        margin: '40px auto',
        padding: '40px 20px',
        textAlign: 'center',
        color: theme.isDark ? '#9ca3af' : '#6b7280'
      }}>
        Loading...
      </div>
    );
  }

  if (!profile?.id) {
    return (
      <div style={{
        maxWidth: 600,
        margin: '40px auto',
        padding: '40px 20px',
        textAlign: 'center',
        color: theme.isDark ? '#fff' : '#1f2937'
      }}>
        <h2>Badges & Achievements</h2>
        <p style={{ color: theme.isDark ? '#9ca3af' : '#6b7280' }}>
          Player profile not found. Please complete your account setup first.
        </p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '20px' }}>
      <BadgeGallery playerId={profile.id} />
    </div>
  );
};

export default BadgesPage;
