import { useAuth0 } from '@auth0/auth0-react';

/**
 * Custom hook that wraps Auth0's useAuth0 hook with additional utilities
 * for the Wolf Goat Pig application.
 */
export const useAuth = () => {
  const auth0 = useAuth0();
  
  return {
    ...auth0,
    // Additional auth utilities can be added here
    isLoggedIn: auth0.isAuthenticated && !auth0.isLoading,
    userName: auth0.user?.name || auth0.user?.email || 'Player',
    userEmail: auth0.user?.email,
    userPicture: auth0.user?.picture
  };
};

export default useAuth;