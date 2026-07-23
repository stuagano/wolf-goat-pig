import { useCallback } from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { acquireAccessToken, isRecoverableAuthError } from "../services/authToken";

/**
 * Provides a token getter that recovers from the "Missing Refresh Token" error
 * (see services/authToken.js), plus a `reauthenticate` helper for the terminal
 * case where even the silent fallback fails and the user must sign in again.
 *
 * Usage:
 *   const { getToken, reauthenticate } = useAccessToken();
 *   const token = await getToken();               // resilient
 *   isRecoverableAuthError(err) && reauthenticate();
 */
export const useAccessToken = () => {
  const { getAccessTokenSilently, loginWithRedirect } = useAuth0();

  const getToken = useCallback(
    (options) => acquireAccessToken(getAccessTokenSilently, options),
    [getAccessTokenSilently],
  );

  const reauthenticate = useCallback(
    () =>
      loginWithRedirect({
        // Send the user back to the page they were on after re-login.
        appState: { returnTo: `${window.location.pathname}${window.location.search}` },
      }),
    [loginWithRedirect],
  );

  return { getToken, reauthenticate, isRecoverableAuthError };
};

export default useAccessToken;
