import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { useTheme } from '../../theme/Provider';

const Profile = ({ style = {} }) => {
  const { user, isAuthenticated, isLoading } = useAuth0();
  const theme = useTheme();

  if (isLoading) {
    return (
      <div style={{ color: 'white', padding: '8px 16px', ...style }}>
        Loading...
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const profileStyle = {
    display: 'flex',
    alignItems: 'center',
    color: 'white',
    padding: '8px 16px',
    borderRadius: '6px',
    background: 'rgba(255, 255, 255, 0.1)',
    ...style
  };

  const avatarStyle = {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    marginRight: '12px',
    border: '2px solid white'
  };

  return (
    <div style={profileStyle}>
      {user?.picture && (
        <img 
          src={user.picture} 
          alt={user.name || 'User'} 
          style={avatarStyle}
        />
      )}
      <div>
        <div style={{ fontWeight: '600', fontSize: '14px' }}>
          {user?.name || 'User'}
        </div>
        <div style={{ fontSize: '12px', opacity: 0.8 }}>
          {user?.email}
        </div>
      </div>
    </div>
  );
};

export default Profile;