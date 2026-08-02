import { useCallback } from "react";
import { useAuth0 } from "@auth0/auth0-react";

import { acquireAccessToken, apiTokenOptions } from "../services/authToken";

export const useAuthenticatedFetch = () => {
  const { getAccessTokenSilently } = useAuth0();

  return useCallback(
    async (url, options = {}) => {
      const token = await acquireAccessToken(getAccessTokenSilently, apiTokenOptions);
      return fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Bearer ${token}`,
        },
      });
    },
    [getAccessTokenSilently],
  );
};

export default useAuthenticatedFetch;
