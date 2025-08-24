import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { useTheme } from '../../theme/Provider';

const LoginButton = ({ style = {} }) => {
  const { loginWithRedirect, isAuthenticated } = useAuth0();
  const theme = useTheme();

  if (isAuthenticated) {
    return null;
  }

  const buttonStyle = {
    ...theme.buttonStyle,
    background: theme.colors.primary,
    color: 'white',
    border: 'none',
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
      onClick={() => loginWithRedirect()}
      onMouseOver={(e) => e.target.style.opacity = '0.9'}
      onMouseOut={(e) => e.target.style.opacity = '1'}
    >
      🔐 Log In
    </button>
  );
};

export default LoginButton;