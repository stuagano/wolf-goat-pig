import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { useTheme } from '../../theme/Provider';

const LogoutButton = ({ style = {} }) => {
  const { logout, isAuthenticated } = useAuth0();
  const theme = useTheme();

  if (!isAuthenticated) {
    return null;
  }

  const buttonStyle = {
    ...theme.buttonStyle,
    background: 'transparent',
    color: 'white',
    border: '2px solid white',
    padding: '8px 16px',
    borderRadius: '6px',
    cursor: 'pointer',
    fontWeight: '600',
    transition: 'all 0.2s',
    ...style
  };

  return (
    <button 
      style={buttonStyle}
      onClick={() => logout({ 
        logoutParams: {
          returnTo: window.location.origin 
        }
      })}
      onMouseOver={(e) => {
        e.target.style.background = 'white';
        e.target.style.color = theme.colors.primary;
      }}
      onMouseOut={(e) => {
        e.target.style.background = 'transparent';
        e.target.style.color = 'white';
      }}
    >
      🚪 Log Out
    </button>
  );
};

export default LogoutButton;